import { cn, formatCurrency } from "../../lib/utils";



export default function ProfitLossTab({ currentData, monthlyFinancials }) {
  return (
    <TabsContent value="profit-loss" className="space-y-6 mt-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 损益汇总 */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">
            损益表
          </h3>
          <div className="space-y-4">
            <div className="p-4 bg-slate-800/40 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400">营业收入</span>
                <span className="text-2xl font-bold text-amber-400">
                  {formatCurrency(currentData.revenue)}
                </span>
              </div>
            </div>
            <div className="p-4 bg-slate-800/40 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400">营业成本</span>
                <span className="text-xl font-bold text-red-400">
                  {formatCurrency(currentData.cost)}
                </span>
              </div>
            </div>
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400">净利润</span>
                <span className="text-2xl font-bold text-emerald-400">
                  {formatCurrency(currentData.profit)}
                </span>
              </div>
              <div className="text-sm text-slate-400 mt-2">
                利润率:{" "}
                {(
                currentData.profit / currentData.revenue *
                100).
                toFixed(1)}
                %
              </div>
            </div>
          </div>
        </div>

        {/* 营收利润趋势图 */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">
            营收与利润趋势
          </h3>
          <DualAxesChart
            data={(monthlyFinancials || []).map((item) => ({
              month: item.month,
              revenue: item.revenue,
              profit: item.profit,
              margin: (item.profit / item.revenue * 100).toFixed(1)
            }))}
            xField="month"
            yField={["revenue", "margin"]}
            leftYAxisTitle="营收 (元)"
            rightYAxisTitle="利润率 (%)"
            height={280}
            leftFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`}
            rightFormatter={(v) => `${v}%`} />
        </div>
      </div>

      {/* 收入成本对比柱状图 */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-3">
          收入成本对比
        </h4>
        <BarChartComponent
          data={(monthlyFinancials || []).flatMap((item) => [
          {
            month: item.month,
            type: "营业收入",
            value: item.revenue
          },
          { month: item.month, type: "营业成本", value: item.cost },
          { month: item.month, type: "净利润", value: item.profit }]
          )}
          xField="month"
          yField="value"
          seriesField="type"
          isGroup
          height={300}
          colors={["#f59e0b", "#ef4444", "#10b981"]}
          formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />
      </div>

      {/* Revenue Trend List */}
      <div>
        <h4 className="text-sm font-medium text-slate-400 mb-3">
          月度营收明细
        </h4>
        <div className="space-y-3">
          {(monthlyFinancials || []).map((item, index) => {
            const maxRevenue = Math.max(
              ...(monthlyFinancials || []).map((m) => m.revenue)
            );
            const percentage = item.revenue / maxRevenue * 100;
            return (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">{item.month}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-white font-medium">
                      {formatCurrency(item.revenue)}
                    </span>
                    {index > 0 &&
                    <span
                      className={cn(
                        "text-xs",
                        item.revenue >
                        monthlyFinancials[index - 1].revenue ?
                        "text-emerald-400" :
                        "text-red-400"
                      )}>
                        {item.revenue >
                      monthlyFinancials[index - 1].revenue ?
                      "↑" :
                      "↓"}
                        {Math.abs(
                        (item.revenue -
                        monthlyFinancials[index - 1].revenue) /
                        monthlyFinancials[index - 1].revenue *
                        100
                      ).toFixed(1)}
                        %
                    </span>
                    }
                  </div>
                </div>
                <Progress
                  value={percentage || "unknown"}
                  className="h-2 bg-slate-700/50" />
              </div>);
          })}
        </div>
      </div>
    </TabsContent>
  );
}
