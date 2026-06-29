import React, { useState } from 'react';
import { formatProb } from '../hooks/useData';

interface PredictionResult {
  team1: { code: string; name: string; name_zh: string; flag: string };
  team2: { code: string; name: string; name_zh: string; flag: string };
  prediction: {
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    expected_goals_home: number;
    expected_goals_away: number;
    top_5_scorelines: { score: string; probability: number }[];
    confidence_level: string;
  };
}

const Predictions: React.FC = () => {
  const [team1, setTeam1] = useState('');
  const [team2, setTeam2] = useState('');
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePredict = async () => {
    if (!team1.trim() || !team2.trim()) {
      setError('请输入两支球队代码');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/predict?team1=${team1.toUpperCase()}&team2=${team2.toUpperCase()}`);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || '预测失败');
      }
      const data: PredictionResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError(e.message || '预测请求失败');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="predictions-page">
      <h2 className="section-title">
        <span className="title-icon">🔮</span>
        任意两队预测
      </h2>

      <div className="predict-form">
        <div className="predict-inputs">
          <div className="predict-input-group">
            <label>球队1代码</label>
            <input
              type="text"
              placeholder="如 ARG"
              value={team1}
              onChange={(e) => setTeam1(e.target.value.toUpperCase())}
              maxLength={3}
              className="predict-input"
            />
          </div>
          <div className="predict-vs-big">⚔️</div>
          <div className="predict-input-group">
            <label>球队2代码</label>
            <input
              type="text"
              placeholder="如 FRA"
              value={team2}
              onChange={(e) => setTeam2(e.target.value.toUpperCase())}
              maxLength={3}
              className="predict-input"
            />
          </div>
        </div>
        <button className="predict-btn" onClick={handlePredict} disabled={loading}>
          {loading ? '预测中...' : '开始预测'}
        </button>
      </div>

      {error && <div className="predict-error">⚠️ {error}</div>}

      {result && (
        <div className="predict-result">
          <div className="predict-result-teams">
            <div className="predict-result-team">
              <span className="predict-result-flag">{result.team1.flag}</span>
              <span className="predict-result-zh">{result.team1.name_zh}</span>
              <span className="predict-result-en">{result.team1.name}</span>
            </div>
            <div className="predict-result-vs">VS</div>
            <div className="predict-result-team">
              <span className="predict-result-flag">{result.team2.flag}</span>
              <span className="predict-result-zh">{result.team2.name_zh}</span>
              <span className="predict-result-en">{result.team2.name}</span>
            </div>
          </div>

          <div className="predict-result-score">
            预测比分: <strong>{result.prediction.top_5_scorelines?.[0]?.score || Math.round(result.prediction.expected_goals_home) + '-' + Math.round(result.prediction.expected_goals_away)}</strong>
          </div>

          <div className="prediction-bars-large">
            <div className="pred-bar-group">
              <div className="pred-bar-label">{result.team1.name_zh} 胜</div>
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-home" style={{ width: `${result.prediction.home_win_prob}%` }} />
              </div>
              <span className="pred-bar-value">{formatProb(result.prediction.home_win_prob)}</span>
            </div>
            <div className="pred-bar-group">
              <div className="pred-bar-label">平局</div>
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-draw" style={{ width: `${result.prediction.draw_prob}%` }} />
              </div>
              <span className="pred-bar-value">{formatProb(result.prediction.draw_prob)}</span>
            </div>
            <div className="pred-bar-group">
              <div className="pred-bar-label">{result.team2.name_zh} 胜</div>
              <div className="pred-bar-wrapper">
                <div className="pred-bar pred-bar-away" style={{ width: `${result.prediction.away_win_prob}%` }} />
              </div>
              <span className="pred-bar-value">{formatProb(result.prediction.away_win_prob)}</span>
            </div>
          </div>

          {/* Total Goals Prediction */}
          {result.prediction.expected_goals_home != null && (() => {
            const lam = result.prediction.expected_goals_home + result.prediction.expected_goals_away;
            const fact = (n: number) => n <= 1 ? 1 : n === 2 ? 2 : n === 3 ? 6 : n === 4 ? 24 : n === 5 ? 120 : 720;
            const poisson = (g: number) => Math.exp(-lam) * Math.pow(lam, g) / fact(g);
            return (
            <div className="total-goals-section">
              <h3 className="tab-section-title">总进球分布与隐含赔率</h3>
              <div className="total-goals-card">
                <div className="tg-row">
                  <span className="tg-label">预期总进球</span>
                  <span className="tg-value">{lam.toFixed(2)}</span>
                </div>
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
              </div>
            </div>
            );
          })()}

          {result.prediction.top_5_scorelines && (
            <div className="scorelines-section">
              <h3 className="tab-section-title">TOP 5 比分概率</h3>
              <div className="scorelines-list">
                {result.prediction.top_5_scorelines.map((sl, i) => {
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
      )}
    </div>
  );
};

export default Predictions;