import React, { useState, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import GroupStandings from './components/GroupStandings';
import Bracket from './components/Bracket';
import MatchAnalysis from './components/MatchAnalysis';
import Predictions from './components/Predictions';
import MonteCarloPanel from './components/MonteCarloPanel';
import SystemStatusBar from './components/SystemStatusBar';
import ParticleBg from './components/ParticleBg';
import { useMonteCarlo } from './hooks/useData';
import type { MonteCarloResult } from './hooks/useData';

type TabId = 'dashboard' | 'standings' | 'bracket' | 'analysis' | 'predictions' | 'montecarlo';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const [analysisMatchId, setAnalysisMatchId] = useState<number | null>(null);

  // Lift Monte Carlo state to App level so it persists across tab switches
  const mc = useMonteCarlo();

  const handleOpenMatch = useCallback((matchId: number) => {
    setAnalysisMatchId(matchId);
    setActiveTab('analysis');
  }, []);

  const tabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'dashboard', label: '赛程总览', icon: '⚽' },
    { id: 'standings', label: '积分榜', icon: '📊' },
    { id: 'bracket', label: '淘汰赛', icon: '🏆' },
    { id: 'analysis', label: '赛前分析', icon: '🔍' },
    { id: 'predictions', label: '预测', icon: '🔮' },
    { id: 'montecarlo', label: '夺冠概率', icon: '🎯' },
  ];

  return (
    <div className="app">
      <ParticleBg />

      {/* Premium Header */}
      <header className="app-header">
        <div className="header-backdrop" />
        <div className="header-content">
          <div className="header-top">
            <div className="header-trophy">🏆</div>
            <div className="header-titles">
              <h1 className="header-main-title">2026 世界杯预测系统</h1>
              <p className="header-subtitle">LIVE PREDICTION · SMART ANALYSIS</p>
            </div>
          </div>
          <div className="header-accent-bar" />
        </div>
        <SystemStatusBar />
      </header>

      {/* Navigation Tabs */}
      <nav className="main-nav">
        <div className="nav-inner">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'nav-tab-active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="nav-tab-icon">{tab.icon}</span>
              <span className="nav-tab-label">{tab.label}</span>
              {tab.id === 'montecarlo' && mc.loading && (
                <span className="nav-tab-running" />
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Monte Carlo background progress banner */}
      {mc.loading && activeTab !== 'montecarlo' && (
        <div className="mc-bg-banner" onClick={() => setActiveTab('montecarlo')}>
          <span className="mc-bg-spinner" />
          <span>蒙特卡洛模拟进行中…</span>
          <span className="mc-bg-action">点击查看</span>
        </div>
      )}

      {/* ⚠️ 温馨提示横幅 */}
      <div className="warning-banner">
        <div className="warning-banner-glow" />
        <div className="warning-banner-inner">
          <span className="warning-icon">⚡</span>
          <div className="warning-divider" />
          <span className="warning-kick">一脚世界波</span>
          <span className="warning-sep">·</span>
          <span className="warning-heart">一颗平常心</span>
          <div className="warning-divider" />
          <span className="warning-text">
            远离非法彩票<span className="warning-dot">·</span>拒绝网络赌博
          </span>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'dashboard' && <Dashboard onOpenMatch={handleOpenMatch} />}
        {activeTab === 'standings' && <GroupStandings />}
        {activeTab === 'bracket' && <Bracket onOpenMatch={handleOpenMatch} />}
        {activeTab === 'analysis' && analysisMatchId && <MatchAnalysis matchId={analysisMatchId} />}
        {activeTab === 'analysis' && !analysisMatchId && (
          <div className="empty-message">请从赛程总览中点击比赛进入分析</div>
        )}
        {activeTab === 'predictions' && <Predictions />}
        {activeTab === 'montecarlo' && <MonteCarloPanel data={mc.data} loading={mc.loading} error={mc.error} runSimulation={mc.runSimulation} />}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <span className="footer-text">2026 FIFA World Cup · Prediction System</span>
          <span className="footer-dot">·</span>
          <span className="footer-text">Powered by Multi-Factor Model + Monte Carlo</span>
        </div>
      </footer>
    </div>
  );
};

export default App;