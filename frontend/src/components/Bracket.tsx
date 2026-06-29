import React from 'react';
import { useBracket, getFlagEmoji } from '../hooks/useData';
import type { BracketData, BracketMatch } from '../hooks/useData';

// 国旗图片URL映射 - 使用 flagcdn.com 的真实国旗图片（与Dashboard一致）
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
  return `https://flagcdn.com/w40/${iso}.png`;
}

// 国旗组件 - 显示真实国旗图片，fallback到emoji（与Dashboard一致）
const FlagImage: React.FC<{ code: string; emoji: string; size?: number; className?: string }> = ({ code, emoji, size = 32, className = '' }) => {
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

interface BracketProps {
  onOpenMatch?: (matchId: number) => void;
}

const Bracket: React.FC<BracketProps> = ({ onOpenMatch }) => {
  const { data, loading, error } = useBracket();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>加载淘汰赛对阵...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-message">⚠️ {error}</div>;
  }

  if (!data || !data.bracket) {
    return <div className="empty-message">暂无淘汰赛数据</div>;
  }

  const b = data.bracket;

  return (
    <div className="bracket-page">
      <h2 className="section-title">
        <span className="title-icon">🏆</span>
        淘汰赛对阵图
        <span className="title-badge">2026</span>
      </h2>

      <div className="bracket-container">
        {/* Round of 32 */}
        <div className="bracket-round">
          <h3 className="bracket-round-title">1/16 决赛</h3>
          <div className="bracket-matches-grid">
            {b.round_of_32.map((m) => (
              <BracketSlot key={m.match_id} match={m} onOpenMatch={onOpenMatch} />
            ))}
          </div>
        </div>

        <div className="bracket-connector">
          <span className="connector-arrow">→</span>
        </div>

        {/* Round of 16 */}
        <div className="bracket-round">
          <h3 className="bracket-round-title">1/8 决赛</h3>
          <div className="bracket-matches-grid">
            {b.round_of_16.map((m) => (
              <BracketSlot key={m.match_id} match={m} onOpenMatch={onOpenMatch} />
            ))}
          </div>
        </div>

        <div className="bracket-connector">
          <span className="connector-arrow">→</span>
        </div>

        {/* Quarter Finals */}
        <div className="bracket-round">
          <h3 className="bracket-round-title">1/4 决赛</h3>
          <div className="bracket-matches-grid">
            {b.quarter_finals.map((m) => (
              <BracketSlot key={m.match_id} match={m} onOpenMatch={onOpenMatch} />
            ))}
          </div>
        </div>

        <div className="bracket-connector">
          <span className="connector-arrow">→</span>
        </div>

        {/* Semi Finals */}
        <div className="bracket-round">
          <h3 className="bracket-round-title">半决赛</h3>
          <div className="bracket-matches-grid">
            {b.semi_finals.map((m) => (
              <BracketSlot key={m.match_id} match={m} onOpenMatch={onOpenMatch} />
            ))}
          </div>
        </div>

        <div className="bracket-connector">
          <span className="connector-arrow">→</span>
        </div>

        {/* Final & Third Place */}
        <div className="bracket-round bracket-final-round">
          <div className="bracket-matches-grid">
            <BracketSlot match={b.third_place} isThird onOpenMatch={onOpenMatch} />
            <div className="bracket-divider" />
            <BracketSlot match={b.final} isFinal onOpenMatch={onOpenMatch} />
          </div>
        </div>
      </div>
    </div>
  );
};

interface BracketSlotProps {
  match: BracketMatch;
  isFinal?: boolean;
  isThird?: boolean;
  onOpenMatch?: (matchId: number) => void;
}

const BracketSlot: React.FC<BracketSlotProps> = ({ match, isFinal, isThird, onOpenMatch }) => {
  const isFinished = match.status === 'finished';
  const isLive = match.status === 'live';
  const isUpcoming = match.status === 'upcoming';
  const isTBD1 = !match.team1 || match.team1 === 'TBD';
  const isTBD2 = !match.team2 || match.team2 === 'TBD';
  const hasPrediction = isUpcoming && match.prediction;
  const canOpen = onOpenMatch && match.match_id && !isTBD1 && !isTBD2;

  // Resolve team display info
  const team1Flag = match.team1_flag || (match.team1 ? getFlagEmoji(match.team1) : '');
  const team2Flag = match.team2_flag || (match.team2 ? getFlagEmoji(match.team2) : '');
  const team1Name = match.team1_name_zh || (isTBD1 ? '待定' : match.team1 || '待定');
  const team2Name = match.team2_name_zh || (isTBD2 ? '待定' : match.team2 || '待定');

  // Winner detection
  const team1Won = isFinished && match.winner === match.team1;
  const team2Won = isFinished && match.winner === match.team2;

  // Score display
  const scoreText = isFinished && match.score1 != null && match.score2 != null
    ? `${match.score1} - ${match.score2}`
    : null;

  const penText = isFinished &&
    match.score1_pen != null && match.score2_pen != null &&
    (match.score1_pen! > 0 || match.score2_pen! > 0)
    ? `(点球 ${match.score1_pen}-${match.score2_pen})`
    : null;

  // Prediction display
  const pred = match.prediction;
  const predScoreText = pred?.predicted_score || null;
  const homeWinPct = pred ? pred.home_win_prob : 0;
  const drawPct = pred ? pred.draw_prob : 0;
  const awayWinPct = pred ? pred.away_win_prob : 0;

  // Format date + kick_off
  const dateDisplay = match.kick_off
    ? formatKickOff(match.date, match.kick_off)
    : match.date;

  return (
    <div
      className={[
        'bracket-slot',
        isFinal ? 'bracket-final' : '',
        isThird ? 'bracket-third' : '',
        isFinished ? 'bracket-slot-finished' : '',
        isLive ? 'bracket-slot-live' : '',
        isUpcoming && !isTBD1 && !isTBD2 ? 'bracket-slot-upcoming' : '',
        (isTBD1 || isTBD2) ? 'bracket-slot-tbd' : '',
        canOpen ? 'bracket-slot-clickable' : '',
      ].filter(Boolean).join(' ')}
      onClick={() => canOpen && onOpenMatch?.(match.match_id)}
      style={{ cursor: canOpen ? 'pointer' : 'default' }}
      role={canOpen ? 'button' : undefined}
      tabIndex={canOpen ? 0 : undefined}
    >
      {/* Header: badge + label */}
      <div className="bracket-slot-header">
        {isFinal && <span className="bracket-slot-badge">🏆 决赛</span>}
        {isThird && <span className="bracket-slot-badge">🥉 三四名</span>}
        <span className="bracket-slot-label">{match.label}</span>
        {isLive && <span className="bracket-live-dot" />}
      </div>

      {/* Team rows */}
      <div className="bracket-slot-body">
        <TeamRow
          code={isTBD1 ? '' : (match.team1 || '')}
          flagEmoji={team1Flag}
          name={team1Name}
          isTBD={isTBD1}
          isWinner={team1Won}
          score={isFinished ? match.score1 : undefined}
          predScore={hasPrediction && predScoreText ? predScoreText.split('-')[0] : undefined}
        />
        <TeamRow
          code={isTBD2 ? '' : (match.team2 || '')}
          flagEmoji={team2Flag}
          name={team2Name}
          isTBD={isTBD2}
          isWinner={team2Won}
          score={isFinished ? match.score2 : undefined}
          predScore={hasPrediction && predScoreText ? predScoreText.split('-')[1] : undefined}
        />
      </div>

      {/* Penalty notation */}
      {penText && (
        <div className="bracket-pen-note">{penText}</div>
      )}

      {/* Prediction bar for upcoming matches */}
      {hasPrediction && (
        <div className="bracket-pred-bar">
          <div className="bracket-pred-bar-track">
            <div
              className="bracket-pred-bar-home"
              style={{ width: `${homeWinPct}%` }}
            />
            <div
              className="bracket-pred-bar-draw"
              style={{ width: `${drawPct}%` }}
            />
            <div
              className="bracket-pred-bar-away"
              style={{ width: `${awayWinPct}%` }}
            />
          </div>
          <div className="bracket-pred-labels">
            <span className="bracket-pred-label-home">{homeWinPct.toFixed(0)}%</span>
            <span className="bracket-pred-label-draw">{drawPct.toFixed(0)}%</span>
            <span className="bracket-pred-label-away">{awayWinPct.toFixed(0)}%</span>
          </div>
        </div>
      )}

      {/* Footer: date + status */}
      <div className="bracket-slot-footer">
        <span className="bracket-slot-date">{dateDisplay}</span>
        <span className={`bracket-slot-status status-${match.status}`}>
          {statusLabel(match.status)}
        </span>
      </div>
    </div>
  );
};

interface TeamRowProps {
  code: string;
  flagEmoji: string;
  name: string;
  isTBD: boolean;
  isWinner: boolean;
  score?: number | null;
  predScore?: string;
}

const TeamRow: React.FC<TeamRowProps> = ({ code, flagEmoji, name, isTBD, isWinner, score, predScore }) => {
  return (
    <div className={[
      'bracket-team-row',
      isWinner ? 'bracket-team-winner' : '',
      isTBD ? 'bracket-team-tbd' : '',
    ].filter(Boolean).join(' ')}>
      {code && !isTBD ? (
        <FlagImage code={code} emoji={flagEmoji} size={24} className="bracket-team-flag-img" />
      ) : (
        <span className="bracket-team-flag">{flagEmoji || '🏳️'}</span>
      )}
      <span className="bracket-team-name">{name}</span>
      <span className="bracket-team-score">
        {score != null ? score : (predScore != null ? predScore : '')}
      </span>
    </div>
  );
};

/** Format kick_off UTC string into a readable local date+time */
function formatKickOff(dateStr: string, kickOff: string): string {
  try {
    const d = new Date(kickOff);
    if (isNaN(d.getTime())) return dateStr;
    const month = d.getMonth() + 1;
    const day = d.getDate();
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return `${month}/${day} ${hours}:${mins}`;
  } catch {
    return dateStr;
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'finished': return '已完赛';
    case 'live': return '进行中';
    case 'upcoming': return '未开赛';
    case 'pending': return '待定';
    default: return status;
  }
}

export default Bracket;
