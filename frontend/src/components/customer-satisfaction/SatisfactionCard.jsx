/**
 * Customer Satisfaction Card Component
 * 客户满意度卡片组件 - 展示单个客户满意度信息
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Star,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  ThumbsUp,
  ThumbsDown,
  AlertCircle,
  Info,
  ChevronUp,
  ChevronDown,
  RefreshCw } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import {
  getSatisfactionScoreConfig,
  getFeedbackTypeConfig as _getFeedbackTypeConfig,
  getPriorityConfig as _getPriorityConfig,
  getFeedbackStatusConfig as _getFeedbackStatusConfig,
  formatSatisfactionScore,
  getSatisfactionColor as _getSatisfactionColor,
  satisfactionConstants } from
"@/lib/constants/customer";import { cn } from "../../lib/utils";

export const SatisfactionCard = ({
  satisfaction = satisfactionConstants.DEFAULT_SATISFACTION_STATS,
  className = "",
  showDetails = true,
  onExpand = null,
  onRefresh = null,
  loading = false,
  lastUpdated = null
}) => {
  const [expanded, setExpanded] = useState(false);

  // 处理展开/收起
  const handleExpand = () => {
    if (onExpand) {
      onExpand(!expanded);
    } else {
      setExpanded(!expanded);
    }
  };

  // 计算满意度趋势指示器
  const satisfactionTrend = useMemo(() => {
    if (satisfaction.previousScore) {
      const diff = satisfaction.averageScore - satisfaction.previousScore;
      if (diff > 0.1) {return { trend: "up", color: "text-emerald-400" };}
      if (diff < -0.1) {return { trend: "down", color: "text-red-400" };}
      return { trend: "stable", color: "text-slate-400" };
    }
    return { trend: "stable", color: "text-slate-400" };
  }, [satisfaction]);

  // 计算满意度等级
  const satisfactionLevel = useMemo(() => {
    return getSatisfactionScoreConfig(satisfaction.averageScore);
  }, [satisfaction.averageScore]);

  // 统计卡片数据
  const statsCards = useMemo(() => [
  {
    title: "总评价数",
    value: satisfaction.totalResponses || 0,
    icon: Star,
    color: "from-blue-500/10 to-cyan-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400"
  },
  {
    title: "平均评分",
    value: formatSatisfactionScore(satisfaction.averageScore),
    subtitle: satisfactionLevel.label,
    icon: ThumbsUp,
    color: satisfaction.progress,
    iconBg: satisfaction.progress.replace("bg-", "bg-").replace("/500", "/20"),
    iconColor: satisfactionLevel.color.replace("text-", "text-")
  },
  {
    title: "正面反馈",
    value: `${satisfaction.positiveRate || 0}%`,
    icon: TrendingUp,
    color: "from-emerald-500/10 to-green-500/5 border-emerald-500/20",
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400",
    progress: satisfaction.positiveRate || 0
  },
  {
    title: "响应率",
    value: `${satisfaction.responseRate || 0}%`,
    icon: Users,
    color: "from-purple-500/10 to-pink-500/5 border-purple-500/20",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400",
    progress: satisfaction.responseRate || 0
  }],
  [satisfaction, satisfactionLevel]);

  // 处理状态显示
  const renderStatusBadge = () => {
    if (loading) {
      return (
        <Badge variant="outline" className="text-slate-400 border-slate-300">
          <Clock className="w-3 h-3 mr-1 animate-spin" />
          加载中...
        </Badge>);

    }

    if (lastUpdated) {
      return (
        <Badge variant="outline" className="text-slate-400 border-slate-300">
          <Clock className="w-3 h-3 mr-1" />
          {lastUpdated}
        </Badge>);

    }

    return (
      <Badge variant="outline" className="text-emerald-400 border-emerald-300">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        已更新
      </Badge>);

  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("w-full", className)}>

      <Card className="border-slate-200 bg-white/80 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                  <ThumbsUp className="w-6 h-6 text-white" />
                </div>
                {satisfactionTrend.trend === "up" &&
                <TrendingUp className="absolute -top-1 -right-1 w-5 h-5 text-emerald-400" />
                }
                {satisfactionTrend.trend === "down" &&
                <TrendingDown className="absolute -top-1 -right-1 w-5 h-5 text-red-400" />
                }
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-slate-800">
                  客户满意度
                </CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  {renderStatusBadge()}
                  {satisfactionTrend.trend !== "stable" &&
                  <span className={`text-sm font-medium ${satisfactionTrend.color}`}>
                      {satisfactionTrend.trend === "up" ? "上升" : "下降"}
                  </span>
                  }
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {onRefresh &&
              <Button
                variant="ghost"
                size="sm"
                onClick={onRefresh}
                className="text-slate-500 hover:text-slate-700">

                  <RefreshCw className="w-4 h-4" />
              </Button>
              }
              {showDetails &&
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExpand}
                className="text-slate-500 hover:text-slate-700">

                  {expanded ?
                <ChevronUp className="w-4 h-4" /> :

                <ChevronDown className="w-4 h-4" />
                }
              </Button>
              }
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* 主指标显示 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {(statsCards || []).map((stat, index) =>
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="group">

                <div className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all">
                  <div className="flex items-center justify-between mb-2">
                    <div className={`p-2 rounded-lg ${stat.iconBg}`}>
                      {(() => { const DynIcon = stat.icon; return <DynIcon className={`w-5 h-5 ${stat.iconColor}`}  />; })()}
                    </div>
                    <div className="text-right">
                      {stat.progress !== undefined &&
                    <Progress
                      value={stat.progress}
                      className="h-1 w-16" />

                    }
                    </div>
                  </div>
                  <div className="text-sm text-slate-500 mb-1">
                    {stat.title}
                  </div>
                  <div className="text-2xl font-bold text-slate-800">
                    {stat.value}
                  </div>
                  {stat.subtitle &&
                <div className="text-xs text-slate-500 mt-1">
                      {stat.subtitle}
                </div>
                }
                </div>
            </motion.div>
            )}
          </div>

          {/* 详细信息区域 */}
          <AnimatePresence>
            {expanded &&
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden">

                <div className="border-t border-slate-200 pt-4 space-y-4">
                  {/* 详细统计 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <div className="text-sm text-slate-600 mb-1">待处理反馈</div>
                      <div className="text-2xl font-bold text-amber-600">
                        {satisfaction.pendingFeedback || 0}
                      </div>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <div className="text-sm text-slate-600 mb-1">客户总数</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {satisfaction.totalCustomers || 0}
                      </div>
                    </div>
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <div className="text-sm text-slate-600 mb-1">解决率</div>
                      <div className="text-2xl font-bold text-emerald-600">
                        {satisfaction.resolvedRate || 0}%
                      </div>
                    </div>
                  </div>

                  {/* 反馈类型分布 */}
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="text-sm font-semibold text-slate-700 mb-3">
                      反馈类型分布
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(satisfactionConstants.feedbackTypeConfig).map(([key, config]) => {
                      const count = satisfaction.feedbackTypeCounts?.[key] || 0;
                      const percentage = satisfaction.totalResponses > 0 ?
                      (count / satisfaction.totalResponses * 100).toFixed(1) :
                      0;

                      return (
                        <div key={key} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${config.color.replace("bg-", "bg-").replace("/10", "/50")}`} />
                              <span className="text-sm text-slate-600">{config.label}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <Progress value={percentage} className="h-2 w-24" />
                              <span className="text-sm text-slate-500 w-12 text-right">
                                {percentage}%
                              </span>
                            </div>
                        </div>);

                    })}
                    </div>
                  </div>
                </div>
            </motion.div>
            }
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>);

};