/**
 * Cost Insights Panel - Main cost insights card (left 2/3)
 * 成本报价洞察面板
 */

import { DollarSign, PieChart, TrendingDown, TrendingUp } from "lucide-react";


import { formatCurrency, formatPercent } from "../../lib/utils";
import { COST_RANGE_LABELS } from "./constants";

export default function CostInsightsPanel({
  costInsights,
  costLoading,
  costTimeRange,
  setCostTimeRange,
  topSupplier,
  trendItems
}) {
  return (
    <Card className="xl:col-span-2 bg-slate-900/60 border-slate-800 text-white">
      <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <CardTitle className="text-lg">成本报价洞察</CardTitle>
          <p className="text-sm text-slate-400 mt-1">
            自动汇总采购成本，辅助报价策略
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-xs border-slate-700 text-slate-300">
            {COST_RANGE_LABELS[costTimeRange]}
          </Badge>
          <Select value={costTimeRange} onValueChange={setCostTimeRange}>
            <SelectTrigger className="w-[130px] border-slate-700">
              <SelectValue placeholder="选择周期" />
            </SelectTrigger>
            <SelectContent className="bg-slate-900 border-slate-700 text-white">
              <SelectItem value="month">本月</SelectItem>
              <SelectItem value="quarter">本季度</SelectItem>
              <SelectItem value="year">本年度</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {costLoading ? (
          <div className="space-y-4 animate-pulse">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, idx) => (
                <div key={idx} className="h-24 rounded-xl bg-slate-800" />
              ))}
            </div>
            <div className="h-32 rounded-xl bg-slate-800" />
          </div>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <CostMetricCard
                label="采购总额"
                value={formatCurrency(costInsights.totalCost || 0)}
                description={`${costInsights.orderCount || 0} 笔订单`}
                icon={DollarSign}
              />
              <CostMetricCard
                label="平均单笔金额"
                value={formatCurrency(costInsights.averageOrderCost || 0)}
                description="实时均价"
                icon={PieChart}
              />
              <CostMetricCard
                label="成本节约"
                value={formatCurrency(costInsights.costSavings || 0)}
                description={`节约率 ${formatPercent(costInsights.savingsRate || 0)}`}
                icon={TrendingDown}
              />
              <CostMetricCard
                label="核心供应商"
                value={topSupplier?.name || "暂无数据"}
                description={
                  topSupplier ? formatCurrency(topSupplier.amount || 0) : "等待真实数据"
                }
                icon={TrendingUp}
              />
            </div>

            <div className="mt-6">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-300">采购趋势</p>
                <span className="text-xs text-slate-500">
                  最近 {trendItems.length || 0} 期
                </span>
              </div>
              {trendItems.length === 0 ? (
                <div className="text-sm text-slate-500 mt-4">
                  暂无趋势数据
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  {(trendItems || []).map((item) => (
                    <div
                      key={item.month}
                      className="flex items-center justify-between rounded-lg border border-slate-800 px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-white">
                          {item.month}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {item.orders || 0} 笔订单
                        </p>
                      </div>
                      <span className="text-base font-semibold text-emerald-400">
                        {formatCurrency(item.amount || 0)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
