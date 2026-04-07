import { cn, formatCurrency } from "../../lib/utils";



export default function CostAnalysisTab({ costBreakdown }) {
  return (
    <TabsContent value="cost" className="space-y-6 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 成本构成饼图 */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">
            成本构成占比
          </h3>
          <PieChartComponent
            data={(costBreakdown || []).map((item) => ({
              category: item.category,
              value: item.amount
            }))}
            angleField="value"
            colorField="category"
            height={300}
            innerRadius={0.6}
            label={{
              type: "spider",
              content: "{name}: {percentage}"
            }}
            formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />
        </div>

        {/* 成本明细列表 */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">
            成本构成明细
          </h3>
          <div className="space-y-3">
            {(costBreakdown || []).map((item, index) => {
              const total = (costBreakdown || []).reduce(
                (sum, c) => sum + c.amount,
                0
              );
              const percentage = item.amount / total * 100;
              const colors = [
              "bg-blue-500",
              "bg-purple-500",
              "bg-amber-500",
              "bg-cyan-500",
              "bg-emerald-500",
              "bg-pink-500"];

              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "w-3 h-3 rounded-full",
                          colors[index % colors.length]
                        )} />
                      <span className="text-slate-400">
                        {item.category}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-white font-medium">
                        {formatCurrency(item.amount)}
                      </span>
                      <span className="text-slate-500 text-xs w-12 text-right">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <Progress
                    value={percentage || "unknown"}
                    className="h-2 bg-slate-700/50" />
                </div>);
            })}
          </div>
        </div>
      </div>

      {/* 成本趋势对比 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          预算与实际对比
        </h3>
        <BarChartComponent
          data={(costBreakdown || []).flatMap((item) => [
          {
            category: item.category,
            type: "预算",
            value: item.budget
          },
          {
            category: item.category,
            type: "实际",
            value: item.amount
          }]
          )}
          xField="category"
          yField="value"
          seriesField="type"
          isGroup
          height={280}
          colors={["#64748b", "#3b82f6"]}
          formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />
      </div>
    </TabsContent>
  );
}
