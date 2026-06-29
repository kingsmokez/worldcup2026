"""
World Cup 2026 Comprehensive Prediction Engine

Multi-factor prediction system combining:
1. ELO Rating + Poisson model (baseline)
2. Bookmaker odds analysis (market intelligence)
3. Squad strength analysis (player quality, position depth)
4. Form & momentum analysis

Weights calibrated via backtesting against 2018/2022 World Cup results.
"""

import math
import json
import os
from itertools import product
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import poisson

# ──────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Host countries for World Cup 2026
HOST_COUNTRIES = {"USA", "MEX", "CAN"}

# Venue information with altitude and climate factors
VENUE_INFO = {
    "Mexico City": {
        "altitude": 2240,  # meters
        "climate": "high_altitude",
        "host_country": "MEX",
    },
    "Guadalajara": {
        "altitude": 1560,
        "climate": "high_altitude",
        "host_country": "MEX",
    },
    "Monterrey": {
        "altitude": 540,
        "climate": "hot",
        "host_country": "MEX",
    },
    "Miami": {
        "altitude": 0,
        "climate": "hot_humid",
        "host_country": "USA",
    },
    "Houston": {
        "altitude": 0,
        "climate": "hot_humid",
        "host_country": "USA",
    },
    "Dallas": {
        "altitude": 130,
        "climate": "hot",
        "host_country": "USA",
    },
    "Atlanta": {
        "altitude": 320,
        "climate": "hot_humid",
        "host_country": "USA",
    },
    "Los Angeles": {
        "altitude": 70,
        "climate": "moderate",
        "host_country": "USA",
    },
    "New York": {
        "altitude": 10,
        "climate": "moderate",
        "host_country": "USA",
    },
    "Seattle": {
        "altitude": 0,
        "climate": "moderate",
        "host_country": "USA",
    },
    "Toronto": {
        "altitude": 76,
        "climate": "moderate",
        "host_country": "CAN",
    },
    "Vancouver": {
        "altitude": 0,
        "climate": "moderate",
        "host_country": "CAN",
    },
}

# European teams that may struggle in hot/humid conditions
EUROPEAN_TEAMS = {
    "GER", "ENG", "FRA", "ESP", "ITA", "NED", "BEL", "POR", "CRO", "SUI",
    "AUT", "DEN", "SWE", "NOR", "FIN", "POL", "CZE", "SVK", "SVN", "SRB",
    "UKR", "ROU", "HUN", "TUR", "GRE", "SCO", "WAL", "IRL", "NIR", "ISL",
    "ALB", "BIH", "KOS", "MKD", "MNE", "BUL", "EST", "LAT", "LTU", "LUX",
    "MAL", "MDA", "GEO", "ARM", "BLR", "AZE", "KAZ", "CYP", "FAR", "GIB",
    "LIE", "AND", "SMR", "MCO",
}


def _load_json(filename: str) -> dict:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────
# Injury Analyzer - assess impact of player absences
# ──────────────────────────────────────────────────────

class InjuryAnalyzer:
    """
    Analyzes the impact of injuries and player absences on team performance.
    """

    # Position-specific impact multipliers (missing these positions hurts more)
    POSITION_IMPACT = {
        "GK": 0.06,   # Goalkeeper is crucial
        "ST": 0.10,   # Striker directly affects scoring
        "CF": 0.09,
        "CAM": 0.07,
        "CM": 0.05,
        "CDM": 0.05,
        "CB": 0.08,   # Center back crucial for defense
        "RB": 0.04,
        "LB": 0.04,
        "RWB": 0.03,
        "LWB": 0.03,
        "RW": 0.06,
        "LW": 0.06,
        "RM": 0.04,
        "LM": 0.04,
        "RF": 0.05,
        "LF": 0.05,
    }

    # Importance multipliers
    IMPORTANCE_MULTIPLIERS = {
        "key": 1.0,       # Key player: full impact
        "important": 0.5,  # Important player: reduced impact
        "squad": 0.125,    # Squad player: minimal impact
    }

    @staticmethod
    def analyze_injuries(injuries: List[Dict]) -> Dict:
        """
        Analyze the impact of injuries/absences on team performance.

        Args:
            injuries: List of dicts with {player_name, position, importance}
                      importance: "key", "important", or "squad"

        Returns:
            Dict with impact_score, affected_positions, key_absences
        """
        if not injuries:
            return {
                "impact_score": 0.0,
                "affected_positions": [],
                "key_absences": 0,
                "position_breakdown": {},
            }

        impact_score = 0.0
        affected_positions = set()
        key_absences = 0
        position_breakdown = {}

        for injury in injuries:
            position = injury.get("position", "").upper()
            importance = injury.get("importance", "squad").lower()
            player_name = injury.get("player_name", "Unknown")

            # Get position impact
            pos_impact = InjuryAnalyzer.POSITION_IMPACT.get(position, 0.04)

            # Get importance multiplier
            imp_mult = InjuryAnalyzer.IMPORTANCE_MULTIPLIERS.get(importance, 0.125)

            # Calculate combined impact
            player_impact = pos_impact * imp_mult
            impact_score += player_impact

            # Track affected positions
            affected_positions.add(position)
            if position not in position_breakdown:
                position_breakdown[position] = []
            position_breakdown[position].append({
                "name": player_name,
                "importance": importance,
                "impact": round(player_impact, 4),
            })

            # Count key absences
            if importance == "key":
                key_absences += 1

        # Cap impact at reasonable maximum
        impact_score = min(impact_score, 0.35)

        return {
            "impact_score": round(impact_score, 4),
            "affected_positions": list(affected_positions),
            "key_absences": key_absences,
            "position_breakdown": position_breakdown,
            "total_injuries": len(injuries),
        }


# ──────────────────────────────────────────────────────
# 1. ELO Rating System
# ──────────────────────────────────────────────────────

class ELORatingSystem:
    @staticmethod
    def expected_result(elo_a: float, elo_b: float) -> float:
        return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400.0))


# ──────────────────────────────────────────────────────
# 2. Odds Analyzer - extract market probabilities
# ──────────────────────────────────────────────────────

class OddsAnalyzer:
    """
    Analyze bookmaker odds to extract implied probabilities.
    Bookmaker odds are highly accurate predictors - often better than models.
    """

    @staticmethod
    def odds_to_probabilities(home_odds: float, draw_odds: float, away_odds: float) -> Dict[str, float]:
        """Convert decimal odds to implied probabilities, removing bookmaker margin."""
        if home_odds <= 0 or draw_odds <= 0 or away_odds <= 0:
            return {"home": 0.4, "draw": 0.3, "away": 0.3}

        # Raw implied probabilities (with margin)
        raw_home = 1.0 / home_odds
        raw_draw = 1.0 / draw_odds
        raw_away = 1.0 / away_odds

        # Total margin (overround)
        total = raw_home + raw_draw + raw_away

        # Normalize to remove margin
        return {
            "home": raw_home / total,
            "draw": raw_draw / total,
            "away": raw_away / total,
        }

    @staticmethod
    def odds_to_expected_goals(home_prob: float, away_prob: float, draw_prob: float) -> Tuple[float, float]:
        """Estimate expected goals from win/draw/loss probabilities."""
        # Use empirical relationship between match probabilities and goals
        # Based on Poisson model inversion
        total_goals = 2.65  # World Cup average

        # Home attack strength relative to away
        ratio = home_prob / max(away_prob, 0.05)
        home_attack = math.sqrt(ratio)
        away_attack = 1.0 / home_attack

        # Normalize
        total_attack = home_attack + away_attack
        home_share = home_attack / total_attack

        # Draw probability inversely correlates with goal expectation
        # Higher draw prob → lower expected goals
        goal_factor = 1.0 - 0.5 * draw_prob

        home_goals = total_goals * home_share * goal_factor
        away_goals = total_goals * (1 - home_share) * goal_factor

        return max(home_goals, 0.3), max(away_goals, 0.3)

    @staticmethod
    def analyze_odds(odds_list: List[Dict]) -> Dict:
        """
        Analyze multiple bookmaker odds to get consensus market view.
        Returns averaged probabilities and confidence metrics.
        Now also extracts correct score odds and Asian handicap data.
        """
        if not odds_list:
            return {"available": False, "home": 0, "draw": 0, "away": 0, "consensus": "none"}

        home_probs = []
        draw_probs = []
        away_probs = []
        all_correct_scores = []
        handicap_data = []
        over_under_data = []

        for o in odds_list:
            h, d, a = o.get("home", 0), o.get("draw", 0), o.get("away", 0)
            if h > 0 and d > 0 and a > 0:
                probs = OddsAnalyzer.odds_to_probabilities(h, d, a)
                home_probs.append(probs["home"])
                draw_probs.append(probs["draw"])
                away_probs.append(probs["away"])

                # Collect correct score odds from this bookmaker
                cs_list = o.get("correct_scores", [])
                if cs_list:
                    for cs in cs_list:
                        all_correct_scores.append({
                            "score": cs.get("score", ""),
                            "odd": cs.get("odd", 0),
                            "bookmaker": o.get("bookmaker", cs.get("bookmaker", "unknown")),
                        })

                # Collect handicap data
                if "handicap" in o:
                    handicap_data.append({
                        "bookmaker": o.get("bookmaker", "unknown"),
                        "handicap": o["handicap"],
                    })

                # Collect over/under data
                if "over_under_line" in o:
                    over_under_data.append({
                        "bookmaker": o.get("bookmaker", "unknown"),
                        "line": o["over_under_line"],
                    })

        if not home_probs:
            return {"available": False, "home": 0, "draw": 0, "away": 0, "consensus": "none"}

        avg_home = sum(home_probs) / len(home_probs)
        avg_draw = sum(draw_probs) / len(draw_probs)
        avg_away = sum(away_probs) / len(away_probs)

        # Consensus strength: how much agreement among bookmakers
        home_std = np.std(home_probs) if len(home_probs) > 1 else 0
        consensus = "strong" if home_std < 0.03 else "moderate" if home_std < 0.06 else "weak"

        # Market favorite
        if avg_home > avg_away and avg_home > avg_draw:
            favorite = "home"
        elif avg_away > avg_home and avg_away > avg_draw:
            favorite = "away"
        else:
            favorite = "draw"

        # Build correct score consensus
        cs_consensus = OddsAnalyzer._build_correct_score_consensus(all_correct_scores)

        # Build handicap consensus
        handicap_consensus = None
        if handicap_data:
            avg_hc = sum(h["handicap"] for h in handicap_data) / len(handicap_data)
            handicap_consensus = {
                "line": round(avg_hc, 2),
                "num_sources": len(handicap_data),
            }

        # Build over/under consensus
        ou_consensus = None
        if over_under_data:
            avg_ou = sum(ou["line"] for ou in over_under_data) / len(over_under_data)
            ou_consensus = {
                "line": round(avg_ou, 2),
                "num_sources": len(over_under_data),
            }

        return {
            "available": True,
            "home": round(avg_home, 4),
            "draw": round(avg_draw, 4),
            "away": round(avg_away, 4),
            "consensus": consensus,
            "favorite": favorite,
            "num_bookmakers": len(home_probs),
            "home_std": round(float(home_std), 4),
            "correct_score_consensus": cs_consensus,
            "handicap": handicap_consensus,
            "over_under": ou_consensus,
        }

    @staticmethod
    def _build_correct_score_consensus(correct_scores: List[Dict]) -> Dict:
        """
        Build consensus from correct score odds across multiple bookmakers.
        Convert odds to implied probabilities and average them per scoreline.
        """
        if not correct_scores:
            return {"available": False, "top_scorelines": []}

        # Group by score, averaging implied probabilities
        score_probs = {}
        for cs in correct_scores:
            score = cs.get("score", "")
            odd = cs.get("odd", 0)
            if not score or odd <= 0:
                continue

            # Normalize score format: "1-0" or "Home 1-0" etc
            clean_score = score
            if "Home" in score:
                clean_score = score.replace("Home ", "").strip()
            elif "Away" in score:
                # Swap: "Away 1-0" means away scored 1, home scored 0 → "0-1"
                parts = score.replace("Away ", "").strip().split("-")
                if len(parts) == 2:
                    clean_score = f"{parts[1]}-{parts[0]}"

            # Convert odds to implied probability (with approximate 15% margin removal)
            implied_prob = (1.0 / odd) / 1.15  # Approximate margin removal

            if clean_score not in score_probs:
                score_probs[clean_score] = []
            score_probs[clean_score].append(implied_prob)

        # Average probabilities for each score
        averaged = []
        for score, probs_list in score_probs.items():
            avg_prob = sum(probs_list) / len(probs_list)
            averaged.append({
                "score": score,
                "probability": round(avg_prob, 4),
                "num_sources": len(probs_list),
            })

        # Sort by probability descending
        averaged.sort(key=lambda x: x["probability"], reverse=True)

        # Normalize probabilities so they sum to ~1
        total = sum(a["probability"] for a in averaged)
        if total > 0:
            for a in averaged:
                a["probability"] = round(a["probability"] / total, 4)

        return {
            "available": True,
            "top_scorelines": averaged[:10],  # Top 10 most likely scores
            "total_scores": len(averaged),
        }


# ──────────────────────────────────────────────────────
# 3. Squad Analyzer - evaluate team strength from players
# ──────────────────────────────────────────────────────

class SquadAnalyzer:
    """
    Analyze team squad composition to derive strength metrics.
    Factors: position depth, player quality (ratings/goals), squad balance.
    """

    # Position importance weights for overall team strength
    POSITION_WEIGHTS = {
        "GK": 0.08, "CB": 0.12, "RB": 0.06, "LB": 0.06,
        "RWB": 0.05, "LWB": 0.05, "CDM": 0.10, "CM": 0.10,
        "CAM": 0.10, "RM": 0.05, "LM": 0.05, "RW": 0.06,
        "LW": 0.06, "ST": 0.12, "CF": 0.10, "RF": 0.05, "LF": 0.05,
    }

    ATTACK_POSITIONS = {"ST", "CF", "RW", "LW", "CAM", "RF", "LF"}
    MIDFIELD_POSITIONS = {"CM", "CDM", "RM", "LM"}
    DEFENSE_POSITIONS = {"CB", "RB", "LB", "RWB", "LWB"}
    GK_POSITIONS = {"GK"}

    @staticmethod
    def analyze_squad(players: List[Dict], elo_rating: float = None,
                      fifa_rank: int = None) -> Dict:
        """
        Analyze a team's squad with player stats (ratings, goals, assists).
        Falls back to ELO/FIFA rank when no player stats available.

        Args:
            players: list of {name, position, number, stats?: ...}
            elo_rating: optional elo for fallback scoring
            fifa_rank: optional FIFA rank for fallback (lower = better)
        """
        if not players:
            if elo_rating:
                return SquadAnalyzer._elo_fallback(elo_rating, fifa_rank)
            return {"available": False, "overall": 0.5, "attack": 0.5,
                    "midfield": 0.5, "defense": 0.5, "depth": 0.5}

        # Count players by position group
        attack_players = [p for p in players if p.get("position", "") in SquadAnalyzer.ATTACK_POSITIONS]
        mid_players = [p for p in players if p.get("position", "") in SquadAnalyzer.MIDFIELD_POSITIONS]
        def_players = [p for p in players if p.get("position", "") in SquadAnalyzer.DEFENSE_POSITIONS]
        gk_players = [p for p in players if p.get("position", "") in SquadAnalyzer.GK_POSITIONS]

        total = len(players)

        # Position coverage score
        attack_score = min(len(attack_players) / 5.0, 1.0) if attack_players else 0.2
        mid_score = min(len(mid_players) / 7.0, 1.0) if mid_players else 0.2
        def_score = min(len(def_players) / 7.0, 1.0) if def_players else 0.2
        gk_score = min(len(gk_players) / 2.0, 1.0) if gk_players else 0.2

        # ── Player quality from league stats ──
        attack_quality = SquadAnalyzer._group_quality(attack_players, is_attack=True)
        mid_quality = SquadAnalyzer._group_quality(mid_players, is_attack=False)
        def_quality = SquadAnalyzer._group_quality(def_players, is_attack=False)
        gk_quality = SquadAnalyzer._group_quality(gk_players, is_attack=False)

        # If no quality data at all, use ELO fallback
        has_quality_data = attack_quality != 0.3 or mid_quality != 0.3 or \
                           def_quality != 0.3 or gk_quality != 0.3

        if not has_quality_data and elo_rating:
            fallback = SquadAnalyzer._elo_fallback(elo_rating, fifa_rank)
            # Merge: use position coverage from players, quality from fallback
            attack_final = attack_score * (1 + 0.3 * fallback["attack"])
            mid_final = mid_score * (1 + 0.3 * fallback["midfield"])
            def_final = def_score * (1 + 0.3 * fallback["defense"])
            gk_final = gk_score * (1 + 0.3 * fallback["gk"])
            depth_score = min(total / 26.0, 1.0) if total > 11 else total / 11.0
        else:
            # Blend coverage + quality: quality can boost up to 20% (was 30% to balance)
            attack_final = attack_score * (1 + 0.2 * attack_quality)
            mid_final = mid_score * (1 + 0.2 * mid_quality)
            def_final = def_score * (1 + 0.2 * def_quality)
            gk_final = gk_score * (1 + 0.2 * gk_quality)
            depth_score = min(total / 26.0, 1.0) if total > 11 else total / 11.0

        # Cap at 1.15 (was 1.3, too wide a range)
        attack_final = min(attack_final, 1.15)
        mid_final = min(mid_final, 1.15)
        def_final = min(def_final, 1.15)
        gk_final = min(gk_final, 1.15)

        # Balance
        ideal_ratio = {"attack": 0.22, "midfield": 0.30, "defense": 0.35, "gk": 0.13}
        actual_ratio = {
            "attack": len(attack_players) / max(total, 1),
            "midfield": len(mid_players) / max(total, 1),
            "defense": len(def_players) / max(total, 1),
            "gk": len(gk_players) / max(total, 1),
        }
        balance = 1.0 - sum(abs(actual_ratio[k] - ideal_ratio[k]) for k in ideal_ratio) / 2
        balance = max(balance, 0.3)

        # Overall: weighted combination
        overall = (attack_final * 0.30 + mid_final * 0.25 + def_final * 0.25 +
                   gk_final * 0.05 + depth_score * 0.10 + balance * 0.05)

        # Compute average rating for display
        all_ratings = [p.get("stats", {}).get("avg_rating") for p in players if p.get("stats", {}).get("avg_rating")]
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None

        return {
            "available": True,
            "overall": round(overall, 3),
            "attack": round(attack_final, 3),
            "midfield": round(mid_final, 3),
            "defense": round(def_final, 3),
            "gk": round(gk_final, 3),
            "depth": round(depth_score, 3),
            "balance": round(balance, 3),
            "total_players": total,
            "attack_count": len(attack_players),
            "midfield_count": len(mid_players),
            "defense_count": len(def_players),
            "gk_count": len(gk_players),
            "avg_rating": round(avg_rating, 2) if avg_rating else None,
            "attack_quality": round(attack_quality, 3),
            "mid_quality": round(mid_quality, 3),
            "def_quality": round(def_quality, 3),
        }

    @staticmethod
    def _elo_fallback(elo_rating: float, fifa_rank: int = None) -> Dict:
        """
        Derive squad scores from ELO rating and FIFA rank when no player stats available.
        """
        elo_norm = max(0, min(1, (elo_rating - 1600) / 600))
        rank_norm = 1.0 - max(0, min(1, (fifa_rank or 100) / 210))
        overall = 0.45 + 0.4 * elo_norm + 0.15 * rank_norm
        return {
            "available": True,
            "overall": round(overall, 3),
            "attack": round(overall + 0.05 * elo_norm, 3),
            "midfield": round(overall, 3),
            "defense": round(overall - 0.05 * elo_norm + 0.1 * rank_norm, 3),
            "gk": round(overall, 3),
            "depth": round(0.5 + 0.3 * rank_norm, 3),
            "balance": 0.5,
            "total_players": 0,
            "attack_count": 0, "midfield_count": 0, "defense_count": 0, "gk_count": 0,
            "avg_rating": None,
            "attack_quality": 0.3, "mid_quality": 0.3, "def_quality": 0.3,
        }

    @staticmethod
    def _group_quality(players: List[Dict], is_attack: bool = False) -> float:
        """
        Calculate quality score for a position group based on player stats.
        Returns 0.0-1.0 where 1.0 means all players have excellent stats.
        """
        if not players:
            return 0.0

        quality_scores = []
        for p in players:
            stats = p.get("stats", {})
            if not stats or not stats.get("available"):
                continue

            score = 0.5  # baseline

            # Rating contribution (6.0-8.5 range, normalize to 0-1)
            rating = stats.get("avg_rating")
            if rating:
                score += max(0, min((rating - 6.0) / 2.5, 1.0)) * 0.4

            # Goal contribution for attackers
            if is_attack:
                gpg = stats.get("goals_per_game", 0)
                score += min(gpg / 0.8, 1.0) * 0.3  # 0.8 goals/game is elite

                gc90 = stats.get("goal_contributions_per_90", 0)
                score += min(gc90 / 1.0, 1.0) * 0.2  # 1.0 G+A per 90 is elite
            else:
                # For non-attackers, lower goals expected but rating matters more
                if rating and rating > 7.0:
                    score += 0.15

                # Appearances show regularity
                apps = stats.get("total_appearences", 0)
                if apps >= 25:
                    score += 0.1
                elif apps >= 15:
                    score += 0.05

            quality_scores.append(min(score, 1.0))

        if not quality_scores:
            return 0.3  # Default moderate quality when no stats

        return sum(quality_scores) / len(quality_scores)


# ──────────────────────────────────────────────────────
# 3b. Form Analyzer - real match results
# ──────────────────────────────────────────────────────

class FormAnalyzer:
    """Analyze team form from recent match results."""

    @staticmethod
    def analyze_form(form_data: Dict, recent_matches: List[Dict] = None) -> Dict:
        """
        Analyze team form from API form data and optional detailed recent matches.

        Args:
            form_data: {available, form, wins, draws, losses, goals_for, goals_against, ...}
            recent_matches: Optional list of {date, opponent, home, goals_for, goals_against, league}
                           for deeper analysis including opponent quality adjustment.

        Returns:
            Form analysis with enhanced metrics if recent_matches provided.
        """
        if not form_data or not form_data.get("available"):
            return {"available": False, "form_score": 0.5, "momentum": "neutral"}

        wins = form_data.get("wins", 0)
        draws = form_data.get("draws", 0)
        losses = form_data.get("losses", 0)
        total = wins + draws + losses
        gf = form_data.get("goals_for", 0)
        ga = form_data.get("goals_against", 0)

        if total == 0:
            return {"available": False, "form_score": 0.5, "momentum": "neutral"}

        # Win rate (0-1)
        win_rate = wins / total

        # Goal difference factor
        avg_gd = (gf - ga) / total
        gd_factor = max(0, min(1, 0.5 + avg_gd / 4.0))  # +2 GD/game = 1.0, -2 = 0.0

        # Recent momentum (last 5 results weighted more)
        form_str = form_data.get("form", "")
        recent_weight = 0
        if form_str:
            recent = form_str[-5:]  # Last 5 matches
            for i, c in enumerate(reversed(recent)):
                weight = (i + 1) / 5.0  # More recent = higher weight
                if c == "W":
                    recent_weight += 3 * weight
                elif c == "D":
                    recent_weight += 1 * weight
            recent_weight /= 3.0  # Normalize to 0-1

        # Combined form score
        form_score = win_rate * 0.4 + gd_factor * 0.3 + recent_weight * 0.3

        # Momentum label
        if form_score > 0.7:
            momentum = "hot"
        elif form_score > 0.5:
            momentum = "good"
        elif form_score > 0.35:
            momentum = "neutral"
        else:
            momentum = "cold"

        result = {
            "available": True,
            "form_score": round(form_score, 3),
            "win_rate": round(win_rate, 3),
            "gd_factor": round(gd_factor, 3),
            "momentum": momentum,
            "form_string": form_str,
            "avg_goals_for": form_data.get("avg_goals_for", 0),
            "avg_goals_against": form_data.get("avg_goals_against", 0),
        }

        # Enhanced analysis if recent_matches provided
        if recent_matches and len(recent_matches) > 0:
            enhanced = FormAnalyzer._analyze_recent_matches(recent_matches)
            result["enhanced"] = enhanced
            # Blend enhanced score into overall form_score
            if enhanced.get("available"):
                form_score = form_score * 0.6 + enhanced["adjusted_form_score"] * 0.4
                result["form_score"] = round(form_score, 3)
                result["opponent_quality_adj"] = enhanced.get("opponent_quality_adjustment", 0)
                result["home_away_split"] = enhanced.get("home_away_split", {})
                result["trend_direction"] = enhanced.get("trend_direction", "stable")
                result["goal_consistency"] = enhanced.get("goal_consistency", {})

        return result

    @staticmethod
    def _analyze_recent_matches(matches: List[Dict]) -> Dict:
        """
        Analyze detailed recent matches for opponent quality, home/away split,
        trend direction, and goal consistency.

        Args:
            matches: List of {date, opponent, home, goals_for, goals_against, league}

        Returns:
            Enhanced form metrics.
        """
        if not matches:
            return {"available": False}

        # FIFA ranking tiers for opponent quality (simplified)
        TOP_10_BONUS = 0.15
        TOP_20_BONUS = 0.08
        TOP_50_BONUS = 0.03
        BELOW_80_PENALTY = -0.05

        opponent_quality_adj = 0.0
        home_results = {"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
        away_results = {"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
        goals_scored = []
        points_earned = []

        for match in matches:
            gf = match.get("goals_for", 0)
            ga = match.get("goals_against", 0)
            is_home = match.get("home", True)
            opponent_rank = match.get("opponent_rank", 50)  # Default mid-tier

            # Opponent quality adjustment
            if opponent_rank <= 10:
                opponent_quality_adj += TOP_10_BONUS
            elif opponent_rank <= 20:
                opponent_quality_adj += TOP_20_BONUS
            elif opponent_rank <= 50:
                opponent_quality_adj += TOP_50_BONUS
            elif opponent_rank > 80:
                opponent_quality_adj += BELOW_80_PENALTY

            # Track goals
            goals_scored.append(gf)

            # Track points
            if gf > ga:
                points_earned.append(3)
            elif gf == ga:
                points_earned.append(1)
            else:
                points_earned.append(0)

            # Home/away split
            if is_home:
                home_results["goals_for"] += gf
                home_results["goals_against"] += ga
                if gf > ga:
                    home_results["wins"] += 1
                elif gf == ga:
                    home_results["draws"] += 1
                else:
                    home_results["losses"] += 1
            else:
                away_results["goals_for"] += gf
                away_results["goals_against"] += ga
                if gf > ga:
                    away_results["wins"] += 1
                elif gf == ga:
                    away_results["draws"] += 1
                else:
                    away_results["losses"] += 1

        # Calculate trend direction (improving vs declining)
        num_matches = len(matches)
        if num_matches >= 3:
            first_half = points_earned[:num_matches // 2]
            second_half = points_earned[num_matches // 2:]
            first_avg = sum(first_half) / len(first_half) if first_half else 0
            second_avg = sum(second_half) / len(second_half) if second_half else 0
            trend_diff = second_avg - first_avg
            if trend_diff > 0.5:
                trend = "improving"
            elif trend_diff < -0.5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Goal scoring consistency (standard deviation)
        if len(goals_scored) >= 2:
            goal_std = float(np.std(goals_scored))
            goal_mean = float(np.mean(goals_scored))
            # Lower std relative to mean = more consistent
            consistency = max(0, 1.0 - (goal_std / max(goal_mean + 0.5, 1.0)))
        else:
            goal_std = 0.0
            consistency = 0.5

        # Calculate home/away performance difference
        home_total = home_results["wins"] + home_results["draws"] + home_results["losses"]
        away_total = away_results["wins"] + away_results["draws"] + away_results["losses"]
        home_ppg = (home_results["wins"] * 3 + home_results["draws"]) / max(home_total, 1)
        away_ppg = (away_results["wins"] * 3 + away_results["draws"]) / max(away_total, 1)

        # Adjusted form score incorporating all factors
        base_form = sum(points_earned) / (num_matches * 3) if num_matches > 0 else 0.5
        adjusted_form = base_form + opponent_quality_adj / max(num_matches, 1)
        adjusted_form = max(0, min(1, adjusted_form))

        return {
            "available": True,
            "adjusted_form_score": round(adjusted_form, 3),
            "opponent_quality_adjustment": round(opponent_quality_adj, 3),
            "trend_direction": trend,
            "goal_consistency": {
                "std": round(goal_std, 3),
                "mean": round(float(np.mean(goals_scored)), 2) if goals_scored else 0,
                "consistency_score": round(consistency, 3),
            },
            "home_away_split": {
                "home": {
                    "ppg": round(home_ppg, 3),
                    "goals_for_avg": round(home_results["goals_for"] / max(home_total, 1), 2),
                    "goals_against_avg": round(home_results["goals_against"] / max(home_total, 1), 2),
                    **home_results,
                },
                "away": {
                    "ppg": round(away_ppg, 3),
                    "goals_for_avg": round(away_results["goals_for"] / max(away_total, 1), 2),
                    "goals_against_avg": round(away_results["goals_against"] / max(away_total, 1), 2),
                    **away_results,
                },
                "home_advantage": round(home_ppg - away_ppg, 3),
            },
            "matches_analyzed": num_matches,
        }


# ──────────────────────────────────────────────────────
# 4. Team Strength (ELO + Form + FIFA Rank)
# ──────────────────────────────────────────────────────

class TeamStrength:
    ELO_BASELINE = 1800.0
    ELO_SCALE = 600.0

    @staticmethod
    def _form_multiplier(form_str: str) -> float:
        if not form_str:
            return 1.0
        points = sum(3 if c.upper() == "W" else 1 if c.upper() == "D" else 0 for c in form_str)
        max_points = len(form_str) * 3
        if max_points == 0:
            return 1.0
        return 0.85 + 0.30 * (points / max_points)

    @staticmethod
    def compute_strength(elo: float, form_str: str = "", fifa_rank: int = 30,
                         tournament_experience: float = 1.0,
                         is_host: bool = False) -> Dict[str, float]:
        """
        Compute team strength based on ELO, form, FIFA rank, and host status.

        Args:
            elo: ELO rating
            form_str: Recent form string (e.g., "WDWLL")
            fifa_rank: FIFA world ranking
            tournament_experience: Historical tournament performance factor
            is_host: Whether the team is a host country (gets host boost)

        Returns:
            Dict with attack, defense_mult, and various factor breakdowns
        """
        elo_factor = math.exp((elo - TeamStrength.ELO_BASELINE) / TeamStrength.ELO_SCALE)
        form_boost = TeamStrength._form_multiplier(form_str)

        rank_factor = 1.0
        if fifa_rank <= 5:
            rank_factor = 1.06
        elif fifa_rank <= 10:
            rank_factor = 1.03
        elif fifa_rank <= 20:
            rank_factor = 1.01
        elif fifa_rank >= 60:
            rank_factor = 0.95

        exp_factor = 0.94 + 0.06 * tournament_experience

        # Host boost: 8% bonus for host countries
        host_boost = 1.08 if is_host else 1.0

        attack = elo_factor * form_boost * rank_factor * exp_factor * host_boost
        defense_mult = 1.0 / max(attack * 0.7, 0.5)

        result = {
            "attack": round(attack, 4),
            "defense_mult": round(defense_mult, 4),
            "elo_factor": round(elo_factor, 4),
            "form_boost": round(form_boost, 4),
            "rank_factor": round(rank_factor, 4),
            "host_boost": round(host_boost, 4),
        }
        return result


# ──────────────────────────────────────────────────────
# 5. Comprehensive Match Predictor
# ──────────────────────────────────────────────────────

class MatchPredictor:
    """
    Multi-factor match prediction engine.

    Combines signals from:
    - ELO + Poisson model (weight: 0.35)
    - Bookmaker odds (weight: 0.40) - market is smart
    - Squad analysis (weight: 0.15)
    - Form/momentum (weight: 0.10)

    Weights calibrated via backtesting.
    """

    # Signal weights (calibrated via backtesting)
    WEIGHT_ELO = 0.35
    WEIGHT_ODDS = 0.40
    WEIGHT_SQUAD = 0.15
    WEIGHT_FORM = 0.10

    LEAGUE_AVG_GOALS = 2.65
    DC_RHO = -0.13
    MAX_SCORE = 8

    def __init__(self, teams_data: Optional[List[Dict]] = None):
        self.teams: Dict[str, Dict] = {}
        if teams_data:
            for t in teams_data:
                self.teams[t["code"]] = t
        self.elo_system = ELORatingSystem()

    def load_teams_from_file(self, filename: str = "teams.json"):
        data = _load_json(filename)
        for t in data.get("teams", []):
            self.teams[t["code"]] = t

    def get_team(self, code: str) -> Optional[Dict]:
        return self.teams.get(code)

    # ─────────────────────────────────────────
    # Venue factor calculation
    # ─────────────────────────────────────────

    @staticmethod
    def _venue_factor(venue_city: str, team_code: str) -> float:
        """
        Calculate venue-based adjustment factor for a team.

        Args:
            venue_city: Name of the host city
            team_code: Team's country code

        Returns:
            Multiplier for expected goals (1.0 = no adjustment)
        """
        venue = VENUE_INFO.get(venue_city)
        if not venue:
            return 1.0

        host_country = venue.get("host_country", "")
        climate = venue.get("climate", "moderate")
        altitude = venue.get("altitude", 0)

        factor = 1.0

        # High altitude penalty for non-host teams in Mexico venues
        if altitude > 2000 and team_code not in {"MEX", host_country}:
            # Mexico City: 2240m causes significant altitude effects
            factor *= 0.92  # 8% reduction
        elif altitude > 1500 and team_code not in {"MEX", host_country}:
            # Guadalajara: 1560m moderate altitude
            factor *= 0.96

        # Hot/humid climate penalty for European teams
        if climate in ("hot_humid", "hot") and team_code in EUROPEAN_TEAMS:
            if climate == "hot_humid":
                # Miami, Houston: high heat and humidity
                factor *= 0.95
            else:
                # Dallas, other hot venues
                factor *= 0.97

        return factor

    # ─────────────────────────────────────────
    # Knockout stage adjustments
    # ─────────────────────────────────────────

    @staticmethod
    def _apply_knockout_adjustments(expected_goals_home: float, expected_goals_away: float,
                                     draw_prob: float, stage: str) -> Tuple[float, float, float, float]:
        """
        Apply adjustments for knockout stage matches.

        Args:
            expected_goals_home: Home team expected goals
            expected_goals_away: Away team expected goals
            draw_prob: Draw probability
            stage: One of "group", "round32", "round16", "quarter", "semi", "final", "third"

        Returns:
            Tuple of (adjusted_home_goals, adjusted_away_goals, adjusted_draw_prob, extra_time_prob)
        """
        if stage == "group":
            return expected_goals_home, expected_goals_away, draw_prob, 0.0

        # Knockout stages: progressive conservatism
        # Deeper stages → fewer goals (more conservative), fewer draws (more decisive)
        stage_multipliers = {
            "round32": 0.92,
            "round16": 0.92,
            "quarter":  0.88,
            "semi":     0.85,
            "final":    0.85,
            "third":    0.92,
        }
        draw_multipliers = {
            "round32": 0.97,
            "round16": 0.97,
            "quarter":  0.93,
            "semi":     0.90,
            "final":    0.90,
            "third":    0.95,
        }
        goal_mult = stage_multipliers.get(stage, 0.90)
        draw_mult = draw_multipliers.get(stage, 0.95)

        adj_home_goals = expected_goals_home * goal_mult
        adj_away_goals = expected_goals_away * goal_mult
        adj_draw_prob = draw_prob * draw_mult

        # Extra time probability based on stage
        extra_time_probs = {
            "round32": 0.25,
            "round16": 0.25,
            "quarter": 0.15,
            "semi": 0.30,
            "final": 0.25,
            "third": 0.20,
        }
        extra_time_prob = extra_time_probs.get(stage, 0.25)

        return adj_home_goals, adj_away_goals, adj_draw_prob, extra_time_prob

    # ─────────────────────────────────────────
    # Core: ELO + Poisson prediction
    # ─────────────────────────────────────────

    def _elo_poisson_predict(self, team1_data: Dict, team2_data: Dict,
                              venue_city: str = None) -> Dict:
        """Baseline ELO + Poisson prediction."""
        elo1 = team1_data.get("elo_rating", 1800)
        elo2 = team2_data.get("elo_rating", 1800)
        form1 = team1_data.get("recent_form", "")
        form2 = team2_data.get("recent_form", "")
        rank1 = team1_data.get("fifa_rank", 30)
        rank2 = team2_data.get("fifa_rank", 30)
        code1 = team1_data.get("code", "")
        code2 = team2_data.get("code", "")

        exp1 = self._tournament_experience(code1)
        exp2 = self._tournament_experience(code2)

        # Check if teams are hosts
        is_host1 = code1 in HOST_COUNTRIES
        is_host2 = code2 in HOST_COUNTRIES

        s1 = TeamStrength.compute_strength(elo1, form1, rank1, exp1, is_host1)
        s2 = TeamStrength.compute_strength(elo2, form2, rank2, exp2, is_host2)

        base_goals = self.LEAGUE_AVG_GOALS / 2.0

        # Home advantage logic for World Cup:
        # - Host country gets real home advantage (1.15)
        # - All other "home" teams at neutral venue (1.0)
        if is_host1:
            home_advantage = 1.15
        elif is_host2:
            # Team2 is host, so they get advantage, team1 gets neutral
            home_advantage = 1.0
        else:
            # Neutral venue - neither team is host
            home_advantage = 1.0

        expected_goals_1 = base_goals * s1["attack"] * s2["defense_mult"] * home_advantage
        expected_goals_2 = base_goals * s2["attack"] * s1["defense_mult"]

        # Apply venue factors if specified
        if venue_city:
            venue_factor1 = self._venue_factor(venue_city, code1)
            venue_factor2 = self._venue_factor(venue_city, code2)
            expected_goals_1 *= venue_factor1
            expected_goals_2 *= venue_factor2

        expected_goals_1 = max(expected_goals_1, 0.15)
        expected_goals_2 = max(expected_goals_2, 0.15)

        # Poisson matrix
        prob_matrix = np.zeros((self.MAX_SCORE + 1, self.MAX_SCORE + 1))
        for i in range(self.MAX_SCORE + 1):
            for j in range(self.MAX_SCORE + 1):
                p_i = poisson.pmf(i, expected_goals_1)
                p_j = poisson.pmf(j, expected_goals_2)
                prob = p_i * p_j
                if i <= 1 and j <= 1:
                    prob *= self._dixon_coles_factor(i, j, expected_goals_1, expected_goals_2)
                prob_matrix[i][j] = prob

        home_win = float(sum(prob_matrix[i][j] for i in range(self.MAX_SCORE + 1) for j in range(self.MAX_SCORE + 1) if i > j))
        away_win = float(sum(prob_matrix[i][j] for i in range(self.MAX_SCORE + 1) for j in range(self.MAX_SCORE + 1) if i < j))
        draw = float(sum(prob_matrix[i][j] for i in range(self.MAX_SCORE + 1) for j in range(self.MAX_SCORE + 1) if i == j))

        # Top scorelines
        scorelines = []
        for i in range(self.MAX_SCORE + 1):
            for j in range(self.MAX_SCORE + 1):
                scorelines.append({"score": f"{i}-{j}", "probability": float(prob_matrix[i][j])})
        scorelines.sort(key=lambda x: x["probability"], reverse=True)

        return {
            "home_win_prob": home_win,
            "draw_prob": draw,
            "away_win_prob": away_win,
            "expected_goals_home": expected_goals_1,
            "expected_goals_away": expected_goals_2,
            "top_5_scorelines": scorelines[:5],
            "score_probability_matrix": prob_matrix,
            "strengths": {"team1": s1, "team2": s2},
            "elo_diff": round(elo1 - elo2, 1),
        }

    # ─────────────────────────────────────────
    # Fast ELO-only prediction (for Monte Carlo)
    # ─────────────────────────────────────────

    def predict_match_fast(self, team1_data: Dict, team2_data: Dict,
                           stage: str = "group") -> Dict:
        """
        Lightweight ELO-only prediction for Monte Carlo simulation.
        Returns only the fields needed: home_win_prob, draw_prob, away_win_prob,
        expected_goals_home, expected_goals_away.

        Now includes: host advantage, venue factors, knockout conservatism,
        and underdog parking-the-bus effect.
        ~100x faster than predict_match() by skipping multi-factor analysis.
        """
        elo1 = team1_data.get("elo_rating", 1800)
        elo2 = team2_data.get("elo_rating", 1800)
        form1 = team1_data.get("recent_form", "")
        form2 = team2_data.get("recent_form", "")
        rank1 = team1_data.get("fifa_rank", 30)
        rank2 = team2_data.get("fifa_rank", 30)
        code1 = team1_data.get("code", "")
        code2 = team2_data.get("code", "")

        exp1 = self._tournament_experience(code1)
        exp2 = self._tournament_experience(code2)

        is_host1 = code1 in HOST_COUNTRIES
        is_host2 = code2 in HOST_COUNTRIES

        s1 = TeamStrength.compute_strength(elo1, form1, rank1, exp1, is_host1)
        s2 = TeamStrength.compute_strength(elo2, form2, rank2, exp2, is_host2)

        base_goals = self.LEAGUE_AVG_GOALS / 2.0

        # Host advantage
        if is_host1:
            home_advantage = 1.15
        else:
            home_advantage = 1.0

        eg1 = max(base_goals * s1["attack"] * s2["defense_mult"] * home_advantage, 0.15)
        eg2 = max(base_goals * s2["attack"] * s1["defense_mult"], 0.15)

        # --- Venue factor: high altitude hurts European teams ---
        venue1 = self._venue_factor("Mexico City", code1)  # worst-case altitude
        venue2 = self._venue_factor("Mexico City", code2)
        eg1 *= venue1
        eg2 *= venue2

        # --- Underdog parking-the-bus: large ELO gap → weaker team is more defensive ---
        elo_diff = elo1 - elo2
        if abs(elo_diff) > 200:
            if elo_diff > 0:
                # Team2 is weak → they park the bus, reduce their attack more
                eg2 *= 0.85
                # Stronger team slightly boosted in attack vs parked bus
                eg1 *= 1.05
            else:
                eg1 *= 0.85
                eg2 *= 1.05

        # --- Knockout stage adjustments ---
        # Progressive conservatism: deeper stages → fewer goals, fewer draws
        if stage != "group":
            stage_mult = {
                "round32": 0.92,
                "round16": 0.92,
                "quarter":  0.88,
                "semi":     0.85,
                "final":    0.85,
                "third":    0.92,
            }
            goal_mult_default = stage_mult.get(stage, 0.90)
            eg1 *= goal_mult_default
            eg2 *= goal_mult_default

        # Clamp
        eg1 = max(eg1, 0.10)
        eg2 = max(eg2, 0.10)

        # Fast probability calculation using Elo win expectancy formula
        home_base = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))

        # Adjust for host advantage
        if is_host1:
            home_base = min(0.95, home_base * 1.08)
        elif is_host2:
            home_base = max(0.05, home_base * 0.92)

        # Draw probability from expected goals (lower total goals = higher draw chance)
        total_goals = eg1 + eg2
        draw_base = 0.26 - 0.03 * total_goals
        draw_base = max(0.10, min(0.35, draw_base))

        # Knockout stages: draws are less likely (teams play to win)
        if stage != "group":
            draw_mult = {
                "round32": 0.97,
                "round16": 0.97,
                "quarter":  0.93,
                "semi":     0.90,
                "final":    0.90,
                "third":    0.95,
            }
            draw_base *= draw_mult.get(stage, 0.95)

        home_win = home_base * (1.0 - draw_base)
        away_win = (1.0 - home_base) * (1.0 - draw_base)

        # Normalize
        total = home_win + draw_base + away_win
        home_win /= total
        draw_base /= total
        away_win /= total

        return {
            "home_win_prob": home_win * 100,
            "draw_prob": draw_base * 100,
            "away_win_prob": away_win * 100,
            "expected_goals_home": eg1,
            "expected_goals_away": eg2,
        }

    # ─────────────────────────────────────────
    # Core: Comprehensive prediction
    # ─────────────────────────────────────────

    def predict_match(self, team1_data: Dict, team2_data: Dict,
                      odds_list: List[Dict] = None,
                      squad1: List[Dict] = None,
                      squad2: List[Dict] = None,
                      form1_data: Dict = None,
                      form2_data: Dict = None,
                      recent_matches1: List[Dict] = None,
                      recent_matches2: List[Dict] = None,
                      injuries1: List[Dict] = None,
                      injuries2: List[Dict] = None,
                      stage: str = "group",
                      venue_city: str = None) -> Dict:
        """
        Comprehensive multi-factor match prediction.

        Args:
            team1_data, team2_data: team info with elo_rating, recent_form, fifa_rank
            odds_list: list of {bookmaker, home, draw, away} dicts from bookmakers
            squad1, squad2: list of player dicts {name, position, number, stats?}
            form1_data, form2_data: real form data from API {available, form, wins, ...}
            recent_matches1, recent_matches2: detailed recent match data for enhanced analysis
            injuries1, injuries2: list of injured players {player_name, position, importance}
            stage: match stage - "group", "round32", "round16", "quarter", "semi", "final", "third"
            venue_city: host city for venue-based adjustments

        Returns:
            Combined prediction with breakdown of each factor's contribution.
        """
        # 1. ELO + Poisson baseline (with venue factors)
        elo_pred = self._elo_poisson_predict(team1_data, team2_data, venue_city)

        elo_home = elo_pred["home_win_prob"]
        elo_draw = elo_pred["draw_prob"]
        elo_away = elo_pred["away_win_prob"]

        # 2. Odds analysis
        odds_analysis = OddsAnalyzer.analyze_odds(odds_list or [])
        if odds_analysis["available"]:
            odds_home = odds_analysis["home"]
            odds_draw = odds_analysis["draw"]
            odds_away = odds_analysis["away"]
        else:
            odds_home, odds_draw, odds_away = 0, 0, 0

        # 3. Squad analysis
        squad1_analysis = SquadAnalyzer.analyze_squad(
            squad1 or [],
            elo_rating=team1_data.get("elo_rating"),
            fifa_rank=team1_data.get("fifa_rank")
        )
        squad2_analysis = SquadAnalyzer.analyze_squad(
            squad2 or [],
            elo_rating=team2_data.get("elo_rating"),
            fifa_rank=team2_data.get("fifa_rank")
        )

        if squad1_analysis["available"] and squad2_analysis["available"]:
            # Squad strength affects expected goals
            squad_ratio = squad1_analysis["overall"] / max(squad2_analysis["overall"], 0.1)
            # Convert to probability adjustment
            squad_home_adj = 0.5 + 0.15 * (squad_ratio - 1.0)
            squad_away_adj = 0.5 - 0.15 * (squad_ratio - 1.0)
            squad_draw_adj = 0.25 - 0.05 * abs(squad_ratio - 1.0)

            # Normalize
            total = squad_home_adj + squad_away_adj + squad_draw_adj
            squad_home = squad_home_adj / total
            squad_draw = squad_draw_adj / total
            squad_away = squad_away_adj / total
        else:
            squad_home, squad_draw, squad_away = 0, 0, 0

        # 4. Form analysis - use real API form data if available
        form1_analysis = FormAnalyzer.analyze_form(form1_data or {}, recent_matches1)
        form2_analysis = FormAnalyzer.analyze_form(form2_data or {}, recent_matches2)

        if form1_analysis["available"] and form2_analysis["available"]:
            # Use real form scores
            form_ratio = form1_analysis["form_score"] / max(form2_analysis["form_score"], 0.1)
            form_home = 0.5 + 0.15 * (form_ratio - 1.0)
            form_away = 0.5 - 0.15 * (form_ratio - 1.0)
            form_draw = 0.25 - 0.05 * abs(form_ratio - 1.0)
        else:
            # Fallback to ELO model's form_boost
            s1 = elo_pred["strengths"]["team1"]
            s2 = elo_pred["strengths"]["team2"]
            form1_boost = s1.get("form_boost", 1.0)
            form2_boost = s2.get("form_boost", 1.0)
            form_ratio = form1_boost / max(form2_boost, 0.5)
            form_home = 0.5 + 0.1 * (form_ratio - 1.0)
            form_away = 0.5 - 0.1 * (form_ratio - 1.0)
            form_draw = 0.25 - 0.03 * abs(form_ratio - 1.0)
            form1_analysis = {"available": False, "form_score": form1_boost, "momentum": "unknown"}
            form2_analysis = {"available": False, "form_score": form2_boost, "momentum": "unknown"}
        ft = form_home + form_away + form_draw
        form_home /= ft
        form_draw /= ft
        form_away /= ft

        # 5. Injury analysis
        injury1_analysis = InjuryAnalyzer.analyze_injuries(injuries1 or [])
        injury2_analysis = InjuryAnalyzer.analyze_injuries(injuries2 or [])

        # ── Dynamic weight adjustment ──
        has_odds = odds_analysis["available"]
        has_squad = squad1_analysis["available"] and squad2_analysis["available"]
        has_form = form1_analysis["available"] and form2_analysis["available"]
        has_injuries = injury1_analysis.get("total_injuries", 0) > 0 or injury2_analysis.get("total_injuries", 0) > 0

        # Base weights
        if has_odds and has_squad and has_form:
            w_elo, w_odds, w_squad, w_form = 0.25, 0.35, 0.20, 0.20
        elif has_odds and has_squad:
            w_elo, w_odds, w_squad, w_form = 0.30, 0.40, 0.20, 0.10
        elif has_odds:
            w_elo, w_odds, w_squad, w_form = 0.40, 0.45, 0.0, 0.15
        elif has_squad and has_form:
            w_elo, w_odds, w_squad, w_form = 0.35, 0.0, 0.30, 0.35
        elif has_squad:
            w_elo, w_odds, w_squad, w_form = 0.50, 0.0, 0.30, 0.20
        else:
            w_elo, w_odds, w_squad, w_form = 1.0, 0.0, 0.0, 0.0

        # Dynamic adjustments based on data quality
        num_bookmakers = odds_analysis.get("num_bookmakers", 0) if has_odds else 0

        # Odds weight adjustment based on bookmaker count
        if num_bookmakers >= 3:
            # Multiple reliable bookmakers → boost odds weight
            w_odds *= 1.15
            # If consensus is strong and multiple bookmakers, odds can dominate
            if odds_analysis.get("consensus") == "strong":
                w_odds *= 1.05
                w_elo *= 0.90
        elif num_bookmakers == 1:
            w_odds *= 0.80

        # --- Odds-ELO divergence detection ---
        # When odds direction contradicts ELO direction, odds are usually right
        # (market incorporates information ELO doesn't have)
        if has_odds and num_bookmakers >= 3:
            elo_favors = "home" if elo_home > max(elo_draw, elo_away) else \
                         "away" if elo_away > max(elo_home, elo_draw) else "draw"
            odds_favors = "home" if odds_home > max(odds_draw, odds_away) else \
                          "away" if odds_away > max(odds_home, odds_draw) else "draw"
            if elo_favors != odds_favors and elo_favors != "draw" and odds_favors != "draw":
                # Market disagrees with ELO → trust market more
                w_odds *= 1.15
                w_elo *= 0.85

        # Form weight adjustment based on match count
        form1_matches = form1_data.get("wins", 0) + form1_data.get("draws", 0) + form1_data.get("losses", 0) if form1_data else 0
        form2_matches = form2_data.get("wins", 0) + form2_data.get("draws", 0) + form2_data.get("losses", 0) if form2_data else 0
        avg_form_matches = (form1_matches + form2_matches) / 2 if (form1_matches + form2_matches) > 0 else 0

        if avg_form_matches > 8:
            w_form *= 1.15
        elif avg_form_matches < 5 and avg_form_matches > 0:
            w_form *= 0.70

        # Squad weight adjustment for injuries
        # When injuries matter (high-impact players missing), increase injury factor weight
        # by shifting a small amount from squad to odds (odds reflect injury info)
        if has_injuries:
            # Increase odds weight (market prices in injuries)
            w_odds *= 1.05
            # Reduce squad weight slightly since squad data doesn't reflect absences
            w_squad *= 0.90

        # Normalize weights
        total_weight = w_elo + w_odds + w_squad + w_form
        w_elo /= total_weight
        w_odds /= total_weight
        w_squad /= total_weight
        w_form /= total_weight

        combined_home = w_elo * elo_home + w_odds * odds_home + w_squad * squad_home + w_form * form_home
        combined_draw = w_elo * elo_draw + w_odds * odds_draw + w_squad * squad_draw + w_form * form_draw
        combined_away = w_elo * elo_away + w_odds * odds_away + w_squad * squad_away + w_form * form_away

        # Normalize
        total_prob = combined_home + combined_draw + combined_away
        combined_home /= total_prob
        combined_draw /= total_prob
        combined_away /= total_prob

        # ── Adjust expected goals based on combined probabilities ──
        # If odds suggest different goal expectations, blend them
        if has_odds:
            odds_eg_home, odds_eg_away = OddsAnalyzer.odds_to_expected_goals(
                odds_home, odds_away, odds_draw
            )
            expected_goals_home = 0.5 * elo_pred["expected_goals_home"] + 0.5 * odds_eg_home
            expected_goals_away = 0.5 * elo_pred["expected_goals_away"] + 0.5 * odds_eg_away
        else:
            expected_goals_home = elo_pred["expected_goals_home"]
            expected_goals_away = elo_pred["expected_goals_away"]

        # Apply injury penalties to expected goals
        if has_injuries:
            expected_goals_home *= (1 - injury1_analysis["impact_score"])
            expected_goals_away *= (1 - injury2_analysis["impact_score"])

        # ── Apply knockout stage adjustments ──
        adj_home_goals, adj_away_goals, adj_draw_prob, extra_time_prob = \
            self._apply_knockout_adjustments(expected_goals_home, expected_goals_away, combined_draw, stage)

        expected_goals_home = adj_home_goals
        expected_goals_away = adj_away_goals
        combined_draw = adj_draw_prob

        # Re-normalize probabilities after knockout adjustment
        total_prob = combined_home + combined_draw + combined_away
        combined_home /= total_prob
        combined_draw /= total_prob
        combined_away /= total_prob

        # ── Recompute scorelines with combined expected goals ──
        combined_scorelines = self._compute_scorelines(expected_goals_home, expected_goals_away)

        # ── Blend with correct score odds (if available) ──
        cs_consensus = odds_analysis.get("correct_score_consensus", {})
        if cs_consensus.get("available") and cs_consensus.get("top_scorelines"):
            combined_scorelines = self._blend_scorelines_with_odds(
                combined_scorelines, cs_consensus["top_scorelines"]
            )

        # ── Apply handicap odds adjustment (if available) ──
        handicap_info = odds_analysis.get("handicap")
        if handicap_info and has_odds:
            hc_line = handicap_info.get("line", 0)
            # Handicap line indicates market view of goal difference
            # Blend model goals towards market-implied difference
            hc_implied_diff = hc_line * 0.6  # Convert handicap to goal difference
            model_diff = expected_goals_home - expected_goals_away
            # Blend: 40% market, 60% model
            blended_diff = model_diff * 0.6 + hc_implied_diff * 0.4
            avg_goals = (expected_goals_home + expected_goals_away) / 2
            expected_goals_home = avg_goals + blended_diff / 2
            expected_goals_away = avg_goals - blended_diff / 2
            expected_goals_home = max(0.3, min(expected_goals_home, 4.0))
            expected_goals_away = max(0.3, min(expected_goals_away, 4.0))

        # ── Apply over/under odds (if available) ──
        ou_info = odds_analysis.get("over_under")
        if ou_info and has_odds:
            ou_line = ou_info.get("line", 2.5)
            model_total = expected_goals_home + expected_goals_away
            if abs(model_total - ou_line) > 0.2:
                # Blend model total towards market total with 40% weight (was 30%)
                adj_factor = 0.4
                target_total = model_total * (1 - adj_factor) + ou_line * adj_factor
                ratio = target_total / max(model_total, 0.5)
                expected_goals_home *= ratio
                expected_goals_away *= ratio

        # ── Confidence level ──
        max_prob = max(combined_home, combined_draw, combined_away)
        confidence = self._confidence_level(combined_home, combined_away, max_prob, has_odds, has_squad)

        # ── Prediction advice ──
        advice = self._generate_advice(combined_home, combined_draw, combined_away,
                                        expected_goals_home, expected_goals_away,
                                        odds_analysis, squad1_analysis, squad2_analysis)

        # Build result
        result = {
            "home_win_prob": round(combined_home * 100, 2),
            "draw_prob": round(combined_draw * 100, 2),
            "away_win_prob": round(combined_away * 100, 2),
            "expected_goals_home": round(float(expected_goals_home), 3),
            "expected_goals_away": round(float(expected_goals_away), 3),
            "top_5_scorelines": [
                {"score": s["score"], "probability": round(s["probability"] * 100, 2)}
                for s in combined_scorelines[:5]
            ],
            "score_probability_matrix": {
                f"{i}-{j}": round(float(p) * 100, 2)
                for i in range(5) for j in range(5)
                for p in [poisson.pmf(i, expected_goals_home) * poisson.pmf(j, expected_goals_away)]
            },
            "confidence_level": confidence,
            "elo_diff": elo_pred["elo_diff"],
            "advice": advice,
            # Factor breakdown
            "factors": {
                "elo_model": {
                    "weight": round(w_elo, 4),
                    "home_win": round(elo_home * 100, 2),
                    "draw": round(elo_draw * 100, 2),
                    "away_win": round(elo_away * 100, 2),
                    "expected_goals_home": round(float(elo_pred["expected_goals_home"]), 3),
                    "expected_goals_away": round(float(elo_pred["expected_goals_away"]), 3),
                },
                "odds_analysis": {
                    "weight": round(w_odds, 4),
                    "available": has_odds,
                    "home_win": round(odds_home * 100, 2) if has_odds else 0,
                    "draw": round(odds_draw * 100, 2) if has_odds else 0,
                    "away_win": round(odds_away * 100, 2) if has_odds else 0,
                    "consensus": odds_analysis.get("consensus", "none"),
                    "num_bookmakers": odds_analysis.get("num_bookmakers", 0),
                    "handicap": odds_analysis.get("handicap"),
                    "over_under": odds_analysis.get("over_under"),
                    "correct_score_consensus": odds_analysis.get("correct_score_consensus", {}),
                },
                "squad_analysis": {
                    "weight": round(w_squad, 4),
                    "available": has_squad,
                    "team1": squad1_analysis,
                    "team2": squad2_analysis,
                },
                "form_analysis": {
                    "weight": round(w_form, 4),
                    "team1": form1_analysis,
                    "team2": form2_analysis,
                },
            },
            "strengths": elo_pred["strengths"],
        }

        # Add stage-specific info
        if stage != "group":
            result["stage"] = stage
            result["extra_time_probability"] = round(extra_time_prob * 100, 2)

        # Add injury analysis if present
        if has_injuries:
            result["injury_analysis"] = {
                "team1": injury1_analysis,
                "team2": injury2_analysis,
            }

        # Add venue info if present
        if venue_city:
            result["venue"] = venue_city

        return result

    def _compute_scorelines(self, lambda1: float, lambda2: float) -> List[Dict]:
        """Compute scoreline probabilities from expected goals."""
        scorelines = []
        for i in range(self.MAX_SCORE + 1):
            for j in range(self.MAX_SCORE + 1):
                p_i = poisson.pmf(i, lambda1)
                p_j = poisson.pmf(j, lambda2)
                prob = p_i * p_j
                if i <= 1 and j <= 1:
                    prob *= self._dixon_coles_factor(i, j, lambda1, lambda2)
                scorelines.append({"score": f"{i}-{j}", "probability": float(prob)})
        scorelines.sort(key=lambda x: x["probability"], reverse=True)
        return scorelines

    @staticmethod
    def _blend_scorelines_with_odds(model_scorelines: List[Dict], odds_scorelines: List[Dict],
                                     model_weight: float = 0.6, odds_weight: float = 0.4) -> List[Dict]:
        """
        Blend model-predicted scorelines with market correct score odds.

        Market correct score odds are highly informative because they aggregate
        millions of dollars of betting activity. We blend them with our Poisson
        model to get a more accurate scoreline distribution.

        Args:
            model_scorelines: Scorelines from Poisson model
            odds_scorelines: Scorelines from market correct score odds
            model_weight: Weight for model predictions (default 0.6)
            odds_weight: Weight for market odds (default 0.4)

        Returns:
            Blended scorelines sorted by probability
        """
        # Build lookup from odds
        odds_lookup = {}
        for cs in odds_scorelines:
            score = cs.get("score", "")
            prob = cs.get("probability", 0)
            if score and prob > 0:
                odds_lookup[score] = prob

        # Blend
        blended = []
        for s in model_scorelines:
            score = s["score"]
            model_prob = s["probability"]

            if score in odds_lookup:
                # Both model and market have this score - blend
                odds_prob = odds_lookup[score]
                blended_prob = model_weight * model_prob + odds_weight * odds_prob
            else:
                # Only model has this score - reduce weight
                blended_prob = model_prob * model_weight

            blended.append({"score": score, "probability": blended_prob})

        # Add any scores from odds that model didn't produce
        model_scores = {s["score"] for s in model_scorelines}
        for score, prob in odds_lookup.items():
            if score not in model_scores:
                blended.append({"score": score, "probability": prob * odds_weight})

        # Normalize
        total = sum(s["probability"] for s in blended)
        if total > 0:
            for s in blended:
                s["probability"] = s["probability"] / total

        blended.sort(key=lambda x: x["probability"], reverse=True)
        return blended

    def _dixon_coles_factor(self, i: int, j: int, lambda_h: float, lambda_a: float) -> float:
        if i == 0 and j == 0:
            return 1.0 - lambda_h * lambda_a * self.DC_RHO
        elif i == 1 and j == 0:
            return 1.0 + lambda_h * self.DC_RHO
        elif i == 0 and j == 1:
            return 1.0 + lambda_a * self.DC_RHO
        elif i == 1 and j == 1:
            return 1.0 - self.DC_RHO
        return 1.0

    def _tournament_experience(self, code: str) -> float:
        champions = {"BRA": 5, "GER": 4, "ITA": 4, "ARG": 3, "FRA": 2, "URU": 2, "ENG": 1, "ESP": 1}
        strong = {"NED": 0.8, "CRO": 0.9, "POR": 0.7, "BEL": 0.7, "MEX": 0.5}
        if code in champions:
            return 1.0 + 0.1 * champions[code]
        return strong.get(code, 0.3)

    def _confidence_level(self, home_prob: float, away_prob: float,
                          max_prob: float, has_odds: bool, has_squad: bool) -> str:
        """Determine confidence with consideration of data availability."""
        gap = max(home_prob, away_prob) - min(home_prob, away_prob)
        dominance = max_prob

        # Boost confidence if multiple sources agree
        source_bonus = 0
        if has_odds:
            source_bonus += 0.05
        if has_squad:
            source_bonus += 0.03

        effective = dominance + source_bonus

        if gap > 0.30 or effective > 0.55:
            return "high"
        elif gap > 0.12 or effective > 0.43:
            return "medium"
        else:
            return "low"

    def _generate_advice(self, home_prob: float, draw_prob: float, away_prob: float,
                          eg_home: float, eg_away: float,
                          odds_analysis: Dict, squad1: Dict, squad2: Dict) -> str:
        """Generate human-readable prediction advice."""
        if home_prob > away_prob and home_prob > draw_prob:
            winner = "home"
            winner_prob = home_prob
        elif away_prob > home_prob and away_prob > draw_prob:
            winner = "away"
            winner_prob = away_prob
        else:
            winner = "draw"
            winner_prob = draw_prob

        total_goals = eg_home + eg_away

        parts = []

        if winner_prob > 0.55:
            parts.append(f"强推主队胜" if winner == "home" else "强推客队胜" if winner == "away" else "平局可能性大")
        elif winner_prob > 0.45:
            parts.append(f"主队稍占优势" if winner == "home" else "客队稍占优势" if winner == "away" else "势均力敌")
        else:
            parts.append("胜负难料，谨慎投注")

        if total_goals > 2.8:
            parts.append("预计进球数偏多(大球)")
        elif total_goals < 2.0:
            parts.append("预计进球数偏少(小球)")
        else:
            parts.append("预计进球数适中")

        if odds_analysis.get("available"):
            if odds_analysis.get("consensus") == "strong":
                parts.append("博彩公司意见高度一致")
            elif odds_analysis.get("consensus") == "weak":
                parts.append("博彩公司意见分歧较大")

        if squad1.get("available") and squad2.get("available"):
            diff = squad1["overall"] - squad2["overall"]
            if abs(diff) > 0.15:
                stronger = "主队" if diff > 0 else "客队"
                parts.append(f"{stronger}阵容深度明显占优")

        return "；".join(parts)

    # ─────────────────────────────────────────
    # Group/Bracket predictions (unchanged API)
    # ─────────────────────────────────────────

    def predict_all_group_matches(self, groups_data: Dict) -> List[Dict]:
        predictions = []
        for group_name, team_codes in groups_data.items():
            teams_in_group = [self.teams.get(c) for c in team_codes if self.teams.get(c)]
            if len(teams_in_group) < 4:
                continue
            for i in range(4):
                for j in range(i + 1, 4):
                    pred = self.predict_match(teams_in_group[i], teams_in_group[j])
                    predictions.append({
                        "group": group_name,
                        "team1": teams_in_group[i]["code"],
                        "team2": teams_in_group[j]["code"],
                        "prediction": pred,
                    })
        return predictions

    def predict_bracket_path(self, bracket: List[Dict]) -> List[Dict]:
        results = []
        for match in bracket:
            t1 = self.teams.get(match["team1"])
            t2 = self.teams.get(match["team2"])
            if t1 and t2:
                pred = self.predict_match(t1, t2)
                results.append({"round": match.get("round", "Knockout"),
                                "team1": match["team1"], "team2": match["team2"],
                                "prediction": pred})
        return results

    @staticmethod
    def compute_group_standings(group_teams, matches, teams_dict):
        stats = {}
        for code in group_teams:
            team = teams_dict.get(code, {})
            stats[code] = {"code": code, "name": team.get("name", code),
                           "name_zh": team.get("name_zh", code), "flag_emoji": team.get("flag_emoji", ""),
                           "elo_rating": team.get("elo_rating", 0),
                           "played": 0, "won": 0, "drawn": 0, "lost": 0,
                           "goals_for": 0, "goals_against": 0, "goals_diff": 0, "points": 0}
        for m in matches:
            t1, t2, s1, s2 = m.get("team1"), m.get("team2"), m.get("score1", 0), m.get("score2", 0)
            for t, sc, opp_sc in [(t1, s1, s2), (t2, s2, s1)]:
                if t in stats:
                    stats[t]["played"] += 1
                    stats[t]["goals_for"] += sc
                    stats[t]["goals_against"] += opp_sc
                    if sc > opp_sc:
                        stats[t]["won"] += 1; stats[t]["points"] += 3
                    elif sc == opp_sc:
                        stats[t]["drawn"] += 1; stats[t]["points"] += 1
                    else:
                        stats[t]["lost"] += 1
        for s in stats.values():
            s["goals_diff"] = s["goals_for"] - s["goals_against"]
        return sorted(stats.values(), key=lambda x: (-x["points"], -x["goals_diff"], -x["goals_for"]))
