/**
 * Issue Statistics Overview Component
 * 问题统计概览组件 - 展示问题管理关键指标
 */

import { useState as _useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Eye,
  BarChart3,
  Users,
  Calendar } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import {
  DEFAULT_ISSUE_STATS,
  getIssueStatusConfig,
  getIssueSeverityConfig,
  getIssueCategoryConfig,
  formatResolutionTime,
  ISSUE_VIEW_MODES } from
"@/lib/constants/issue";
import {
  SimpleBarChart,
  SimpleLineChart,
  SimplePieChart } from
"../administrative/StatisticsCharts";

export const IssueStatsOverview = ({
  stats = DEFAULT_ISSUE_STATS,
  viewMode = "list",
  onViewModeChange = null,
  onRefresh = null,
  loading = false,
  timeRange = "week",
  onTimeRangeChange = null,
  className = ""
}) => {
  // 计算关键指标
  const keyMetrics = useMemo(() => {
    const total = stats.total || 0;
    const resolved = stats.resolved || 0;
    const closed = stats.closed || 0;
    const completionRate = total > 0 ? ((resolved + closed) / total * 100).toFixed(1) : 0;

    return {
      completionRate,
      avgResolutionTime: stats.avgResolutionTime || 0,
      slaCompliance: stats.slaCompliance || 0,
      blockingRate: total > 0 ? (stats.blocking / total * 100).toFixed(1) : 0,
      overdueRate: total > 0 ? (stats.overdue / total * 100).toFixed(1) : 0,
      todayCreated: stats.createdToday || 0,
      todayResolved: stats.resolvedToday || 0
    };
  }, [stats]);

  // 统计卡片配置
  const statsCards = [
  {
    title: "待处理",
    value: stats.open || 0,
    subtitle: "需要关注的问题",
    icon: AlertCircle,
    color: "from-blue-500/10 to-cyan-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400",
    trend: stats.createdToday > 0 ? "up" : "neutral",
    trendValue: stats.createdToday
  },
  {
    title: "处理中",
    value: stats.processing || 0,
    subtitle: "正在解决的问题",
    icon: Clock,
    color: "from-yellow-500/10 to-amber-500/5 border-yellow-500/20",
    iconBg: "bg-yellow-500/20",
    iconColor: "text-yellow-400",
    trend: "neutral"
  },
  {
    title: "已解决",
    value: stats.resolved || 0,
    subtitle: "等待验证的问题",
    icon: CheckCircle2,
    color: "from-green-500/10 to-emerald-500/5 border-green-500/20",
    iconBg: "bg-green-500/20",
    iconColor: "text-green-400",
    trend: stats.resolvedToday > 0 ? "up" : "neutral",
    trendValue: stats.resolvedToday
  },
  {
    title: "已关闭",
    value: stats.closed || 0,
    subtitle: "已完成的问题",
    icon: CheckCircle2,
    color: "from-gray-500/10 to-slate-500/5 border-gray-500/20",
    iconBg: "bg-gray-500/20",
    iconColor: "text-gray-400",
    trend: "neutral"
  },
  {
    title: "阻塞问题",
    value: stats.blocking || 0,
    subtitle: `${keyMetrics.blockingRate}% 占比`,
    icon: AlertTriangle,
    color: "from-red-500/10 to-rose-500/5 border-red-500/20",
    iconBg: "bg-red-500/20",
    iconColor: "text-red-400",
    trend: stats.blocking > 0 ? "up" : "neutral"
  },
  {
    title: "已逾期",
    value: stats.overdue || 0,
    subtitle: `${keyMetrics.overdueRate}% 逾期率`,
    icon: XCircle,
    color: "from-orange-500/10 to-red-500/5 border-orange-500/20",
    iconBg: "bg-orange-500/20",
    iconColor: "text-orange-400",
    trend: stats.overdue > 0 ? "up" : "neutral"
  }];


  // 性能指标卡片
  const performanceCards = [
  {
    title: "解决率",
    value: `${keyMetrics.completionRate}%`,
    subtitle: "问题解决效率",
    icon: TrendingUp,
    color: "from-emerald-500/10 to-green-500/5 border-emerald-500/20",
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400",
    progress: parseFloat(keyMetrics.completionRate)
  },
  {
    title: "平均解决时间",
    value: formatResolutionTime(keyMetrics.avgResolutionTime),
    subtitle: "问题处理速度",
    icon: Clock,
    color: "from-blue-500/10 to-indigo-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400"
  },
  {
    title: "SLA 合规率",
    value: `${keyMetrics.slaCompliance}%`,
    subtitle: "服务水平达成",
    icon: Activity,
    color: "from-purple-500/10 to-pink-500/5 border-purple-500/20",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400",
    progress: parseFloat(keyMetrics.slaCompliance)
  }];


  // 渲染趋势指示器
  const renderTrendIndicator = (trend, value) => {
    if (trend === "neutral" || !value) {return null;}

    return (
      <div className={cn(
        "flex items-center gap-1 text-xs",
        trend === "up" ? "text-emerald-400" : "text-red-400"
      )}>
        {trend === "up" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        <span>+{value}</span>
      </div>);

  };

  // 状态分布数据
  const statusDistributionData = useMemo(() => {
    return Object.entries(stats.byStatus || {}).map(([status, count]) => ({
      name: getIssueStatusConfig(status).label,
      value: count,
      color: getIssueStatusConfig(status).color
    }));
  }, [stats.byStatus]);

  // 严重程度分布数据
  const severityDistributionData = useMemo(() => {
    return Object.entries(stats.bySeverity || {}).map(([severity, count]) => ({
      name: getIssueSeverityConfig(severity).label,
      value: count,
      color: getIssueSeverityConfig(severity).color
    }));
  }, [stats.bySeverity]);

  // 分类分布数据
  const categoryDistributionData = useMemo(() => {
    return Object.entries(stats.byCategory || {}).map(([category, count]) => ({
      name: getIssueCategoryConfig(category).label,
      value: count,
      color: getIssueCategoryConfig(category).color
    }));
  }, [stats.byCategory]);

  return (
    <div className={cn("space-y-6", className)}>
      {/* 控制栏 */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <select
              value={timeRange}
              onChange={(e) => onTimeRangeChange?.(e.target.value)}
              className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">

              <option value="day">今日</option>
              <option value="week">本周</option>
              <option value="month">本月</option>
              <option value="quarter">本季度</option>
              <option value="year">本年度</option>
            </select>
          </div>
          
          {onRefresh &&
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            className="text-xs">

              <Activity className={cn("w-3 h-3 mr-1", loading && "animate-spin")} />
              刷新
          </Button>
          }
        </div>

        {onViewModeChange &&
        <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">视图模式:</span>
            {ISSUE_VIEW_MODES.map((mode) =>
          <Button
            key={mode.value}
            variant={viewMode === mode.value ? "default" : "outline"}
            size="sm"
            onClick={() => onViewModeChange(mode.value)}
            className="text-xs">

                <mode.icon className="w-3 h-3 mr-1"  />
                {mode.label}
          </Button>
          )}
        </div>
        }
      </motion.div>

      {/* 主要统计卡片 */}
      <motion.div
        variants={{
          hidden: { opacity: 0 },
          show: {
            opacity: 1,
            transition: {
              staggerChildren: 0.1
            }
          }
        }}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">

        {(statsCards || []).map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              variants={{
                hidden: { opacity: 0, y: 20 },
                show: { opacity: 1, y: 0 }
              }}
              transition={{ delay: index * 0.05 }}>

              <Card className={cn(
                "border transition-all duration-200 hover:shadow-lg hover:-translate-y-1",
                card.color
              )}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm text-slate-400">{card.title}</p>
                      <p className="text-2xl font-bold text-white mt-1">
                        {card.value}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {card.subtitle}
                      </p>
                      {renderTrendIndicator(card.trend, card.trendValue)}
                    </div>
                    <div className={cn("p-2 rounded-lg", card.iconBg)}>
                      <Icon className={cn("w-5 h-5", card.iconColor)} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>);

        })}
      </motion.div>

      {/* 性能指标 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {(performanceCards || []).map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.05 }}>

              <Card className={cn("border", card.color)}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={cn("p-2 rounded-lg", card.iconBg)}>
                        <Icon className={cn("w-4 h-4", card.iconColor)} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{card.title}</p>
                        <p className="text-xs text-slate-500">{card.subtitle}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-white">{card.value}</p>
                    </div>
                  </div>
                  
                  {card.progress !== undefined &&
                  <div className="space-y-1">
                      <Progress
                      value={card.progress}
                      className="h-2" />

                      <div className="flex justify-between text-xs text-slate-500">
                        <span>0%</span>
                        <span>{card.progress}%</span>
                        <span>100%</span>
                      </div>
                  </div>
                  }
                </CardContent>
              </Card>
            </motion.div>);

        })}
      </motion.div>

      {/* 图表分析区域 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">

        {/* 问题状态分布 */}
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              问题状态分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            {statusDistributionData.length > 0 ?
            <SimplePieChart
              data={statusDistributionData}
              height={200} /> :


            <div className="text-center py-8 text-slate-400">
                暂无数据
            </div>
            }
          </CardContent>
        </Card>

        {/* 严重程度分布 */}
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-400" />
              严重程度分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            {severityDistributionData.length > 0 ?
            <SimpleBarChart
              data={severityDistributionData}
              height={200} /> :


            <div className="text-center py-8 text-slate-400">
                暂无数据
            </div>
            }
          </CardContent>
        </Card>

        {/* 分类分布 */}
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              问题分类分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            {categoryDistributionData.length > 0 ?
            <SimplePieChart
              data={categoryDistributionData}
              height={200} /> :


            <div className="text-center py-8 text-slate-400">
                暂无数据
            </div>
            }
          </CardContent>
        </Card>
      </motion.div>

      {/* 今日活动 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}>

        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-400" />
              今日活动
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-blue-400">{keyMetrics.todayCreated}</p>
                <p className="text-xs text-slate-500">新建问题</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-green-400">{keyMetrics.todayResolved}</p>
                <p className="text-xs text-slate-500">今日解决</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-yellow-400">{stats.processing || 0}</p>
                <p className="text-xs text-slate-500">处理中</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-purple-400">{stats.blocking || 0}</p>
                <p className="text-xs text-slate-500">阻塞问题</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>);

};

export default IssueStatsOverview;