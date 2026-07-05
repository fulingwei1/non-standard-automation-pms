/**
 * TeamRankingBoard - 团队业绩排名组件
 * 显示销售业绩排名表格和指标权重配置
 */

import { motion } from "framer-motion";
import { Award } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Button,
  Progress,
} from "../../../ui";
import { cn } from "../../../../lib/utils";
import {
  formatMetricValueDisplay,
  formatMetricScoreDisplay,
  buildMetricDetailMap,
  formatDateTime,
} from "@/lib/constants/salesTeam";

export default function TeamRankingBoard({
  rankingData,
  rankingConfig,
  rankingType,
  onRankingTypeChange,
  filters,
  onConfigClick,
  loading,
  metricConfigList,
  rankingOptions,
  selectedRankingOption,
}) {
  return (
    <motion.div variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}>
      <Card className="border border-slate-700/70 bg-slate-900/40">
        <CardHeader>
          <div className="flex flex-col gap-4">
            {/* 标题和操作区 */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/40">
                  <Award className="h-5 w-5 text-amber-400" />
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2 text-base text-white">
                    销售业绩排名
                    <Badge
                      variant="outline"
                      className="bg-slate-800/80 text-xs border-slate-600 text-slate-200"
                    >
                      {rankingData.length} 名成员
                    </Badge>
                  </CardTitle>
                  <p className="text-xs text-slate-500 mt-1">
                    模型支持综合评分与多指标排名，由销售总监维护权重
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <select
                  value={rankingType}
                  onChange={(e) => onRankingTypeChange(e.target.value)}
                  className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {(rankingOptions || []).map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={onConfigClick}
                >
                  权重配置
                </Button>
              </div>
            </div>

            {/* 统计信息 */}
            <div className="flex flex-wrap gap-3 text-xs text-slate-500">
              <span>
                统计区间：{filters.startDate} ~ {filters.endDate}
              </span>
              {selectedRankingOption && (
                <span className="text-emerald-400">
                  当前排序：{selectedRankingOption.label}
                </span>
              )}
              {rankingConfig?.updated_at && (
                <span>
                  最新调整：
                  {formatDateTime(rankingConfig.updated_at)}
                </span>
              )}
            </div>

            {/* 指标权重配置 */}
            {metricConfigList.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {(metricConfigList || []).map((metric) => (
                  <div
                    key={`${metric.key}-${metric.data_source}`}
                    className="p-3 rounded-lg border border-slate-700/60 bg-slate-800/50"
                  >
                    <div className="flex items-center justify-between text-sm text-slate-200">
                      <span>{metric.label}</span>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[11px]",
                          metric.is_primary
                            ? "text-amber-300 border-amber-400/50"
                            : "text-slate-400 border-slate-600",
                        )}
                      >
                        {(Number(metric.weight || 0) * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <Progress
                      value={Number(metric.weight || 0) * 100}
                      className="h-1.5 bg-slate-700/60 mt-2"
                    />
                    <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                      <span>
                        {metric.is_primary ? "核心指标" : "辅助指标"}
                      </span>
                      <span>{metric.data_source}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardHeader>

        {/* 排名表格 */}
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : rankingData.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              暂无排名数据
            </div>
          ) : (
            <div className="overflow-x-auto -mx-4 md:mx-0">
              <table className="min-w-full divide-y divide-slate-700/60 text-sm">
                <thead>
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                      排名
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                      成员
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">
                      综合得分
                    </th>
                    {(metricConfigList || []).map((metric) => (
                      <th
                        key={`header-${metric.key}`}
                        className="px-3 py-2 text-left text-xs font-semibold text-slate-400 whitespace-nowrap"
                      >
                        <div className="text-slate-300">
                          {metric.label}
                        </div>
                        <div className="text-[11px] text-slate-500">
                          权重 {(Number(metric.weight || 0) * 100).toFixed(0)}%
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {(rankingData || []).map((item, index) => {
                    const metricMap = buildMetricDetailMap(
                      item.metrics || [],
                    );
                    return (
                      <tr
                        key={item.user_id}
                        className={cn(
                          "hover:bg-slate-800/40 transition-colors",
                          index === 0 && "bg-amber-500/5",
                          index === 1 && "bg-blue-500/5",
                          index === 2 && "bg-purple-500/5",
                        )}
                      >
                        <td className="px-3 py-3 text-base font-semibold text-white">
                          {item.rank}
                        </td>
                        <td className="px-3 py-3">
                          <div className="font-medium text-white">
                            {item.user_name}
                          </div>
                          <div className="text-xs text-slate-400">
                            {item.department_name || "未分配"}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-emerald-400 font-semibold whitespace-nowrap">
                          {Number(item.score || 0).toFixed(1)} 分
                        </td>
                        {(metricConfigList || []).map((metric) => {
                          const detail =
                            metricMap[metric.key] ||
                            metricMap[metric.data_source];
                          const isSortMetric =
                            rankingType === (metric.data_source || metric.key);
                          return (
                            <td
                              key={`${item.user_id}-${metric.key}`}
                              className={cn(
                                "px-3 py-3 text-xs whitespace-nowrap",
                                isSortMetric && "text-emerald-300",
                              )}
                            >
                              <div className="font-semibold text-white">
                                {formatMetricValueDisplay(detail, metric)}
                              </div>
                              <div className="text-[11px] text-slate-500">
                                {formatMetricScoreDisplay(detail)}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
