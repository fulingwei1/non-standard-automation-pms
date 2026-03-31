import { cn } from "../../lib/utils";

export function HealthDonut({ data }) {
  const total = data.total;
  const safeTotal = total > 0 ? total : 1;
  const healthyPercent = total > 0 ? (data.healthy / safeTotal) * 100 : 0;
  const atRiskPercent = total > 0 ? (data.atRisk / safeTotal) * 100 : 0;
  const blockedPercent = total > 0 ? (data.blocked / safeTotal) * 100 : 0;

  return (
    <div className="flex items-center gap-6">
      {/* Donut Chart */}
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          {/* Background */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-surface-2"
          />
          {/* Healthy */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${healthyPercent} ${100 - healthyPercent}`}
            strokeDashoffset="0"
            className="text-emerald-500"
          />
          {/* At Risk */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${atRiskPercent} ${100 - atRiskPercent}`}
            strokeDashoffset={`${-healthyPercent}`}
            className="text-amber-500"
          />
          {/* Blocked */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${blockedPercent} ${100 - blockedPercent}`}
            strokeDashoffset={`${-(healthyPercent + atRiskPercent)}`}
            className="text-red-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{total}</span>
          <span className="text-xs text-slate-400">项目</span>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-3">
        {[
          { label: "正常", value: data.healthy, color: "bg-emerald-500" },
          { label: "风险", value: data.atRisk, color: "bg-amber-500" },
          { label: "阻塞", value: data.blocked, color: "bg-red-500" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={cn("w-3 h-3 rounded-full", item.color)} />
            <span className="text-sm text-slate-400">{item.label}</span>
            <span className="text-sm font-medium text-white ml-auto">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
