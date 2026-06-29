import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useSystemStatus } from '../hooks/useData';

const API_BASE = '/api';

const SystemStatusBar: React.FC = () => {
  const { data } = useSystemStatus();
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const msgTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => () => { if (msgTimer.current) clearTimeout(msgTimer.current); }, []);

  const handleRefreshOdds = useCallback(async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    if (msgTimer.current) clearTimeout(msgTimer.current);
    try {
      const res = await fetch(`${API_BASE}/refresh-odds`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setRefreshMsg({ text: json.message || '✅ 赔率已刷新，预测已更新', ok: true });
      // Notify other components to refresh
      window.dispatchEvent(new CustomEvent('refresh-data', { detail: json }));
      msgTimer.current = setTimeout(() => setRefreshMsg(null), 6000);
    } catch (e: any) {
      setRefreshMsg({ text: '❌ ' + (e.message || '网络错误'), ok: false });
      msgTimer.current = setTimeout(() => setRefreshMsg(null), 4000);
    } finally {
      setRefreshing(false);
    }
  }, []);

  if (!data) return null;

  const isApiLive = data.api_key_configured && data.api_source === 'api-football-v3';
  const sourceLabel = isApiLive ? '实时API' : '本地数据';
  const sourceColor = isApiLive ? '#00f0ff' : '#f59e0b';

  return (
    <div className="system-status-bar">
      <div className="status-indicator">
        <span className="status-dot" style={{ backgroundColor: sourceColor }} />
        <span className="status-source" style={{ color: sourceColor }}>{sourceLabel}</span>
      </div>
      {data.last_updated && (
        <span className="status-updated">
          更新于 {new Date(data.last_updated).toLocaleTimeString('zh-CN')}
        </span>
      )}

      {/* ── 赔率刷新按钮 ── */}
      <button
        className={`status-refresh-btn${refreshing ? ' refreshing' : ''}`}
        onClick={handleRefreshOdds}
        disabled={refreshing}
      >
        <span className="refresh-btn-icon">{refreshing ? '⏳' : '⚡'}</span>
        <span className="refresh-btn-text">{refreshing ? '拉取数据中…' : '一键刷新数据'}</span>
        {refreshing && <span className="refresh-btn-dots"><i>.</i><i>.</i><i>.</i></span>}
        {!refreshing && <span className="refresh-btn-ring" />}
      </button>

      {/* ── 结果提示浮层 ── */}
      {refreshMsg && (
        <div className={`refresh-toast${refreshMsg.ok ? '' : ' toast-error'}`}>
          <span className="toast-icon">{refreshMsg.ok ? '✅' : '⚠️'}</span>
          <span className="toast-text">{refreshMsg.text}</span>
          <div
            className={`toast-timeline${refreshMsg.ok ? '' : ' error'}`}
            style={{ animationDuration: refreshMsg.ok ? '6s' : '4s' }}
          />
        </div>
      )}
    </div>
  );
};

export default SystemStatusBar;