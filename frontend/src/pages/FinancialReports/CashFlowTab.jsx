import { cn, formatCurrency } from "../../lib/utils";

export default function CashFlowTab({ cashFlowData }) {
  return (
    <TabsContent value="cash-flow" className="space-y-6 mt-6">
      {/* 现金流趋势图 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          现金流量趋势
        </h3>
        <AreaChartComponent
          data={(cashFlowData || []).flatMap((item) => [
          {
            month: item.month,
            type: "现金流入",
            value: item.inflow
          },
          {
            month: item.month,
            type: "现金流出",
            value: -item.outflow
          },
          { month: item.month, type: "净现金流", value: item.net }]
          )}
          xField="month"
          yField="value"
          seriesField="type"
          height={300}
          colors={["#10b981", "#ef4444", "#3b82f6"]}
          formatter={(v) => `¥${(Math.abs(v) / 10000).toFixed(0)}万`} />
      </div>

      {/* 现金流明细 */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          现金流量明细
        </h3>
        <div className="space-y-4">
          {(cashFlowData || []).map((item, index) => {
            const maxFlow = Math.max(
              ...(cashFlowData || []).map((c) => Math.abs(c.net))
            );
            const percentage = Math.abs(item.net) / maxFlow * 100;
            return (
              <div
                key={index}
                className="p-4 bg-slate-800/40 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-slate-400">{item.month}</span>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-xs text-slate-500">
                        流入
                      </div>
                      <div className="text-sm font-medium text-emerald-400">
                        {formatCurrency(item.inflow)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-500">
                        流出
                      </div>
                      <div className="text-sm font-medium text-red-400">
                        {formatCurrency(item.outflow)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-slate-500">
                        净流量
                      </div>
                      <div
                        className={cn(
                          "text-lg font-bold",
                          item.net > 0 ?
                          "text-emerald-400" :
                          "text-red-400"
                        )}>
                        {formatCurrency(item.net)}
                      </div>
                    </div>
                  </div>
                </div>
                <Progress
                  value={percentage || "unknown"}
                  className={cn(
                    "h-2",
                    item.net > 0 ?
                    "bg-emerald-500/20" :
                    "bg-red-500/20"
                  )} />
              </div>);
          })}
        </div>
      </div>
    </TabsContent>
  );
}
