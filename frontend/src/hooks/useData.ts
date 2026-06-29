import { useState, useEffect, useCallback, useMemo } from 'react';

// ─────────────────────────────────────
// Types (matching backend response)
// ─────────────────────────────────────

export interface TeamInfo {
  code: string;
  name: string;
  name_zh: string;
  elo_rating: number;
  flag_emoji?: string;
}

export interface ApiMatch {
  id: number;
  round: string;
  group_name: string;
  date: string;
  kick_off: string;  // UTC时间，如 "2026-06-11T19:00:00Z"
  team1: string;
  team1_name: string;
  team1_zh: string;
  team1_flag: string;
  team1_elo: number;
  team1_fifa_rank?: number;
  team1_formation?: string;
  team2: string;
  team2_name: string;
  team2_zh: string;
  team2_flag: string;
  team2_elo: number;
  team2_fifa_rank?: number;
  team2_formation?: string;
  score1: number | null;
  score2: number | null;
  status: string;
  stage: string;
}

export interface MatchPrediction {
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  expected_goals_home: number;
  expected_goals_away: number;
  top_5_scorelines: Scoreline[];
  confidence_level: string;
  elo_diff?: number;
}

export interface Scoreline {
  score: string;
  probability: number;
}

export interface PlayerData {
  number: number;
  name: string;
  name_zh: string;
  position: string;
  position_zh: string;
}

export interface H2HStats {
  total: number;
  home_wins: number;
  draws: number;
  away_wins: number;
}

export interface H2HMatch {
  year: number;
  tournament: string;
  date: string;
  team1: string;
  team2: string;
  score1: number;
  score2: number;
  round: string;
}

export interface H2HData {
  stats: H2HStats;
  matches: H2HMatch[];
}

export interface OddsEntry {
  bookmaker: string;
  home: number;
  draw: number;
  away: number;
}

export interface OddsData {
  bookmakers: OddsEntry[];
  correct_scores: string[];
}

export interface MatchDetail {
  match: ApiMatch;
  players: {
    team1: PlayerData[];
    team2: PlayerData[];
  };
  h2h: H2HData;
  odds: OddsData;
  prediction: MatchPrediction;
}

export interface ApiMatchWithPrediction extends ApiMatch {
  prediction?: MatchPrediction;
}

export interface DashboardData {
  upcoming_matches: ApiMatchWithPrediction[];
  upcoming_by_date: Record<string, ApiMatchWithPrediction[]>;
  recent_finished: ApiMatchWithPrediction[];
  total_upcoming: number;
}

export interface GroupStandingItem {
  code: string;
  name: string;
  name_zh: string;
  flag_emoji: string;
  elo_rating: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goals_diff: number;
  points: number;
}

export interface GroupData {
  group: string;
  standings: GroupStandingItem[];
}

export interface GroupsResponse {
  groups: GroupData[];
  total_groups: number;
}

export interface BracketMatch {
  match_id: number;
  label: string;
  team1: string | null;      // team code or "TBD"
  team1_name?: string;
  team1_name_zh?: string;
  team1_flag?: string;
  team2: string | null;
  team2_name?: string;
  team2_name_zh?: string;
  team2_flag?: string;
  date: string;
  kick_off?: string;
  status: string;            // "upcoming", "finished", "live"
  score1?: number | null;
  score2?: number | null;
  score1_pen?: number | null;
  score2_pen?: number | null;
  winner?: string | null;
  prediction?: {
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    expected_goals_home: number;
    expected_goals_away: number;
    top_5_scorelines: { score: string; probability: number }[];
    predicted_score?: string;
    confidence_level: string;
  } | null;
}

export interface BracketData {
  round_of_32: BracketMatch[];
  round_of_16: BracketMatch[];
  quarter_finals: BracketMatch[];
  semi_finals: BracketMatch[];
  third_place: BracketMatch;
  final: BracketMatch;
}

export interface BracketResponse {
  bracket: BracketData;
  total_knockout_matches: number;
  status: string;
  finished_matches?: number;
  next_match?: {
    match_id: number;
    team1: string;
    team2: string;
    date: string;
    kick_off: string;
  };
}

// New types for Monte Carlo, Recent Matches, System Status, Backtest
export interface RecentMatch {
  date: string;
  opponent_name: string;
  opponent_name_zh?: string;
  opponent_code: string;
  is_home: boolean;
  goals_for: number;
  goals_against: number;
  result: 'W' | 'D' | 'L';
  league: string;
  competition_type: string;
}

export interface InjuryInfo {
  player_name: string;
  team_name: string;
  reason: string;
  type: string;
}

export interface MonteCarloResult {
  num_simulations: number;
  champion_probs: Record<string, number>;
  top_10_champions: { code: string; name: string; name_zh: string; probability: number }[];
  most_likely_final: { team1: string; team2: string; probability: number } | null;
  most_likely_champion: { team: string; probability: number } | null;
  stage_probs: Record<string, Record<string, number>>;
}

export interface SystemStatus {
  status: string;
  last_updated: string;
  matches_loaded: number;
  backtest_completed: boolean;
  api_source: string;
  api_key_configured: boolean;
  football_data_key_configured: boolean;
  cache_type: string;
  refresh_scheduler_running: boolean;
}

export interface BacktestYearResult {
  year: number;
  total_matches: number;
  correct_direction: number;
  direction_accuracy: number;
  exact_score_correct: number;
  exact_score_rate: number;
  within_one_goal: number;
  within_one_goal_rate: number;
  group_stage_accuracy: number;
  knockout_accuracy: number;
}

// ─────────────────────────────────────
// Utility functions
// ─────────────────────────────────────

/**
 * Format probability.
 * Backend returns percentages (0-100), NOT fractions.
 * So we display `${p.toFixed(1)}%` directly.
 */
export function formatProb(p: number): string {
  if (p == null || isNaN(p)) return '—';
  return `${p.toFixed(1)}%`;
}

export function team1Info(match: ApiMatch) {
  return {
    code: match.team1,
    name: match.team1_name,
    name_zh: match.team1_zh,
    flag: match.team1_flag,
    elo: match.team1_elo,
  };
}

export function team2Info(match: ApiMatch) {
  return {
    code: match.team2,
    name: match.team2_name,
    name_zh: match.team2_zh,
    flag: match.team2_flag,
    elo: match.team2_elo,
  };
}

// ─────────────────────────────────────
// API base URL
// ─────────────────────────────────────

const API_BASE = '/api';
const FETCH_TIMEOUT = 15000; // 15 second timeout for all API calls
const MONTE_CARLO_TIMEOUT = 300000; // 5 min for Monte Carlo simulation
const BACKTEST_TIMEOUT = 120000; // 2 min for backtest

/**
 * Fetch with timeout - prevents infinite loading if server is slow/unresponsive.
 */
async function fetchWithTimeout(url: string, options?: RequestInit, timeout: number = FETCH_TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Fetch with automatic retry for backend-not-ready scenarios (502, ECONNREFUSED, network errors).
 * Retries up to `retries` times with exponential backoff, starting at `baseDelay` ms.
 */
async function fetchWithRetry(
  url: string,
  options?: RequestInit,
  timeout: number = FETCH_TIMEOUT,
  retries: number = 6,
  baseDelay: number = 1500,
): Promise<Response> {
  let lastError: Error | null = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetchWithTimeout(url, options, timeout);
      // 502/503 means backend isn't ready yet — retry
      if ((res.status === 502 || res.status === 503) && attempt < retries) {
        const delay = baseDelay * Math.pow(1.5, attempt);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      return res;
    } catch (e: any) {
      lastError = e;
      // Network error (ECONNREFUSED, abort, etc.) — retry if attempts remain
      if (attempt < retries) {
        const delay = baseDelay * Math.pow(1.5, attempt);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
    }
  }
  throw lastError || new Error('Request failed after retries');
}

// ─────────────────────────────────────
// Data hooks
// ─────────────────────────────────────

export function useDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithRetry(`${API_BASE}/dashboard`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: DashboardData = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

export function useGroups() {
  const [data, setData] = useState<GroupsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithRetry(`${API_BASE}/groups`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: GroupsResponse = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Refresh on "refresh-data" custom event from the refresh button
  useEffect(() => {
    const handler = () => fetchData();
    window.addEventListener('refresh-data', handler);
    return () => window.removeEventListener('refresh-data', handler);
  }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

export function useBracket() {
  const [data, setData] = useState<BracketResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithRetry(`${API_BASE}/bracket`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: BracketResponse = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load bracket');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

export function useMatchDetail(matchId: number) {
  const [data, setData] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/match/${matchId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: MatchDetail = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load match detail');
    } finally {
      setLoading(false);
    }
  }, [matchId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return { data, loading, error, refresh: fetchData };
}

export function useTeamMap(teamList?: TeamInfo[]) {
  return useMemo(() => {
    const map: Record<string, TeamInfo> = {};
    if (teamList) {
      for (const t of teamList) {
        map[t.code] = t;
      }
    }
    return map;
  }, [teamList]);
}

export function getFlagEmoji(code: string): string {
  const FLAGS: Record<string, string> = {
    ARG: '🇦🇷', BRA: '🇧🇷', FRA: '🇫🇷', ENG: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', ESP: '🇪🇸',
    GER: '🇩🇪', POR: '🇵🇹', NED: '🇳🇱', ITA: '🇮🇹', BEL: '🇧🇪',
    URU: '🇺🇾', CRO: '🇭🇷', COL: '🇨🇴', MEX: '🇲🇽', USA: '🇺🇸',
    MAR: '🇲🇦', SEN: '🇸🇳', JPN: '🇯🇵', KOR: '🇰🇷', IRN: '🇮🇷',
    AUS: '🇦🇺', EGY: '🇪🇬', GHA: '🇬🇭', CIV: '🇨🇮', SRB: '🇷🇸',
    SUI: '🇨🇭', DEN: '🇩🇰', ECU: '🇪🇨', POL: '🇵🇱', CAN: '🇨🇦',
    KSA: '🇸🇦', QAT: '🇶🇦',
    RSA: '🇿🇦', CZE: '🇨🇿', BIH: '🇧🇦', HAI: '🇭🇹', SCO: '🏴',
    PAR: '🇵🇾', TUR: '🇹🇷', CUW: '🇨🇼', SWE: '🇸🇪', TUN: '🇹🇳',
    NZL: '🇳🇿', CPV: '🇨🇻', IRQ: '🇮🇶', NOR: '🇳🇴', ALG: '🇩🇿',
    AUT: '🇦🇹', JOR: '🇯🇴', COD: '🇨🇩', UZB: '🇺🇿', PAN: '🇵🇦',
    // Historical opponents
    RUS: '🇷🇺', PER: '🇵🇪', VEN: '🇻🇪', CHI: '🇨🇱', HUN: '🇭🇺',
    ISR: '🇮🇱', GRE: '🇬🇷', ROU: '🇷🇴', FIN: '🇫🇮', ALB: '🇦🇱',
    IRL: '🇮🇪', IDN: '🇮🇩', PLE: '🇵🇸', BHR: '🇧🇭', LBN: '🇱🇧',
    SVK: '🇸🇰', SVN: '🇸🇮', WAL: '🏴󠁧󠁢󠁷󠁬󠁳󠁿', NIR: '🇬🇧',
    MKD: '🇲🇰', MNE: '🇲🇪', KOS: '🇽🇰', GAB: '🇬🇦', ZIM: '🇿🇼',
    BLR: '🇧🇾', LUX: '🇱🇺',
  };
  return FLAGS[code] || '🏳️';
}

// ─────────────────────────────────────
// New hooks: Monte Carlo, Recent Matches, System Status, Backtest
// ─────────────────────────────────────

export function useMonteCarlo() {
  const [data, setData] = useState<MonteCarloResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSimulation = useCallback(async (numSims: number = 10000) => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/monte-carlo?num_sims=${numSims}`, { method: 'POST' }, MONTE_CARLO_TIMEOUT);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json: MonteCarloResult = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      if (e.name === 'AbortError') {
        setError('请求超时，请减少模拟次数或稍后重试');
      } else {
        setError(e.message || 'Simulation failed');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, runSimulation };
}

export function useRecentMatches(teamCode: string) {
  const [data, setData] = useState<RecentMatch[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/recent-matches/${teamCode}?last=10`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json.matches || []);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [teamCode]);

  useEffect(() => { fetchData(); }, [fetchData]);
  return { data, loading, error, refresh: fetchData };
}

export function useSystemStatus() {
  const [data, setData] = useState<SystemStatus | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetchWithRetry(`${API_BASE}/status`);
      if (!res.ok) return;
      const json: SystemStatus = await res.json();
      setData(json);
    } catch {}
  }, []);

  useEffect(() => { fetchData(); const interval = setInterval(fetchData, 60000); return () => clearInterval(interval); }, [fetchData]);
  return { data };
}

export function useBacktest() {
  const [data, setData] = useState<BacktestYearResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchWithTimeout(`${API_BASE}/backtest`, undefined, BACKTEST_TIMEOUT);
      if (res.status === 503) throw new Error('回测数据正在计算中，请稍后刷新页面');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      // Transform server response into BacktestYearResult array
      const results: BacktestYearResult[] = [];
      if (json.results) {
        for (const [year, r] of Object.entries(json.results)) {
          if (year === 'average') continue;
          results.push({
            year: parseInt(year),
            total_matches: (r as any).total_matches || 0,
            correct_direction: (r as any).direction_accuracy ? Math.round((r as any).direction_accuracy * ((r as any).total_matches || 0) / 100) : 0,
            direction_accuracy: (r as any).direction_accuracy || 0,
            exact_score_correct: (r as any).exact_score_accuracy ? Math.round((r as any).exact_score_accuracy * ((r as any).total_matches || 0) / 100) : 0,
            exact_score_rate: (r as any).exact_score_accuracy || 0,
            within_one_goal: (r as any).within_one_goal_accuracy ? Math.round((r as any).within_one_goal_accuracy * ((r as any).total_matches || 0) / 100) : 0,
            within_one_goal_rate: (r as any).within_one_goal_accuracy || 0,
            group_stage_accuracy: (r as any).group_stage_accuracy || 0,
            knockout_accuracy: (r as any).knockout_accuracy || 0,
          });
        }
      }
      setData(results);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Failed to load backtest');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  return { data, loading, error, refetch: fetchData };
}