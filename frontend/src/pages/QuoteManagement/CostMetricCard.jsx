/**
 * Cost Metric Card Component
 * 成本指标卡片组件
 */

export default function CostMetricCard({ label, value, description, icon: Icon }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
        {Icon && <Icon className="h-4 w-4 text-slate-300" />}
        {label}
      </div>
      <div className="text-2xl font-semibold text-white">{value}</div>
      {description && <p className="text-xs text-slate-500">{description}</p>}
    </div>
  );
}
