"""
World Cup 2026 Prediction System - FastAPI Server

Provides REST API for:
- Dashboard (upcoming matches with predictions)
- Group standings
- Knockout bracket
- Match details with predictions, players, H2H, and odds
- Backtest results
- Data refresh
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

# ─────────────────────────────────────────────
# Load .env file (auto-detect project root)
# ─────────────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value and key not in os.environ:
                os.environ[key] = value
    print(f"[Server] Loaded environment from {_ENV_FILE}")
elif os.path.exists(os.path.join(_PROJECT_ROOT, ".env.example")):
    print(f"[Server] ⚠ No .env file found. Copy .env.example to .env and add your API keys.")
    print(f"[Server]   cp {_ENV_FILE}.example {_ENV_FILE}")
else:
    print(f"[Server] No .env file found. Set API_FOOTBALL_KEY env var for live data.")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db, full_init, get_all_teams, get_groups_standings,
    get_upcoming_matches as db_get_upcoming_matches,
    get_match_detail as db_get_match_detail,
    get_match_squads,
    insert_match, update_match_result,
)
from predictor import MatchPredictor
from backtester import Backtester
from data_fetcher import DataFetcher
from monte_carlo import MonteCarloSimulator

# ─────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="World Cup 2026 Prediction API",
    description="Real-time prediction system for the 2026 FIFA World Cup",
    version="1.0.0",
)

# CORS - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Global state
# ─────────────────────────────────────────────

predictor = MatchPredictor()
backtester = Backtester()
data_fetcher = DataFetcher()
BACKTEST_RESULTS: Dict = {}
LAST_UPDATED: Optional[str] = None
MATCHES_LOADED: int = 0

# Team code → Chinese name mapping (for recent matches display)
TEAM_ZH: Dict[str, str] = {
    "ARG": "阿根廷", "BRA": "巴西", "FRA": "法国", "ENG": "英格兰",
    "ESP": "西班牙", "GER": "德国", "POR": "葡萄牙", "NED": "荷兰",
    "ITA": "意大利", "BEL": "比利时", "URU": "乌拉圭", "CRO": "克罗地亚",
    "COL": "哥伦比亚", "MEX": "墨西哥", "USA": "美国", "MAR": "摩洛哥",
    "SEN": "塞内加尔", "JPN": "日本", "KOR": "韩国", "IRN": "伊朗",
    "AUS": "澳大利亚", "EGY": "埃及", "GHA": "加纳", "CIV": "科特迪瓦",
    "SRB": "塞尔维亚", "SUI": "瑞士", "DEN": "丹麦", "ECU": "厄瓜多尔",
    "POL": "波兰", "CAN": "加拿大", "KSA": "沙特阿拉伯", "QAT": "卡塔尔",
    "NGA": "尼日利亚", "CRC": "哥斯达黎加", "TUN": "突尼斯", "CMR": "喀麦隆",
    "RSA": "南非", "CZE": "捷克", "BIH": "波黑", "HAI": "海地",
    "SCO": "苏格兰", "PAR": "巴拉圭", "TUR": "土耳其", "CUW": "库拉索",
    "SWE": "瑞典", "NZL": "新西兰", "CPV": "佛得角", "IRQ": "伊拉克",
    "NOR": "挪威", "ALG": "阿尔及利亚", "AUT": "奥地利", "JOR": "约旦",
    "COD": "刚果金", "UZB": "乌兹别克斯坦", "PAN": "巴拿马", "CHN": "中国",
    "UKR": "乌克兰", "RUS": "俄罗斯", "PER": "秘鲁", "VEN": "委内瑞拉",
    "CHI": "智利", "HUN": "匈牙利", "ISR": "以色列", "GRE": "希腊",
    "ROU": "罗马尼亚", "FIN": "芬兰", "ALB": "阿尔巴尼亚", "IRL": "爱尔兰",
    "IDN": "印度尼西亚", "PLE": "巴勒斯坦", "BHR": "巴林", "LBN": "黎巴嫩",
    "SVK": "斯洛伐克", "SVN": "斯洛文尼亚", "WAL": "威尔士", "NIR": "北爱尔兰",
    "MKD": "北马其顿", "MNE": "黑山", "KOS": "科索沃", "GAB": "加蓬",
    "ZIM": "津巴布韦", "BLR": "白俄罗斯", "LUX": "卢森堡", "ZAM": "赞比亚",
    "ANG": "安哥拉", "BFA": "布基纳法索", "MLI": "马里", "MTN": "毛里塔尼亚",
    "NAM": "纳米比亚", "SUD": "苏丹", "TOG": "多哥", "UGA": "乌干达",
}

# ─────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    global LAST_UPDATED, MATCHES_LOADED, BACKTEST_RESULTS

    print("[Server] Initializing database...")
    init_db()
    full_init()

    # Ensure odds data exists (generate from ELO if not present)
    from database import SessionLocal, Odds, Match, Team
    with SessionLocal() as session:
        odds_count = session.query(Odds).count()
        if odds_count == 0:
            from database import _generate_initial_odds
            n_odds = _generate_initial_odds(session)
            print(f"[Server] Generated {n_odds} odds entries from ELO ratings")
        else:
            print(f"[Server] Found {odds_count} existing odds entries")

    # Load teams into predictor
    teams = get_all_teams()
    teams_data = []
    for t in teams:
        teams_data.append({
            "code": t["code"],
            "name": t["name"],
            "name_zh": t["name_zh"],
            "elo_rating": t["elo_rating"],
            "fifa_rank": t["fifa_rank"],
            "recent_form": t.get("recent_form", ""),
            "flag_emoji": t.get("flag_emoji", ""),
        })
    predictor.teams = {t["code"]: t for t in teams_data}
    MATCHES_LOADED = len(teams)

    # Server is ready immediately — run heavy tasks in background
    print(f"[Server] Ready. {MATCHES_LOADED} teams loaded. (Background tasks starting...)")

    async def _background_tasks():
        global LAST_UPDATED, BACKTEST_RESULTS
        # Run backtests in a thread pool to avoid blocking the event loop
        print("[Server] Running backtests in background (thread pool)...")
        try:
            backtester.predictor.teams = predictor.teams
            loop = asyncio.get_event_loop()
            BACKTEST_RESULTS = await loop.run_in_executor(None, backtester.run_all_backtests)
            print("[Server] Backtests completed.")
        except Exception as e:
            print(f"[Server] Backtest error (non-fatal): {e}")
            BACKTEST_RESULTS = {}

        # Refresh data in background
        print("[Server] Fetching latest data in background...")
        try:
            refresh = await asyncio.wait_for(data_fetcher.refresh_data(), timeout=30.0)
            LAST_UPDATED = refresh.get("last_updated", str(datetime.now()))
            print("[Server] Data refresh completed.")
        except asyncio.TimeoutError:
            print("[Server] Data refresh timed out (30s), using local data.")
            LAST_UPDATED = str(datetime.now())
        except Exception as e:
            print(f"[Server] Data fetch error (non-fatal): {e}")
            LAST_UPDATED = str(datetime.now())

        # Start background refresh scheduler
        try:
            await data_fetcher.start_refresh_scheduler()
        except Exception as e:
            print(f"[Server] Refresh scheduler error (non-fatal): {e}")

    asyncio.create_task(_background_tasks())


@app.on_event("shutdown")
async def shutdown_event():
    await data_fetcher.stop_refresh_scheduler()
    await data_fetcher.close()


# ─────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {"service": "World Cup 2026 Prediction API", "version": "1.0.0"}


@app.get("/api/status")
async def api_status():
    """System status endpoint."""
    return {
        "status": "ready",
        "last_updated": LAST_UPDATED or str(datetime.now()),
        "matches_loaded": MATCHES_LOADED,
        "backtest_completed": len(BACKTEST_RESULTS) > 0,
        "api_source": "api-football-v3" if data_fetcher.api_available else "local-json",
        "api_key_configured": bool(os.environ.get("API_FOOTBALL_KEY", "")),
        "football_data_key_configured": bool(os.environ.get("FOOTBALL_DATA_KEY", "")),
        "cache_type": "sqlite",
        "refresh_scheduler_running": data_fetcher._scheduler_running if hasattr(data_fetcher, '_scheduler_running') else False,
    }


@app.get("/api/dashboard")
async def api_dashboard():
    """
    Main dashboard data:
    - Upcoming matches with predictions
    - Recent finished matches
    - When API key is configured, enriches with live fixture data
    """
    try:
        all_teams = get_all_teams()
        teams_dict = {t["code"]: t for t in all_teams}

        # Get upcoming matches from DB
        upcoming = db_get_upcoming_matches(days=7)

        # If API is available, try to enrich with live fixture data (with timeout)
        if data_fetcher.api_available:
            try:
                api_fixtures = await asyncio.wait_for(
                    data_fetcher.fetch_fixtures_from_api(), timeout=10.0
                )
                if api_fixtures:
                    # Update match dates and statuses from API
                    fixture_map = {}
                    for fx in api_fixtures:
                        key = (fx["team1"], fx["team2"])
                        fixture_map[key] = fx
                        # Also try reverse order
                        key_rev = (fx["team2"], fx["team1"])
                        fixture_map[key_rev] = fx

                    for match in upcoming:
                        key = (match["team1"], match["team2"])
                        fx = fixture_map.get(key)
                        if fx:
                            # Update date from API
                            if fx.get("date"):
                                match["date"] = fx["date"]
                            if fx.get("kick_off"):
                                match["kick_off"] = fx["kick_off"]
                            # Update status from API
                            if fx.get("status"):
                                match["status"] = fx["status"]
            except Exception as e:
                print(f"[Server] Dashboard API enrichment error (non-fatal): {e}")

        # Add predictions to upcoming matches (with cached odds if available)
        upcoming_with_pred = []
        for match in upcoming:
            t1_data = teams_dict.get(match["team1"], {
                "code": match["team1"],
                "elo_rating": 1800,
                "fifa_rank": 30,
                "recent_form": "",
            })
            t2_data = teams_dict.get(match["team2"], {
                "code": match["team2"],
                "elo_rating": 1800,
                "fifa_rank": 30,
                "recent_form": "",
            })

            try:
                # Get odds from DB (already generated by _generate_initial_odds or from API cache)
                match_odds_list = match.get("odds", {}).get("bookmakers", []) if isinstance(match.get("odds"), dict) else []

                prediction = predictor.predict_match(
                    t1_data, t2_data,
                    odds_list=match_odds_list if match_odds_list else None,
                )
            except Exception as e:
                prediction = {"error": str(e)}

            match["prediction"] = prediction
            upcoming_with_pred.append(match)

        # Group matches by date for better organization
        matches_by_date: Dict[str, List] = {}
        for m in upcoming_with_pred:
            date = m.get("date", "TBD")
            if date not in matches_by_date:
                matches_by_date[date] = []
            matches_by_date[date].append(m)

        # Recent finished matches (empty for 2026 before tournament)
        recent_finished: List[Dict] = []

        return {
            "upcoming_matches": upcoming_with_pred,
            "upcoming_by_date": matches_by_date,
            "recent_finished": recent_finished,
            "total_upcoming": len(upcoming_with_pred),
            "data_source": "api-football" if data_fetcher.api_available else "local-json",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/groups")
async def api_groups():
    """Real group standings computed from recent matches data."""
    try:
        from database import get_groups_standings, get_all_teams

        teams = get_all_teams()
        groups: Dict[str, List[Dict]] = {}
        for t in teams:
            g = t.get("group_name", "")
            if g not in groups:
                groups[g] = []
            groups[g].append(t)

        # Load recent match results
        import json, os as _os2
        _data_dir = _os2.path.join(_os2.path.dirname(_os2.path.dirname(_os2.path.abspath(__file__))), "data")
        _recent_path = _os2.path.join(_data_dir, "recent_matches.json")
        _recent_db = {}
        if _os2.path.exists(_recent_path):
            _recent_db = json.load(open(_recent_path, "r", encoding="utf-8"))
        # Also load WC history
        _wc_matches = []
        for _y in ["2022", "2018"]:
            _wc_path = _os2.path.join(_data_dir, f"wc{_y}.json")
            if _os2.path.exists(_wc_path):
                _d = json.load(open(_wc_path, "r", encoding="utf-8"))
                _wc_matches.extend(_d.get("group_matches", []) + _d.get("knockout_matches", []))

        result = []
        for g_name, g_teams in sorted(groups.items()):
            stats = []
            for t in g_teams:
                code = t["code"]
                team_matches = list(_recent_db.get(code, []))
                # Add WC matches as additional data
                for _m in _wc_matches:
                    if _m.get("team1") == code or _m.get("team2") == code:
                        _ih = _m["team1"] == code
                        _gf = _m.get("score1", 0) if _ih else _m.get("score2", 0)
                        _ga = _m.get("score2", 0) if _ih else _m.get("score1", 0)
                        _r = "W" if _gf > _ga else "D" if _gf == _ga else "L"
                        team_matches.append({"result": _r, "goals_for": _gf, "goals_against": _ga})
                # Add WC matches as played stats too

                p, w, d, l, gf, ga, pts = 0, 0, 0, 0, 0, 0, 0
                for m in team_matches:
                    p += 1
                    gf += m["goals_for"]
                    ga += m["goals_against"]
                    if m["result"] == "W": w += 1; pts += 3
                    elif m["result"] == "D": d += 1; pts += 1
                    else: l += 1

                stats.append({
                    "code": code,
                    "name": t.get("name", code),
                    "name_zh": TEAM_ZH.get(code, code),
                    "flag_emoji": t.get("flag_emoji", ""),
                    "elo_rating": t.get("elo_rating", 0),
                    "played": p,
                    "won": w, "drawn": d, "lost": l,
                    "goals_for": gf, "goals_against": ga,
                    "goals_diff": gf - ga,
                    "points": pts,
                })

            # Sort: points → GD → GF
            stats.sort(key=lambda x: (-x["points"], -x["goals_diff"], -x["goals_for"]))
            result.append({"group": g_name, "standings": stats})

        return {"groups": result, "total_groups": len(result)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bracket")
async def api_bracket():
    """Knockout bracket structure with current state, predictions, and results.

    2026 World Cup format: 48 teams, 12 groups (A-L).
    Top 2 from each group (24 teams) + 8 best 3rd place teams = 32 teams advance.
    Knockout stages: Round of 32 -> Round of 16 -> Quarter-finals -> Semi-finals -> Third Place -> Final.

    Reads real knockout matches from the database, generates predictions for
    matches where both teams are known, and includes results for finished matches.
    """
    from database import SessionLocal, Match, Team, Odds

    # ── Stage mapping: DB stage value → bracket response key ──
    STAGE_TO_BRACKET_KEY = {
        "round32": "round_of_32",
        "round16": "round_of_16",
        "quarter": "quarter_finals",
        "semi": "semi_finals",
        "third": "third_place",
        "final": "final",
    }

    # ── R16 bracket connections (which R32 match winners feed into each R16 match) ──
    # Format: R16 match_id → (source_match_id_for_team1, source_match_id_for_team2)
    R16_CONNECTIONS = {
        89: (73, 76),
        90: (74, 75),
        91: (77, 79),
        92: (78, 80),
        93: (81, 82),
        94: (83, 84),
        95: (86, 88),
        96: (85, 87),
    }

    # ── QF bracket connections ──
    QF_CONNECTIONS = {
        97: (89, 90),
        98: (91, 92),
        99: (93, 94),
        100: (95, 96),
    }

    # ── SF bracket connections ──
    SF_CONNECTIONS = {
        101: (97, 98),
        102: (99, 100),
    }

    # ── Third Place / Final connections ──
    THIRD_PLACE_CONNECTIONS = (101, 102)  # losers of SF
    FINAL_CONNECTIONS = (101, 102)  # winners of SF

    # ── Helper: determine winner of a finished match ──
    def _get_winner(match_row):
        """Return winner team code for a finished match, or None."""
        if match_row.status != "finished":
            return None
        s1, s2 = match_row.score1 or 0, match_row.score2 or 0
        if s1 > s2:
            return match_row.team1
        elif s2 > s1:
            return match_row.team2
        # Check penalties
        sp1, sp2 = match_row.score1_pen, match_row.score2_pen
        if sp1 is not None and sp2 is not None:
            if sp1 > sp2:
                return match_row.team1
            elif sp2 > sp1:
                return match_row.team2
        return None  # draw without penalty result (shouldn't happen in knockout)

    # ── Helper: determine loser of a finished match ──
    def _get_loser(match_row):
        """Return loser team code for a finished match, or None."""
        winner = _get_winner(match_row)
        if winner is None:
            return None
        if winner == match_row.team1:
            return match_row.team2
        return match_row.team1

    # ── Helper: build label for a match based on connections ──
    def _build_connection_label(conn_type, source_ids):
        """Build label like 'W73 vs W76' or 'L101 vs L102'."""
        prefix = "W" if conn_type == "winner" else "L"
        return f"{prefix}{source_ids[0]} vs {prefix}{source_ids[1]}"

    # ── Helper: resolve team from source match ──
    def _resolve_from_source(match_by_id, source_match_id, conn_type):
        """Resolve team code from a source match. Returns (team_code_or_TBD, label_part)."""
        source = match_by_id.get(source_match_id)
        if not source:
            prefix = "W" if conn_type == "winner" else "L"
            return "TBD", f"{prefix}{source_match_id}"

        if conn_type == "winner":
            winner = _get_winner(source)
            if winner:
                return winner, None  # team resolved, no label part needed
            # Not finished yet → reference by match
            return "TBD", f"W{source_match_id}"
        else:  # loser
            loser = _get_loser(source)
            if loser:
                return loser, None
            return "TBD", f"L{source_match_id}"

    # ── Helper: build prediction for a match ──
    def _build_prediction(team1_code, team2_code, teams_dict, stage):
        """Generate prediction for a match where both teams are known."""
        t1_data = teams_dict.get(team1_code, {
            "code": team1_code,
            "elo_rating": 1800,
            "fifa_rank": 30,
            "recent_form": "",
        })
        t2_data = teams_dict.get(team2_code, {
            "code": team2_code,
            "elo_rating": 1800,
            "fifa_rank": 30,
            "recent_form": "",
        })
        try:
            pred = predictor.predict_match(t1_data, t2_data, stage=stage)
            # Extract the most likely scoreline for predicted_score
            top_scorelines = pred.get("top_5_scorelines", [])
            predicted_score = top_scorelines[0]["score"] if top_scorelines else None
            return {
                "home_win_prob": pred.get("home_win_prob"),
                "draw_prob": pred.get("draw_prob"),
                "away_win_prob": pred.get("away_win_prob"),
                "expected_goals_home": pred.get("expected_goals_home"),
                "expected_goals_away": pred.get("expected_goals_away"),
                "top_5_scorelines": top_scorelines,
                "predicted_score": predicted_score,
                "confidence_level": pred.get("confidence_level"),
            }
        except Exception as e:
            return {"error": str(e)}

    # ── Helper: build a single match entry for the bracket ──
    def _build_match_entry(match_row, teams_dict, match_by_id, connections=None, conn_type=None):
        """Build a bracket match entry dict from a Match row.

        connections: tuple of (source_match_id_1, source_match_id_2) for later rounds
        conn_type: "winner" or "loser" to resolve teams from source matches
        """
        t1_code = match_row.team1
        t2_code = match_row.team2
        t1_is_tbd = (t1_code == "TBD" or t1_code is None)
        t2_is_tbd = (t2_code == "TBD" or t2_code is None)

        # Build label
        label = match_row.round or ""

        # If teams are TBD and we have connections, try to resolve from source matches
        if connections and conn_type:
            # Try to resolve team1 from source
            if t1_is_tbd:
                t1_resolved, t1_label = _resolve_from_source(match_by_id, connections[0], conn_type)
                t1_code = t1_resolved
                t1_is_tbd = (t1_code == "TBD")

            # Try to resolve team2 from source
            if t2_is_tbd:
                t2_resolved, t2_label = _resolve_from_source(match_by_id, connections[1], conn_type)
                t2_code = t2_resolved
                t2_is_tbd = (t2_code == "TBD")

            # Build label from connections if original label is empty/generic
            if not label or label == "Knockout":
                label = _build_connection_label(conn_type, connections)

        # If label is still empty, construct from team codes
        if not label:
            t1_display = t1_code if not t1_is_tbd else "TBD"
            t2_display = t2_code if not t2_is_tbd else "TBD"
            label = f"{t1_display} vs {t2_display}"

        # Look up team info
        t1_info = teams_dict.get(t1_code) if not t1_is_tbd else None
        t2_info = teams_dict.get(t2_code) if not t2_is_tbd else None

        # Determine status
        status = match_row.status or "upcoming"

        # Determine winner
        winner = _get_winner(match_row)

        # Build prediction (only if both teams are known and match not finished)
        prediction = None
        if not t1_is_tbd and not t2_is_tbd and status != "finished":
            prediction = _build_prediction(t1_code, t2_code, teams_dict, match_row.stage)

        entry = {
            "match_id": match_row.id,
            "label": label,
            "team1": t1_code if not t1_is_tbd else "TBD",
            "team1_name": t1_info.get("name", t1_code) if t1_info else ("TBD" if t1_is_tbd else t1_code),
            "team1_name_zh": t1_info.get("name_zh", TEAM_ZH.get(t1_code, t1_code)) if t1_info else ("TBD" if t1_is_tbd else TEAM_ZH.get(t1_code, t1_code)),
            "team1_flag": t1_info.get("flag_emoji", "") if t1_info else "",
            "team2": t2_code if not t2_is_tbd else "TBD",
            "team2_name": t2_info.get("name", t2_code) if t2_info else ("TBD" if t2_is_tbd else t2_code),
            "team2_name_zh": t2_info.get("name_zh", TEAM_ZH.get(t2_code, t2_code)) if t2_info else ("TBD" if t2_is_tbd else TEAM_ZH.get(t2_code, t2_code)),
            "team2_flag": t2_info.get("flag_emoji", "") if t2_info else "",
            "date": match_row.date or "",
            "kick_off": match_row.kick_off or "",
            "status": status,
            "score1": match_row.score1,
            "score2": match_row.score2,
            "score1_pen": match_row.score1_pen,
            "score2_pen": match_row.score2_pen,
            "winner": winner,
            "prediction": prediction,
        }
        return entry

    try:
        with SessionLocal() as session:
            # Load all knockout matches (stage != 'group')
            knockout_matches = session.query(Match).filter(Match.stage != "group").order_by(Match.id).all()

            # Load all teams for lookup
            all_teams = session.query(Team).all()
            teams_dict = {}
            for t in all_teams:
                teams_dict[t.code] = {
                    "code": t.code,
                    "name": t.name,
                    "name_zh": t.name_zh,
                    "elo_rating": t.elo_rating,
                    "fifa_rank": t.fifa_rank,
                    "recent_form": t.recent_form or "",
                    "flag_emoji": t.flag_emoji or "",
                }

            # Build match_by_id lookup for resolving connections
            match_by_id = {m.id: m for m in knockout_matches}

            # Group matches by stage
            matches_by_stage: Dict[str, list] = {}
            for m in knockout_matches:
                stage = m.stage or "group"
                if stage not in matches_by_stage:
                    matches_by_stage[stage] = []
                matches_by_stage[stage].append(m)

            # Build bracket structure
            bracket = {}

            # ── Round of 32 ──
            r32_matches = matches_by_stage.get("round32", [])
            bracket["round_of_32"] = [
                _build_match_entry(m, teams_dict, match_by_id)
                for m in r32_matches
            ]

            # ── Round of 16 ──
            r16_matches = matches_by_stage.get("round16", [])
            r16_entries = []
            for m in r16_matches:
                conn = R16_CONNECTIONS.get(m.id)
                r16_entries.append(_build_match_entry(
                    m, teams_dict, match_by_id,
                    connections=conn, conn_type="winner"
                ))
            bracket["round_of_16"] = r16_entries

            # ── Quarter-finals ──
            qf_matches = matches_by_stage.get("quarter", [])
            qf_entries = []
            for m in qf_matches:
                conn = QF_CONNECTIONS.get(m.id)
                qf_entries.append(_build_match_entry(
                    m, teams_dict, match_by_id,
                    connections=conn, conn_type="winner"
                ))
            bracket["quarter_finals"] = qf_entries

            # ── Semi-finals ──
            sf_matches = matches_by_stage.get("semi", [])
            sf_entries = []
            for m in sf_matches:
                conn = SF_CONNECTIONS.get(m.id)
                sf_entries.append(_build_match_entry(
                    m, teams_dict, match_by_id,
                    connections=conn, conn_type="winner"
                ))
            bracket["semi_finals"] = sf_entries

            # ── Third Place ──
            third_matches = matches_by_stage.get("third", [])
            if third_matches:
                m = third_matches[0]
                bracket["third_place"] = _build_match_entry(
                    m, teams_dict, match_by_id,
                    connections=THIRD_PLACE_CONNECTIONS, conn_type="loser"
                )
            else:
                bracket["third_place"] = {
                    "match_id": None, "label": "L101 vs L102",
                    "team1": "TBD", "team1_name": "TBD", "team1_name_zh": "TBD", "team1_flag": "",
                    "team2": "TBD", "team2_name": "TBD", "team2_name_zh": "TBD", "team2_flag": "",
                    "date": "", "kick_off": "", "status": "upcoming",
                    "score1": None, "score2": None, "score1_pen": None, "score2_pen": None,
                    "winner": None, "prediction": None,
                }

            # ── Final ──
            final_matches = matches_by_stage.get("final", [])
            if final_matches:
                m = final_matches[0]
                bracket["final"] = _build_match_entry(
                    m, teams_dict, match_by_id,
                    connections=FINAL_CONNECTIONS, conn_type="winner"
                )
            else:
                bracket["final"] = {
                    "match_id": None, "label": "W101 vs W102",
                    "team1": "TBD", "team1_name": "TBD", "team1_name_zh": "TBD", "team1_flag": "",
                    "team2": "TBD", "team2_name": "TBD", "team2_name_zh": "TBD", "team2_flag": "",
                    "date": "", "kick_off": "", "status": "upcoming",
                    "score1": None, "score2": None, "score1_pen": None, "score2_pen": None,
                    "winner": None, "prediction": None,
                }

            # ── Compute summary stats ──
            total_knockout = len(knockout_matches)
            finished_count = sum(1 for m in knockout_matches if m.status == "finished")

            # Determine overall bracket status
            if finished_count == 0:
                bracket_status = "knockout"
            elif finished_count == total_knockout and total_knockout > 0:
                bracket_status = "completed"
            else:
                bracket_status = "knockout"

            # Find next upcoming match
            next_match = None
            upcoming_ko = [m for m in knockout_matches if m.status == "upcoming"]
            if upcoming_ko:
                # Sort by date/kick_off
                upcoming_ko.sort(key=lambda m: (m.date or "9999", m.kick_off or "9999"))
                nm = upcoming_ko[0]
                nm_t1 = nm.team1 if nm.team1 != "TBD" else "TBD"
                nm_t2 = nm.team2 if nm.team2 != "TBD" else "TBD"
                next_match = {
                    "match_id": nm.id,
                    "team1": nm_t1,
                    "team2": nm_t2,
                    "date": nm.date or "",
                    "kick_off": nm.kick_off or "",
                }

        return {
            "bracket": bracket,
            "total_knockout_matches": total_knockout,
            "status": bracket_status,
            "finished_matches": finished_count,
            "next_match": next_match,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/match/{match_id}")
async def api_match_detail(match_id: int):
    """
    Full match detail with prediction, players, H2H, and odds.
    When API-Football key is configured, enriches data from live API.
    Returns structured response:
    {
        "match": { flat match data },
        "players": { "team1": [...], "team2": [...] },
        "h2h": { "stats": {...}, "matches": [...] },
        "odds": { "bookmakers": [...], "correct_scores": [...] },
        "prediction": { prediction data }
    }
    """
    try:
        detail = db_get_match_detail(match_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

        match_flat = detail["match"]
        t1_code = match_flat["team1"]
        t2_code = match_flat["team2"]

        # Add prediction using comprehensive multi-factor model
        prediction = {}
        try:
            pred_input1 = {
                "code": t1_code,
                "elo_rating": match_flat.get("team1_elo", 1800),
                "fifa_rank": match_flat.get("team1_fifa_rank", 30),
                "recent_form": match_flat.get("team1_recent_form", ""),
            }
            pred_input2 = {
                "code": t2_code,
                "elo_rating": match_flat.get("team2_elo", 1800),
                "fifa_rank": match_flat.get("team2_fifa_rank", 30),
                "recent_form": match_flat.get("team2_recent_form", ""),
            }

            # Get odds list for prediction
            odds_list = detail["odds"].get("bookmakers", [])

            # Get squad data for prediction
            squad1 = detail["players"].get("team1", [])
            squad2 = detail["players"].get("team2", [])

            prediction = predictor.predict_match(
                pred_input1, pred_input2,
                odds_list=odds_list,
                squad1=squad1,
                squad2=squad2,
            )
        except Exception as e:
            prediction = {"error": str(e)}

        # Enrich from API if available
        api_players = None
        api_odds = None
        api_h2h = None
        api_prediction = None
        api_form1 = None
        api_form2 = None
        api_injuries = None
        api_recent1 = None
        api_recent2 = None

        if data_fetcher.api_available:
            try:
                # Try to get fixture_id from API fixtures
                fixtures = await data_fetcher.fetch_fixtures_from_api()
                fixture_id = None
                team1_api_id = None
                team2_api_id = None

                for fx in fixtures:
                    if (fx["team1"] == t1_code and fx["team2"] == t2_code) or \
                       (fx["team1"] == t2_code and fx["team2"] == t1_code):
                        fixture_id = fx.get("fixture_id")
                        break

                # Try to get team IDs from API teams
                api_teams = await data_fetcher.fetch_teams_from_api()
                for at in api_teams:
                    if at["code"] == t1_code:
                        team1_api_id = at.get("id")
                    if at["code"] == t2_code:
                        team2_api_id = at.get("id")

                # Fetch squad with player season stats from API
                if team1_api_id:
                    squad1_stats = await data_fetcher.fetch_squad_with_stats_from_api(team1_api_id)
                    if squad1_stats:
                        api_players = {"team1": squad1_stats}
                    else:
                        squad1 = await data_fetcher.fetch_squad_from_api(team1_api_id)
                        if squad1:
                            api_players = {"team1": squad1}
                if team2_api_id:
                    squad2_stats = await data_fetcher.fetch_squad_with_stats_from_api(team2_api_id)
                    if squad2_stats:
                        if api_players is None:
                            api_players = {}
                        api_players["team2"] = squad2_stats
                    else:
                        squad2 = await data_fetcher.fetch_squad_from_api(team2_api_id)
                        if squad2:
                            if api_players is None:
                                api_players = {}
                            api_players["team2"] = squad2

                # Fetch team recent form from API
                if team1_api_id:
                    api_form1 = await data_fetcher.fetch_team_form_from_api(team1_api_id)
                if team2_api_id:
                    api_form2 = await data_fetcher.fetch_team_form_from_api(team2_api_id)

                # Fetch odds from API
                if fixture_id:
                    api_odds = await data_fetcher.fetch_odds_from_api(fixture_id)
                    api_prediction = await data_fetcher.fetch_predictions_from_api(fixture_id)

                # Fetch H2H from API
                if team1_api_id and team2_api_id:
                    api_h2h = await data_fetcher.fetch_h2h_from_api(team1_api_id, team2_api_id)

                # Fetch injuries for this fixture
                if fixture_id:
                    api_injuries = await data_fetcher.fetch_injuries_from_api(fixture_id)

                # Fetch recent matches for both teams
                if team1_api_id:
                    api_recent1 = await data_fetcher.fetch_recent_matches_from_api(team1_api_id, 10)
                if team2_api_id:
                    api_recent2 = await data_fetcher.fetch_recent_matches_from_api(team2_api_id, 10)

            except Exception as e:
                print(f"[Server] API enrichment error (non-fatal): {e}")

        # Fetch sporttery.cn odds (Chinese sports lottery - additional source)
        sporttery_odds = None
        try:
            sporttery_odds_list = await asyncio.wait_for(
                data_fetcher.fetch_odds_from_sporttery(
                    match_flat.get("team1_name", ""),
                    match_flat.get("team2_name", "")
                ),
                timeout=8.0
            )
            if sporttery_odds_list:
                sporttery_odds = sporttery_odds_list
        except asyncio.TimeoutError:
            print("[Server] sporttery.cn odds fetch timed out")
        except Exception as e:
            print(f"[Server] sporttery.cn odds error (non-fatal): {e}")

        # Merge: API data takes priority, fallback to DB
        players = detail["players"]
        if api_players:
            if "team1" in api_players and api_players["team1"]:
                players["team1"] = api_players["team1"]
            if "team2" in api_players and api_players["team2"]:
                players["team2"] = api_players["team2"]

        h2h = api_h2h if api_h2h and api_h2h.get("stats", {}).get("total", 0) > 0 else \
            {"stats": detail["h2h"]["stats"], "matches": detail["h2h"]["matches"]}

        # If no API H2H, use local
        if not api_h2h:
            h2h_matches = _get_h2h_history(t1_code, t2_code)
            h2h_stats = _compute_h2h_stats(h2h_matches, t1_code)
            h2h = {"stats": h2h_stats, "matches": h2h_matches}

        odds = detail["odds"]
        if api_odds:
            odds["bookmakers"] = api_odds

        # Merge sporttery.cn odds into bookmakers list
        if sporttery_odds:
            if "bookmakers" not in odds:
                odds["bookmakers"] = []
            for so in sporttery_odds:
                odds["bookmakers"].append(so)

        # Merge prediction: our ELO model + API prediction
        if api_prediction:
            prediction["api_prediction"] = api_prediction

        # Re-run prediction with enriched data (API odds + sporttery odds + API players + API form + injuries)
        injuries_data = {}
        if api_injuries:
            injuries_data = {
                t1_code: [i for i in api_injuries if i.get("team") == t1_code],
                t2_code: [i for i in api_injuries if i.get("team") == t2_code],
            }

        if api_odds or sporttery_odds or api_players or api_form1 or api_form2 or api_injuries:
            try:
                enriched_odds = odds.get("bookmakers", [])
                enriched_squad1 = players.get("team1", [])
                enriched_squad2 = players.get("team2", [])
                prediction = predictor.predict_match(
                    pred_input1, pred_input2,
                    odds_list=enriched_odds,
                    squad1=enriched_squad1,
                    squad2=enriched_squad2,
                    form1_data=api_form1,
                    form2_data=api_form2,
                    injuries=injuries_data,
                )
                if api_prediction:
                    prediction["api_prediction"] = api_prediction
            except Exception as e:
                print(f"[Server] Re-prediction with enriched data failed: {e}")

        # Build injuries response
        injuries_response = {t1_code: [], t2_code: []}
        if api_injuries:
            injuries_response = injuries_data

        # Build recent matches response (with local fallback)
        recent_matches_response = {}
        for _team_code, _api_matches in [(t1_code, api_recent1), (t2_code, api_recent2)]:
            if _api_matches:
                recent_matches_response[_team_code] = _api_matches
            else:
                # Local fallback
                try:
                    import json as _rj, os as _ro
                    _rd = _ro.path.join(_ro.path.dirname(_ro.path.dirname(_ro.path.abspath(__file__))), "data")
                    _rp = _ro.path.join(_rd, "recent_matches.json")
                    _loaded = []
                    if _ro.path.exists(_rp):
                        _db = _rj.load(open(_rp, "r", encoding="utf-8"))
                        if _team_code in _db:
                            _loaded = list(_db[_team_code])
                    # Append WC data
                    for _y in ["2022", "2018"]:
                        _wc = _ro.path.join(_rd, f"wc{_y}.json")
                        if not _ro.path.exists(_wc): continue
                        _wc_d = _rj.load(open(_wc, "r", encoding="utf-8"))
                        for _m in _wc_d.get("group_matches", []) + _wc_d.get("knockout_matches", []):
                            if _m.get("team1") != _team_code and _m.get("team2") != _team_code:
                                continue
                            _dup = any(x.get("date") == _m.get("date") and x.get("opponent_code") in (_m["team1"], _m["team2"]) for x in _loaded)
                            if _dup: continue
                            _ih = _m["team1"] == _team_code
                            _gf = _m.get("score1", 0) if _ih else _m.get("score2", 0)
                            _ga = _m.get("score2", 0) if _ih else _m.get("score1", 0)
                            _r = "W" if _gf > _ga else "D" if _gf == _ga else "L"
                            _opp = _m["team2"] if _ih else _m["team1"]
                            _e = {"date": _m.get("date",f"{_y}-06-01"),"opponent_name":_opp,"opponent_name_zh":TEAM_ZH.get(_opp,_opp),"opponent_code":_opp,"is_home":_ih,"goals_for":_gf,"goals_against":_ga,"result":_r,"league":f"{_y} World Cup {_m.get('round','')}","competition_type":"World Cup"}
                            if _m.get("score1_pen") is not None:
                                _e["penalty"] = f"{_m['score1_pen']}-{_m['score2_pen']}"
                            _loaded.append(_e)
                    _loaded.sort(key=lambda x: x.get("date",""), reverse=True)
                    recent_matches_response[_team_code] = _loaded
                except Exception as _e:
                    print(f"[Server] Match detail recent fallback error for {_team_code}: {_e}")
                    recent_matches_response[_team_code] = []

        return {
            "match": match_flat,
            "players": players,
            "h2h": h2h,
            "odds": odds,
            "prediction": prediction,
            "injuries": injuries_response,
            "recent_matches": recent_matches_response,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest")
async def api_backtest(with_factors: bool = Query(False), with_stage: bool = Query(False)):
    """Backtest results for 2018 and 2022."""
    if not BACKTEST_RESULTS:
        raise HTTPException(status_code=503, detail="Backtests not yet completed")

    summary = backtester.get_summary()
    # If client wants multi-factor or stage-adjusted results, run them
    extra = {}
    if with_factors or with_stage:
        for year in [2018, 2022]:
            result = backtester.run_backtest(year, backtest_with_factors=with_factors, stage_adjustments=with_stage)
            extra[year] = {
                "multi_factor": result.get("multi_factor"),
                "stage_adjusted": result.get("stage_adjusted"),
            }
    return {
        "results": summary,
        "detail": {str(year): data for year, data in BACKTEST_RESULTS.items()},
        "extra": extra if extra else None,
    }


@app.post("/api/monte-carlo")
async def api_monte_carlo(num_sims: int = Query(10000, description="Number of simulations")):
    """Run Monte Carlo tournament simulation."""
    # Build groups from DB
    teams = get_all_teams()
    groups = {}
    for t in teams:
        g = t["group_name"]
        if g not in groups:
            groups[g] = []
        groups[g].append(t["code"])

    # Build teams_data for predictor
    teams_data = {t["code"]: t for t in teams}

    # Run simulation in thread pool to avoid blocking the event loop
    simulator = MonteCarloSimulator(predictor, teams_data)
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None, lambda: simulator.run_simulation(groups, num_sims=min(num_sims, 50000))
    )
    return results


@app.get("/api/recent-matches/{team_code}")
async def api_recent_matches(team_code: str, last: int = Query(10)):
    """Get recent matches for a team (API first, local fallback)."""
    code = team_code.upper()
    matches = []
    source = "local"

    # Try API first
    if data_fetcher.api_available:
        try:
            api_teams = await data_fetcher.fetch_teams_from_api()
            team_api_id = None
            for at in api_teams:
                if at.get("code", "").upper() == code:
                    team_api_id = at.get("id")
                    break
            if team_api_id:
                api_matches = await data_fetcher.fetch_recent_matches_from_api(team_api_id, last)
                if api_matches:
                    return {"team": code, "matches": api_matches, "source": "api"}
        except Exception as e:
            print(f"[Server] Recent matches API error for {code}: {e}")

    # Fallback: local recent_matches.json (2024-2026 friendly/qualifiers/competitions)
    # then append World Cup 2018/2022 data for completeness
    try:
        import json as _json, os as _os
        _backend_dir = _os.path.dirname(_os.path.abspath(__file__))
        _data_dir = _os.path.join(_os.path.dirname(_backend_dir), "data")

        # 1. Load curated recent matches (qualifiers, friendlies, Nations League, etc.)
        _recent_path = _os.path.join(_data_dir, "recent_matches.json")
        if _os.path.exists(_recent_path):
            _recent_db = _json.load(open(_recent_path, "r", encoding="utf-8"))
            if code in _recent_db:
                matches = list(_recent_db[code])
                # Add Chinese names
                for _m in matches:
                    _m["opponent_name_zh"] = TEAM_ZH.get(_m.get("opponent_code", ""), _m.get("opponent_name", ""))

        # 2. Also append World Cup data for extra historical context
        for year in ["2022", "2018"]:
            path = _os.path.join(_data_dir, f"wc{year}.json")
            if not _os.path.exists(path):
                continue
            wc_data = _json.load(open(path, "r", encoding="utf-8"))
            all_m = wc_data.get("group_matches", []) + wc_data.get("knockout_matches", [])
            for m in all_m:
                t1 = m.get("team1", "")
                t2 = m.get("team2", "")
                if t1 == code or t2 == code:
                    # Check if match already exists in recent (by date + opponent)
                    dup = any(x.get("date") == m.get("date") and x.get("opponent_code") in (t1, t2) for x in matches)
                    if dup:
                        continue
                    is_home = t1 == code
                    gf = m.get("score1", 0) if is_home else m.get("score2", 0)
                    ga = m.get("score2", 0) if is_home else m.get("score1", 0)
                    if gf > ga: result = "W"
                    elif gf == ga: result = "D"
                    else: result = "L"
                    opponent = t2 if is_home else t1
                    pen1, pen2 = m.get("score1_pen"), m.get("score2_pen")
                    entry = {
                        "date": m.get("date", f"{year}-06-01"),
                        "opponent_name": opponent,
                        "opponent_name_zh": TEAM_ZH.get(opponent, opponent),
                        "opponent_code": opponent,
                        "is_home": is_home,
                        "goals_for": gf,
                        "goals_against": ga,
                        "result": result,
                        "league": f"{year} World Cup {m.get('round', '')}",
                        "competition_type": "World Cup",
                    }
                    if pen1 is not None and pen2 is not None:
                        entry["penalty"] = f"{pen1}-{pen2}"
                    matches.append(entry)

        # Sort by date descending, limit to requested count
        matches.sort(key=lambda x: x.get("date", ""), reverse=True)
        matches = matches[:last]

    except Exception as e:
        print(f"[Server] Local recent matches error for {code}: {e}")

    return {
        "team": code,
        "matches": matches,
        "source": source if matches else "unavailable",
    }


@app.get("/api/injuries/{fixture_id}")
async def api_injuries(fixture_id: int):
    """Get injury/absence data for a match."""
    if data_fetcher.api_available:
        injuries = await data_fetcher.fetch_injuries_from_api(fixture_id)
        return {"fixture_id": fixture_id, "injuries": injuries, "source": "api"}
    return {"fixture_id": fixture_id, "injuries": [], "source": "unavailable"}


@app.post("/api/refresh")
async def api_refresh():
    """Trigger data refresh."""
    global LAST_UPDATED
    try:
        result = await data_fetcher.refresh_data()
        LAST_UPDATED = result.get("last_updated", str(datetime.now()))
        return {
            "success": True,
            "message": "Data refreshed successfully",
            "last_updated": LAST_UPDATED,
            "details": {
                "matches_count": result.get("matches_count", 0),
                "teams_count": result.get("teams_count", 0),
                "odds_count": result.get("odds_count", 0),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@app.post("/api/refresh-odds")
async def api_refresh_odds():
    """
    Force refresh all odds data from API + sporttery.cn,
    then recalculate predictions for all upcoming matches.
    Returns count of updated matches and odds sources.
    """
    global LAST_UPDATED
    try:
        from database import get_upcoming_matches as db_get_upcoming_matches, get_match_detail as db_get_match_detail

        upcoming = db_get_upcoming_matches(days=14)

        updated_odds = 0
        failed_odds = 0
        all_bookmakers = []
        sporttery_odds_list = None

        # 1. Fetch sporttery.cn odds (covers all matches at once)
        try:
            sporttery_odds_list = await asyncio.wait_for(
                data_fetcher.fetch_odds_from_sporttery("", ""),
                timeout=12.0
            )
        except asyncio.TimeoutError:
            print("[Refresh] sporttery.cn timeout")
        except Exception as e:
            print(f"[Refresh] sporttery.cn error: {e}")

        # 2. Fetch API odds for each upcoming match
        for match in upcoming:
            fixture_id = match.get("fixture_id") or match.get("api_fixture_id")
            if not fixture_id:
                continue
            try:
                api_odds = await asyncio.wait_for(
                    data_fetcher.fetch_odds_from_api(fixture_id),
                    timeout=8.0
                )
                if api_odds:
                    updated_odds += 1
                    all_bookmakers.extend(api_odds)
                else:
                    failed_odds += 1
            except asyncio.TimeoutError:
                failed_odds += 1
            except Exception as e:
                failed_odds += 1

        # 3. Refresh group standings from API
        standings_updated = False
        try:
            from database import SessionLocal, Match, update_match_result as _umr
            from database import update_match_result
            api_standings = await asyncio.wait_for(
                data_fetcher.fetch_standings_from_api(),
                timeout=15.0
            )
            if api_standings:
                standings_updated = True
                print(f"[Refresh] Standings refreshed: {len(api_standings)} groups")
        except asyncio.TimeoutError:
            print("[Refresh] Standings fetch timeout")
        except Exception as e:
            print(f"[Refresh] Standings error: {e}")

        # 4. Update match results from API fixtures
        matches_updated = 0
        try:
            api_fixtures = await asyncio.wait_for(
                data_fetcher.fetch_fixtures_from_api(),
                timeout=20.0
            )
            from database import SessionLocal, Match, update_match_result
            from datetime import datetime as _dt
            for fx in api_fixtures:
                if fx.get("status") != "finished":
                    continue
                s1 = fx.get("score1")
                s2 = fx.get("score2")
                if s1 is None or s2 is None:
                    continue
                t1 = fx.get("team1")
                t2 = fx.get("team2")
                if not t1 or not t2:
                    continue
                with SessionLocal() as session:
                    match = session.query(Match).filter(
                        Match.team1 == t1, Match.team2 == t2,
                        Match.status != "finished"
                    ).first()
                    if match:
                        old_status = match.status
                        match.score1 = int(s1)
                        match.score2 = int(s2)
                        match.status = "finished"
                        session.commit()
                        matches_updated += 1
        except asyncio.TimeoutError:
            print("[Refresh] Fixtures fetch timeout")
        except Exception as e:
            print(f"[Refresh] Fixtures error: {e}")

        # 5. Merge sporttery odds
        if sporttery_odds_list:
            for so in sporttery_odds_list:
                if "bookmaker" in so:
                    all_bookmakers.append(so)

        # 6. Re-run predictions for all upcoming matches with fresh odds
        recalculated = 0
        for match in upcoming:
            try:
                detail = db_get_match_detail(match["id"])
                if not detail:
                    continue
                pred_input1 = {
                    "code": match["team1"],
                    "elo_rating": match.get("team1_elo", 1800),
                    "fifa_rank": match.get("team1_fifa_rank", 30),
                    "recent_form": match.get("team1_recent_form", ""),
                }
                pred_input2 = {
                    "code": match["team2"],
                    "elo_rating": match.get("team2_elo", 1800),
                    "fifa_rank": match.get("team2_fifa_rank", 30),
                    "recent_form": match.get("team2_recent_form", ""),
                }

                # Use fresh odds for this match
                match_odds = [o for o in all_bookmakers if True]  # Apply all odds
                prediction = predictor.predict_match(
                    pred_input1, pred_input2,
                    odds_list=match_odds[:10] if match_odds else None,
                )

                # Store updated prediction in DB
                from database import SessionLocal, Match
                with SessionLocal() as session:
                    m = session.query(Match).filter(Match.id == match["id"]).first()
                    if m:
                        import json as _json
                        m.prediction_json = _json.dumps(prediction)
                        session.commit()

                recalculated += 1
            except Exception as e:
                print(f"[Refresh] Prediction recalc error for match {match['id']}: {e}")

        LAST_UPDATED = str(datetime.now())

        # Build status message
        msg_parts = []
        if matches_updated > 0:
            msg_parts.append(f"比分 {matches_updated} 场")
        if updated_odds > 0:
            msg_parts.append(f"赔率 {updated_odds} 场")
        if recalculated > 0:
            msg_parts.append(f"预测 {recalculated} 场")
        if standings_updated:
            msg_parts.append("积分榜已更新")
        if not msg_parts:
            msg_parts.append("数据已刷新")
        msg = "✅ " + " · ".join(msg_parts)

        return {
            "success": True,
            "message": msg,
            "last_updated": LAST_UPDATED,
            "details": {
                "odds_updated": updated_odds,
                "odds_failed": failed_odds,
                "predictions_recalculated": recalculated,
                "sporttery_available": sporttery_odds_list is not None,
                "standings_updated": standings_updated,
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"赔率刷新失败: {str(e)}")


@app.post("/api/refresh-knockout")
async def api_refresh_knockout():
    """
    Force refresh knockout match results from API.
    Called after each match finishes to pull the latest scores.
    Also advances the bracket (updates TBD slots with winners).
    """
    global LAST_UPDATED
    try:
        from database import SessionLocal, Match

        updated_matches = 0
        advanced_slots = 0

        # 1. Fetch fresh fixtures from API (invalidate cache first)
        if data_fetcher.api_available:
            data_fetcher.cache.delete("api_fixtures")
            fixtures = await asyncio.wait_for(
                data_fetcher.fetch_fixtures_from_api(), timeout=20.0
            )
        else:
            fixtures = data_fetcher.cache.get("api_fixtures") or []

        # 2. Update finished matches
        finished = [f for f in fixtures if f.get("status") == "finished"]
        with SessionLocal() as session:
            for fx in finished:
                t1 = fx.get("team1", "")
                t2 = fx.get("team2", "")
                s1 = fx.get("score1")
                s2 = fx.get("score2")
                if not t1 or not t2 or s1 is None or s2 is None:
                    continue

                # Find matching upcoming/live match
                match = session.query(Match).filter(
                    Match.team1 == t1, Match.team2 == t2,
                    Match.status != "finished"
                ).first()
                if not match:
                    match = session.query(Match).filter(
                        Match.team1 == t2, Match.team2 == t1,
                        Match.status != "finished"
                    ).first()

                if match:
                    match.score1 = int(s1)
                    match.score2 = int(s2)
                    match.status = "finished"
                    updated_matches += 1

            if updated_matches > 0:
                session.commit()

            # 3. Advance bracket: fill in TBD slots based on finished matches
            # Round of 32 winners → Round of 16 TBD slots
            knockout_matches = session.query(Match).filter(
                Match.stage != "group"
            ).all()

            # Build a map of match_id → winner
            match_winners = {}
            for m in knockout_matches:
                if m.status == "finished" and m.score1 is not None and m.score2 is not None:
                    if m.score1 > m.score2:
                        match_winners[m.id] = m.team1
                    elif m.score2 > m.score1:
                        match_winners[m.id] = m.team2
                    # Draw in knockout → would need penalty info, skip for now

            # Define bracket connections: R16 match ID → (R32 match ID for team1, R32 match ID for team2)
            BRACKET_CONNECTIONS = {
                # Round of 16
                89: (73, 76), 90: (74, 75),
                91: (77, 79), 92: (78, 80),
                93: (81, 82), 94: (83, 84),
                95: (86, 88), 96: (85, 87),
                # Quarter Finals
                97: (89, 90), 98: (91, 92),
                99: (93, 94), 100: (95, 96),
                # Semi Finals
                101: (97, 98), 102: (99, 100),
                # Third Place
                103: (101, 102),  # L101 vs L102
                # Final
                104: (101, 102),  # W101 vs W102
            }

            for target_match_id, (src_match1, src_match2) in BRACKET_CONNECTIONS.items():
                target = session.query(Match).filter(Match.id == target_match_id).first()
                if not target:
                    continue

                # For Third Place match, we need the LOSERS
                is_third_place = (target_match_id == 103)

                w1 = match_winners.get(src_match1)
                w2 = match_winners.get(src_match2)

                if is_third_place:
                    # Need losers, not winners
                    src1_match = session.query(Match).filter(Match.id == src_match1).first()
                    src2_match = session.query(Match).filter(Match.id == src_match2).first()
                    if src1_match and src1_match.status == "finished":
                        if src1_match.score1 > src1_match.score2:
                            l1 = src1_match.team2
                        else:
                            l1 = src1_match.team1
                        if target.team1 == "TBD" or target.team1 != l1:
                            target.team1 = l1
                            advanced_slots += 1
                    if src2_match and src2_match.status == "finished":
                        if src2_match.score1 > src2_match.score2:
                            l2 = src2_match.team2
                        else:
                            l2 = src2_match.team1
                        if target.team2 == "TBD" or target.team2 != l2:
                            target.team2 = l2
                            advanced_slots += 1
                else:
                    # Normal: winners advance
                    if w1 and (target.team1 == "TBD" or target.team1 != w1):
                        target.team1 = w1
                        advanced_slots += 1
                    if w2 and (target.team2 == "TBD" or target.team2 != w2):
                        target.team2 = w2
                        advanced_slots += 1

            if advanced_slots > 0:
                session.commit()

        LAST_UPDATED = str(datetime.now())

        msg_parts = []
        if updated_matches > 0:
            msg_parts.append(f"更新 {updated_matches} 场比赛结果")
        if advanced_slots > 0:
            msg_parts.append(f"推进 {advanced_slots} 个对阵位")
        if not msg_parts:
            msg_parts.append("暂无新结果")

        return {
            "success": True,
            "message": "✅ " + " · ".join(msg_parts),
            "details": {
                "matches_updated": updated_matches,
                "slots_advanced": advanced_slots,
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"刷新淘汰赛结果失败: {str(e)}")


@app.get("/api/teams")
async def api_teams():
    """Get all teams with their data."""
    try:
        teams = get_all_teams()
        return {"teams": teams, "total": len(teams)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/team/{team_code}")
async def api_team_detail(team_code: str):
    """Get detailed info for a specific team."""
    teams = get_all_teams()
    for t in teams:
        if t["code"].upper() == team_code.upper():
            return t
    raise HTTPException(status_code=404, detail=f"Team {team_code} not found")


@app.get("/api/predict")
async def api_predict_match(
    team1: str = Query(..., description="Team 1 code (e.g. ARG)"),
    team2: str = Query(..., description="Team 2 code (e.g. FRA)"),
):
    """Quick prediction for any two teams."""
    teams = get_all_teams()
    teams_dict = {t["code"]: t for t in teams}

    t1 = teams_dict.get(team1.upper())
    t2 = teams_dict.get(team2.upper())

    if not t1:
        raise HTTPException(status_code=404, detail=f"Team {team1} not found")
    if not t2:
        raise HTTPException(status_code=404, detail=f"Team {team2} not found")

    pred = predictor.predict_match(t1, t2)
    return {
        "team1": {"code": t1["code"], "name": t1["name"], "name_zh": t1["name_zh"], "flag": t1.get("flag_emoji", "")},
        "team2": {"code": t2["code"], "name": t2["name"], "name_zh": t2["name_zh"], "flag": t2.get("flag_emoji", "")},
        "prediction": pred,
    }


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_h2h_history(code1: str, code2: str) -> List[Dict]:
    """Get head-to-head history between two teams from historical data."""
    h2h = []
    for year in [2018, 2022]:
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            path = os.path.join(data_dir, f"wc{year}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                all_matches = data.get("group_matches", []) + data.get("knockout_matches", [])
                for m in all_matches:
                    t1, t2 = m.get("team1"), m.get("team2")
                    if (t1 == code1 and t2 == code2) or (t1 == code2 and t2 == code1):
                        h2h.append({
                            "year": year,
                            "tournament": data.get("tournament", ""),
                            "date": m.get("date", ""),
                            "team1": t1,
                            "team2": t2,
                            "score1": m.get("score1"),
                            "score2": m.get("score2"),
                            "round": m.get("round", ""),
                        })
        except Exception:
            continue
    return h2h


def _compute_h2h_stats(h2h_matches: List[Dict], team1_code: str) -> Dict:
    """Compute H2H statistics from match history."""
    total = len(h2h_matches)
    home_wins = 0
    away_wins = 0
    draws = 0

    for m in h2h_matches:
        s1 = m.get("score1") or 0
        s2 = m.get("score2") or 0
        if s1 > s2:
            if m["team1"] == team1_code:
                home_wins += 1
            else:
                away_wins += 1
        elif s2 > s1:
            if m["team2"] == team1_code:
                home_wins += 1
            else:
                away_wins += 1
        else:
            draws += 1

    return {
        "total": total,
        "home_wins": home_wins,
        "draws": draws,
        "away_wins": away_wins,
    }


# ─────────────────────────────────────────────
# Static files (frontend)
# ─────────────────────────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


# ─────────────────────────────────────────────
# Run with: uvicorn server:app --host 0.0.0.0 --port 8000
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=6100, reload=True)