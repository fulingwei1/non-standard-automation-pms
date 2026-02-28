/**
 * Satisfaction Analytics Component (Refactored to shadcn/Tailwind)
 * 满意度分析组件
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Badge,
} from "../ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { CHART_COLORS, SATISFACTION_LEVELS } from "@/lib/constants/customer";

const SatisfactionAnalytics = ({
  surveys = [],
  responses = [],
  loading = false,
}) => {
  const stats = useMemo(() => {
    const surveyCount = surveys.length;
    const responseCount = responses.length;
    const avgScore =
      responseCount > 0
        ? (responses || []).reduce(
            (acc, r) => acc + Number(r.satisfactionLevel || 0),
            0
          ) / responseCount
        : 0;

    const dist = {};
    Object.keys(SATISFACTION_LEVELS).forEach((k) => (dist[k] = 0));
    (responses || []).forEach((r) => {
      const hit = Object.entries(SATISFACTION_LEVELS).find(
        ([_, cfg]) => cfg.value === r.satisfactionLevel
      );
      if (hit) {
        dist[hit[0]] += 1;
      }
    });

    return { surveyCount, responseCount, avgScore, dist };
  }, [responses, surveys.length]);

  const getLevelConfig = (level) => {
    const config = SATISFACTION_LEVELS[level];
    if (!config)
      return {
        icon: "😐",
        label: "未知",
        color: "text-slate-400",
        bgColor: "bg-slate-500/20",
        borderColor: "border-slate-500/30",
        progressColor: "bg-slate-500",
      };

    const colorMap = {
      "#52c41a": {
        bg: "bg-emerald-500/20",
        text: "text-emerald-400",
        border: "border-emerald-500/30",
        progress: "bg-emerald-500",
      },
      "#1890ff": {
        bg: "bg-blue-500/20",
        text: "text-blue-400",
        border: "border-blue-500/30",
        progress: "bg-blue-500",
      },
      "#faad14": {
        bg: "bg-amber-500/20",
        text: "text-amber-400",
        border: "border-amber-500/30",
        progress: "bg-amber-500",
      },
      "#ff7a45": {
        bg: "bg-orange-500/20",
        text: "text-orange-400",
        border: "border-orange-500/30",
        progress: "bg-orange-500",
      },
      "#ff4d4f": {
        bg: "bg-red-500/20",
        text: "text-red-400",
        border: "border-red-500/30",
        progress: "bg-red-500",
      },
    };

    const colors = colorMap[config.color] || colorMap["#1890ff"];

    return {
      icon: config.icon,
      label: config.label,
      color: colors.text,
      bgColor: colors.bg,
      borderColor: colors.border,
      progressColor: colors.progress,
    };
  };

  const StatCard = ({ title, value, suffix, trend }) => (
    <Card className="bg-slate-900/50 border-white/10">
      <CardContent className="p-4">
        <div>
          <p className="text-xs text-slate-400 mb-1">{title}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-white">{value}</span>
            {suffix && <span className="text-sm text-slate-400">{suffix}</span>}
          </div>
          {trend && (
            <div
              className={cn(
                "flex items-center gap-1 text-xs mt-1",
                trend > 0 ? "text-emerald-400" : "text-red-400"
              )}
            >
              {trend > 0 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              <span>{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  if (loading && responses.length === 0) {
    return (
      <Card className="bg-slate-900/50 border-white/10">
        <CardContent className="p-8 text-center">
          <div className="animate-pulse text-slate-400">加载中...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="调查数量" value={stats.surveyCount} />
        <StatCard title="反馈数量" value={stats.responseCount} />
        <StatCard
          title="平均满意度"
          value={stats.avgScore.toFixed(2)}
          suffix="/5.0"
          trend={5.2}
        />
      </motion.div>

      {/* 满意度分布 */}
      <Card className="bg-slate-900/50 border-white/10">
        <CardHeader>
          <CardTitle className="text-white text-lg">满意度分布</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(stats.dist).map(([key, count]) => {
            const config = getLevelConfig(key);
            const percent =
              stats.responseCount > 0
                ? (count / stats.responseCount) * 100
                : 0;

            return (
              <motion.div
                key={key}
                variants={fadeIn}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{config.icon}</span>
                    <span className={cn("text-sm font-medium", config.color)}>
                      {config.label}
                    </span>
                    <span className="text-xs text-slate-500">
                      {count} 条
                    </span>
                  </div>
                  <span className="text-sm text-slate-400">
                    {percent.toFixed(1)}%
                  </span>
                </div>
                <Progress
                  value={Number(percent.toFixed(1))}
                  className="h-2"
                  indicatorClassName={config.progressColor}
                />
              </motion.div>
            );
          })}

          {stats.responseCount === 0 && (
            <div className="text-center py-8 text-slate-400">
              暂无反馈数据
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default SatisfactionAnalytics;
