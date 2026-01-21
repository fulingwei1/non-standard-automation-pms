/**
 * 统计卡片组件
 *
 * 显示项目阶段的关键统计指标
 */
import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { STAGE_STATUS, HEALTH_STATUS } from "../constants";

/**
 * 单个统计卡片
 */
function StatCard({ title, value, icon: Icon, color, trend, trendLabel, className }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className={cn("bg-gray-800/50 border-gray-700 hover:border-gray-600 transition-colors", className)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="p-2 rounded-lg"
                style={{ backgroundColor: `${color}20` }}
              >
                <Icon className="h-5 w-5" style={{ color }} />
              </div>
              <div>
                <p className="text-xs text-gray-400">{title}</p>
                <p className="text-2xl font-bold text-white">{value}</p>
              </div>
            </div>
            {trend !== undefined && (
              <div className={cn(
                "flex items-center gap-1 text-xs",
                trend >= 0 ? "text-green-400" : "text-red-400"
              )}>
                <TrendingUp className={cn("h-3 w-3", trend < 0 && "rotate-180")} />
                <span>{Math.abs(trend)}%</span>
                {trendLabel && <span className="text-gray-500">{trendLabel}</span>}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * 统计卡片组
 */
export function StatisticsCards({ statistics }) {
  if (!statistics) return null;

  const cards = [
    {
      title: "总项目数",
      value: statistics.total_projects || 0,
      icon: Activity,
      color: "#3B82F6",
    },
    {
      title: "进行中",
      value: statistics.in_progress_count || 0,
      icon: Clock,
      color: STAGE_STATUS.IN_PROGRESS.color,
    },
    {
      title: "已完成",
      value: statistics.completed_count || 0,
      icon: CheckCircle2,
      color: STAGE_STATUS.COMPLETED.color,
    },
    {
      title: "已延期",
      value: statistics.delayed_count || 0,
      icon: AlertTriangle,
      color: STAGE_STATUS.DELAYED.color,
    },
    {
      title: "受阻",
      value: statistics.blocked_count || 0,
      icon: XCircle,
      color: STAGE_STATUS.BLOCKED.color,
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {cards.map((card, index) => (
        <StatCard key={index} {...card} />
      ))}
    </div>
  );
}

/**
 * 进度概览卡片
 */
export function ProgressOverviewCard({ data }) {
  if (!data) return null;

  const {
    total_stages = 0,
    completed_stages = 0,
    total_nodes = 0,
    completed_nodes = 0,
    total_tasks = 0,
    completed_tasks = 0,
    overall_progress = 0,
  } = data;

  const items = [
    { label: "阶段", completed: completed_stages, total: total_stages },
    { label: "节点", completed: completed_nodes, total: total_nodes },
    { label: "任务", completed: completed_tasks, total: total_tasks },
  ].filter(item => item.total > 0);

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-300">进度概览</h3>
          <span className="text-2xl font-bold text-blue-400">
            {overall_progress.toFixed(1)}%
          </span>
        </div>

        {/* 进度条 */}
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-4">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 to-green-500"
            initial={{ width: 0 }}
            animate={{ width: `${overall_progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>

        {/* 详细统计 */}
        <div className="grid grid-cols-3 gap-4">
          {items.map((item, index) => (
            <div key={index} className="text-center">
              <p className="text-xs text-gray-400">{item.label}</p>
              <p className="text-sm font-medium text-white">
                {item.completed} / {item.total}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 按分类统计卡片
 */
export function CategoryStatsCard({ byCategory }) {
  if (!byCategory || Object.keys(byCategory).length === 0) return null;

  const categoryLabels = {
    sales: "销售阶段",
    presales: "售前阶段",
    execution: "执行阶段",
    closure: "收尾阶段",
  };

  const categoryColors = {
    sales: "#8B5CF6",
    presales: "#06B6D4",
    execution: "#3B82F6",
    closure: "#22C55E",
  };

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <h3 className="text-sm font-medium text-gray-300 mb-4">按分类统计</h3>
        <div className="space-y-3">
          {Object.entries(byCategory).map(([category, count]) => (
            <div key={category} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: categoryColors[category] || "#6B7280" }}
                />
                <span className="text-sm text-gray-300">
                  {categoryLabels[category] || category}
                </span>
              </div>
              <span className="text-sm font-medium text-white">{count}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 当前阶段分布卡片
 */
export function CurrentStageDistributionCard({ byCurrentStage }) {
  if (!byCurrentStage || Object.keys(byCurrentStage).length === 0) return null;

  // 按数量排序，取前5
  const sortedStages = Object.entries(byCurrentStage)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const total = sortedStages.reduce((sum, [, count]) => sum + count, 0);

  return (
    <Card className="bg-gray-800/50 border-gray-700">
      <CardContent className="p-4">
        <h3 className="text-sm font-medium text-gray-300 mb-4">当前阶段分布</h3>
        <div className="space-y-3">
          {sortedStages.map(([stageCode, count]) => {
            const percentage = total > 0 ? (count / total * 100).toFixed(0) : 0;
            return (
              <div key={stageCode}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-300">{stageCode}</span>
                  <span className="text-sm text-gray-400">{count} ({percentage}%)</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default StatisticsCards;
