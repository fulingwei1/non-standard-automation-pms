export function MiniBarChart({ data }) {
  if (!data || data?.length === 0) {
    return <div className="text-sm text-slate-400">暂无产值数据</div>;
  }
  const maxValue = Math.max(...(data || []).map((d) => d.revenue), 0);
  if (maxValue === 0) {
    return <div className="text-sm text-slate-400">暂无产值数据</div>;
  }
  const safeMax = maxValue;

  return (
    <div className="flex items-end gap-2 h-32">
      {(data || []).map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col items-center gap-1">
            <span className="text-xs text-slate-400">
              {(item.revenue / 100).toFixed(0)}K
            </span>
            <div
              className="w-full bg-gradient-to-t from-accent/50 to-accent rounded-t-sm transition-all hover:from-accent/70"
              style={{ height: `${(item.revenue / safeMax) * 80}px` }}
            />
          </div>
          <span className="text-xs text-slate-500">{item.month}</span>
        </div>
      ))}
    </div>
  );
}
