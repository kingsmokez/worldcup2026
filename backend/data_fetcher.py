"""
Real-time Data Fetcher for World Cup 2026

Primary: API-Football v3 (api-football-v1.p.rapidapi.com)
Fallback: Local JSON data files

API-Football free tier: 100 requests/day, includes all endpoints.
Set API_FOOTBALL_KEY env var to enable live data.
"""

import asyncio
import json
import os
import math
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CACHE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_cache.db")

# API-Football v3 - supports two platforms:
# 1. RapidAPI: https://api-football-v1.p.rapidapi.com/v3 (X-RapidAPI-Key header)
# 2. api-football.com direct: https://api.api-football.com/v3 (x-apisports-key header)
# NOTE: Read lazily via property so .env loading in server.py takes effect
_API_FOOTBALL_KEY_CACHED = None
_API_FOOTBALL_KEY_LOADED = False

def _get_api_football_key() -> str:
    """Lazy-load API key so .env file is read first."""
    global _API_FOOTBALL_KEY_CACHED, _API_FOOTBALL_KEY_LOADED
    if not _API_FOOTBALL_KEY_LOADED:
        _API_FOOTBALL_KEY_CACHED = os.environ.get("API_FOOTBALL_KEY", "")
        _API_FOOTBALL_KEY_LOADED = True
    return _API_FOOTBALL_KEY_CACHED

API_FOOTBALL_KEY = property(lambda self: _get_api_football_key())  # For class attribute access

# Module-level convenience (used by server.py import)
def _refresh_api_keys():
    """Force refresh API keys from environment (called after .env load)."""
    global _API_FOOTBALL_KEY_CACHED, _API_FOOTBALL_KEY_LOADED, API_FOOTBALL_KEY_MODULE
    _API_FOOTBALL_KEY_LOADED = False
    API_FOOTBALL_KEY_MODULE = _get_api_football_key()

# Module-level variable that server.py imports
API_FOOTBALL_KEY_MODULE = os.environ.get("API_FOOTBALL_KEY", "")

# football-data.org - secondary API source
FOOTBALL_DATA_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

# Auto-detect platform based on key format or env var
API_FOOTBALL_PLATFORM = os.environ.get("API_FOOTBALL_PLATFORM", "auto")  # auto, rapidapi, direct

# World Cup 2026 league ID in API-Football
WC_LEAGUE_ID = 1
WC_SEASON = 2026

REQUEST_TIMEOUT = 15.0

# Cache settings
CACHE_TTL = timedelta(hours=6)  # Default cache TTL
INJURY_CACHE_TTL = timedelta(hours=12)  # Injuries update less frequently
ODDS_CACHE_TTL = timedelta(hours=2)  # Odds more volatile

# API rate limiting
DAILY_API_LIMIT = 100
API_LIMIT_THRESHOLD = 90  # Switch to cache-only at this threshold
FOOTBALL_DATA_RATE_LIMIT = 10  # requests per minute for football-data.org

# Request priorities (higher = more important)
REQUEST_PRIORITY = {
    "match_detail": 100,
    "fixtures": 50,
    "standings": 50,
    "odds": 30,
    "predictions": 20,
    "general": 10,
}


# ─────────────────────────────────────────────
# SQLite Cache Database
# ─────────────────────────────────────────────

class CacheDB:
    """SQLite-backed persistent cache for API responses."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = CACHE_DB_PATH):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = CACHE_DB_PATH):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        """Initialize cache tables."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_requests (
                date TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT value_json, timestamp FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row["value_json"])
            except json.JSONDecodeError:
                return None
        return None

    def set(self, key: str, value: Any, ttl_seconds: float = None):
        """Set cache value with timestamp."""
        conn = self._get_conn()
        cursor = conn.cursor()
        timestamp = datetime.now().timestamp()
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value_json, timestamp) VALUES (?, ?, ?)",
            (key, json.dumps(value), timestamp)
        )
        conn.commit()

    def is_valid(self, key: str, ttl: timedelta = CACHE_TTL) -> bool:
        """Check if cached entry is still valid based on TTL."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if not row:
            return False
        cached_time = datetime.fromtimestamp(row["timestamp"])
        return datetime.now() - cached_time < ttl

    def get_timestamp(self, key: str) -> Optional[datetime]:
        """Get the timestamp of a cached entry."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM cache WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return datetime.fromtimestamp(row["timestamp"])
        return None

    def delete(self, key: str):
        """Delete a cached entry."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
        conn.commit()

    def clear_expired(self, ttl: timedelta = CACHE_TTL):
        """Clear expired cache entries."""
        conn = self._get_conn()
        cursor = conn.cursor()
        threshold = (datetime.now() - ttl).timestamp()
        cursor.execute("DELETE FROM cache WHERE timestamp < ?", (threshold,))
        conn.commit()

    # API request tracking
    def get_request_count(self) -> int:
        """Get today's API request count."""
        conn = self._get_conn()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT count FROM api_requests WHERE date = ?", (today,))
        row = cursor.fetchone()
        return row["count"] if row else 0

    def increment_request_count(self):
        """Increment today's API request count."""
        conn = self._get_conn()
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            """INSERT INTO api_requests (date, count) VALUES (?, 1)
               ON CONFLICT(date) DO UPDATE SET count = count + 1""",
            (today,)
        )
        conn.commit()

    def can_make_request(self, threshold: int = API_LIMIT_THRESHOLD) -> bool:
        """Check if we can make another API request today."""
        return self.get_request_count() < threshold


# Global cache instance
_cache_db = CacheDB()


# ─────────────────────────────────────────────
# Position mapping (API-Football -> our format)
# ─────────────────────────────────────────────

POSITION_MAP = {
    "Goalkeeper": ("GK", "门将"),
    "Defender": ("CB", "后卫"),
    "Midfielder": ("CM", "中场"),
    "Attacker": ("ST", "前锋"),
}

DETAILED_POS_MAP = {
    # Goalkeeper
    "GK": ("GK", "门将"),
    # Defenders
    "CB": ("CB", "中后卫"), "RB": ("RB", "右后卫"), "LB": ("LB", "左后卫"),
    "RWB": ("RWB", "右翼卫"), "LWB": ("LWB", "左翼卫"),
    # Midfielders
    "CDM": ("CDM", "后腰"), "CM": ("CM", "中前卫"), "CAM": ("CAM", "前腰"),
    "RM": ("RM", "右前卫"), "LM": ("LM", "左前卫"),
    # Attackers
    "ST": ("ST", "前锋"), "CF": ("CF", "中锋"),
    "RW": ("RW", "右边锋"), "LW": ("LW", "左边锋"),
    "RF": ("RF", "右前锋"), "LF": ("LF", "左前锋"),
}

# Team code mapping: API-Football team name -> our code
TEAM_NAME_TO_CODE: Dict[str, str] = {
    "Argentina": "ARG", "Brazil": "BRA", "France": "FRA", "England": "ENG",
    "Spain": "ESP", "Germany": "GER", "Portugal": "POR", "Netherlands": "NED",
    "Italy": "ITA", "Belgium": "BEL", "Uruguay": "URU", "Croatia": "CRO",
    "Colombia": "COL", "Mexico": "MEX", "United States": "USA",
    "Morocco": "MAR", "Senegal": "SEN", "Japan": "JPN", "South Korea": "KOR",
    "Iran": "IRN", "Australia": "AUS", "Egypt": "EGY", "Ghana": "GHA",
    "Ivory Coast": "CIV", "Serbia": "SRB", "Switzerland": "SUI",
    "Denmark": "DEN", "Ecuador": "ECU", "Poland": "POL", "Canada": "CAN",
    "Saudi Arabia": "KSA", "Qatar": "QAT", "Nigeria": "NGA",
    "Costa Rica": "CRC", "Tunisia": "TUN", "Cameroon": "CMR",
    "South Africa": "RSA", "Korea Republic": "KOR", "Korea DPR": "PRK",
    "Iraq": "IRQ", "Uzbekistan": "UZB", "Jordan": "JOR", "Oman": "OMN",
    "Palestine": "PSE", "Kuwait": "KUW", "Bahrain": "BAH",
    "China": "CHN", "Thailand": "THA", "Vietnam": "VIE",
    "Indonesia": "IDN", "Malaysia": "MYS", "Philippines": "PHI",
    "New Zealand": "NZL", "Honduras": "HON", "Panama": "PAN",
    "Jamaica": "JAM", "Trinidad and Tobago": "TRI", "El Salvador": "SLV",
    "Guatemala": "GUA", "Cuba": "CUB", "Dominican Republic": "DOM",
    "Haiti": "HAI", "Suriname": "SUR", "Venezuela": "VEN",
    "Paraguay": "PAR", "Chile": "CHI", "Peru": "PER", "Bolivia": "BOL",
    "Ukraine": "UKR", "Russia": "RUS", "Sweden": "SWE", "Norway": "NOR",
    "Finland": "FIN", "Austria": "AUT", "Czech Republic": "CZE",
    "Romania": "ROU", "Turkey": "TUR", "Wales": "WAL", "Scotland": "SCO",
    "Republic of Ireland": "IRE",
}


# ─────────────────────────────────────────────
# Data Fetcher
# ─────────────────────────────────────────────

class DataFetcher:
    """Async data fetcher with API-Football v3 + local fallback."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.last_updated: Optional[datetime] = None
        # Lazy API key check - reads from environment at time of first use
        self._api_key: Optional[str] = None
        self._football_data_key: Optional[str] = None
        self._platform: Optional[str] = None
        self._base_url: Optional[str] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._refresh_running: bool = False
        self._football_data_requests: int = 0  # Track per-minute rate limit
        self._football_data_reset_time: Optional[datetime] = None
        self.cache = _cache_db  # Use SQLite cache

    @property
    def api_available(self) -> bool:
        """Check if API-Football key is configured (lazy - reads from env)."""
        if self._api_key is None:
            self._api_key = os.environ.get("API_FOOTBALL_KEY", "")
        return bool(self._api_key)

    @property
    def football_data_available(self) -> bool:
        """Check if football-data.org key is configured."""
        if self._football_data_key is None:
            self._football_data_key = os.environ.get("FOOTBALL_DATA_KEY", "")
        return bool(self._football_data_key)

    @property
    def platform(self) -> str:
        """Detect API platform: rapidapi or direct."""
        if self._platform is not None:
            return self._platform

        if API_FOOTBALL_PLATFORM == "rapidapi":
            self._platform = "rapidapi"
        elif API_FOOTBALL_PLATFORM == "direct":
            self._platform = "direct"
        else:
            # Auto-detect: try direct first, fallback to rapidapi
            self._platform = "direct"  # Default to direct (api-football.com)
        return self._platform

    @property
    def base_url(self) -> str:
        """Get API base URL based on platform."""
        if self._platform == "rapidapi":
            return "https://api-football-v1.p.rapidapi.com/v3"
        # Direct api-football.com / api-sports.io
        return "https://v3.football.api-sports.io"

    async def _ensure_client(self):
        if self.client is None:
            # Try to detect system proxy
            import ssl
            ssl_context = ssl.create_default_context()

            # Check for common proxy settings
            proxy_url = None
            for var in ["HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"]:
                val = os.environ.get(var, "")
                if val:
                    proxy_url = val
                    break

            # Also check Windows system proxy
            if not proxy_url:
                try:
                    import urllib.request
                    proxy_handler = urllib.request.getproxies()
                    if "https" in proxy_handler:
                        proxy_url = proxy_handler["https"]
                    elif "http" in proxy_handler:
                        proxy_url = proxy_handler["http"]
                except Exception:
                    pass

            if proxy_url:
                print(f"[Fetcher] Using proxy: {proxy_url}")
                self.client = httpx.AsyncClient(
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                    proxy=proxy_url,
                )
            else:
                self.client = httpx.AsyncClient(
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                )

    async def close(self):
        if self._refresh_running:
            self._refresh_running = False
            if self._refresh_task:
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass
        if self.client:
            await self.client.aclose()
            self.client = None

    def _is_cache_valid(self, key: str, ttl: timedelta = CACHE_TTL) -> bool:
        return self.cache.is_valid(key, ttl)

    def _set_cache(self, key: str, value: Any, ttl_seconds: float = None):
        self.cache.set(key, value, ttl_seconds)

    def _get_cache(self, key: str, ttl: timedelta = CACHE_TTL) -> Optional[Any]:
        if self.cache.is_valid(key, ttl):
            return self.cache.get(key)
        return None

    def _can_make_request(self, priority: str = "general") -> bool:
        """Check if we can make an API request based on rate limits and priority."""
        return self.cache.can_make_request(API_LIMIT_THRESHOLD)

    # ─────────────────────────────────────────
    # API-Football v3 requests
    # ─────────────────────────────────────────

    async def _api_get(self, endpoint: str, params: Dict = None, _retry: bool = True, priority: str = "general") -> Optional[Dict]:
        """Make authenticated request to API-Football v3."""
        api_key = os.environ.get("API_FOOTBALL_KEY", "")
        if not api_key:
            print("[Fetcher] No API_FOOTBALL_KEY set, skipping API call")
            return None

        # Check rate limiting
        if not self._can_make_request(priority):
            print(f"[Fetcher] API rate limit approaching, skipping {endpoint} (priority: {priority})")
            return None

        await self._ensure_client()

        # Build headers based on platform
        if self.platform == "rapidapi":
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
            }
        else:
            # Direct api-football.com
            headers = {
                "x-apisports-key": api_key,
            }

        url = f"{self.base_url}/{endpoint}"

        try:
            resp = await self.client.get(
                url,
                headers=headers,
                params=params or {},
            )
            # Increment request count on success
            if resp.status_code in (200, 403, 429):
                self.cache.increment_request_count()

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", 0)
                print(f"[Fetcher] API {endpoint}: {results} results (platform={self.platform})")
                return data
            elif resp.status_code == 403 and _retry:
                # Wrong platform - try the other one (only once)
                old_platform = self._platform
                if self._platform == "direct":
                    print("[Fetcher] Direct API returned 403, trying RapidAPI...")
                    self._platform = "rapidapi"
                elif self._platform == "rapidapi":
                    print("[Fetcher] RapidAPI returned 403, trying direct API...")
                    self._platform = "direct"
                self._base_url = None
                if self._platform != old_platform:
                    return await self._api_get(endpoint, params, _retry=False, priority=priority)
                print(f"[Fetcher] API 403 - both platforms failed: {resp.text[:200]}")
                return None
            elif resp.status_code == 403:
                print(f"[Fetcher] API 403 - subscription issue: {resp.text[:200]}")
                return None
            elif resp.status_code == 429:
                print("[Fetcher] API rate limit hit (429), using cache/fallback")
                return None
            else:
                print(f"[Fetcher] API error {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"[Fetcher] API request failed: {e}")
            return None

    # ─────────────────────────────────────────
    # football-data.org API (secondary source)
    # ─────────────────────────────────────────

    async def _football_data_get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to football-data.org API."""
        fd_key = os.environ.get("FOOTBALL_DATA_KEY", "")
        if not fd_key:
            print("[Fetcher] No FOOTBALL_DATA_KEY set, skipping football-data.org call")
            return None

        # Rate limiting: 10 requests per minute
        now = datetime.now()
        if self._football_data_reset_time is None or (now - self._football_data_reset_time) > timedelta(minutes=1):
            self._football_data_requests = 0
            self._football_data_reset_time = now

        if self._football_data_requests >= FOOTBALL_DATA_RATE_LIMIT:
            print("[Fetcher] football-data.org rate limit reached (10/min), waiting...")
            return None

        await self._ensure_client()

        headers = {
            "X-Auth-Token": fd_key,
        }

        url = f"{FOOTBALL_DATA_BASE_URL}/{endpoint}"

        try:
            resp = await self.client.get(
                url,
                headers=headers,
                params=params or {},
            )
            self._football_data_requests += 1

            if resp.status_code == 200:
                data = resp.json()
                print(f"[Fetcher] football-data.org {endpoint}: success")
                return data
            elif resp.status_code == 429:
                print("[Fetcher] football-data.org rate limit hit (429)")
                return None
            else:
                print(f"[Fetcher] football-data.org error {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"[Fetcher] football-data.org request failed: {e}")
            return None

    # ─────────────────────────────────────────
    # Fetch teams from API
    # ─────────────────────────────────────────

    async def fetch_teams_from_api(self) -> List[Dict]:
        """Fetch World Cup teams from API-Football."""
        cache_key = "api_teams"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("teams", {
            "league": WC_LEAGUE_ID,
            "season": WC_SEASON,
        })

        if not data or "response" not in data:
            print("[Fetcher] API teams unavailable, using local data")
            return await self._load_teams_from_local()

        teams = []
        for item in data["response"]:
            team = item.get("team", {})
            venue = item.get("venue", {})

            name = team.get("name", "")
            code = TEAM_NAME_TO_CODE.get(name, team.get("code", name[:3].upper()))

            teams.append({
                "code": code,
                "name": name,
                "name_zh": self._get_team_name_zh(code, name),
                "logo": team.get("logo", ""),
                "country": team.get("country", ""),
                "founded": team.get("founded", ""),
                "venue": venue.get("name", ""),
            })

        self._set_cache(cache_key, teams)
        return teams

    # ─────────────────────────────────────────
    # Fetch fixtures (matches) from API
    # ─────────────────────────────────────────

    async def fetch_fixtures_from_api(self) -> List[Dict]:
        """Fetch World Cup fixtures from API-Football."""
        cache_key = "api_fixtures"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("fixtures", {
            "league": WC_LEAGUE_ID,
            "season": WC_SEASON,
        })

        if not data or "response" not in data:
            print("[Fetcher] API fixtures unavailable, using local data")
            return []

        fixtures = []
        for item in data["response"]:
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            league = item.get("league", {})
            score = item.get("score", {})

            home = teams.get("home", {})
            away = teams.get("away", {})

            home_name = home.get("name", "")
            away_name = away.get("name", "")
            home_code = TEAM_NAME_TO_CODE.get(home_name, home.get("id", ""))
            away_code = TEAM_NAME_TO_CODE.get(away_name, away.get("id", ""))

            # Determine group from round info
            round_info = league.get("round", "")
            group_name = self._extract_group(round_info)

            # Determine stage
            stage = "group"
            round_lower = round_info.lower()
            if "32" in round_lower or "1/16" in round_lower:
                stage = "round32"
            elif "16" in round_lower or "1/8" in round_lower or "round of" in round_lower:
                stage = "round16"
            elif "8" in round_lower or "quarter" in round_lower:
                stage = "quarter"
            elif "semi" in round_lower:
                stage = "semi"
            elif "3rd" in round_lower or "third" in round_lower:
                stage = "third"
            elif "final" in round_lower:
                stage = "final"

            # Match status
            short_status = fixture.get("status", {}).get("short", "")
            if short_status in ("1H", "2H", "HT", "ET", "BT", "P", "SUSP", "INT", "LIVE"):
                status = "live"
            elif short_status == "FT" or short_status == "AET" or short_status == "PEN":
                status = "finished"
            else:
                status = "upcoming"

            fixtures.append({
                "fixture_id": fixture.get("id"),
                "date": fixture.get("date", "")[:10] if fixture.get("date") else "",
                "timestamp": fixture.get("timestamp"),
                "status": status,
                "status_short": short_status,
                "round": round_info,
                "group_name": group_name,
                "stage": stage,
                "team1": home_code,
                "team1_name": home_name,
                "team1_logo": home.get("logo", ""),
                "team2": away_code,
                "team2_name": away_name,
                "team2_logo": away.get("logo", ""),
                "score1": goals.get("home"),
                "score2": goals.get("away"),
                "score_ht": score.get("halftime", {}),
                "score_ft": score.get("fulltime", {}),
            })

        self._set_cache(cache_key, fixtures)
        return fixtures

    # ─────────────────────────────────────────
    # Fetch squad/players from API
    # ─────────────────────────────────────────

    async def fetch_squad_from_api(self, team_id: int) -> List[Dict]:
        """Fetch team squad from API-Football."""
        cache_key = f"api_squad_{team_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("players/squads", {"team": team_id})

        if not data or "response" not in data:
            return []

        players = []
        for item in data["response"]:
            for p in item.get("players", []):
                pos_short = p.get("position", "")
                pos_info = DETAILED_POS_MAP.get(pos_short, POSITION_MAP.get(pos_short, (pos_short, pos_short)))

                players.append({
                    "id": p.get("id"),
                    "name": p.get("name", ""),
                    "name_zh": p.get("name", ""),  # API doesn't provide Chinese names
                    "number": p.get("number"),
                    "position": pos_info[0],
                    "position_zh": pos_info[1],
                })

        self._set_cache(cache_key, players)
        return players

    # ─────────────────────────────────────────
    # Fetch odds from API
    # ─────────────────────────────────────────

    async def fetch_odds_from_api(self, fixture_id: int) -> List[Dict]:
        """Fetch match odds from API-Football with fallback to football-data.org."""
        cache_key = f"api_odds_{fixture_id}"
        cached = self._get_cache(cache_key, ODDS_CACHE_TTL)
        if cached is not None:
            return cached

        data = await self._api_get("odds", {
            "fixture": fixture_id,
        }, priority="odds")

        odds_list = []
        correct_scores = []

        if data and "response" in data:
            for item in data["response"]:
                for bk in item.get("bookmakers", []):
                    bookmaker_name = bk.get("name", "Unknown")
                    bets = bk.get("bets", [])
                    odds_entry = {"bookmaker": bookmaker_name}

                    # Find Match Winner bet (1X2)
                    for bet in bets:
                        if bet.get("name") == "Match Winner":
                            values = bet.get("values", [])
                            home_val = next((v["odd"] for v in values if v["value"] == "Home"), None)
                            draw_val = next((v["odd"] for v in values if v["value"] == "Draw"), None)
                            away_val = next((v["odd"] for v in values if v["value"] == "Away"), None)
                            if home_val and draw_val and away_val:
                                odds_entry["home"] = float(home_val)
                                odds_entry["draw"] = float(draw_val)
                                odds_entry["away"] = float(away_val)
                            break

                    # Extract Correct Score odds
                    for bet in bets:
                        if bet.get("name") == "Correct Score":
                            for v in bet.get("values", []):
                                score = v.get("value", "")
                                odd = v.get("odd")
                                if score and odd:
                                    try:
                                        correct_scores.append({
                                            "score": score,
                                            "odd": float(odd),
                                            "bookmaker": bookmaker_name,
                                        })
                                    except ValueError:
                                        pass
                            break

                    if "home" in odds_entry:
                        odds_entry["correct_scores"] = correct_scores
                        odds_list.append(odds_entry)

        # Fallback to football-data.org if no odds found
        if not odds_list and os.environ.get("FOOTBALL_DATA_KEY", ""):
            fallback_odds = await self._fetch_odds_from_football_data(fixture_id)
            if fallback_odds:
                odds_list = fallback_odds

        if odds_list:
            self._set_cache(cache_key, odds_list)
        return odds_list

    async def _fetch_odds_from_football_data(self, fixture_id: int) -> List[Dict]:
        """Fetch odds from football-data.org as fallback."""
        # Note: football-data.org uses different match IDs
        # This is a placeholder - would need mapping from our fixture_id to their match ID
        # For now, return empty list as the ID mapping is not available
        print(f"[Fetcher] football-data.org odds fallback not available for fixture {fixture_id} (ID mapping needed)")
        return []

    # ─────────────────────────────────────────
    # Fetch odds from sporttery.cn (Chinese sports lottery)
    # ─────────────────────────────────────────

    async def fetch_sporttery_odds(self) -> Dict[str, Dict]:
        """
        Fetch odds from sporttery.cn (Chinese National Sports Lottery).
        Returns odds mapped by team name pairs.

        sporttery.cn provides:
        - SP values (reciprocal of decimal odds, i.e. implied probability with margin)
        - Let球 (handicap/Asian handicap)
        - 大小盘 (over/under)
        - 比分 (correct score)
        """
        cache_key = "sporttery_odds_all"
        cached = self._get_cache(cache_key, ODDS_CACHE_TTL)
        if cached is not None:
            return cached

        odds_map = {}
        try:
            async with httpx.AsyncClient(timeout=15.0, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://www.sporttery.cn/jc/jsq/zqbf/",
            }) as client:
                resp = await client.get("https://www.sporttery.cn/jc/jsq/zqbf/")
                if resp.status_code != 200:
                    print(f"[Fetcher] sporttery.cn returned HTTP {resp.status_code}")
                    return odds_map

                html = resp.text

                # Parse embedded JSON data from the page
                # sporttery.cn loads match data as JavaScript variables
                # Look for matchData or similar JSON structures
                import re

                # Try to find match data in script tags
                # Common patterns: var matchData = {...} or window.__INITIAL_STATE__ = {...}
                json_patterns = [
                    r'(?:var|let|const)\s+matchData\s*=\s*(\{.+?\});',
                    r'(?:var|let|const)\s+matchList\s*=\s*(\[.+?\]);',
                    r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});',
                    r'"matchList"\s*:\s*(\[.+?\])',
                    r'"data"\s*:\s*(\[.+?\])',
                ]

                json_str = None
                for pattern in json_patterns:
                    match = re.search(pattern, html, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        break

                if json_str:
                    try:
                        match_data = json.loads(json_str)
                        odds_map = self._parse_sporttery_data(match_data)
                    except json.JSONDecodeError:
                        pass

                # If JSON parsing failed, try parsing HTML tables
                if not odds_map:
                    odds_map = self._parse_sporttery_html(html)

        except httpx.TimeoutException:
            print("[Fetcher] sporttery.cn request timed out")
        except Exception as e:
            print(f"[Fetcher] sporttery.cn fetch error: {e}")

        if odds_map:
            self._set_cache(cache_key, odds_map)
        return odds_map

    def _parse_sporttery_data(self, data: Any) -> Dict[str, Dict]:
        """Parse sporttery.cn JSON data into odds map."""
        odds_map = {}

        matches = []
        if isinstance(data, list):
            matches = data
        elif isinstance(data, dict):
            # Try common keys
            for key in ["matchList", "data", "matches", "result", "list"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        matches = val
                        break
                    elif isinstance(val, dict):
                        for k2 in ["matchList", "data", "matches"]:
                            if k2 in val and isinstance(val[k2], list):
                                matches = val[k2]
                                break
                        break

        for m in matches:
            if not isinstance(m, dict):
                continue

            # Extract team names
            home_team = m.get("homeTeamName", "") or m.get("homeName", "") or m.get("home", "")
            away_team = m.get("awayTeamName", "") or m.get("awayName", "") or m.get("away", "")
            if not home_team or not away_team:
                continue

            key = f"{home_team}|{away_team}"

            # Extract SP values (sporttery format: SP = 1/odds)
            # win/draw/loss SP values
            sp_win = m.get("spWin") or m.get("spH") or m.get("spHome")
            sp_draw = m.get("spDraw") or m.get("spD")
            sp_loss = m.get("spLoss") or m.get("spA") or m.get("spAway")

            odds_entry = {
                "bookmaker": "sporttery",
                "source": "sporttery.cn",
            }

            if sp_win and sp_draw and sp_loss:
                try:
                    # SP values are decimal odds (reciprocal format in Chinese lottery)
                    odds_entry["home"] = float(sp_win)
                    odds_entry["draw"] = float(sp_draw)
                    odds_entry["away"] = float(sp_loss)
                except (ValueError, TypeError):
                    pass

            # Extract handicap (Asian handicap)
            handicap = m.get("letBall") or m.get("handicap") or m.get("let")
            if handicap is not None:
                try:
                    odds_entry["handicap"] = float(handicap)
                except (ValueError, TypeError):
                    pass

            # Extract over/under
            ou_line = m.get("bs0") or m.get("overUnderLine") or m.get("sizeLine")
            if ou_line is not None:
                try:
                    odds_entry["over_under_line"] = float(ou_line)
                except (ValueError, TypeError):
                    pass

            # Extract correct score odds
            cs_odds = {}
            for cs_key in ["scoreOdds", "bfOdds", "correctScore"]:
                cs_data = m.get(cs_key)
                if cs_data and isinstance(cs_data, dict):
                    cs_odds = cs_data
                    break
            if cs_odds:
                odds_entry["correct_scores"] = [
                    {"score": k, "odd": float(v), "bookmaker": "sporttery"}
                    for k, v in cs_odds.items()
                    if isinstance(v, (int, float, str))
                ]

            if "home" in odds_entry:
                odds_map[key] = odds_entry

        return odds_map

    def _parse_sporttery_html(self, html: str) -> Dict[str, Dict]:
        """Parse sporttery.cn HTML table into odds map (fallback)."""
        odds_map = {}
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")

            # Find match rows in the table
            rows = soup.select("tr[data-mid]") or soup.select(".match-tr") or soup.select("tbody tr")

            for row in rows:
                try:
                    # Try to find team names and SP values
                    home_el = row.select_one(".home-name") or row.select_one(".team-home") or row.select_one("td:nth-child(2)")
                    away_el = row.select_one(".away-name") or row.select_one(".team-away") or row.select_one("td:nth-child(4)")

                    if not home_el or not away_el:
                        continue

                    home_team = home_el.get_text(strip=True)
                    away_team = away_el.get_text(strip=True)

                    if not home_team or not away_team:
                        continue

                    # Find SP/odds cells
                    sp_cells = row.select(".sp-val") or row.select(".odds-val") or row.select("td[class*='sp']")

                    if len(sp_cells) >= 3:
                        key = f"{home_team}|{away_team}"
                        try:
                            odds_map[key] = {
                                "bookmaker": "sporttery",
                                "source": "sporttery.cn",
                                "home": float(sp_cells[0].get_text(strip=True)),
                                "draw": float(sp_cells[1].get_text(strip=True)),
                                "away": float(sp_cells[2].get_text(strip=True)),
                            }
                        except (ValueError, TypeError):
                            continue
                except Exception:
                    continue
        except ImportError:
            print("[Fetcher] BeautifulSoup not available for HTML parsing")
        except Exception as e:
            print(f"[Fetcher] sporttery HTML parse error: {e}")

        return odds_map

    async def fetch_odds_from_sporttery(self, home_team_name: str = None, away_team_name: str = None) -> List[Dict]:
        """
        Fetch odds from sporttery.cn for a specific match.
        Returns list compatible with the existing odds format.
        """
        all_odds = await self.fetch_sporttery_odds()
        if not all_odds:
            return []

        # If specific team names given, try to match
        if home_team_name and away_team_name:
            # Try exact match first
            key = f"{home_team_name}|{away_team_name}"
            if key in all_odds:
                entry = all_odds[key]
                return [entry]

            # Try fuzzy match (partial name matching)
            for k, v in all_odds.items():
                parts = k.split("|")
                if len(parts) == 2:
                    if (home_team_name in parts[0] or parts[0] in home_team_name) and \
                       (away_team_name in parts[1] or parts[1] in away_team_name):
                        return [v]

        # Return all odds
        return list(all_odds.values())

    # ─────────────────────────────────────────
    # Fetch predictions from API
    # ─────────────────────────────────────────

    async def fetch_predictions_from_api(self, fixture_id: int) -> Optional[Dict]:
        """Fetch match prediction from API-Football."""
        data = await self._api_get("predictions", {"fixture": fixture_id})

        if not data or "response" not in data or len(data["response"]) == 0:
            return None

        pred = data["response"][0]
        predictions = pred.get("predictions", {})
        advice = predictions.get("advice", "")
        percent = predictions.get("percent", {})

        # Parse winner percentage
        home_pct = self._parse_percent(percent.get("home", ""))
        draw_pct = self._parse_percent(percent.get("draw", ""))
        away_pct = self._parse_percent(percent.get("away", ""))

        # Goals
        goals = predictions.get("goals", {})
        home_goals = goals.get("home", "-")
        away_goals = goals.get("away", "-")

        # Under/over
        under_over = predictions.get("under_over", "")

        return {
            "home_win_prob": home_pct,
            "draw_prob": draw_pct,
            "away_win_prob": away_pct,
            "advice": advice,
            "expected_goals_home": float(home_goals) if isinstance(home_goals, (int, float, str)) and str(home_goals) != "-" else 0,
            "expected_goals_away": float(away_goals) if isinstance(away_goals, (int, float, str)) and str(away_goals) != "-" else 0,
            "under_over": under_over,
        }

    # ─────────────────────────────────────────
    # Fetch head-to-head from API
    # ─────────────────────────────────────────

    async def fetch_h2h_from_api(self, team1_id: int, team2_id: int, last: int = 10) -> Dict:
        """Fetch head-to-head data from API-Football."""
        data = await self._api_get("fixtures/headtohead", {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last,
        })

        if not data or "response" not in data:
            return {"stats": {"total": 0, "home_wins": 0, "draws": 0, "away_wins": 0}, "matches": []}

        matches = []
        home_wins = 0
        draws = 0
        away_wins = 0

        for item in data["response"]:
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            fixture = item.get("fixture", {})
            league = item.get("league", {})

            home = teams.get("home", {})
            away = teams.get("away", {})
            s1 = goals.get("home", 0) or 0
            s2 = goals.get("away", 0) or 0

            if s1 > s2:
                home_wins += 1
            elif s1 == s2:
                draws += 1
            else:
                away_wins += 1

            matches.append({
                "year": fixture.get("date", "")[:4] if fixture.get("date") else "",
                "tournament": league.get("name", ""),
                "date": fixture.get("date", "")[:10] if fixture.get("date") else "",
                "team1": home.get("name", ""),
                "team2": away.get("name", ""),
                "score1": s1,
                "score2": s2,
                "round": league.get("round", ""),
            })

        return {
            "stats": {
                "total": len(matches),
                "home_wins": home_wins,
                "draws": draws,
                "away_wins": away_wins,
            },
            "matches": matches,
        }

    # ─────────────────────────────────────────
    # Fetch player season stats from API
    # ─────────────────────────────────────────

    async def fetch_player_stats_from_api(self, player_id: int, season: int = 2024) -> Dict:
        """Fetch player's season statistics (league stats, ratings, goals, assists)."""
        cache_key = f"api_player_stats_{player_id}_{season}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("players", {
            "id": player_id,
            "season": season,
        })

        if not data or "response" not in data or len(data["response"]) == 0:
            return {"available": False}

        p = data["response"][0]
        player_info = p.get("player", {})
        stats_list = p.get("statistics", [])

        # Aggregate stats across all competitions (pick the main league)
        total_apps = 0
        total_goals = 0
        total_assists = 0
        total_minutes = 0
        ratings = []
        main_league_stats = None

        for s in stats_list:
            apps = s.get("games", {}).get("appearences", 0) or 0
            goals = s.get("goals", {}).get("total", 0) or 0
            assists = s.get("goals", {}).get("assists", 0) or 0
            minutes = s.get("games", {}).get("minutes", 0) or 0
            rating = s.get("games", {}).get("rating")

            total_apps += apps
            total_goals += goals
            total_assists += assists
            total_minutes += minutes

            if rating:
                try:
                    ratings.append(float(rating))
                except (ValueError, TypeError):
                    pass

            # Pick the main domestic league (most appearances)
            league_name = s.get("league", {}).get("name", "")
            league_type = s.get("league", {}).get("type", "")
            if league_type == "League" and (main_league_stats is None or apps > main_league_stats.get("appearences", 0)):
                main_league_stats = {
                    "league": league_name,
                    "appearences": apps,
                    "goals": goals,
                    "assists": assists,
                    "rating": float(rating) if rating else None,
                    "minutes": minutes,
                }

        avg_rating = sum(ratings) / len(ratings) if ratings else None

        result = {
            "available": True,
            "player_id": player_id,
            "name": player_info.get("name", ""),
            "age": player_info.get("age"),
            "total_appearences": total_apps,
            "total_goals": total_goals,
            "total_assists": total_assists,
            "total_minutes": total_minutes,
            "avg_rating": round(avg_rating, 3) if avg_rating else None,
            "main_league": main_league_stats,
            # Derived metrics
            "goals_per_game": round(total_goals / max(total_apps, 1), 3),
            "assists_per_game": round(total_assists / max(total_apps, 1), 3),
            "goal_contributions_per_90": round((total_goals + total_assists) / max(total_minutes / 90, 1), 3),
        }

        self._set_cache(cache_key, result)
        return result

    # ─────────────────────────────────────────
    # Fetch squad with stats from API
    # ─────────────────────────────────────────

    async def fetch_squad_with_stats_from_api(self, team_id: int, season: int = 2024) -> List[Dict]:
        """Fetch team squad with player season statistics."""
        cache_key = f"api_squad_stats_{team_id}_{season}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        # First get squad list
        squad = await self.fetch_squad_from_api(team_id)
        if not squad:
            return []

        # Fetch stats for each player (limit to avoid rate limits)
        # Only fetch top 11 most important players to save API calls
        important_positions = {"ST", "CF", "CAM", "CM", "CDM", "CB", "RB", "LB", "GK", "RW", "LW"}
        priority_players = [p for p in squad if p.get("position") in important_positions][:11]

        enriched_squad = []
        for p in squad:
            player_data = dict(p)
            if p in priority_players and p.get("id"):
                try:
                    stats = await self.fetch_player_stats_from_api(p["id"], season)
                    if stats.get("available"):
                        player_data["stats"] = stats
                except Exception:
                    pass
            enriched_squad.append(player_data)

        self._set_cache(cache_key, enriched_squad)
        return enriched_squad

    # ─────────────────────────────────────────
    # Fetch team recent form from API
    # ─────────────────────────────────────────

    async def fetch_team_form_from_api(self, team_id: int, last: int = 10) -> Dict:
        """Fetch team's recent match results for form analysis."""
        cache_key = f"api_team_form_{team_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("fixtures", {
            "team": team_id,
            "last": last,
        })

        if not data or "response" not in data:
            return {"available": False, "form": "", "wins": 0, "draws": 0, "losses": 0}

        matches = []
        form_str = ""
        wins = draws = losses = 0
        goals_for = 0
        goals_against = 0

        for fx in data["response"]:
            teams = fx.get("teams", {})
            goals = fx.get("goals", {})
            fixture = fx.get("fixture", {})
            league = fx.get("league", {})

            home = teams.get("home", {})
            away = teams.get("away", {})
            is_home = home.get("id") == team_id

            gf = goals.get("home", 0) if is_home else goals.get("away", 0)
            ga = goals.get("away", 0) if is_home else goals.get("home", 0)

            goals_for += gf or 0
            goals_against += ga or 0

            if gf > ga:
                form_str += "W"
                wins += 1
            elif gf == ga:
                form_str += "D"
                draws += 1
            else:
                form_str += "L"
                losses += 1

            matches.append({
                "date": fixture.get("date", "")[:10],
                "opponent": away.get("name", "") if is_home else home.get("name", ""),
                "home": is_home,
                "goals_for": gf,
                "goals_against": ga,
                "league": league.get("name", ""),
            })

        total = wins + draws + losses
        result = {
            "available": True,
            "form": form_str,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "total": total,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goals_diff": goals_for - goals_against,
            "win_rate": round(wins / max(total, 1), 3),
            "avg_goals_for": round(goals_for / max(total, 1), 2),
            "avg_goals_against": round(goals_against / max(total, 1), 2),
            "matches": matches,
        }

        self._set_cache(cache_key, result)
        return result

    # ─────────────────────────────────────────
    # Fetch injuries from API
    # ─────────────────────────────────────────

    async def fetch_injuries_from_api(self, fixture_id: int) -> List[Dict]:
        """Fetch player injuries/suspensions for a fixture from API-Football."""
        cache_key = f"api_injuries_{fixture_id}"
        cached = self._get_cache(cache_key, INJURY_CACHE_TTL)
        if cached is not None:
            return cached

        data = await self._api_get("injuries", {
            "fixture": fixture_id,
        }, priority="match_detail")

        if not data or "response" not in data:
            return []

        injuries = []
        for item in data["response"]:
            player = item.get("player", {})
            team = item.get("team", {})

            # Determine reason: injured or suspended
            reason_raw = item.get("reason", "").lower() if item.get("reason") else ""
            if "suspend" in reason_raw or "ban" in reason_raw or "card" in reason_raw:
                reason = "suspended"
            else:
                reason = "injured"

            injuries.append({
                "player_name": player.get("name", ""),
                "player_id": player.get("id"),
                "team_name": team.get("name", ""),
                "reason": reason,
                "type": "missing",
            })

        self._set_cache(cache_key, injuries)
        return injuries

    # ─────────────────────────────────────────
    # Fetch recent matches from API
    # ─────────────────────────────────────────

    async def fetch_recent_matches_from_api(self, team_id: int, last: int = 10) -> List[Dict]:
        """
        Fetch team's recent matches with full details.
        Used for "近10场比赛" feature.
        """
        cache_key = f"api_recent_matches_{team_id}_{last}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("fixtures", {
            "team": team_id,
            "last": last,
        }, priority="fixtures")

        if not data or "response" not in data:
            return []

        matches = []
        for fx in data["response"]:
            teams = fx.get("teams", {})
            goals = fx.get("goals", {})
            fixture = fx.get("fixture", {})
            league = fx.get("league", {})

            home = teams.get("home", {})
            away = teams.get("away", {})
            is_home = home.get("id") == team_id

            gf = goals.get("home", 0) if is_home else goals.get("away", 0)
            ga = goals.get("away", 0) if is_home else goals.get("home", 0)

            # Determine result
            if gf > ga:
                result = "W"
            elif gf == ga:
                result = "D"
            else:
                result = "L"

            # Determine competition type
            league_type = league.get("type", "")
            if league_type == "League":
                competition_type = "League"
            elif league_type == "Cup" or "cup" in league.get("name", "").lower():
                competition_type = "Cup"
            elif league_type == "Friendly" or "friendly" in league.get("name", "").lower():
                competition_type = "Friendly"
            else:
                competition_type = league_type or "Other"

            opponent_name = away.get("name", "") if is_home else home.get("name", "")
            opponent_code = TEAM_NAME_TO_CODE.get(opponent_name, opponent_name[:3].upper() if opponent_name else "")

            matches.append({
                "date": fixture.get("date", "")[:10] if fixture.get("date") else "",
                "opponent_name": opponent_name,
                "opponent_code": opponent_code,
                "opponent_id": away.get("id") if is_home else home.get("id"),
                "is_home": is_home,
                "goals_for": gf or 0,
                "goals_against": ga or 0,
                "result": result,
                "league": league.get("name", ""),
                "competition_type": competition_type,
            })

        self._set_cache(cache_key, matches)
        return matches

    # ─────────────────────────────────────────
    # Scheduled refresh
    # ─────────────────────────────────────────

    async def start_refresh_scheduler(self) -> None:
        """Start background scheduler for periodic data refresh."""
        if self._refresh_running:
            print("[Fetcher] Refresh scheduler already running")
            return

        self._refresh_running = True
        self._refresh_task = asyncio.create_task(self._refresh_loop())
        print("[Fetcher] Started refresh scheduler")

    async def _refresh_loop(self) -> None:
        """Background loop that refreshes data periodically.
        
        During knockout stage (June 28 - July 19, 2026):
        - Check for match results every 15 minutes
        - Refresh fixtures/standings every cycle
        - Refresh odds every cycle
        
        Outside knockout:
        - Standard 2-hour refresh cycle
        """
        # Determine if we're in the knockout stage
        now = datetime.now()
        knockout_start = datetime(2026, 6, 28)
        knockout_end = datetime(2026, 7, 20)
        in_knockout = knockout_start <= now <= knockout_end
        
        try:
            while self._refresh_running:
                try:
                    # Refresh core data
                    print("[Fetcher] Scheduled refresh: fixtures, standings")
                    if self.api_available:
                        # Invalidate fixtures cache to get fresh results
                        self.cache.delete("api_fixtures")
                        await self.fetch_fixtures_from_api()
                        await self.fetch_standings_from_api()

                    # Refresh odds for upcoming fixtures
                    fixtures = self.cache.get("api_fixtures") or []
                    upcoming_fixtures = [f for f in fixtures if f.get("status") == "upcoming"]
                    for fx in upcoming_fixtures[:5]:  # Limit to 5 to save API calls
                        fixture_id = fx.get("fixture_id")
                        if fixture_id:
                            print(f"[Fetcher] Scheduled refresh: odds for fixture {fixture_id}")
                            await self.fetch_odds_from_api(fixture_id)

                    # Update knockout match results in DB from API fixtures
                    if in_knockout:
                        await self._update_knockout_results_from_api(fixtures)

                    self.last_updated = datetime.now()
                    print(f"[Fetcher] Scheduled refresh complete at {self.last_updated}")

                except Exception as e:
                    print(f"[Fetcher] Scheduled refresh error: {e}")

                # Sleep interval: 15 min during knockout, 2 hours otherwise
                sleep_seconds = 15 * 60 if in_knockout else 2 * 60 * 60
                await asyncio.sleep(sleep_seconds)

        except asyncio.CancelledError:
            print("[Fetcher] Refresh scheduler cancelled")

    async def _update_knockout_results_from_api(self, fixtures: List[Dict]) -> None:
        """Update knockout match results in the database from API fixture data.
        
        Called by the refresh loop during the knockout stage. Checks for finished
        matches in the API data and updates the corresponding DB records.
        """
        if not fixtures:
            return
        
        try:
            from database import SessionLocal, Match
            
            finished_fixtures = [f for f in fixtures if f.get("status") == "finished"]
            if not finished_fixtures:
                return
            
            updated = 0
            with SessionLocal() as session:
                for fx in finished_fixtures:
                    t1 = fx.get("team1", "")
                    t2 = fx.get("team2", "")
                    s1 = fx.get("score1")
                    s2 = fx.get("score2")
                    if not t1 or not t2 or s1 is None or s2 is None:
                        continue
                    
                    # Find the matching match in DB that isn't yet finished
                    match = session.query(Match).filter(
                        Match.team1 == t1, Match.team2 == t2,
                        Match.status != "finished"
                    ).first()
                    
                    # Also try reverse order
                    if not match:
                        match = session.query(Match).filter(
                            Match.team1 == t2, Match.team2 == t1,
                            Match.status != "finished"
                        ).first()
                    
                    if match:
                        match.score1 = int(s1)
                        match.score2 = int(s2)
                        match.status = "finished"
                        
                        # Handle penalty scores if available
                        score_ft = fx.get("score_ft", {})
                        if isinstance(score_ft, dict):
                            ft_home = score_ft.get("home")
                            ft_away = score_ft.get("away")
                            # If the match went to penalties, the FT score might be different
                            # API stores full-time (including ET) score in goals
                        
                        updated += 1
                
                if updated > 0:
                    session.commit()
                    print(f"[Fetcher] Updated {updated} knockout match results from API")
                    
        except Exception as e:
            print(f"[Fetcher] Error updating knockout results: {e}")

    async def stop_refresh_scheduler(self) -> None:
        """Stop the background refresh scheduler."""
        if self._refresh_running:
            self._refresh_running = False
            if self._refresh_task:
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass
            print("[Fetcher] Stopped refresh scheduler")

    # ─────────────────────────────────────────
    # Fetch standings from API
    # ─────────────────────────────────────────

    async def fetch_standings_from_api(self) -> List[Dict]:
        """Fetch group standings from API-Football."""
        cache_key = "api_standings"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._api_get("standings", {
            "league": WC_LEAGUE_ID,
            "season": WC_SEASON,
        })

        if not data or "response" not in data or len(data["response"]) == 0:
            return []

        standings = []
        league_data = data["response"][0]
        for group_data in league_data.get("league", {}).get("standings", []):
            group_name = ""
            group_teams = []
            for idx, entry in enumerate(group_data):
                if idx == 0:
                    # Extract group letter
                    group_name = entry.get("group", "").replace("Group ", "").strip()

                team = entry.get("team", {})
                name = team.get("name", "")
                code = TEAM_NAME_TO_CODE.get(name, name[:3].upper())

                all_stats = entry.get("all", {})
                group_teams.append({
                    "code": code,
                    "name": name,
                    "name_zh": self._get_team_name_zh(code, name),
                    "flag_emoji": "",
                    "logo": team.get("logo", ""),
                    "elo_rating": 0,
                    "played": all_stats.get("played", 0),
                    "won": all_stats.get("win", 0),
                    "drawn": all_stats.get("draw", 0),
                    "lost": all_stats.get("lose", 0),
                    "goals_for": all_stats.get("goals", {}).get("for", 0),
                    "goals_against": all_stats.get("goals", {}).get("against", 0),
                    "goals_diff": entry.get("goalsDiff", 0),
                    "points": entry.get("points", 0),
                    "rank": entry.get("rank", 0),
                })

            standings.append({
                "group": group_name,
                "standings": group_teams,
            })

        self._set_cache(cache_key, standings)
        return standings

    # ─────────────────────────────────────────
    # Main refresh entry point
    # ─────────────────────────────────────────

    async def refresh_data(self) -> Dict:
        """
        Main entry point: refresh all data from API and return summary.
        Falls back to local JSON when API is unavailable.
        """
        await self._ensure_client()
        results = {}

        # 1. Teams
        if self.api_available:
            results["teams"] = await self.fetch_teams_from_api()
        else:
            results["teams"] = await self._load_teams_from_local()

        # 2. Fixtures
        if self.api_available:
            results["fixtures"] = await self.fetch_fixtures_from_api()
        else:
            results["fixtures"] = []

        # 3. Standings
        if self.api_available:
            results["standings"] = await self.fetch_standings_from_api()
        else:
            results["standings"] = []

        # 4. Sporttery odds (scrape from sporttery.cn)
        sporttery_count = 0
        try:
            sporttery_odds = await asyncio.wait_for(
                self.fetch_sporttery_odds(), timeout=20.0
            )
            sporttery_count = len(sporttery_odds)
            if sporttery_count > 0:
                # Save to data directory for later use
                sporttery_path = os.path.join(DATA_DIR, "sporttery_odds.json")
                with open(sporttery_path, "w", encoding="utf-8") as f:
                    json.dump(list(sporttery_odds.values()), f, ensure_ascii=False, indent=2)
                print(f"[Fetcher] Saved {sporttery_count} sporttery odds entries")
        except asyncio.TimeoutError:
            print("[Fetcher] Sporttery odds fetch timed out")
        except Exception as e:
            print(f"[Fetcher] Sporttery odds error: {e}")

        # 5. Also try browser-based scraping if available
        if sporttery_count == 0:
            try:
                sporttery_count = await self._scrape_sporttery_playwright()
            except Exception as e:
                print(f"[Fetcher] Sporttery browser scrape error: {e}")

        self.last_updated = datetime.now()

        return {
            "success": True,
            "last_updated": self.last_updated.isoformat(),
            "matches_count": len(results.get("fixtures", [])),
            "teams_count": len(results.get("teams", [])),
            "odds_count": sporttery_count,
            "data_source": "api-football" if self.api_available else "local-json",
            "raw_results": results,
        }

    # ─────────────────────────────────────────
    # Local fallback
    # ─────────────────────────────────────────

    async def _scrape_sporttery_playwright(self) -> int:
        """
        Scrape sporttery.cn using Playwright browser.
        Returns count of odds entries found.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("[Fetcher] Playwright not installed, skipping browser scrape")
            print("  Install: pip install playwright && playwright install chromium")
            return 0

        print("[Fetcher] Launching Playwright browser for sporttery.cn...")
        odds_count = 0

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                )
                page = await context.new_page()

                # Capture API responses
                api_data = []

                async def handle_response(response):
                    url = response.url
                    if any(kw in url for kw in ["match", "odds", "zqbf", "list", "data"]):
                        try:
                            ct = response.headers.get("content-type", "")
                            if "json" in ct or url.endswith(".json"):
                                body = await response.json()
                                api_data.append({"url": url, "data": body})
                        except Exception:
                            pass

                page.on("response", handle_response)

                await page.goto("https://www.sporttery.cn/jc/jsq/zqbf/",
                                wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)

                # Try scrolling to load more
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await page.wait_for_timeout(1000)

                # Extract data from captured API responses
                all_matches = []
                for resp in api_data:
                    data = resp["data"]
                    if isinstance(data, list) and len(data) > 0:
                        all_matches.extend(data)
                    elif isinstance(data, dict):
                        for key in ["data", "list", "matchList", "result"]:
                            if key in data and isinstance(data[key], list):
                                all_matches.extend(data[key])

                # If no API data, try extracting from page DOM
                if not all_matches:
                    js_result = await page.evaluate("""
                        () => {
                            const rows = document.querySelectorAll('tr, .match-item, .match-row');
                            const results = [];
                            for (const row of rows) {
                                const texts = [];
                                row.querySelectorAll('td, span, div').forEach(el => {
                                    const t = el.textContent.trim();
                                    if (t && t.length < 50) texts.push(t);
                                });
                                if (texts.length >= 3) results.push(texts);
                            }
                            return JSON.stringify(results);
                        }
                    """)
                    try:
                        dom_data = json.loads(js_result)
                        for item in dom_data:
                            if isinstance(item, list) and len(item) >= 3:
                                all_matches.append({"raw": item, "source": "dom"})
                    except Exception:
                        pass

                # Parse and save
                if all_matches:
                    parsed = self._parse_sporttery_scraped_data(all_matches)
                    odds_count = len(parsed)

                    if odds_count > 0:
                        sporttery_path = os.path.join(DATA_DIR, "sporttery_odds.json")
                        with open(sporttery_path, "w", encoding="utf-8") as f:
                            json.dump(parsed, f, ensure_ascii=False, indent=2)
                        print(f"[Fetcher] Playwright: saved {odds_count} sporttery odds entries")

                        # Also update the cache
                        for entry in parsed:
                            key = f"{entry.get('home_team', '')}|{entry.get('away_team', '')}"
                            if key and "home" in entry:
                                cache_key = f"sporttery_{key}"
                                self._set_cache(cache_key, entry)
                    else:
                        print(f"[Fetcher] Playwright: found {len(all_matches)} raw items but could not parse odds")

                await browser.close()

        except Exception as e:
            print(f"[Fetcher] Playwright scrape error: {e}")

        return odds_count

    def _parse_sporttery_scraped_data(self, raw_data: list) -> list:
        """Parse scraped sporttery data into standard odds format."""
        parsed = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue

            home = (item.get("homeTeamName") or item.get("homeName") or
                    item.get("home") or item.get("hostName") or "")
            away = (item.get("awayTeamName") or item.get("awayName") or
                    item.get("away") or item.get("guestName") or "")

            sp_win = item.get("spWin") or item.get("spH") or item.get("hSp") or 0
            sp_draw = item.get("spDraw") or item.get("spD") or item.get("dSp") or 0
            sp_loss = item.get("spLoss") or item.get("spA") or item.get("aSp") or 0

            entry = {
                "bookmaker": "sporttery",
                "source": "sporttery.cn",
                "home_team": home,
                "away_team": away,
                "match_date": item.get("matchDate") or item.get("date") or "",
                "match_num": str(item.get("matchNum") or item.get("id") or ""),
            }

            try:
                if float(sp_win) > 0 and float(sp_draw) > 0 and float(sp_loss) > 0:
                    entry["home"] = float(sp_win)
                    entry["draw"] = float(sp_draw)
                    entry["away"] = float(sp_loss)
            except (ValueError, TypeError):
                continue

            handicap = item.get("letBall") or item.get("handicap") or item.get("let")
            if handicap is not None:
                try:
                    entry["handicap"] = float(handicap)
                except (ValueError, TypeError):
                    pass

            ou = item.get("bs0") or item.get("sizeLine") or item.get("overUnderLine")
            if ou is not None:
                try:
                    entry["over_under_line"] = float(ou)
                except (ValueError, TypeError):
                    pass

            if "home" in entry:
                parsed.append(entry)

        return parsed

    async def _load_teams_from_local(self) -> List[Dict]:
        """Load teams from local JSON."""
        try:
            data = self._load_json_file("teams.json")
            teams = []
            for t in data.get("teams", []):
                teams.append({
                    "code": t["code"],
                    "name": t.get("name", ""),
                    "name_zh": t.get("name_zh", ""),
                    "logo": "",
                    "country": t.get("confederation", ""),
                    "group": t.get("group", ""),
                    "elo_rating": t.get("elo_rating", 1800),
                    "fifa_rank": t.get("fifa_rank", 30),
                    "formation": t.get("formation", "4-3-3"),
                    "flag_emoji": t.get("flag_emoji", ""),
                })
            return teams
        except Exception as e:
            print(f"[Fetcher] Local load error: {e}")
            return []

    # ─────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────

    def _load_json_file(self, filename: str) -> dict:
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _extract_group(round_str: str) -> str:
        """Extract group letter from round string like 'Group A - Match 1'."""
        if "Group" in round_str:
            parts = round_str.split("Group")
            if len(parts) > 1:
                letter = parts[1].strip().split()[0].strip(" -")
                if letter and len(letter) <= 2:
                    return letter
        return ""

    @staticmethod
    def _parse_percent(val: str) -> float:
        """Parse percentage string like '45%' to float."""
        if not val:
            return 0.0
        try:
            return float(val.replace("%", "").strip())
        except ValueError:
            return 0.0

    @staticmethod
    def _get_team_name_zh(code: str, fallback: str) -> str:
        """Get Chinese team name from code."""
        ZH_NAMES = {
            "ARG": "阿根廷", "BRA": "巴西", "FRA": "法国", "ENG": "英格兰",
            "ESP": "西班牙", "GER": "德国", "POR": "葡萄牙", "NED": "荷兰",
            "ITA": "意大利", "BEL": "比利时", "URU": "乌拉圭", "CRO": "克罗地亚",
            "COL": "哥伦比亚", "MEX": "墨西哥", "USA": "美国", "MAR": "摩洛哥",
            "SEN": "塞内加尔", "JPN": "日本", "KOR": "韩国", "IRN": "伊朗",
            "AUS": "澳大利亚", "EGY": "埃及", "GHA": "加纳", "CIV": "科特迪瓦",
            "SRB": "塞尔维亚", "SUI": "瑞士", "DEN": "丹麦", "ECU": "厄瓜多尔",
            "POL": "波兰", "CAN": "加拿大", "KSA": "沙特阿拉伯", "QAT": "卡塔尔",
            "NGA": "尼日利亚", "CRC": "哥斯达黎加", "TUN": "突尼斯", "CMR": "喀麦隆",
            "RSA": "南非", "PRK": "朝鲜", "IRQ": "伊拉克", "UZB": "乌兹别克斯坦",
            "JOR": "约旦", "OMN": "阿曼", "PSE": "巴勒斯坦", "KUW": "科威特",
            "BAH": "巴林", "CHN": "中国", "THA": "泰国", "VIE": "越南",
            "IDN": "印度尼西亚", "MYS": "马来西亚", "PHI": "菲律宾",
            "NZL": "新西兰", "HON": "洪都拉斯", "PAN": "巴拿马", "JAM": "牙买加",
            "TRI": "特立尼达和多巴哥", "SLV": "萨尔瓦多", "GUA": "危地马拉",
            "CUB": "古巴", "DOM": "多米尼加", "HAI": "海地", "SUR": "苏里南",
            "VEN": "委内瑞拉", "PAR": "巴拉圭", "CHI": "智利", "PER": "秘鲁",
            "BOL": "玻利维亚", "UKR": "乌克兰", "RUS": "俄罗斯", "SWE": "瑞典",
            "NOR": "挪威", "FIN": "芬兰", "AUT": "奥地利", "CZE": "捷克",
            "ROU": "罗马尼亚", "TUR": "土耳其", "WAL": "威尔士", "SCO": "苏格兰",
            "IRE": "爱尔兰",
        }
        return ZH_NAMES.get(code, fallback)


# ─────────────────────────────────────────────
# Standalone run
# ─────────────────────────────────────────────

async def main():
    fetcher = DataFetcher()
    try:
        result = await fetcher.refresh_data()
        print(json.dumps({
            "success": result["success"],
            "last_updated": result["last_updated"],
            "matches_count": result["matches_count"],
            "teams_count": result["teams_count"],
            "data_source": result["data_source"],
        }, indent=2, ensure_ascii=False))
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
