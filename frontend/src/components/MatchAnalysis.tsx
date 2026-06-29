import React, { useState } from 'react';
import { useMatchDetail, formatProb, useRecentMatches, getFlagEmoji } from '../hooks/useData';
import type { MatchDetail, PlayerData, H2HMatch, H2HStats, OddsEntry, RecentMatch } from '../hooks/useData';
import Formation from './Formation';

// 国旗图片URL映射
function getFlagUrl(code: string): string {
  const FLAG_MAP: Record<string, string> = {
    ARG: 'ar', BRA: 'br', FRA: 'fr', ENG: 'gb-eng', ESP: 'es',
    GER: 'de', POR: 'pt', NED: 'nl', ITA: 'it', BEL: 'be',
    URU: 'uy', CRO: 'hr', COL: 'co', MEX: 'mx', USA: 'us',
    MAR: 'ma', SEN: 'sn', JPN: 'jp', KOR: 'kr', IRN: 'ir',
    AUS: 'au', EGY: 'eg', GHA: 'gh', CIV: 'ci', SRB: 'rs',
    SUI: 'ch', DEN: 'dk', ECU: 'ec', POL: 'pl', CAN: 'ca',
    KSA: 'sa', QAT: 'qa', NGA: 'ng', CRC: 'cr', TUN: 'tn',
    CMR: 'cm', RSA: 'za', CHN: 'cn', UKR: 'ua', SWE: 'se',
    ALG: 'dz', AUT: 'at', BIH: 'ba', COD: 'cd', CPV: 'cv',
    CUW: 'cw', CZE: 'cz', HAI: 'ht', IRQ: 'iq', JOR: 'jo',
    NOR: 'no', NZL: 'nz', PAN: 'pa', PAR: 'py', SCO: 'gb-sct',
    TUR: 'tr', UZB: 'uz',
  };
  const iso = FLAG_MAP[code] || code.toLowerCase();
  // Fallback for historical opponents not in the 48-team mapping
  const FALLBACK_FLAGS: Record<string, string> = {
    RUS: 'ru', KSA: 'sa', PER: 'pe', VEN: 've', CHI: 'cl',
    HUN: 'hu', POL: 'pl', ISR: 'il', GRE: 'gr', ROU: 'ro',
    FIN: 'fi', ALB: 'al', IRL: 'ie', IDN: 'id', PLE: 'ps',
    BHR: 'bh', LBN: 'lb', GAB: 'ga', ZIM: 'zw', BLR: 'by',
    SVK: 'sk', SVN: 'si', WAL: 'gb-wls', NIR: 'gb-nir',
    MKD: 'mk', MNE: 'me', KOS: 'xk', LUX: 'lu',
  };
  const finalIso = FALLBACK_FLAGS[code] || iso;
  return `https://flagcdn.com/w160/${finalIso}.png`;
}

const FlagImage: React.FC<{ code: string; emoji: string; size?: number }> = ({ code, emoji, size = 64 }) => {
  const [imgError, setImgError] = useState(false);
  const boxH = Math.round(size * 0.66);
  return (
    <span className="flag-img-box" style={{ width: size, height: boxH }}>
      {imgError ? (
        <span style={{ fontSize: Math.round(size * 0.55), lineHeight: 1 }}>{emoji}</span>
      ) : (
        <img
          className="flag-img"
          src={getFlagUrl(code)}
          alt={`${code} flag`}
          style={{ width: size, height: boxH }}
          onError={() => setImgError(true)}
        />
      )}
    </span>
  );
};
interface Props {
  matchId: number;
}

type TabKey = 'prediction' | 'players' | 'h2h' | 'odds' | 'formation' | 'recent';

const MatchAnalysis: React.FC<Props> = ({ matchId }) => {
  const { data, loading, error } = useMatchDetail(matchId);
  const [activeTab, setActiveTab] = useState<TabKey>('prediction');

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>加载比赛数据...</p>
      </div>
    );
  }

  if (error) {
    return <div className="error-message">⚠️ {error}</div>;
  }

  if (!data) {
    return <div className="empty-message">未找到赛前数据</div>;
  }

  const m = data.match;
  const tabs: { key: TabKey; label: string }[] = [
    { key: 'prediction', label: '赛前预测' },
    { key: 'players', label: '球员信息' },
    { key: 'h2h', label: '历史交锋' },
    { key: 'odds', label: '赔率数据' },
    { key: 'formation', label: '阵型' },
    { key: 'recent', label: '近10场' },
  ];

  return (
    <div className="match-analysis">
      {/* Match header - 国旗在队名上方 */}
      <div className="analysis-header">
        <div className="analysis-team team-a">
          <FlagImage code={m.team1} emoji={m.team1_flag} size={72} />
          <span className="analysis-name-zh">{m.team1_zh}</span>
          <span className="analysis-name-en">{m.team1_name}</span>
        </div>
        <div className="analysis-vs">
          <span className="analysis-vs-text">VS</span>
          <span className="analysis-group">{m.group_name}组 · {m.round}</span>
        </div>
        <div className="analysis-team team-b">
          <FlagImage code={m.team2} emoji={m.team2_flag} size={72} />
          <span className="analysis-name-zh">{m.team2_zh}</span>
          <span className="analysis-name-en">{m.team2_name}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="analysis-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`analysis-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="analysis-content">
        {activeTab === 'prediction' && <PredictionTab data={data} />}
        {activeTab === 'players' && <PlayersTab data={data} />}
        {activeTab === 'h2h' && <H2HTab data={data} />}
        {activeTab === 'odds' && <OddsTab data={data} />}
        {activeTab === 'formation' && <FormationTab data={data} />}
        {activeTab === 'recent' && <RecentMatchesTab team1Code={m.team1} team1Name={m.team1_zh} team2Code={m.team2} team2Name={m.team2_zh} />}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// Prediction Tab
// ─────────────────────────────────────────────

const PredictionTab: React.FC<{ data: MatchDetail }> = ({ data }) => {
  const pred = data.prediction;
  if (!pred || (pred as any).error) {
    return <div className="empty-message-sm">暂无预测数据</div>;
  }

  const factors = (pred as any).factors;
  const advice = (pred as any).advice;

  return (
    <div className="tab-prediction">
      {/* Advice banner */}
      {advice && (
        <div className="prediction-advice">
          <span className="advice-icon">💡</span>
          <span className="advice-text">{advice}</span>
        </div>
      )}

      <h3 className="tab-section-title">综合概率预测</h3>
      <div className="prediction-bars-large">
        <div className="pred-bar-group">
          <div className="pred-bar-label">{data.match.team1_zh} 胜</div>
          <div className="pred-bar-wrapper">
            <div className="pred-bar pred-bar-home" style={{ width: `${pred.home_win_prob}%` }} />
          </div>
          <span className="pred-bar-value">{formatProb(pred.home_win_prob)}</span>
        </div>
        <div className="pred-bar-group">
          <div className="pred-bar-label">平局</div>
          <div className="pred-bar-wrapper">
            <div className="pred-bar pred-bar-draw" style={{ width: `${pred.draw_prob}%` }} />
          </div>
          <span className="pred-bar-value">{formatProb(pred.draw_prob)}</span>
        </div>
        <div className="pred-bar-group">
          <div className="pred-bar-label">{data.match.team2_zh} 胜</div>
          <div className="pred-bar-wrapper">
            <div className="pred-bar pred-bar-away" style={{ width: `${pred.away_win_prob}%` }} />
          </div>
          <span className="pred-bar-value">{formatProb(pred.away_win_prob)}</span>
        </div>
      </div>

      {/* Total Goals Prediction */}
      {(() => {
        const lam = pred.expected_goals_home + pred.expected_goals_away;
        const fact = (n: number) => n <= 1 ? 1 : n === 2 ? 2 : n === 3 ? 6 : n === 4 ? 24 : n === 5 ? 120 : 720;
        const poisson = (g: number) => Math.exp(-lam) * Math.pow(lam, g) / fact(g);
        // Over lines: P(goals > line)
        const over = (line: number) => {
          let sum = 0;
          for (let g = Math.floor(line) + 1; g <= 15; g++) sum += poisson(g);
          return sum;
        };
        return (
        <div className="total-goals-section">
          <h3 className="tab-section-title">
            总进球预测
            <span className="tg-subtitle">（基于Poisson模型 · 博彩大小球赔率暂缺）</span>
          </h3>
          <div className="total-goals-card">
            <div className="tg-row">
              <span className="tg-label">预期总进球</span>
              <span className="tg-value">{lam.toFixed(2)}</span>
            </div>

            {/* Exact goal distribution with odds */}
            <div className="tg-table-title">每个总进球数概率及隐含赔率</div>
            <div className="tg-grid">
              {[0,1,2,3,4,5,6].map(g => {
                const p = poisson(g);
                const odd = p > 0.001 ? (1 / p).toFixed(2) : '—';
                return (
                  <div key={g} className="tg-cell">
                    <span className="tg-cell-num">{g}<span className="tg-cell-unit">球</span></span>
                    <span className="tg-cell-bar-bg">
                      <span className="tg-cell-bar" style={{ height: `${Math.max(3, p * 100)}%` }} />
                    </span>
                    <span className="tg-cell-prob">{(p * 100).toFixed(1)}%</span>
                    <span className="tg-cell-odds">@{odd}</span>
                  </div>
                );
              })}
              <div className="tg-cell">
                <span className="tg-cell-num">7+<span className="tg-cell-unit">球</span></span>
                <span className="tg-cell-bar-bg">
                  <span className="tg-cell-bar" style={{ height: `${Math.max(3, (1 - [0,1,2,3,4,5,6].reduce((s,g) => s + poisson(g), 0)) * 100)}%` }} />
                </span>
                <span className="tg-cell-prob">{((1 - [0,1,2,3,4,5,6].reduce((s,g) => s + poisson(g), 0)) * 100).toFixed(1)}%</span>
                <span className="tg-cell-odds">@—</span>
              </div>
            </div>

            {/* Over/Under lines */}
            <div className="tg-table-title" style={{ marginTop: 16 }}>大小球盘口 (模型隐含)</div>
            <div className="tg-ou-grid">
              {[0.5, 1.5, 2.5, 3.5, 4.5].map(line => {
                const overProb = over(line);
                const underProb = 1 - overProb;
                return (
                  <div key={line} className="tg-ou-cell">
                    <span className="tg-ou-line">
                      {line % 1 === 0 ? `${line}.0` : `${line}`}
                    </span>
                    <div className="tg-ou-rows">
                      <span className="tg-ou-row">
                        <span className="tg-ou-label">大</span>
                        <span className="tg-ou-val">{(overProb * 100).toFixed(0)}%</span>
                        <span className="tg-ou-odd">
                          {overProb > 0.01 ? `@${(1 / overProb).toFixed(2)}` : '@—'}
                        </span>
                      </span>
                      <span className="tg-ou-row">
                        <span className="tg-ou-label" style={{color:'#f59e0b'}}>小</span>
                        <span className="tg-ou-val">{(underProb * 100).toFixed(0)}%</span>
                        <span className="tg-ou-odd">
                          {underProb > 0.01 ? `@${(1 / underProb).toFixed(2)}` : '@—'}
                        </span>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="tg-note">
              * 最可能比分({pred.top_5_scorelines?.[0]?.score || '-'})的总进球为 <strong>{parseInt(pred.top_5_scorelines?.[0]?.score?.split('-')[0] || '0') + parseInt(pred.top_5_scorelines?.[0]?.score?.split('-')[1] || '0')}</strong> 球，
              但概率分布上预期总进球为 <strong>{lam.toFixed(2)}</strong> 球。
              二者不一致时，预期总进球更可靠（考虑了所有比分可能性的加权平均）。
            </div>
          </div>
        </div>
        );
      })()}

      {/* Confidence badge */}
      <div className="confidence-badge">
        置信度：
        <span className={`confidence-${pred.confidence_level}`}>
          {pred.confidence_level === 'high' ? '高' : pred.confidence_level === 'medium' ? '中' : '低'}
        </span>
        {pred.elo_diff !== undefined && (
          <span className="elo-diff">ELO差值: {pred.elo_diff > 0 ? '+' : ''}{pred.elo_diff}</span>
        )}
      </div>

      <div className="predicted-score-display">
        <span className="score-label">最可能比分</span>
        <span className="score-value">{pred.top_5_scorelines?.[0]?.score || Math.round(pred.expected_goals_home) + '-' + Math.round(pred.expected_goals_away)}</span>
      </div>

      {/* Factor breakdown */}
      {factors && (
        <div className="factors-breakdown">
          <h3 className="tab-section-title">多因素分析</h3>
          <div className="factors-grid">
            {/* ELO Model */}
            <div className="factor-card">
              <div className="factor-header">
                <span className="factor-name">ELO模型</span>
                <span className="factor-weight">权重 {(factors.elo_model?.weight * 100).toFixed(0)}%</span>
              </div>
              <div className="factor-probs">
                <div className="factor-prob">
                  <span>主胜</span>
                  <span className="factor-prob-val">{factors.elo_model?.home_win?.toFixed(1)}%</span>
                </div>
                <div className="factor-prob">
                  <span>平局</span>
                  <span className="factor-prob-val">{factors.elo_model?.draw?.toFixed(1)}%</span>
                </div>
                <div className="factor-prob">
                  <span>客胜</span>
                  <span className="factor-prob-val">{factors.elo_model?.away_win?.toFixed(1)}%</span>
                </div>
              </div>
              <div className="factor-detail">
                预期进球: {factors.elo_model?.expected_goals_home?.toFixed(2)} - {factors.elo_model?.expected_goals_away?.toFixed(2)}
              </div>
            </div>

            {/* Odds Analysis */}
            <div className="factor-card">
              <div className="factor-header">
                <span className="factor-name">赔率分析</span>
                <span className="factor-weight">权重 {(factors.odds_analysis?.weight * 100).toFixed(0)}%</span>
              </div>
              {factors.odds_analysis?.available ? (
                <>
                  <div className="factor-probs">
                    <div className="factor-prob">
                      <span>主胜</span>
                      <span className="factor-prob-val">{factors.odds_analysis?.home_win?.toFixed(1)}%</span>
                    </div>
                    <div className="factor-prob">
                      <span>平局</span>
                      <span className="factor-prob-val">{factors.odds_analysis?.draw?.toFixed(1)}%</span>
                    </div>
                    <div className="factor-prob">
                      <span>客胜</span>
                      <span className="factor-prob-val">{factors.odds_analysis?.away_win?.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="factor-detail">
                    {factors.odds_analysis?.num_bookmakers}家机构 · 一致性{factors.odds_analysis?.consensus === 'strong' ? '强' : factors.odds_analysis?.consensus === 'moderate' ? '中' : '弱'}
                  </div>
                </>
              ) : (
                <div className="factor-detail">赔率数据暂未更新</div>
              )}
            </div>

            {/* Squad Analysis */}
            <div className="factor-card">
              <div className="factor-header">
                <span className="factor-name">阵容分析</span>
                <span className="factor-weight">权重 {(factors.squad_analysis?.weight * 100).toFixed(0)}%</span>
              </div>
              {factors.squad_analysis?.available ? (
                <div className="squad-comparison">
                  <div className="squad-team">
                    <span className="squad-team-name">{data.match.team1_zh}</span>
                    <div className="squad-bars">
                      <div className="squad-bar-row">
                        <span>进攻</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill attack" style={{ width: `${factors.squad_analysis.team1.attack * 100}%` }} /></div>
                      </div>
                      <div className="squad-bar-row">
                        <span>中场</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill midfield" style={{ width: `${factors.squad_analysis.team1.midfield * 100}%` }} /></div>
                      </div>
                      <div className="squad-bar-row">
                        <span>防守</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill defense" style={{ width: `${factors.squad_analysis.team1.defense * 100}%` }} /></div>
                      </div>
                    </div>
                    <span className="squad-overall">综合 {factors.squad_analysis.team1.overall.toFixed(2)}</span>
                  </div>
                  <div className="squad-team">
                    <span className="squad-team-name">{data.match.team2_zh}</span>
                    <div className="squad-bars">
                      <div className="squad-bar-row">
                        <span>进攻</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill attack" style={{ width: `${factors.squad_analysis.team2.attack * 100}%` }} /></div>
                      </div>
                      <div className="squad-bar-row">
                        <span>中场</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill midfield" style={{ width: `${factors.squad_analysis.team2.midfield * 100}%` }} /></div>
                      </div>
                      <div className="squad-bar-row">
                        <span>防守</span>
                        <div className="squad-bar-bg"><div className="squad-bar-fill defense" style={{ width: `${factors.squad_analysis.team2.defense * 100}%` }} /></div>
                      </div>
                    </div>
                    <span className="squad-overall">综合 {factors.squad_analysis.team2.overall.toFixed(2)}</span>
                  </div>
                </div>
              ) : (
                <div className="factor-detail">阵容数据暂未更新</div>
              )}
            </div>

            {/* Form Analysis */}
            <div className="factor-card">
              <div className="factor-header">
                <span className="factor-name">状态分析</span>
                <span className="factor-weight">权重 {(factors.form_analysis?.weight * 100).toFixed(0)}%</span>
              </div>
              {factors.form_analysis?.team1?.available && factors.form_analysis?.team2?.available ? (
                <div className="form-comparison">
                  <div className="form-team">
                    <span className="form-team-name">{data.match.team1_zh}</span>
                    <div className="form-string">{factors.form_analysis.team1.form_string || '-'}</div>
                    <div className="form-stats-row">
                      <span>胜率 {((factors.form_analysis.team1.win_rate || 0) * 100).toFixed(0)}%</span>
                      <span>场均进 {(factors.form_analysis.team1.avg_goals_for || 0).toFixed(1)}</span>
                      <span>场均失 {(factors.form_analysis.team1.avg_goals_against || 0).toFixed(1)}</span>
                    </div>
                    <span className={`momentum-badge momentum-${factors.form_analysis.team1.momentum}`}>
                      {factors.form_analysis.team1.momentum === 'hot' ? '火热' :
                       factors.form_analysis.team1.momentum === 'good' ? '良好' :
                       factors.form_analysis.team1.momentum === 'neutral' ? '一般' : '低迷'}
                    </span>
                  </div>
                  <div className="form-team">
                    <span className="form-team-name">{data.match.team2_zh}</span>
                    <div className="form-string">{factors.form_analysis.team2.form_string || '-'}</div>
                    <div className="form-stats-row">
                      <span>胜率 {((factors.form_analysis.team2.win_rate || 0) * 100).toFixed(0)}%</span>
                      <span>场均进 {(factors.form_analysis.team2.avg_goals_for || 0).toFixed(1)}</span>
                      <span>场均失 {(factors.form_analysis.team2.avg_goals_against || 0).toFixed(1)}</span>
                    </div>
                    <span className={`momentum-badge momentum-${factors.form_analysis.team2.momentum}`}>
                      {factors.form_analysis.team2.momentum === 'hot' ? '火热' :
                       factors.form_analysis.team2.momentum === 'good' ? '良好' :
                       factors.form_analysis.team2.momentum === 'neutral' ? '一般' : '低迷'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="factor-detail">近期战绩数据暂未更新（世界杯开赛后自动获取）</div>
              )}
            </div>
          </div>
        </div>
      )}

      {pred.top_5_scorelines && pred.top_5_scorelines.length > 0 && (
        <div className="scorelines-section">
          <h3 className="tab-section-title">TOP 5 比分概率</h3>
          <div className="scorelines-list">
            {pred.top_5_scorelines.map((sl, i) => {
              const impliedOdds = sl.probability > 0 ? (100 / sl.probability).toFixed(2) : '—';
              return (
                <div key={i} className="scoreline-item">
                  <span className="scoreline-rank">#{i + 1}</span>
                  <span className="scoreline-score">{sl.score}</span>
                  <span className="scoreline-prob">{formatProb(sl.probability)}</span>
                  <span className="scoreline-odds">赔率 {impliedOdds}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// Players Tab - REAL DATA
// ─────────────────────────────────────────────

const PlayersTab: React.FC<{ data: MatchDetail }> = ({ data }) => {
  const { players } = data;
  const hasPlayers1 = players.team1 && players.team1.length > 0;
  const hasPlayers2 = players.team2 && players.team2.length > 0;

  return (
    <div className="tab-players">
      <div className="players-columns">
        {/* Team 1 players */}
        <div className="players-column">
          <h3 className="players-team-title">
            <FlagImage code={data.match.team1} emoji={data.match.team1_flag} size={32} />
            {data.match.team1_zh}
          </h3>
          {hasPlayers1 ? (
            <div className="players-grid">
              {players.team1.map((p, i) => (
                <PlayerCard key={i} player={p} />
              ))}
            </div>
          ) : (
            <div className="empty-message-sm">暂无{data.match.team1_zh}球员数据</div>
          )}
        </div>

        {/* Team 2 players */}
        <div className="players-column">
          <h3 className="players-team-title">
            <FlagImage code={data.match.team2} emoji={data.match.team2_flag} size={32} />
            {data.match.team2_zh}
          </h3>
          {hasPlayers2 ? (
            <div className="players-grid">
              {players.team2.map((p, i) => (
                <PlayerCard key={i} player={p} />
              ))}
            </div>
          ) : (
            <div className="empty-message-sm">暂无{data.match.team2_zh}球员数据</div>
          )}
        </div>
      </div>
    </div>
  );
};

const PlayerCard: React.FC<{ player: PlayerData }> = ({ player }) => {
  // Generate initials for avatar
  const initials = player.name_zh ? player.name_zh.slice(0, 1) : player.name.slice(0, 1);

  return (
    <div className="player-card">
      <div className="player-avatar">{initials}</div>
      <div className="player-info">
        <div className="player-number">#{player.number}</div>
        <div className="player-name-zh">{player.name_zh}</div>
        <div className="player-name-en">{player.name}</div>
        <div className="player-position">{player.position_zh || player.position}</div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// H2H Tab - REAL DATA
// ─────────────────────────────────────────────

const H2HTab: React.FC<{ data: MatchDetail }> = ({ data }) => {
  const { h2h } = data;
  const hasData = h2h && h2h.matches && h2h.matches.length > 0;
  const stats: H2HStats = h2h?.stats || { total: 0, home_wins: 0, draws: 0, away_wins: 0 };

  if (!hasData) {
    return (
      <div className="tab-h2h-empty">
        <div className="h2h-empty-icon">🤝</div>
        <p className="h2h-empty-text">两队历史上暂无交锋记录</p>
        <p className="h2h-empty-sub">2026年世界杯将是两队首次在世界杯赛场上相遇</p>
      </div>
    );
  }

  return (
    <div className="tab-h2h">
      {/* Stats summary */}
      <div className="h2h-stats">
        <h3 className="tab-section-title">交锋统计</h3>
        <div className="h2h-stats-grid">
          <div className="h2h-stat-card">
            <span className="h2h-stat-value">{stats.total}</span>
            <span className="h2h-stat-label">总场次</span>
          </div>
          <div className="h2h-stat-card">
            <span className="h2h-stat-value">{stats.home_wins}</span>
            <span className="h2h-stat-label">{data.match.team1_zh}胜</span>
          </div>
          <div className="h2h-stat-card">
            <span className="h2h-stat-value">{stats.draws}</span>
            <span className="h2h-stat-label">平局</span>
          </div>
          <div className="h2h-stat-card">
            <span className="h2h-stat-value">{stats.away_wins}</span>
            <span className="h2h-stat-label">{data.match.team2_zh}胜</span>
          </div>
        </div>
      </div>

      {/* Match history */}
      <div className="h2h-matches">
        <h3 className="tab-section-title">历史交锋记录</h3>
        <div className="h2h-matches-list">
          {h2h.matches.map((m, i) => (
            <H2HMatchCard key={i} match={m} />
          ))}
        </div>
      </div>
    </div>
  );
};

const H2HMatchCard: React.FC<{ match: H2HMatch }> = ({ match }) => {
  return (
    <div className="h2h-match-card">
      <div className="h2h-match-header">
        <span className="h2h-match-year">{match.year}</span>
        <span className="h2h-match-round">{match.round}</span>
      </div>
      <div className="h2h-match-score">
        <span className="h2h-team">{match.team1}</span>
        <span className="h2h-score">{match.score1} - {match.score2}</span>
        <span className="h2h-team">{match.team2}</span>
      </div>
      {match.date && <div className="h2h-match-date">{match.date}</div>}
    </div>
  );
};

// ─────────────────────────────────────────────
// Odds Tab
// ─────────────────────────────────────────────

const OddsTab: React.FC<{ data: MatchDetail }> = ({ data }) => {
  const { odds, prediction } = data;
  const hasOdds = odds && odds.bookmakers && odds.bookmakers.length > 0;

  // Extract odds analysis from prediction factors
  const oddsAnalysis = (prediction as any)?.factors?.odds_analysis;
  const handicapInfo = oddsAnalysis?.handicap;
  const overUnderInfo = oddsAnalysis?.over_under;
  const csConsensus = oddsAnalysis?.correct_score_consensus;

  if (!hasOdds && !oddsAnalysis?.available) {
    return <div className="empty-message-sm">赔率数据暂未更新</div>;
  }

  return (
    <div className="tab-odds">
      <h3 className="tab-section-title">赔率数据</h3>

      {/* 1X2 Odds Table */}
      {hasOdds && (
        <div className="odds-section">
          <h4 className="odds-sub-title">胜平负 (1X2)</h4>
          <div className="odds-table-wrapper">
            <table className="odds-table">
              <thead>
                <tr>
                  <th>机构</th>
                  <th>主胜</th>
                  <th>平局</th>
                  <th>客胜</th>
                </tr>
              </thead>
              <tbody>
                {odds.bookmakers.map((bm, i) => (
                  <tr key={i}>
                    <td className="odds-bookmaker">{bm.bookmaker}</td>
                    <td className="odds-value odds-home">{bm.home?.toFixed(2) || '—'}</td>
                    <td className="odds-value odds-draw">{bm.draw?.toFixed(2) || '—'}</td>
                    <td className="odds-value odds-away">{bm.away?.toFixed(2) || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Handicap & Over/Under */}
      {(handicapInfo || overUnderInfo) && (
        <div className="odds-section" style={{ marginTop: 16 }}>
          <h4 className="odds-sub-title">盘口 & 大小球</h4>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {handicapInfo && (
              <div className="odds-market-card">
                <div className="odds-market-label">亚盘 (让球)</div>
                <div className="odds-market-value">
                  {handicapInfo.line > 0 ? '+' : ''}{handicapInfo.line}
                </div>
                <div className="odds-market-sources">
                  {handicapInfo.num_sources}家机构
                </div>
              </div>
            )}
            {overUnderInfo && (
              <div className="odds-market-card">
                <div className="odds-market-label">大小球</div>
                <div className="odds-market-value">
                  {overUnderInfo.line}
                </div>
                <div className="odds-market-sources">
                  {overUnderInfo.num_sources}家机构
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Correct Score Odds */}
      {csConsensus?.available && csConsensus.top_scorelines?.length > 0 && (
        <div className="odds-section" style={{ marginTop: 16 }}>
          <h4 className="odds-sub-title">比分赔率 (市场共识)</h4>
          <div className="odds-table-wrapper">
            <table className="odds-table">
              <thead>
                <tr>
                  <th>比分</th>
                  <th>概率</th>
                  <th>赔率</th>
                  <th>数据源</th>
                </tr>
              </thead>
              <tbody>
                {csConsensus.top_scorelines.slice(0, 8).map((cs: any, i: number) => {
                  const impliedOdds = cs.probability > 0 ? (1 / cs.probability).toFixed(2) : '—';
                  return (
                    <tr key={i}>
                      <td className="odds-bookmaker" style={{ fontWeight: 600 }}>{cs.score}</td>
                      <td className="odds-value">{(cs.probability * 100).toFixed(1)}%</td>
                      <td className="odds-value" style={{ color: '#4fc3f7', fontWeight: 600 }}>{impliedOdds}</td>
                      <td className="odds-value" style={{ color: '#888' }}>{cs.num_sources}家</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Market consensus info */}
      {oddsAnalysis?.available && (
        <div className="odds-section" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13, color: '#aaa' }}>
            <span>市场共识: {oddsAnalysis.consensus === 'strong' ? '强' : oddsAnalysis.consensus === 'moderate' ? '中' : '弱'}</span>
            <span>数据源: {oddsAnalysis.num_bookmakers}家机构</span>
            <span>赔率权重: {(oddsAnalysis.weight * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────
// Formation Tab
// ─────────────────────────────────────────────

const FormationTab: React.FC<{ data: MatchDetail }> = ({ data }) => {
  const m = data.match;
  return (
    <div className="tab-formation">
      <Formation
        team1Code={m.team1}
        team1NameZh={m.team1_zh}
        team1Formation={m.team1_formation || '4-3-3'}
        team1Players={data.players.team1 || []}
        team1Flag={m.team1_flag}
        team2Code={m.team2}
        team2NameZh={m.team2_zh}
        team2Formation={m.team2_formation || '4-3-3'}
        team2Players={data.players.team2 || []}
        team2Flag={m.team2_flag}
      />
    </div>
  );
};

// ─────────────────────────────────────────────
// Recent Matches Tab
// ─────────────────────────────────────────────

const RecentMatchesTab: React.FC<{ team1Code: string; team1Name: string; team2Code: string; team2Name: string }> = ({ team1Code, team1Name, team2Code, team2Name }) => {
  const { data: matches1, loading: l1, error: e1 } = useRecentMatches(team1Code);
  const { data: matches2, loading: l2, error: e2 } = useRecentMatches(team2Code);

  if (l1 || l2) return <div className="loading-container"><div className="loading-spinner" /><p>加载近期战绩...</p></div>;

  return (
    <div className="tab-recent">
      <div className="recent-columns">
        <div className="recent-column">
          <h3 className="tab-section-title">{team1Name} 近10场</h3>
          {matches1 && matches1.length > 0 ? (
            <div className="recent-matches-list">
              {matches1.map((m, i) => <RecentMatchCard key={i} match={m} />)}
            </div>
          ) : (
            <div className="empty-message-sm">近期战绩数据暂未更新</div>
          )}
        </div>
        <div className="recent-column">
          <h3 className="tab-section-title">{team2Name} 近10场</h3>
          {matches2 && matches2.length > 0 ? (
            <div className="recent-matches-list">
              {matches2.map((m, i) => <RecentMatchCard key={i} match={m} />)}
            </div>
          ) : (
            <div className="empty-message-sm">近期战绩数据暂未更新</div>
          )}
        </div>
      </div>
    </div>
  );
};

const RecentMatchCard: React.FC<{ match: RecentMatch }> = ({ match }) => {
  const resultClass = match.result === 'W' ? 'result-w' : match.result === 'D' ? 'result-d' : 'result-l';
  const resultLabel = match.result === 'W' ? '胜' : match.result === 'D' ? '平' : '负';

  return (
    <div className="recent-match-card">
      <span className={`recent-result ${resultClass}`}>{resultLabel}</span>
      <div className="recent-match-info">
        <span className="recent-opponent">
          {match.is_home ? '主' : '客'} vs{' '}
          <FlagImage code={match.opponent_code} emoji={getFlagEmoji(match.opponent_code)} size={20} />
          {' '}
          <span className="recent-opponent-name">{match.opponent_name_zh || match.opponent_name}</span>
        </span>
        <span className="recent-score">
          {match.goals_for} - {match.goals_against}
        </span>
      </div>
      <span className="recent-league">{match.league}</span>
      <span className="recent-date">{match.date}</span>
    </div>
  );
};

export default MatchAnalysis;