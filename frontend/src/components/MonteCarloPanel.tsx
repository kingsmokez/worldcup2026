import React, { useState } from 'react';
import { formatProb, getFlagEmoji } from '../hooks/useData';
import type { MonteCarloResult } from '../hooks/useData';

interface MonteCarloProps {
  data: MonteCarloResult | null;
  loading: boolean;
  error: string | null;
  runSimulation: (numSims: number) => void;
}

const MonteCarloPanel: React.FC<MonteCarloProps> = ({ data, loading, error, runSimulation }) => {
  const [numSims, setNumSims] = useState(5000);

  return (
    <div className="monte-carlo-page">
      <h2 className="section-title">
        <span className="title-icon">🎯</span>
        蒙特卡洛锦标赛模拟
      </h2>
      <p className="section-subtitle">
        通过模拟整个世界杯赛程 {numSims} 次，计算每支球队的夺冠概率
      </p>

      <div className="mc-controls">
        <div className="mc-sim-selector">
          <label>模拟次数</label>
          <select value={numSims} onChange={(e) => setNumSims(parseInt(e.target.value))} className="mc-select">
            <option value={1000}>1,000 次（快速）</option>
            <option value={5000}>5,000 次（推荐）</option>
            <option value={10000}>10,000 次（精确）</option>
            <option value={50000}>50,000 次（高精度）</option>
          </select>
        </div>
        <button
          className="mc-run-btn"
          onClick={() => runSimulation(numSims)}
          disabled={loading}
        >
          {loading ? '模拟中...' : '开始模拟'}
        </button>
      </div>

      {loading && (
        <div className="mc-loading">
          <div className="loading-spinner" />
          <p>正在模拟 {numSims.toLocaleString()} 次世界杯赛程...</p>
          <p className="mc-loading-hint">模拟在后台运行，你可以切换到其他页面查看</p>
        </div>
      )}

      {error && <div className="error-message">⚠️ {error}</div>}

      {data && !loading && (
        <div className="mc-results">
          <div className="mc-summary">
            <div className="mc-summary-card">
              <span className="mc-summary-value">{data.num_simulations.toLocaleString()}</span>
              <span className="mc-summary-label">模拟次数</span>
            </div>
            {data.most_likely_champion && (
              <div className="mc-summary-card mc-highlight">
                <span className="mc-summary-flag">{getFlagEmoji(data.most_likely_champion.team)}</span>
                <span className="mc-summary-value">{(data.most_likely_champion.probability * 100).toFixed(1)}%</span>
                <span className="mc-summary-label">最可能冠军</span>
              </div>
            )}
            {data.most_likely_final && (
              <div className="mc-summary-card">
                <span className="mc-summary-value">
                  {getFlagEmoji(data.most_likely_final.team1)} vs {getFlagEmoji(data.most_likely_final.team2)}
                </span>
                <span className="mc-summary-label">最可能决赛 {(data.most_likely_final.probability * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>

          <h3 className="tab-section-title">TOP 10 夺冠概率</h3>
          <div className="mc-top10">
            {data.top_10_champions.map((team, i) => (
              <div key={team.code} className="mc-team-row">
                <span className="mc-rank">#{i + 1}</span>
                <span className="mc-flag">{getFlagEmoji(team.code)}</span>
                <span className="mc-team-name-zh">{team.name_zh}</span>
                <span className="mc-team-name-en">{team.name}</span>
                <div className="mc-prob-bar-wrapper">
                  <div className="mc-prob-bar" style={{ width: `${team.probability * 100}%` }} />
                </div>
                <span className="mc-prob-value">{(team.probability * 100).toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MonteCarloPanel;
