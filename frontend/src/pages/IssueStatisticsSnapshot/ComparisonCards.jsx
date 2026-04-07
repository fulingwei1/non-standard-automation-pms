/**
 * ComparisonCards — 4 个指标对比卡片（总问题数 / 待处理 / 已解决 / 阻塞问题）
 */
import { cn } from "../../lib/utils";

/**
 * Single metric comparison card.
 *
 * @param {{
 *   label: string,
 *   current: number,
 *   previous: number,
 *   valueColor?: string,
 *   positiveIsGood?: boolean,
 * }} props
 */
function MetricCard({ label, current, previous, valueColor = "text-white", positiveIsGood = false }) {
  const delta = current - previous;
  const isUp = delta > 0;
  // "good" direction: for resolved, up is green; for total/open/blocking, up is red
  const isPositive = positiveIsGood ? isUp : !isUp;
  const trendColor = isPositive ? "text-green-400" : "text-red-400";
  const pct = previous
    ? Math.abs((delta / previous) * 100).toFixed(1)
    : null;

  return (
    <Card className="bg-surface-50 border-white/5">
      <CardContent className="p-4">
        <div className="text-sm text-slate-400 mb-1">{label}</div>
        <div className="flex items-center justify-between">
          <div className={cn("text-2xl font-bold", valueColor)}>{current}</div>
          {previous != null && pct !== null && (
            <div className={cn("text-sm flex items-center gap-1", trendColor)}>
              {isUp ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              {pct}%
            </div>
          )}
        </div>
        {previous != null && (
          <div className="text-xs text-slate-500 mt-1">期初: {previous}</div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * @param {{ comparison: { total, open, resolved, blocking } }} props
 */
export function ComparisonCards({ comparison }) {
  if (!comparison) { return null; }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <MetricCard
        label="总问题数"
        current={comparison.total.current}
        previous={comparison.total.previous}
        valueColor="text-white"
        positiveIsGood={false}
      />
      <MetricCard
        label="待处理"
        current={comparison.open.current}
        previous={comparison.open.previous}
        valueColor="text-blue-400"
        positiveIsGood={false}
      />
      <MetricCard
        label="已解决"
        current={comparison.resolved.current}
        previous={comparison.resolved.previous}
        valueColor="text-green-400"
        positiveIsGood={true}
      />
      <MetricCard
        label="阻塞问题"
        current={comparison.blocking.current}
        previous={comparison.blocking.previous}
        valueColor="text-red-400"
        positiveIsGood={false}
      />
    </div>
  );
}
