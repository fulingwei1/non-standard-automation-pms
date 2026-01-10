import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import {
  AlertTriangle,
  TrendingDown,
  Users,
  Clock,
  DollarSign,
  BarChart2,
  PieChart,
  Info
} from 'lucide-react';

/**
 * 丢标原因配置
 */
const LOSS_REASONS = {
  PRICE_TOO_HIGH: { label: '价格过高', color: 'bg-red-500' },
  TECH_NOT_MATCH: { label: '技术不匹配', color: 'bg-orange-500' },
  DELIVERY_TOO_LONG: { label: '交期过长', color: 'bg-yellow-500' },
  COMPETITOR_ADVANTAGE: { label: '竞对优势', color: 'bg-blue-500' },
  CUSTOMER_BUDGET: { label: '客户预算', color: 'bg-purple-500' },
  CUSTOMER_CANCEL: { label: '客户取消', color: 'bg-slate-500' },
  RELATIONSHIP: { label: '关系不足', color: 'bg-pink-500' },
  OTHER: { label: '其他', color: 'bg-gray-500' }
};

/**
 * 格式化金额
 */
const formatAmount = (amount) => {
  if (!amount && amount !== 0) return '-';
  const num = parseFloat(amount);
  if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}万`;
  }
  return num.toLocaleString();
};

/**
 * 资源浪费概览卡片
 */
const ResourceWasteOverview = ({ data }) => {
  if (!data) {
    return (
      <Card className="border-slate-200">
        <CardContent className="py-8 text-center text-slate-500">
          <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>暂无数据</p>
        </CardContent>
      </Card>
    );
  }

  const {
    total_leads,
    won_leads,
    lost_leads,
    overall_win_rate,
    total_investment_hours,
    wasted_hours,
    wasted_cost,
    waste_rate
  } = data;

  const wasteRatePercent = Math.round(waste_rate * 100);

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          资源浪费概览
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* 总线索数 */}
          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <div className="text-2xl font-bold text-slate-700">{total_leads}</div>
            <div className="text-xs text-slate-500">总线索数</div>
          </div>

          {/* 中标率 */}
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {Math.round(overall_win_rate * 100)}%
            </div>
            <div className="text-xs text-slate-500">
              中标率 ({won_leads}/{won_leads + lost_leads})
            </div>
          </div>

          {/* 浪费工时 */}
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {wasted_hours?.toFixed(0) || 0}
            </div>
            <div className="text-xs text-slate-500">
              浪费工时 ({wasteRatePercent}%)
            </div>
          </div>

          {/* 浪费成本 */}
          <div className="text-center p-3 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              ¥{formatAmount(wasted_cost)}
            </div>
            <div className="text-xs text-slate-500">浪费成本</div>
          </div>
        </div>

        {/* 浪费率进度条 */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>资源利用效率</span>
            <span>{100 - wasteRatePercent}% 有效 / {wasteRatePercent}% 浪费</span>
          </div>
          <div className="flex h-4 rounded-full overflow-hidden">
            <div
              className="bg-green-500"
              style={{ width: `${100 - wasteRatePercent}%` }}
            />
            <div
              className="bg-red-400"
              style={{ width: `${wasteRatePercent}%` }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 丢标原因分布
 */
const LossReasonDistribution = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Card className="border-slate-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <PieChart className="h-5 w-5 text-slate-500" />
            丢标原因分布
          </CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-slate-500">
          <p>暂无丢标数据</p>
        </CardContent>
      </Card>
    );
  }

  const total = Object.values(data).reduce((sum, count) => sum + count, 0);
  const sortedReasons = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .map(([reason, count]) => ({
      reason,
      count,
      percent: Math.round((count / total) * 100),
      ...LOSS_REASONS[reason] || LOSS_REASONS.OTHER
    }));

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <PieChart className="h-5 w-5 text-slate-500" />
          丢标原因分布
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedReasons.map((item, index) => (
            <div key={index} className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full ${item.color}`} />
              <span className="text-sm text-slate-700 flex-1">{item.label}</span>
              <div className="w-24">
                <Progress value={item.percent} className="h-2" indicatorClassName={item.color} />
              </div>
              <span className="text-sm text-slate-500 w-16 text-right">
                {item.count}次 ({item.percent}%)
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 销售人员绩效排行
 */
const SalespersonPerformanceRanking = ({ data, type = 'waste' }) => {
  if (!data?.length) {
    return (
      <Card className="border-slate-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-5 w-5 text-slate-500" />
            销售人员绩效
          </CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-slate-500">
          <p>暂无数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-5 w-5 text-slate-500" />
            销售人员绩效
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {type === 'waste' ? '按浪费排序' : '按中标率排序'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.slice(0, 10).map((sp, index) => {
            const winRatePercent = Math.round(sp.win_rate * 100);
            const isHighPerformer = winRatePercent >= 30;

            return (
              <div
                key={sp.salesperson_id}
                className={`p-3 rounded-lg ${index < 3 && type === 'waste' ? 'bg-red-50' : 'bg-slate-50'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      index < 3 ? 'bg-red-500 text-white' : 'bg-slate-300 text-slate-700'
                    }`}>
                      {index + 1}
                    </span>
                    <span className="font-medium text-slate-700">{sp.salesperson_name}</span>
                    {sp.department && (
                      <span className="text-xs text-slate-400">{sp.department}</span>
                    )}
                  </div>
                  <Badge
                    variant={isHighPerformer ? 'default' : 'destructive'}
                    className="text-xs"
                  >
                    中标率 {winRatePercent}%
                  </Badge>
                </div>

                <div className="grid grid-cols-4 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500">总线索</span>
                    <p className="font-medium">{sp.total_leads}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">中标/丢标</span>
                    <p className="font-medium">{sp.won_leads}/{sp.lost_leads}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">浪费工时</span>
                    <p className="font-medium text-orange-600">{sp.wasted_hours?.toFixed(0) || 0}h</p>
                  </div>
                  <div>
                    <span className="text-slate-500">浪费成本</span>
                    <p className="font-medium text-red-600">¥{formatAmount(sp.wasted_cost)}</p>
                  </div>
                </div>

                {sp.top_loss_reasons?.length > 0 && (
                  <div className="mt-2 flex items-center gap-1 flex-wrap">
                    <span className="text-xs text-slate-500">主要原因:</span>
                    {sp.top_loss_reasons.map((r, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {LOSS_REASONS[r.reason]?.label || r.reason} ({r.count})
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 月度趋势
 */
const MonthlyWasteTrend = ({ data }) => {
  if (!data?.length) {
    return (
      <Card className="border-slate-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart2 className="h-5 w-5 text-slate-500" />
            月度趋势
          </CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-slate-500">
          <p>暂无趋势数据</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-slate-200">
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center gap-2">
          <BarChart2 className="h-5 w-5 text-slate-500" />
          月度趋势
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {data.map((item, index) => (
            <div key={index} className="grid grid-cols-12 gap-2 items-center text-xs">
              <span className="col-span-2 text-slate-500">{item.month}</span>
              <div className="col-span-6">
                <div className="flex h-4 rounded overflow-hidden">
                  <div
                    className="bg-green-500"
                    style={{ width: `${(1 - item.waste_rate) * 100}%` }}
                    title={`有效: ${(1 - item.waste_rate) * 100}%`}
                  />
                  <div
                    className="bg-red-400"
                    style={{ width: `${item.waste_rate * 100}%` }}
                    title={`浪费: ${item.waste_rate * 100}%`}
                  />
                </div>
              </div>
              <span className="col-span-2 text-right text-green-600">
                {Math.round(item.win_rate * 100)}%
              </span>
              <span className="col-span-2 text-right text-red-500">
                {item.wasted_hours?.toFixed(0)}h
              </span>
            </div>
          ))}
        </div>
        <div className="flex justify-end gap-4 mt-2 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded" /> 有效利用
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-400 rounded" /> 资源浪费
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

export {
  ResourceWasteOverview,
  LossReasonDistribution,
  SalespersonPerformanceRanking,
  MonthlyWasteTrend,
  formatAmount
};
