/**
 * 供应商绩效评分卡组件
 * @component PerformanceScoreCard
 */

import React from 'react';
import { TrendingUp, Package, DollarSign, Clock, Award } from 'lucide-react';
import { Card, CardContent } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Progress } from '../../../../components/ui/progress';
import type { SupplierPerformance } from '../../../../types/purchase';

interface PerformanceScoreCardProps {
  performance: SupplierPerformance;
}

const RATING_CONFIG = {
  'A+': { color: 'bg-green-600 text-white', label: 'A+', desc: '优秀' },
  'A': { color: 'bg-green-500 text-white', label: 'A', desc: '良好' },
  'B': { color: 'bg-blue-500 text-white', label: 'B', desc: '合格' },
  'C': { color: 'bg-yellow-500 text-white', label: 'C', desc: '一般' },
  'D': { color: 'bg-red-500 text-white', label: 'D', desc: '不合格' },
};

const PerformanceScoreCard: React.FC<PerformanceScoreCardProps> = ({ performance }) => {
  const ratingConfig = RATING_CONFIG[performance.rating];

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold">{performance.supplier_name}</h3>
            <p className="text-sm text-gray-500">
              评估期间：{performance.evaluation_period} ({performance.period_start} ~ {performance.period_end})
            </p>
          </div>
          <div className="text-right">
            <Badge className={`${ratingConfig.color} px-4 py-2 text-lg`}>
              {ratingConfig.label}
            </Badge>
            <p className="text-sm text-gray-500 mt-1">{ratingConfig.desc}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* 准时交货率 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium">准时交货率</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {performance.on_time_delivery_rate.toFixed(1)}%
            </p>
            <Progress value={performance.on_time_delivery_rate} className="h-2" />
            <p className="text-xs text-gray-500">
              {performance.on_time_orders}/{performance.total_orders} 单准时
            </p>
          </div>

          {/* 质量合格率 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Package className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium">质量合格率</span>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {performance.quality_pass_rate.toFixed(1)}%
            </p>
            <Progress value={performance.quality_pass_rate} className="h-2" />
            <p className="text-xs text-gray-500">
              合格 {performance.qualified_qty} / 总 {performance.total_received_qty}
            </p>
          </div>

          {/* 价格竞争力 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium">价格竞争力</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">
              {performance.price_competitiveness.toFixed(1)}
            </p>
            <Progress value={performance.price_competitiveness} className="h-2" />
            <p className="text-xs text-gray-500">
              vs 市场 {performance.avg_price_vs_market > 0 ? '+' : ''}{performance.avg_price_vs_market.toFixed(1)}%
            </p>
          </div>

          {/* 响应速度 */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium">响应速度</span>
            </div>
            <p className="text-2xl font-bold text-orange-600">
              {performance.response_speed_score.toFixed(1)}
            </p>
            <Progress value={performance.response_speed_score} className="h-2" />
            <p className="text-xs text-gray-500">
              平均 {performance.avg_response_hours.toFixed(1)} 小时
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">综合评分</p>
            <p className="text-3xl font-bold text-blue-600">{performance.overall_score.toFixed(1)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">总订单数</p>
            <p className="text-xl font-bold">{performance.total_orders}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">总金额</p>
            <p className="text-xl font-bold">¥{performance.total_amount.toLocaleString()}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PerformanceScoreCard;
