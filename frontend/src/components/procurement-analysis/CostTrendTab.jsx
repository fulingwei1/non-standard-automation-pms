/**
 * 采购成本趋势分析 Tab 组件
 * 显示采购成本趋势图表和月度明细表格
 */
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import ProcurementStatsCard from './ProcurementStatsCard';
import { STATS_CARD_CONFIGS, formatAmount as _formatAmount } from '@/lib/constants/procurementAnalysis';

/**
 * 成本趋势 Tab 组件
 * @param {object} props
 * @param {object} props.data - 成本趋势数据
 */
export default function CostTrendTab({ data }) {
  const { summary, trend_data } = data || {};

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {summary &&
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {STATS_CARD_CONFIGS.costTrend.map((config) =>
        <ProcurementStatsCard
          key={config.key}
          label={config.label}
          value={summary[config.key]}
          icon={config.icon}
          color={config.color} />

        )}
      </div>
      }

      {/* 成本趋势图表 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>采购成本趋势</CardTitle>
          <CardDescription>按月统计采购金额变化</CardDescription>
        </CardHeader>
        <CardContent>
          {trend_data?.length > 0 ?
          <div className="space-y-4">
              {/* 简单趋势图 */}
              <div className="h-64 flex items-end gap-2">
                {trend_data.map((item, index) => {
                const maxValue = Math.max(...trend_data.map((d) => d.amount));
                const height = item.amount / maxValue * 100;
                return (
                  <div key={index} className="flex-1 flex flex-col items-center">
                      <div
                      className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t hover:from-blue-500 hover:to-blue-300 transition-all cursor-pointer relative group"
                      style={{ height: `${height}%`, minHeight: height > 0 ? '20px' : '0' }}>

                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-900 px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                          ¥{item.amount?.toLocaleString()}
                        </div>
                      </div>
                      <div className="text-xs text-slate-400 mt-2">{item.period}</div>
                  </div>);

              })}
              </div>
          </div> :

          <div className="text-center py-12 text-slate-400">暂无数据</div>
          }
        </CardContent>
      </Card>

      {/* 成本趋势表格 */}
      {trend_data?.length > 0 &&
      <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle>月度明细</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">月份</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">采购金额</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">订单数量</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">平均订单额</th>
                    <th className="text-right py-3 px-4 text-slate-400 font-medium">环比增长率</th>
                  </tr>
                </thead>
                <tbody>
                  {trend_data.map((item, index) =>
                <tr key={index} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4">{item.period}</td>
                      <td className="text-right py-3 px-4 font-medium">¥{item.amount?.toLocaleString()}</td>
                      <td className="text-right py-3 px-4">{item.order_count}</td>
                      <td className="text-right py-3 px-4">¥{item.avg_amount?.toLocaleString()}</td>
                      <td className="text-right py-3 px-4">
                        {item.mom_rate !== undefined ?
                    <span className={`flex items-center justify-end gap-1 ${item.mom_rate >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {item.mom_rate >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            {item.mom_rate}%
                    </span> :
                    '-'}
                      </td>
                </tr>
                )}
                </tbody>
              </table>
            </div>
          </CardContent>
      </Card>
      }
    </div>);

}