/**
 * 多年趋势图组件
 * 展示战略执行的多年趋势分析
 */
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus, BarChart3, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Badge } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn, staggerContainer } from "../../../lib/animations";
import { CHART_COLORS } from "../../../lib/constants/strategy";

export function MultiYearTrendChart({ trendData }) {
  if (!trendData || !trendData.years || trendData.years.length === 0) {
    return (
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="w-5 h-5 text-primary" />
            多年趋势分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500">
            暂无历史趋势数据
          </div>
        </CardContent>
      </Card>
    );
  }

  const { years, metrics } = trendData;

  // 计算趋势
  const getTrend = (values) => {
    if (!values || values.length < 2) return 0;
    const latest = values[values.length - 1] || 0;
    const previous = values[values.length - 2] || 0;
    if (previous === 0) return 0;
    return ((latest - previous) / previous) * 100;
  };

  const TrendIcon = ({ value }) => {
    if (value > 0) return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (value < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  // 简单的柱状图渲染
  const renderBar = (value, maxValue, color) => {
    const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
    return (
      <div
        className="w-full rounded-t transition-all duration-500"
        style={{
          height: `${Math.max(height, 5)}%`,
          backgroundColor: color,
        }}
      />
    );
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 年度对比图表 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="w-5 h-5 text-primary" />
              年度战略执行对比
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* 健康度趋势 */}
              {metrics?.health_scores && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">健康度评分趋势</span>
                    <div className="flex items-center gap-1">
                      <TrendIcon value={getTrend(metrics.health_scores)} />
                      <span
                        className={cn(
                          "text-sm",
                          getTrend(metrics.health_scores) >= 0
                            ? "text-emerald-400"
                            : "text-red-400"
                        )}
                      >
                        {Math.abs(getTrend(metrics.health_scores)).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-end gap-4 h-32 px-4">
                    {years.map((year, idx) => (
                      <div key={year} className="flex-1 flex flex-col items-center">
                        <div className="w-full h-24 flex items-end justify-center">
                          {renderBar(
                            metrics.health_scores[idx] || 0,
                            100,
                            CHART_COLORS.primary
                          )}
                        </div>
                        <span className="text-xs text-slate-400 mt-2">{year}</span>
                        <span className="text-xs text-white font-medium">
                          {metrics.health_scores[idx]?.toFixed(1) || 0}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* KPI 达标率趋势 */}
              {metrics?.kpi_achievement_rates && (
                <div className="space-y-2 pt-4 border-t border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">KPI达标率趋势</span>
                    <div className="flex items-center gap-1">
                      <TrendIcon value={getTrend(metrics.kpi_achievement_rates)} />
                      <span
                        className={cn(
                          "text-sm",
                          getTrend(metrics.kpi_achievement_rates) >= 0
                            ? "text-emerald-400"
                            : "text-red-400"
                        )}
                      >
                        {Math.abs(getTrend(metrics.kpi_achievement_rates)).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-end gap-4 h-32 px-4">
                    {years.map((year, idx) => (
                      <div key={year} className="flex-1 flex flex-col items-center">
                        <div className="w-full h-24 flex items-end justify-center">
                          {renderBar(
                            metrics.kpi_achievement_rates[idx] || 0,
                            100,
                            CHART_COLORS.success
                          )}
                        </div>
                        <span className="text-xs text-slate-400 mt-2">{year}</span>
                        <span className="text-xs text-white font-medium">
                          {metrics.kpi_achievement_rates[idx]?.toFixed(1) || 0}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 工作完成率趋势 */}
              {metrics?.work_completion_rates && (
                <div className="space-y-2 pt-4 border-t border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">工作完成率趋势</span>
                    <div className="flex items-center gap-1">
                      <TrendIcon value={getTrend(metrics.work_completion_rates)} />
                      <span
                        className={cn(
                          "text-sm",
                          getTrend(metrics.work_completion_rates) >= 0
                            ? "text-emerald-400"
                            : "text-red-400"
                        )}
                      >
                        {Math.abs(getTrend(metrics.work_completion_rates)).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-end gap-4 h-32 px-4">
                    {years.map((year, idx) => (
                      <div key={year} className="flex-1 flex flex-col items-center">
                        <div className="w-full h-24 flex items-end justify-center">
                          {renderBar(
                            metrics.work_completion_rates[idx] || 0,
                            100,
                            CHART_COLORS.purple
                          )}
                        </div>
                        <span className="text-xs text-slate-400 mt-2">{year}</span>
                        <span className="text-xs text-white font-medium">
                          {metrics.work_completion_rates[idx]?.toFixed(1) || 0}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 年度详情卡片 */}
      <motion.div variants={fadeIn}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {years.map((year, idx) => (
            <Card
              key={year}
              className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50"
            >
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Calendar className="w-4 h-4 text-primary" />
                  {year}年度
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">健康度</span>
                  <span className="text-lg font-bold text-white">
                    {metrics?.health_scores?.[idx]?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">KPI达标率</span>
                  <span className="text-lg font-bold text-emerald-400">
                    {metrics?.kpi_achievement_rates?.[idx]?.toFixed(1) || 0}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">工作完成率</span>
                  <span className="text-lg font-bold text-purple-400">
                    {metrics?.work_completion_rates?.[idx]?.toFixed(1) || 0}%
                  </span>
                </div>
                {metrics?.kpi_counts && (
                  <div className="flex items-center justify-between pt-2 border-t border-slate-700/50">
                    <span className="text-sm text-slate-400">KPI数量</span>
                    <Badge variant="outline">{metrics.kpi_counts[idx] || 0}</Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
