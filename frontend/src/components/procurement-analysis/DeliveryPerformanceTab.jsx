/**
 * 供应商交期准时率分析 Tab 组件
 * 显示供应商交期绩效统计和排名
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import ProcurementStatsCard from './ProcurementStatsCard';
import { STATS_CARD_CONFIGS, getOnTimeRateRating, getOnTimeRateBadgeColor } from '@/lib/constants/procurementAnalysis';

/**
 * 交期准时率 Tab 组件
 * @param {object} props
 * @param {object} props.data - 交期准时率数据
 */
export default function DeliveryPerformanceTab({ data }) {
  const { summary, supplier_performance } = data || {};

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <ProcurementStatsCard
            label={STATS_CARD_CONFIGS.deliveryPerformance[0].label}
            value={summary.total_suppliers}
            icon={STATS_CARD_CONFIGS.deliveryPerformance[0].icon}
            color={STATS_CARD_CONFIGS.deliveryPerformance[0].color}
          />
          <ProcurementStatsCard
            label={STATS_CARD_CONFIGS.deliveryPerformance[1].label}
            value={summary.avg_on_time_rate}
            icon={STATS_CARD_CONFIGS.deliveryPerformance[1].icon}
            color={STATS_CARD_CONFIGS.deliveryPerformance[1].color}
            suffix={STATS_CARD_CONFIGS.deliveryPerformance[1].suffix}
          />
          <ProcurementStatsCard
            label={STATS_CARD_CONFIGS.deliveryPerformance[2].label}
            value={summary.total_delayed_orders}
            icon={STATS_CARD_CONFIGS.deliveryPerformance[2].icon}
            color={STATS_CARD_CONFIGS.deliveryPerformance[2].color}
          />
          <ProcurementStatsCard
            label={STATS_CARD_CONFIGS.deliveryPerformance[3].label}
            value={null}
            icon={STATS_CARD_CONFIGS.deliveryPerformance[3].icon}
            color={STATS_CARD_CONFIGS.deliveryPerformance[3].color}
            rating={summary.avg_on_time_rate !== undefined ? (
              <span className={getOnTimeRateRating(summary.avg_on_time_rate).color}>
                {getOnTimeRateRating(summary.avg_on_time_rate).label}
              </span>
            ) : null}
          />
        </div>
      )}

      {/* 供应商绩效表格 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle>供应商交期绩效排名</CardTitle>
          <CardDescription>按准时率降序排列</CardDescription>
        </CardHeader>
        <CardContent>
          {supplier_performance?.length > 0 ? (
            <div className="space-y-3">
              {(supplier_performance || []).map((item, index) => (
                <div key={item.supplier_id} className="flex items-center gap-4 p-4 bg-slate-700/30 rounded-lg">
                  <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{item.supplier_name}</div>
                    <div className="text-xs text-slate-400">{item.supplier_code}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-slate-400">交货总数</div>
                    <div className="font-medium">{item.total_deliveries}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-slate-400">准时交货</div>
                    <div className="font-medium text-emerald-400">{item.on_time_deliveries}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-slate-400">延期交货</div>
                    <div className="font-medium text-red-400">{item.delayed_deliveries}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-slate-400">准时率</div>
                    <Badge className={getOnTimeRateBadgeColor(item.on_time_rate)}>
                      {item.on_time_rate}%
                    </Badge>
                  </div>
                  {item.avg_delay_days > 0 && (
                    <div className="text-center">
                      <div className="text-sm text-slate-400">平均延期</div>
                      <div className="font-medium text-amber-400">{item.avg_delay_days}天</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
