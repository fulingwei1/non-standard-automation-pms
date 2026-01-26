/**
 * 执行状态面板组件
 * 展示战略执行追踪状态
 */
import { motion } from "framer-motion";
import {
  BarChart3,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Clock,
  TrendingUp,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Badge,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn, staggerContainer } from "../../../lib/animations";
import { BSC_DIMENSIONS } from "../../../lib/constants/strategy";

export function ExecutionStatusPanel({ executionStats }) {
  if (!executionStats) {
    return (
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <BarChart3 className="w-5 h-5 text-primary" />
            执行状态追踪
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500">
            暂无执行状态数据
          </div>
        </CardContent>
      </Card>
    );
  }

  const { kpi, work, byDimension } = executionStats;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 整体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* KPI 执行状态 */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                KPI 执行状态
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">达标率</span>
                <span className="text-2xl font-bold text-emerald-400">
                  {kpi.onTrackRate.toFixed(1)}%
                </span>
              </div>
              <Progress value={kpi.onTrackRate} className="h-2" />
              <div className="grid grid-cols-4 gap-3 pt-4">
                <div className="text-center p-3 rounded-lg bg-slate-800/40">
                  <p className="text-lg font-semibold text-white">{kpi.total}</p>
                  <p className="text-xs text-slate-400">总数</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-emerald-500/10">
                  <p className="text-lg font-semibold text-emerald-400">
                    {kpi.onTrack}
                  </p>
                  <p className="text-xs text-slate-400">达标</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-amber-500/10">
                  <p className="text-lg font-semibold text-amber-400">
                    {kpi.atRisk}
                  </p>
                  <p className="text-xs text-slate-400">预警</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-red-500/10">
                  <p className="text-lg font-semibold text-red-400">
                    {kpi.offTrack}
                  </p>
                  <p className="text-xs text-slate-400">落后</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 重点工作执行状态 */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <CheckCircle2 className="w-5 h-5 text-purple-400" />
                年度重点工作
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">完成率</span>
                <span className="text-2xl font-bold text-purple-400">
                  {work.completionRate.toFixed(1)}%
                </span>
              </div>
              <Progress value={work.completionRate} className="h-2" />
              <div className="grid grid-cols-2 gap-3 pt-4">
                <div className="text-center p-3 rounded-lg bg-slate-800/40">
                  <p className="text-lg font-semibold text-white">{work.total}</p>
                  <p className="text-xs text-slate-400">总数</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-emerald-500/10">
                  <p className="text-lg font-semibold text-emerald-400">
                    {work.completed}
                  </p>
                  <p className="text-xs text-slate-400">已完成</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 各维度执行详情 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BarChart3 className="w-5 h-5 text-primary" />
              各维度执行详情
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {byDimension?.map((item) => {
                const dimConfig = BSC_DIMENSIONS[item.dimension];
                const DimIcon = dimConfig?.icon || BarChart3;
                const kpiRate =
                  item.kpi_total > 0
                    ? ((item.kpi_on_track / item.kpi_total) * 100).toFixed(1)
                    : 0;
                const workRate =
                  item.work_total > 0
                    ? ((item.work_completed / item.work_total) * 100).toFixed(1)
                    : 0;

                return (
                  <div
                    key={item.dimension}
                    className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn("p-2 rounded-lg", dimConfig?.bgColor)}
                        >
                          <DimIcon
                            className="w-4 h-4"
                            style={{ color: dimConfig?.color }}
                          />
                        </div>
                        <span className="font-medium text-white">
                          {dimConfig?.name || item.dimension}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-slate-400">KPI达标:</span>
                          <span className="text-emerald-400 font-medium">
                            {kpiRate}%
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-slate-400">工作完成:</span>
                          <span className="text-purple-400 font-medium">
                            {workRate}%
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="grid grid-cols-6 gap-2 text-xs text-center">
                      <div className="p-2 rounded bg-slate-700/50">
                        <p className="text-white font-semibold">
                          {item.kpi_total}
                        </p>
                        <p className="text-slate-400">KPI总数</p>
                      </div>
                      <div className="p-2 rounded bg-emerald-500/10">
                        <p className="text-emerald-400 font-semibold">
                          {item.kpi_on_track}
                        </p>
                        <p className="text-slate-400">达标</p>
                      </div>
                      <div className="p-2 rounded bg-amber-500/10">
                        <p className="text-amber-400 font-semibold">
                          {item.kpi_at_risk}
                        </p>
                        <p className="text-slate-400">预警</p>
                      </div>
                      <div className="p-2 rounded bg-red-500/10">
                        <p className="text-red-400 font-semibold">
                          {item.kpi_off_track}
                        </p>
                        <p className="text-slate-400">落后</p>
                      </div>
                      <div className="p-2 rounded bg-slate-700/50">
                        <p className="text-white font-semibold">
                          {item.work_total}
                        </p>
                        <p className="text-slate-400">工作总数</p>
                      </div>
                      <div className="p-2 rounded bg-purple-500/10">
                        <p className="text-purple-400 font-semibold">
                          {item.work_completed}
                        </p>
                        <p className="text-slate-400">已完成</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
