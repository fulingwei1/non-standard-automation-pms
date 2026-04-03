import { Card, CardContent, CardHeader, CardTitle, Badge, Progress } from "../../components/ui";
import { agingBucketOrder, agingBucketLabelMap, agingBucketColorMap } from "./constants";

/**
 * AgingAnalysis — displays the accounts-receivable aging breakdown card,
 * including per-bucket tiles and a simple bar chart.
 *
 * @param {{ agingData: object, formatCurrency: (v: any) => string }} props
 */
export function AgingAnalysis({ agingData, formatCurrency }) {
  if (!agingData) return null;

  const sortedBuckets = Object.entries(agingData.aging_buckets || {}).sort(
    ([a], [b]) => (agingBucketOrder[a] || 99) - (agingBucketOrder[b] || 99)
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>应收账款账龄分析</CardTitle>
          <div className="text-sm text-slate-400">
            总计待收: {formatCurrency(agingData.total_unpaid || 0)}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Bucket tiles */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {sortedBuckets.map(([key, bucket]) => {
              const percentage =
                agingData.total_unpaid > 0
                  ? ((bucket.amount || 0) / agingData.total_unpaid) * 100
                  : 0;

              return (
                <Card key={key} className="border-slate-700">
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-300">
                          {agingBucketLabelMap[key] || key}
                        </span>
                        <Badge
                          className={agingBucketColorMap[key] || "bg-blue-500"}
                        >
                          {bucket.count || 0} 笔
                        </Badge>
                      </div>
                      <div className="text-2xl font-bold text-white">
                        {formatCurrency(bucket.amount || 0)}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">占比</span>
                          <span className="text-slate-300">
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                        <Progress value={percentage || "unknown"} className="h-2" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Bar chart */}
          {agingData.total_unpaid > 0 && (
            <div className="mt-6 pt-6 border-t border-slate-700">
              <h4 className="text-sm font-semibold text-slate-300 mb-4">
                账龄分布
              </h4>
              <div className="flex items-end gap-2 h-32">
                {sortedBuckets.map(([key, bucket]) => {
                  const height =
                    agingData.total_unpaid > 0
                      ? ((bucket.amount || 0) / agingData.total_unpaid) * 100
                      : 0;

                  return (
                    <div
                      key={key}
                      className="flex-1 flex flex-col items-center gap-2"
                    >
                      <div className="w-full flex flex-col items-center justify-end h-full">
                        <div
                          className={`w-full ${
                            agingBucketColorMap[key] || "bg-blue-500"
                          } rounded-t transition-all hover:opacity-80 cursor-pointer`}
                          style={{ height: `${height}%` }}
                          title={`${agingBucketLabelMap[key]}: ${formatCurrency(
                            bucket.amount || 0
                          )}`}
                        />
                      </div>
                      <span className="text-xs text-slate-400 text-center">
                        {agingBucketLabelMap[key] || key}
                      </span>
                      <span className="text-xs text-slate-500">
                        {formatCurrency(bucket.amount || 0)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
