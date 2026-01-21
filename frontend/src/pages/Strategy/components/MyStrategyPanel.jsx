/**
 * 我的战略面板组件
 * 展示当前用户负责的 KPI 和年度重点工作
 */
import { motion } from "framer-motion";
import {
  User,
  Target,
  Calendar,
  CheckCircle2,
  AlertCircle,
  Clock,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Progress,
  Button,
} from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn, staggerContainer } from "../../../lib/animations";
import { getHealthConfig, ANNUAL_WORK_STATUS } from "../constants";

export function MyStrategyPanel({ myStrategy }) {
  if (!myStrategy) {
    return (
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="w-5 h-5 text-primary" />
            我的战略任务
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-slate-500">
            暂无分配的战略任务
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    my_kpis = [],
    my_annual_works = [],
    my_personal_kpis = [],
    total_kpi_count = 0,
    completed_kpi_count = 0,
  } = myStrategy;

  const kpiCompletionRate =
    total_kpi_count > 0
      ? ((completed_kpi_count / total_kpi_count) * 100).toFixed(1)
      : 0;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 个人统计 */}
      <motion.div variants={fadeIn}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-4 text-center">
              <Target className="w-6 h-6 mx-auto mb-2 text-blue-400" />
              <p className="text-2xl font-bold text-white">{my_kpis.length}</p>
              <p className="text-xs text-slate-400">负责KPI</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-4 text-center">
              <Calendar className="w-6 h-6 mx-auto mb-2 text-purple-400" />
              <p className="text-2xl font-bold text-white">
                {my_annual_works.length}
              </p>
              <p className="text-xs text-slate-400">年度工作</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-4 text-center">
              <User className="w-6 h-6 mx-auto mb-2 text-cyan-400" />
              <p className="text-2xl font-bold text-white">
                {my_personal_kpis.length}
              </p>
              <p className="text-xs text-slate-400">个人KPI</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-4 text-center">
              <TrendingUp className="w-6 h-6 mx-auto mb-2 text-emerald-400" />
              <p className="text-2xl font-bold text-emerald-400">
                {kpiCompletionRate}%
              </p>
              <p className="text-xs text-slate-400">完成率</p>
            </CardContent>
          </Card>
        </div>
      </motion.div>

      {/* 我负责的 KPI */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="w-5 h-5 text-blue-400" />
                我负责的 KPI
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {my_kpis.length} 个
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {my_kpis.length > 0 ? (
              <div className="space-y-3">
                {my_kpis.slice(0, 5).map((kpi) => {
                  const healthConfig = getHealthConfig(kpi.health_status);
                  const progress =
                    kpi.target_value > 0
                      ? ((kpi.current_value / kpi.target_value) * 100).toFixed(1)
                      : 0;

                  return (
                    <div
                      key={kpi.id}
                      className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/80 transition-all cursor-pointer"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">
                          {kpi.name}
                        </span>
                        {healthConfig && (
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs",
                              healthConfig.bgColor,
                              healthConfig.textColor
                            )}
                          >
                            {healthConfig.label}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400 mb-2">
                        <span>
                          当前: {kpi.current_value} {kpi.unit}
                        </span>
                        <span>
                          目标: {kpi.target_value} {kpi.unit}
                        </span>
                      </div>
                      <Progress value={parseFloat(progress)} className="h-1.5" />
                    </div>
                  );
                })}
                {my_kpis.length > 5 && (
                  <Button variant="ghost" className="w-full text-sm">
                    查看全部 {my_kpis.length} 个 KPI
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-slate-500">
                暂无负责的 KPI
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 我的年度工作 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Calendar className="w-5 h-5 text-purple-400" />
                我的年度工作
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {my_annual_works.length} 个
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {my_annual_works.length > 0 ? (
              <div className="space-y-3">
                {my_annual_works.slice(0, 5).map((work) => {
                  const statusConfig = ANNUAL_WORK_STATUS[work.status];
                  const StatusIcon = statusConfig?.icon || Clock;

                  return (
                    <div
                      key={work.id}
                      className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/80 transition-all cursor-pointer"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">
                          {work.name}
                        </span>
                        {statusConfig && (
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs flex items-center gap-1",
                              work.status === "COMPLETED"
                                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                                : work.status === "IN_PROGRESS"
                                ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                                : work.status === "DELAYED"
                                ? "bg-red-500/20 text-red-400 border-red-500/30"
                                : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                            )}
                          >
                            <StatusIcon className="w-3 h-3" />
                            {statusConfig.label}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400 mb-2">
                        <span>
                          {work.start_date} ~ {work.end_date}
                        </span>
                        <span>进度: {work.progress || 0}%</span>
                      </div>
                      <Progress value={work.progress || 0} className="h-1.5" />
                    </div>
                  );
                })}
                {my_annual_works.length > 5 && (
                  <Button variant="ghost" className="w-full text-sm">
                    查看全部 {my_annual_works.length} 项工作
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-slate-500">
                暂无年度工作
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 我的个人 KPI */}
      {my_personal_kpis.length > 0 && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <User className="w-5 h-5 text-cyan-400" />
                  我的个人 KPI
                </CardTitle>
                <Badge variant="outline" className="text-xs">
                  {my_personal_kpis.length} 个
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {my_personal_kpis.slice(0, 5).map((pkpi) => (
                  <div
                    key={pkpi.id}
                    className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/80 transition-all cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">
                        {pkpi.name}
                      </span>
                      <span className="text-xs text-slate-400">
                        权重: {pkpi.weight}%
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span>目标: {pkpi.target_value}</span>
                      {pkpi.self_rating && (
                        <span>自评: {pkpi.self_rating}分</span>
                      )}
                      {pkpi.manager_rating && (
                        <span className="text-emerald-400">
                          主管评: {pkpi.manager_rating}分
                        </span>
                      )}
                    </div>
                  </div>
                ))}
                {my_personal_kpis.length > 5 && (
                  <Button variant="ghost" className="w-full text-sm">
                    查看全部 {my_personal_kpis.length} 个个人 KPI
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
