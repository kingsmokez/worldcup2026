import { useLiveScores, formatDate } from '../hooks/useData';
import { Activity, Circle } from 'lucide-react';

export default function LiveScoreBar() {
  const { data, loading, error } = useLiveScores();

  if (loading) {
    return (
      <div className="glass-strong border-t border-b border-white/5 px-4 py-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gray-600" />
          <div className="skeleton h-4 w-64" />
        </div>
      </div>
    );
  }

  if (error || !data || data.length === 0) {
    const liveCount = data?.filter(m => m.status === 'live').length ?? 0;

    return (
      <div className="glass-strong border-t border-b border-white/5 px-4 py-2">
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <Activity size={14} />
          <span>{liveCount > 0 ? `${liveCount} 场比赛进行中` : '暂无进行中的比赛'}</span>
        </div>
      </div>
    );
  }

  const liveMatches = data.filter(m => m.status === 'live');
  const finishedMatches = data.filter(m => m.status === 'finished').slice(-5);

  const tickerItems = [
    ...liveMatches.map(m => ({
      text: `${m.team1_name} ${m.score1 ?? 0} - ${m.score2 ?? 0} ${m.team2_name}`,
      isLive: true,
    })),
    ...finishedMatches.map(m => ({
      text: `${m.team1_name} ${m.score1} - ${m.score2} ${m.team2_name}`,
      isLive: false,
    })),
  ];

  return (
    <div className="glass-strong border-t border-b border-white/5 px-4 py-2 overflow-hidden">
      <div className="flex items-center gap-3">
        {liveMatches.length > 0 && (
          <div className="flex items-center gap-1.5 shrink-0">
            <Circle size={8} className="text-crimson-500 fill-crimson-500 animate-pulse-dot" />
            <span className="text-crimson-500 text-xs font-medium font-display tracking-wider">LIVE</span>
          </div>
        )}
        <div className="overflow-hidden flex-1 relative">
          <div className="flex gap-8 whitespace-nowrap animate-slide-in-right">
            {tickerItems.map((item, i) => (
              <span
                key={i}
                className={`text-sm font-mono ${item.isLive ? 'text-gold-400' : 'text-gray-400'} ${i > 0 ? 'border-l border-white/10 pl-8' : ''}`}
              >
                {item.text}
              </span>
            ))}
            {/* Duplicate for seamless scrolling */}
            <span className="text-sm font-mono text-gray-400 border-l border-white/10 pl-8">
              {tickerItems.length > 0 ? tickerItems[0]?.text : '等待比赛数据...'}
            </span>
          </div>
        </div>
        <span className="text-xs text-gray-600 font-mono shrink-0">
          实时更新 · 60s
        </span>
      </div>
    </div>
  );
}