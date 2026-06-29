import React from 'react';
import { useDashboard, formatProb, team1Info, team2Info } from '../hooks/useData';
import type { ApiMatchWithPrediction } from '../hooks/useData';

// 格式化UTC时间为北京时间显示
function formatBeijingTime(kickOff: string): string {
  if (!kickOff || kickOff === 'TBD') return '时间待定';
  try {
    const date = new Date(kickOff);
    if (isNaN(date.getTime())) return kickOff;
    // 转换为北京时间 (UTC+8)
    const bjDate = new Date(date.getTime() + 8 * 60 * 60 * 1000);
    const month = bjDate.getUTCMonth() + 1;
    const day = bjDate.getUTCDate();
    const hour = bjDate.getUTCHours().toString().padStart(2, '0');
    const minute = bjDate.getUTCMinutes().toString().padStart(2, '0');
    return `${month}月${day}日 ${hour}:${minute}`;
  } catch {
    return kickOff;
  }
}

// 从kick_off获取排序用的日期key（北京时间日期）
function getBeijingDateKey(kickOff: string): string {
  if (!kickOff || kickOff === 'TBD') return '9999-99-99';
  try {
    const date = new Date(kickOff);
    if (isNaN(date.getTime())) return '9999-99-99';
    const bjDate = new Date(date.getTime() + 8 * 60 * 60 * 1000);
    const y = bjDate.getUTCFullYear();
    const m = (bjDate.getUTCMonth() + 1).toString().padStart(2, '0');
    const d = bjDate.getUTCDate().toString().padStart(2, '0');
    return `${y}-${m}-${d}`;
  } catch {
    return '9999-99-99';
  }
}

// 国旗图片URL映射 - 使用 flagcdn.com 的真实国旗图片
function getFlagUrl(code: string): string {
  const FLAG_MAP: Record<string, string> = {
    ARG: 'ar', BRA: 'br', FRA: 'fr', ENG: 'gb-eng', ESP: 'es',
    GER: 'de', POR: 'pt', NED: 'nl', ITA: 'it', BEL: 'be',
    URU: 'uy', CRO: 'hr', COL: 'co', MEX: 'mx', USA: 'us',
    MAR: 'ma', SEN: 'sn', JPN: 'jp', KOR: 'kr', IRN: 'ir',
    AUS: 'au', EGY: 'eg', GHA: 'gh', CIV: 'ci', SRB: 'rs',
    SUI: 'ch', DEN: 'dk', ECU: 'ec', POL: 'pl', CAN: 'ca',
    KSA: 'sa', QAT: 'qa', NGA: 'ng', CRC: 'cr', TUN: 'tn',
    CMR: 'cm', RSA: 'za', PRK: 'kp', IRQ: 'iq', UZB: 'uz',
    JOR: 'jo', OMN: 'om', PSE: 'ps', KUW: 'kw', BAH: 'bh',
    CHN: 'cn', THA: 'th', VIE: 'vn', IDN: 'id', MYS: 'my',
    PHI: 'ph', NZL: 'nz', HON: 'hn', PAN: 'pa', JAM: 'jm',
    TRI: 'tt', SLV: 'sv', GUA: 'gt', CUB: 'cu', DOM: 'do',
    HAI: 'ht', SUR: 'sr', VEN: 've', PAR: 'py', CHI: 'cl',
    PER: 'pe', BOL: 'bo', UKR: 'ua', RUS: 'ru', SWE: 'se',
    NOR: 'no', FIN: 'fi', AUT: 'at', CZE: 'cz', ROU: 'ro',
    TUR: 'tr', WAL: 'gb-wls', SCO: 'gb-sct', IRE: 'ie',
    BIH: 'ba', CUW: 'cw', CPV: 'cv', ALG: 'dz', COD: 'cd',
  };
  const iso = FLAG_MAP[code] || code.toLowerCase();
  return `https://flagcdn.com/w80/${iso}.png`;
}

// 国旗组件 - 显示真实国旗图片，fallback到emoji
const FlagImage: React.FC<{ code: string; emoji: string; size?: number; className?: string }> = ({ code, emoji, size = 48, className = '' }) => {
  const [imgError, setImgError] = React.useState(false);
  const url = getFlagUrl(code);

  if (imgError) {
    return <span className={className} style={{ fontSize: size * 0.8 }}>{emoji}</span>;
  }

  return (
    <img
      src={url}
      alt={`${code} flag`}
      className={className}
      style={{ width: size, height: size * 0.6, objectFit: 'contain' }}
      onError={() => setImgError(true)}
    />
  );
};

interface DashboardProps {
  onOpenMatch?: (matchId: number) => void;
}

type FilterMode = 'all' | 'group' | 'date';

const Dashboard: React.FC<DashboardProps> = ({ onOpenMatch }) => {
  const { data, loading, error, refresh } = useDashboard();
  const [filterMode, setFilterMode] = React.useState<FilterMode>('all');
  const [selectedGroup, setSelectedGroup] = React.useState<string>('A');
  const [selectedDate, setSelectedDate] = React.useState<string>('');

  // 提取所有小组和日期
  const groups = React.useMemo(() => {
    if (!data) return [];
    const set = new Set(data.upcoming_matches.map(m => m.group_name));
    return Array.from(set).sort();
  }, [data]);

  const dates = React.useMemo(() => {
    if (!data) return [];
    const set = new Set(data.upcoming_matches.map(m => {
      if (m.kick_off) return getBeijingDateKey(m.kick_off);
      return m.date || 'TBD';
    }));
    return Array.from(set).sort();
  }, [data]);

  // 筛选后的比赛
  const filteredMatches = React.useMemo(() => {
    if (!data) return [];
    let matches: ApiMatchWithPrediction[];
    if (filterMode === 'group') matches = data.upcoming_matches.filter(m => m.group_name === selectedGroup);
    else if (filterMode === 'date') {
      const target = selectedDate || dates[0] || '';
      matches = data.upcoming_matches.filter(m => {
        const key = m.kick_off ? getBeijingDateKey(m.kick_off) : m.date;
        return key === target;
      });
    } else {
      matches = data.upcoming_matches;
    }
    // 按开赛时间排序
    return matches.sort((a, b) => {
      const aTime = a.kick_off ? new Date(a.kick_off).getTime() : Infinity;
      const bTime = b.kick_off ? new Date(b.kick_off).getTime() : Infinity;
      return aTime - bTime;
    });
  }, [data, filterMode, selectedGroup, selectedDate, dates]);

  // 按筛选模式分组显示
  const groupedMatches = React.useMemo(() => {
    if (filterMode === 'group') {
      // 按北京时间日期分组
      const map = new Map<string, ApiMatchWithPrediction[]>();
      for (const m of filteredMatches) {
        const key = m.kick_off ? getBeijingDateKey(m.kick_off) : (m.date || 'TBD');
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(m);
      }
      return Array.from(map.entries()).map(([date, matches]) => {
        // 格式化日期标签
        let label = date;
        if (date !== 'TBD' && date !== '9999-99-99') {
          const parts = date.split('-');
          if (parts.length === 3) label = `${parseInt(parts[1])}月${parseInt(parts[2])}日`;
        }
        return { label, matches };
      });
    }
    if (filterMode === 'date') {
      // 按北京时间日期分组
      const map = new Map<string, ApiMatchWithPrediction[]>();
      for (const m of filteredMatches) {
        const key = m.kick_off ? getBeijingDateKey(m.kick_off) : (m.date || 'TBD');
        if (!map.has(key)) map.set(key, []);
        map.get(key)!.push(m);
      }
      return Array.from(map.entries()).map(([date, matches]) => ({ label: date, matches }));
    }
    // 全部模式：按小组分组
    const map = new Map<string, ApiMatchWithPrediction[]>();
    for (const m of filteredMatches) {
      const key = `${m.group_name}组`;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(m);
    }
    return Array.from(map.entries()).map(([group, matches]) => ({ label: group, matches }));
  }, [filteredMatches, filterMode]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>加载数据中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-message">
        <p>⚠️ {error}</p>
        <button onClick={() => refresh()} style={{ marginTop: 8, padding: '6px 16px', cursor: 'pointer' }}>
          重新加载
        </button>
      </div>
    );
  }

  if (!data || data.upcoming_matches.length === 0) {
    return <div className="empty-message">暂无赛程数据</div>;
  }

  return (
    <div className="dashboard">
      <section className="section upcoming-matches-section">
        <h2 className="section-title">
          <span className="title-icon">⚽</span>
          赛程总览
          <span className="title-badge">{filteredMatches.length} 场</span>
        </h2>

        {/* 筛选栏 */}
        <div className="filter-bar">
          <div className="filter-mode-tabs">
            <button
              className={`filter-tab ${filterMode === 'all' ? 'active' : ''}`}
              onClick={() => setFilterMode('all')}
            >全部</button>
            <button
              className={`filter-tab ${filterMode === 'group' ? 'active' : ''}`}
              onClick={() => setFilterMode('group')}
            >按小组</button>
            <button
              className={`filter-tab ${filterMode === 'date' ? 'active' : ''}`}
              onClick={() => setFilterMode('date')}
            >按日期</button>
          </div>

          {filterMode === 'group' && (
            <div className="filter-chips">
              {groups.map(g => (
                <button
                  key={g}
                  className={`filter-chip ${selectedGroup === g ? 'active' : ''}`}
                  onClick={() => setSelectedGroup(g)}
                >{g}组</button>
              ))}
            </div>
          )}

          {filterMode === 'date' && (
            <div className="filter-chips">
              {dates.map(d => {
                let display = d;
                if (d !== 'TBD' && d !== '9999-99-99' && d.includes('-')) {
                  const parts = d.split('-');
                  if (parts.length === 3) display = `${parseInt(parts[1])}月${parseInt(parts[2])}日`;
                }
                return (
                  <button
                    key={d}
                    className={`filter-chip ${selectedDate === d ? 'active' : ''}`}
                    onClick={() => setSelectedDate(d)}
                  >{display}</button>
                );
              })}
            </div>
          )}
        </div>

        <p className="section-subtitle">点击任意比赛卡片查看详细预测分析</p>

        {/* 分组显示 */}
        {groupedMatches.map(({ label, matches }) => (
          <div key={label} className="match-group-section">
            <h3 className="match-group-label">{label}</h3>
            <div className="matches-grid">
              {matches.map((match) => (
                <MatchCard key={match.id} match={match} onOpenMatch={onOpenMatch} />
              ))}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
};

interface MatchCardProps {
  match: ApiMatchWithPrediction;
  onOpenMatch?: (matchId: number) => void;
}

const MatchCard: React.FC<MatchCardProps> = ({ match, onOpenMatch }) => {
  const t1 = team1Info(match);
  const t2 = team2Info(match);
  const pred = match.prediction;
  const hasPred = pred && !pred.hasOwnProperty('error');

  return (
    <div
      className="match-card"
      onClick={() => onOpenMatch?.(match.id)}
      style={{ cursor: onOpenMatch ? 'pointer' : 'default' }}
    >
      {/* Group label */}
      <div className="match-card-header">
        <span className="match-group">{match.group_name}组</span>
        <span className="match-round">{match.round}</span>
      </div>

      {/* VS Section - 国旗在队名上方 */}
      <div className="match-teams">
        <div className="team-block team-left">
          <FlagImage code={t1.code} emoji={t1.flag || ''} size={56} className="team-flag-img" />
          <span className="team-name-zh">{t1.name_zh}</span>
          <span className="team-name-en">{t1.name}</span>
          <span className="team-elo">ELO {Math.round(t1.elo)}</span>
        </div>

        <div className="vs-divider">
          <span className="vs-text">VS</span>
        </div>

        <div className="team-block team-right">
          <FlagImage code={t2.code} emoji={t2.flag || ''} size={56} className="team-flag-img" />
          <span className="team-name-zh">{t2.name_zh}</span>
          <span className="team-name-en">{t2.name}</span>
          <span className="team-elo">ELO {Math.round(t2.elo)}</span>
        </div>
      </div>

      {/* Match date */}
      <div className="match-date">
        {match.kick_off ? (
          <span className="kickoff-time">北京时间 {formatBeijingTime(match.kick_off)}</span>
        ) : (
          <span>{match.date}</span>
        )}
      </div>

      {/* Prediction bars */}
      {hasPred && (
        <div className="prediction-section">
          <div className="prediction-bars">
            <div className="pred-bar-group">
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-home" style={{ width: `${pred!.home_win_prob}%` }} />
              </div>
              <div className="pred-labels">
                <span className="pred-label pred-label-home">{t1.name_zh}胜 {formatProb(pred!.home_win_prob)}</span>
              </div>
            </div>
            <div className="pred-bar-group">
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-draw" style={{ width: `${pred!.draw_prob}%` }} />
              </div>
              <div className="pred-labels">
                <span className="pred-label pred-label-draw">平局 {formatProb(pred!.draw_prob)}</span>
              </div>
            </div>
            <div className="pred-bar-group">
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-away" style={{ width: `${pred!.away_win_prob}%` }} />
              </div>
              <div className="pred-labels">
                <span className="pred-label pred-label-away">{t2.name_zh}胜 {formatProb(pred!.away_win_prob)}</span>
              </div>
            </div>
          </div>

          {/* Predicted score */}
          <div className="predicted-score">
            预测比分: <strong>{pred!.top_5_scorelines?.[0]?.score || Math.round(pred!.expected_goals_home) + '-' + Math.round(pred!.expected_goals_away)}</strong>
          </div>

          {/* Odds info from prediction factors */}
          {(pred as any)?.factors?.odds_analysis?.available && (
            <div className="odds-quick-info">
              <span className="odds-badge">
                {(pred as any).factors.odds_analysis.num_bookmakers}家机构
              </span>
              <span className="odds-badge">
                赔率 {(pred as any).factors.odds_analysis.home_win?.toFixed(1)}% / {(pred as any).factors.odds_analysis.draw?.toFixed(1)}% / {(pred as any).factors.odds_analysis.away_win?.toFixed(1)}%
              </span>
              <span className="odds-badge">
                权重 {((pred as any).factors.odds_analysis.weight * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* 点击提示 */}
      {onOpenMatch && (
        <div className="match-card-footer-hint">点击查看详细分析 →</div>
      )}
    </div>
  );
};

export default Dashboard;
