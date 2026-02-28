/**
 * Customer Satisfaction Overview Component (Refactored to shadcn/Tailwind)
 * 客户满意度概览组件
 */

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Smile,
  Meh,
  Frown,
  Trophy,
  TrendingUp,
  TrendingDown,
  User,
  Star,
  FilePlus,
  BarChart3,
  MessageSquareWarning,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Progress,
  Button,
} from "../ui";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import {
  SATISFACTION_LEVELS,
  SURVEY_STATUS,
  CHART_COLORS,
  satisfactionScoreConfig,
} from "@/lib/constants/customer";

const CustomerSatisfactionOverview = ({ data, loading, onRefresh: _onRefresh }) => {
  const [_selectedPeriod, _setSelectedPeriod] = useState("month");

  const overviewStats = useMemo(() => {
    if (!data?.surveys) {
      return {};
    }

    const totalSurveys = data.surveys?.length;
    const completedSurveys = (data.surveys || []).filter(
      (s) => s.status === "completed"
    ).length;
    const avgScore =
      (data.surveys || []).reduce((acc, s) => acc + (s.avgScore || 0), 0) /
        totalSurveys || 0;
    const responseRate =
      ((completedSurveys / totalSurveys) * 100).toFixed(1);

    return {
      totalSurveys,
      completedSurveys,
      avgScore: avgScore.toFixed(1),
      responseRate,
      trend: data.trend || { direction: "up", percentage: 5.2 },
    };
  }, [data]);

  const satisfactionDistribution = useMemo(() => {
    if (!data?.responses) {
      return {};
    }

    const distribution = {};
    Object.keys(SATISFACTION_LEVELS).forEach((key) => {
      distribution[key] = 0;
    });

    (data.responses || []).forEach((response) => {
      const level = Object.entries(SATISFACTION_LEVELS).find(
        ([_, config]) => config.value === response.satisfactionLevel
      );
      if (level) {
        distribution[level[0]]++;
      }
    });

    return distribution;
  }, [data]);

  const totalResponses = data?.responses?.length || 0;

  const getLevelConfig = (level) => {
    const config = SATISFACTION_LEVELS[level];
    if (!config)
      return {
        icon: Meh,
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
    const iconMap = {
      VERY_SATISFIED: Smile,
      SATISFIED: Smile,
      NEUTRAL: Meh,
      DISSATISFIED: Frown,
      VERY_DISSATISFIED: Frown,
    };

    return {
      icon: iconMap[level] || Meh,
      label: config.label,
      color: colors.text,
      bgColor: colors.bg,
      borderColor: colors.border,
      progressColor: colors.progress,
    };
  };

  const StatCard = ({ title, value, suffix, icon: Icon, trend, color }) => (
    <Card className="bg-slate-900/50 border-white/10">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
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
                  trend.direction === "up"
                    ? "text-emerald-400"
                    : "text-red-400"
                )}
              >
                {trend.direction === "up" ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span>{trend.percentage}%</span>
              </div>
            )}
          </div>
          {Icon && (
            <div className={cn("p-2 rounded-lg", color)}>
              <Icon className="w-5 h-5" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 关键指标卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="平均满意度"
          value={overviewStats.avgScore}
          suffix="/ 5.0"
          icon={Star}
          color="bg-blue-500/20 text-blue-400"
        />
        <StatCard
          title="完成调查数"
          value={overviewStats.completedSurveys}
          suffix={`/ ${overviewStats.totalSurveys}`}
          icon={Trophy}
          color="bg-emerald-500/20 text-emerald-400"
        />
        <StatCard
          title="响应率"
          value={overviewStats.responseRate}
          suffix="%"
          icon={User}
          color="bg-amber-500/20 text-amber-400"
        />
        <StatCard
          title="满意度趋势"
          value={overviewStats.trend.percentage}
          suffix="%"
          icon={overviewStats.trend.direction === "up" ? TrendingUp : TrendingDown}
          trend={overviewStats.trend}
          color={
            overviewStats.trend.direction === "up"
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-red-500/20 text-red-400"
          }
        />
      </motion.div>

      {/* 满意度分布 */}
      <Card className="bg-slate-900/50 border-white/10">
        <CardHeader>
          <CardTitle className="text-white text-lg">满意度分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            {Object.entries(satisfactionDistribution).map(([level, count]) => {
              const config = getLevelConfig(level);
              const Icon = config.icon;
              const percentage =
                totalResponses > 0 ? ((count / totalResponses) * 100).toFixed(1) : 0;

              return (
                <motion.div
                  key={level}
                  variants={fadeIn}
                  className="p-4 bg-slate-800/50 rounded-lg border border-white/5 text-center"
                >
                  <Icon className={cn("w-8 h-8 mx-auto mb-2", config.color)} />
                  <div className={cn("text-xl font-bold", config.color)}>{count}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    {config.label} ({percentage}%)
                  </div>
                  <Progress
                    value={parseFloat(percentage)}
                    className={cn("h-1.5 mt-2", config.progressColor)}
                    indicatorClassName={config.progressColor}
                  />
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card className="bg-slate-900/50 border-white/10">
        <CardHeader>
          <CardTitle className="text-white text-lg">快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-white/5 hover:border-emerald-500/30 transition-colors cursor-pointer group">
                <CardContent className="p-6 text-center">
                  <FilePlus className="w-10 h-10 mx-auto mb-3 text-emerald-400 group-hover:scale-110 transition-transform" />
                  <div className="font-medium text-white mb-1">创建新调查</div>
                  <div className="text-xs text-slate-400">
                    设计新的满意度调查问卷
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-white/5 hover:border-blue-500/30 transition-colors cursor-pointer group">
                <CardContent className="p-6 text-center">
                  <BarChart3 className="w-10 h-10 mx-auto mb-3 text-blue-400 group-hover:scale-110 transition-transform" />
                  <div className="font-medium text-white mb-1">查看分析报告</div>
                  <div className="text-xs text-slate-400">
                    详细的满意度数据分析
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-white/5 hover:border-red-500/30 transition-colors cursor-pointer group">
                <CardContent className="p-6 text-center">
                  <MessageSquareWarning className="w-10 h-10 mx-auto mb-3 text-red-400 group-hover:scale-110 transition-transform" />
                  <div className="font-medium text-white mb-1">处理负面反馈</div>
                  <div className="text-xs text-slate-400">
                    回复和处理不满意反馈
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default CustomerSatisfactionOverview;
