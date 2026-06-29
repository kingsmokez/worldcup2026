import { useEffect, useRef, useState } from 'react';
import { useBacktest } from '../hooks/useData';
import type { BacktestYearResult } from '../hooks/useData';
import { Trophy, Target, TrendingUp, BarChart3, CheckCircle2, XCircle } from 'lucide-react';

export default function BacktestPanel() {
  const { data, loading, error, refetch } = useBacktest();

  if (loading) {
    return <BacktestSkeleton />;
  }

  if (error) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-4 animate-fade-in">
        <div className="glass p-8 rounded-sm text-center max-w-md">
          <div className="text-crimson-500 text-5xl mb-4 font-display">!</div>
          <h3 className="text-xl font-display text-white mb-2">回溯数据加载失败</h3>
          <p className="text-gray-400 text-sm mb-4">{error}</p>
          <button
            onClick={refetch}
            className="px-6 py-2 bg-gold-400/10 border border-gold-400/30 text-gold-400 hover:bg-gold-400/20 transition-colors font-display tracking-wider text-sm"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-4 animate-fade-in">
        <div className="glass p-8 rounded-sm text-center max-w-md">
          <Trophy size={48} className="mx-auto text-gray-600 mb-4" />
          <h3 className="text-xl font-display text-white mb-2">暂无回溯数据</h3>
          <p className="text-gray-400 text-sm">系统正在分析历史赛事数据</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h2 className="font-display text-3xl tracking-wider gold-bar">
          <span className="text-gradient-gold">预测模型回溯</span>
        </h2>
        <p className="text-gray-500 text-xs mt-2">历史世界杯预测准确率分析</p>
      </div>

      {/* Year Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {data.map((result, i) => (
          <YearCard key={result.year} result={result} index={i} />
        ))}
      </div>

      {/* Combined Summary */}
      {data.length >= 2 && (
        <div className="mb-8 stagger-3 animate-slide-up">
          <CombinedSummary results={data} />
        </div>
      )}

      {/* Stage Comparison */}
      <div className="mb-8 stagger-4 animate-slide-up">
        <StageComparison results={data} />
      </div>

      {/* Metrics Legend */}
      <div className="glass border border-white/5 p-4 stagger-5 animate-slide-up">
        <h5 className="text-[10px] font-display tracking-widest text-gray-500 uppercase mb-3">
          指标说明
        </h5>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs text-gray-400">
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-electric-500 mt-1 shrink-0" />
            <div>
              <span className="text-white font-medium">方向准确率</span>
              <p className="text-gray-600">正确预测胜/平/负方向的比例</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-mint-500 mt-1 shrink-0" />
            <div>
              <span className="text-white font-medium">精确比分率</span>
              <p className="text-gray-600">完全准确预测最终比分的比例</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-amber-500 mt-1 shrink-0" />
            <div>
              <span className="text-white font-medium">误差1球以内率</span>
              <p className="text-gray-600">预测比分与真实比分差距在1球以内的比例</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ========== YEAR CARD ==========
function YearCard({ result, index }: { result: BacktestYearResult; index: number }) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 300 + index * 200);
    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div className={`glass border border-white/5 p-6 stagger-${index + 1} animate-slide-up`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-display text-2xl tracking-wider text-white">
            {result.year}
            <span className="text-gold-400 ml-2">世界杯</span>
          </h3>
          <p className="text-[10px] text-gray-600 font-mono mt-0.5">
            {result.total_matches} 场比赛
          </p>
        </div>
        <div className="w-12 h-12 border-2 border-gold-400/30 flex items-center justify-center">
          <Trophy size={20} className="text-gold-400" />
        </div>
      </div>

      {/* Semi-circle Gauges */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <GaugeItem
          label="方向准确率"
          value={result.direction_accuracy}
          color="electric"
          detail={`${result.correct_direction}/${result.total_matches}`}
        />
        <GaugeItem
          label="精确比分"
          value={result.exact_score_rate}
          color="mint"
          detail={`${result.exact_score_correct}/${result.total_matches}`}
        />
        <GaugeItem
          label="误差≤1球"
          value={result.within_one_goal_rate}
          color="amber"
          detail={`${result.within_one_goal}/${result.total_matches}`}
        />
      </div>

      {/* Stage Breakdown */}
      <div className="border-t border-white/5 pt-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500 font-display tracking-wider">小组赛</span>
            <span className="font-mono text-sm text-electric-400">{result.group_stage_accuracy.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-500 font-display tracking-wider">淘汰赛</span>
            <span className="font-mono text-sm text-crimson-400">{result.knockout_accuracy.toFixed(1)}%</span>
          </div>
        </div>
        {/* Progress bar comparison */}
        <div className="flex gap-1 mt-2">
          <div className="flex-1 h-1.5 bg-white/5 overflow-hidden">
            <div
              className="h-full bg-electric-500 transition-all duration-1500 ease-out"
              style={{ width: animated ? `${result.group_stage_accuracy}%` : '0%' }}
            />
          </div>
          <div className="flex-1 h-1.5 bg-white/5 overflow-hidden">
            <div
              className="h-full bg-crimson-500 transition-all duration-1500 ease-out delay-300"
              style={{ width: animated ? `${result.knockout_accuracy}%` : '0%' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ========== GAUGE ITEM ==========
function GaugeItem({
  label,
  value,
  color,
  detail,
}: {
  label: string;
  value: number;
  color: 'electric' | 'mint' | 'amber';
  detail: string;
}) {
  const colorMap = {
    electric: { stroke: '#2563EB', bg: 'rgba(37,99,235,0.1)', text: 'text-electric-400' },
    mint: { stroke: '#10B981', bg: 'rgba(16,185,129,0.1)', text: 'text-mint-500' },
    amber: { stroke: '#F59E0B', bg: 'rgba(245,158,11,0.1)', text: 'text-amber-500' },
  };

  const c = colorMap[color];
  const percentage = value;
  const radius = 32;
  const circumference = Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center text-center">
      {/* SVG Semi-circle */}
      <svg width="76" height="48" viewBox="0 0 76 48" className="mb-1">
        <path
          d="M 6 44 A 32 32 0 0 1 70 44"
          fill="none"
          stroke={c.bg}
          strokeWidth="5"
          strokeLinecap="round"
        />
        <path
          d="M 6 44 A 32 32 0 0 1 70 44"
          fill="none"
          stroke={c.stroke}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-1500 ease-out"
        />
      </svg>
      <div className={`font-mono text-lg font-bold ${c.text}`}>
        {percentage.toFixed(0)}%
      </div>
      <div className="text-[9px] text-gray-500 font-display tracking-wider mt-0.5">
        {label}
      </div>
      <div className="text-[9px] text-gray-600 font-mono">
        {detail}
      </div>
    </div>
  );
}

// ========== COMBINED SUMMARY ==========
function CombinedSummary({ results }: { results: BacktestYearResult[] }) {
  const totalMatches = results.reduce((sum, r) => sum + r.total_matches, 0);
  const totalCorrect = results.reduce((sum, r) => sum + r.correct_direction, 0);
  const combinedAccuracy = totalMatches > 0 ? (totalCorrect / totalMatches) * 100 : 0;

  return (
    <div className="glass border border-gold-400/20 p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 bg-gold-400/10 border border-gold-400/30 flex items-center justify-center">
          <Target size={16} className="text-gold-400" />
        </div>
        <h4 className="font-display text-xl tracking-wider text-white">
          综合回溯结果
          <span className="text-gray-600 text-xs ml-2 font-body">
            ({results.map(r => r.year).join(' + ')})
          </span>
        </h4>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="font-mono text-2xl font-bold text-white">{totalMatches}</div>
          <div className="text-[10px] text-gray-500 font-display tracking-wider">总比赛数</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-2xl font-bold text-electric-400">
            {combinedAccuracy.toFixed(1)}%
          </div>
          <div className="text-[10px] text-gray-500 font-display tracking-wider">综合方向准确率</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-2xl font-bold text-mint-500">
            {(() => {
              const totalExact = results.reduce((s, r) => s + r.exact_score_correct, 0);
              return totalMatches > 0 ? ((totalExact / totalMatches) * 100).toFixed(1) : '0.0';
            })()}%
          </div>
          <div className="text-[10px] text-gray-500 font-display tracking-wider">精确比分率</div>
        </div>
        <div className="text-center">
          <div className="font-mono text-2xl font-bold text-amber-500">
            {(() => {
              const totalWithin = results.reduce((s, r) => s + r.within_one_goal, 0);
              return totalMatches > 0 ? ((totalWithin / totalMatches) * 100).toFixed(1) : '0.0';
            })()}%
          </div>
          <div className="text-[10px] text-gray-500 font-display tracking-wider">误差≤1球率</div>
        </div>
      </div>
    </div>
  );
}

// ========== STAGE COMPARISON ==========
function StageComparison({ results }: { results: BacktestYearResult[] }) {
  const avgGroup = results.length > 0
    ? results.reduce((s, r) => s + r.group_stage_accuracy, 0) / results.length
    : 0;
  const avgKnockout = results.length > 0
    ? results.reduce((s, r) => s + r.knockout_accuracy, 0) / results.length
    : 0;

  return (
    <div className="glass border border-white/5 p-6">
      <h4 className="text-sm font-display tracking-wider text-gold-400 mb-6 gold-bar inline-block">
        小组赛 vs 淘汰赛 准确率对比
      </h4>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Group Stage */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-gray-400 font-display tracking-wider">小组赛</span>
            <span className="font-mono text-lg text-electric-400">{avgGroup.toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-white/5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-electric-500 to-electric-400 transition-all duration-1500 ease-out"
              style={{ width: `${avgGroup}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-gray-600 font-mono">
            {results.map(r => (
              <span key={r.year}>{r.year}: {r.group_stage_accuracy.toFixed(1)}%</span>
            ))}
          </div>
        </div>

        {/* Knockout Stage */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-gray-400 font-display tracking-wider">淘汰赛</span>
            <span className="font-mono text-lg text-crimson-400">{avgKnockout.toFixed(1)}%</span>
          </div>
          <div className="h-3 bg-white/5 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-crimson-500 to-crimson-400 transition-all duration-1500 ease-out delay-300"
              style={{ width: `${avgKnockout}%` }}
            />
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-gray-600 font-mono">
            {results.map(r => (
              <span key={r.year}>{r.year}: {r.knockout_accuracy.toFixed(1)}%</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ========== SKELETON ==========
function BacktestSkeleton() {
  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <div className="skeleton h-10 w-64 mb-2" />
        <div className="skeleton h-4 w-48" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {[1, 2].map(i => (
          <div key={i} className="glass p-6 border border-white/5">
            <div className="flex justify-between mb-6">
              <div>
                <div className="skeleton h-8 w-32 mb-1" />
                <div className="skeleton h-3 w-16" />
              </div>
              <div className="skeleton h-12 w-12" />
            </div>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[1, 2, 3].map(j => (
                <div key={j} className="flex flex-col items-center gap-2">
                  <div className="skeleton h-12 w-12 rounded-full" />
                  <div className="skeleton h-5 w-10" />
                  <div className="skeleton h-3 w-12" />
                </div>
              ))}
            </div>
            <div className="skeleton h-12 w-full" />
          </div>
        ))}
      </div>
      <div className="skeleton h-32 w-full mb-8" />
      <div className="skeleton h-24 w-full" />
    </div>
  );
}