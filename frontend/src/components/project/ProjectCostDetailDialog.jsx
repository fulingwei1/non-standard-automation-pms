import { useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { formatCurrency, formatPercent, generateCostChartData, getCostStatus } from '../../lib/utils/cost';
import { TrendingUp, TrendingDown, AlertCircle, DollarSign } from 'lucide-react';

/**
 * 项目成本明细弹窗
 */
export default function ProjectCostDetailDialog({ open, onOpenChange, project }) {
  const costSummary = project?.cost_summary;
  const costBreakdown = costSummary?.cost_breakdown;

  // 生成饼图数据
  const chartData = useMemo(() => {
    if (!costBreakdown) return [];
    return generateCostChartData(costBreakdown);
  }, [costBreakdown]);

  // 获取成本状态
  const costStatus = getCostStatus(costSummary);

  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-slate-800 border border-white/10 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium mb-1">{data.name}</p>
          <p className="text-slate-300 text-sm">
            金额: {formatCurrency(data.value)}
          </p>
          <p className="text-slate-400 text-xs">
            占比: {((data.value / costSummary.total_cost) * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (!project || !costSummary) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl bg-slate-900/95 backdrop-blur-xl border-white/10">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-white">
            成本明细 - {project.project_name}
          </DialogTitle>
          <p className="text-slate-400 text-sm mt-1">
            项目编号: {project.project_code}
          </p>
        </DialogHeader>

        <div className="space-y-6">
          {/* 成本概览 */}
          <div className="grid grid-cols-3 gap-4">
            {/* 总成本 */}
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 rounded-xl p-4 border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-5 w-5 text-blue-400" />
                <span className="text-slate-400 text-sm">总成本</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(costSummary.total_cost)}
              </p>
            </div>

            {/* 预算 */}
            <div className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 rounded-xl p-4 border border-emerald-500/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-emerald-400" />
                <span className="text-slate-400 text-sm">预算</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(costSummary.budget)}
              </p>
            </div>

            {/* 差异 */}
            <div className={`bg-gradient-to-br rounded-xl p-4 border ${
              costSummary.overrun 
                ? 'from-red-500/10 to-red-600/5 border-red-500/20' 
                : 'from-emerald-500/10 to-emerald-600/5 border-emerald-500/20'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                {costSummary.overrun ? (
                  <AlertCircle className="h-5 w-5 text-red-400" />
                ) : (
                  <TrendingDown className="h-5 w-5 text-emerald-400" />
                )}
                <span className="text-slate-400 text-sm">差异</span>
              </div>
              <p className={`text-2xl font-bold ${
                costSummary.overrun ? 'text-red-400' : 'text-emerald-400'
              }`}>
                {costSummary.variance > 0 ? '+' : ''}{formatCurrency(costSummary.variance)}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {costSummary.variance_pct > 0 ? '+' : ''}{formatPercent(costSummary.variance_pct)}
              </p>
            </div>
          </div>

          {/* 预算使用率 */}
          <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5">
            <div className="flex justify-between items-center mb-3">
              <span className="text-slate-400 text-sm">预算使用率</span>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-white">
                  {formatPercent(costSummary.budget_used_pct, 1)}
                </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  costStatus.status === 'danger' 
                    ? 'bg-red-500/20 text-red-300'
                    : costStatus.status === 'warning'
                    ? 'bg-yellow-500/20 text-yellow-300'
                    : 'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {costStatus.label}
                </span>
              </div>
            </div>
            <div className="relative w-full h-3 bg-white/5 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all duration-500 ${
                  costSummary.overrun 
                    ? 'bg-red-500' 
                    : costSummary.budget_used_pct >= 90
                    ? 'bg-yellow-500'
                    : costSummary.budget_used_pct >= 80
                    ? 'bg-amber-500'
                    : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(costSummary.budget_used_pct, 100)}%` }}
              />
            </div>
          </div>

          {/* 成本明细 */}
          <div className="grid grid-cols-2 gap-6">
            {/* 饼图 */}
            {chartData.length > 0 && (
              <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5">
                <h3 className="text-white font-semibold mb-4">成本结构</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* 明细表 */}
            <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5">
              <h3 className="text-white font-semibold mb-4">成本明细</h3>
              <div className="space-y-3">
                {[
                  { label: '人工成本', value: costBreakdown?.labor, color: 'bg-blue-500' },
                  { label: '材料成本', value: costBreakdown?.material, color: 'bg-emerald-500' },
                  { label: '设备成本', value: costBreakdown?.equipment, color: 'bg-amber-500' },
                  { label: '差旅成本', value: costBreakdown?.travel, color: 'bg-purple-500' },
                  { label: '其他成本', value: costBreakdown?.other, color: 'bg-gray-500' },
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${item.color}`} />
                      <span className="text-slate-300 text-sm">{item.label}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-medium">
                        {formatCurrency(item.value || 0)}
                      </p>
                      {costSummary.total_cost > 0 && (
                        <p className="text-xs text-slate-500">
                          {formatPercent((item.value || 0) / costSummary.total_cost * 100, 1)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 提示信息 */}
          {costSummary.overrun && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-red-300 font-medium mb-1">项目已超支</p>
                  <p className="text-red-200/80 text-sm">
                    实际成本超出预算 {formatCurrency(Math.abs(costSummary.variance))}
                    （{formatPercent(Math.abs(costSummary.variance_pct))}），
                    请及时采取成本控制措施。
                  </p>
                </div>
              </div>
            </div>
          )}

          {!costSummary.overrun && costSummary.budget_used_pct >= 90 && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-yellow-300 font-medium mb-1">预算即将用尽</p>
                  <p className="text-yellow-200/80 text-sm">
                    当前预算使用率已达 {formatPercent(costSummary.budget_used_pct, 1)}，
                    剩余预算仅 {formatCurrency(costSummary.budget - costSummary.total_cost)}，
                    请注意控制成本。
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
