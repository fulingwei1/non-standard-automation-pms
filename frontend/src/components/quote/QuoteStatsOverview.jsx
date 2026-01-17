/**
 * Quote Statistics Overview Component
 * 报价统计概览组件 - 展示报价管理关键指标
 */

import { useState as _useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Send,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Calendar,
  AlertTriangle,
  Eye,
  BarChart3,
  Users,
  Building2,
  Percent } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import {
  DEFAULT_QUOTE_STATS,
  getQuoteStatusConfig as _getQuoteStatusConfig,
  calculateConversionRate,
  formatCurrency,
  QUOTE_VIEW_MODES } from
"./quoteConstants";
import {
  SimpleBarChart,
  SimpleLineChart,
  SimplePieChart } from
"../administrative/StatisticsCharts";

export const QuoteStatsOverview = ({
  stats = DEFAULT_QUOTE_STATS,
  viewMode = "list",
  onViewModeChange = null,
  onRefresh = null,
  loading = false,
  timeRange = "month",
  onTimeRangeChange = null,
  className = ""
}) => {
  // 计算关键指标
  const keyMetrics = useMemo(() => {
    const _total = stats.total || 0;
    const converted = stats.converted || 0;
    const sent = stats.sent || 0;

    return {
      conversionRate: calculateConversionRate(converted, sent),
      avgAmount: stats.avgAmount || 0,
      avgMargin: stats.avgMargin || 0,
      monthlyGrowth: stats.growth || 0,
      expiringSoonCount: stats.expiringSoon || 0,
      thisMonth: stats.thisMonth || 0,
      lastMonth: stats.lastMonth || 0
    };
  }, [stats]);

  // 统计卡片配置
  const statsCards = [
  {
    title: "总报价数",
    value: stats.total || 0,
    subtitle: "全部报价单据",
    icon: FileText,
    color: "from-blue-500/10 to-cyan-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400",
    trend: keyMetrics.monthlyGrowth > 0 ? "up" : keyMetrics.monthlyGrowth < 0 ? "down" : "neutral",
    trendValue: keyMetrics.monthlyGrowth
  },
  {
    title: "草稿",
    value: stats.draft || 0,
    subtitle: "待提交审批",
    icon: Clock,
    color: "from-slate-500/10 to-gray-500/5 border-slate-500/20",
    iconBg: "bg-slate-500/20",
    iconColor: "text-slate-400"
  },
  {
    title: "审批中",
    value: stats.inReview || 0,
    subtitle: "等待审批决定",
    icon: Clock,
    color: "from-amber-500/10 to-yellow-500/5 border-amber-500/20",
    iconBg: "bg-amber-500/20",
    iconColor: "text-amber-400"
  },
  {
    title: "已批准",
    value: stats.approved || 0,
    subtitle: "可发送给客户",
    icon: CheckCircle2,
    color: "from-green-500/10 to-emerald-500/5 border-green-500/20",
    iconBg: "bg-green-500/20",
    iconColor: "text-green-400"
  },
  {
    title: "已发送",
    value: stats.sent || 0,
    subtitle: "已送达客户",
    icon: Send,
    color: "from-purple-500/10 to-pink-500/5 border-purple-500/20",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400"
  },
  {
    title: "已转换",
    value: stats.converted || 0,
    subtitle: "成功转换为订单",
    icon: Target,
    color: "from-emerald-500/10 to-green-500/5 border-emerald-500/20",
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400"
  }];


  // 财务指标卡片
  const financialCards = [
  {
    title: "总报价金额",
    value: formatCurrency(stats.totalAmount || 0),
    subtitle: "所有报价累计金额",
    icon: DollarSign,
    color: "from-green-500/10 to-emerald-500/5 border-green-500/20",
    iconBg: "bg-green-500/20",
    iconColor: "text-green-400"
  },
  {
    title: "平均报价金额",
    value: formatCurrency(keyMetrics.avgAmount),
    subtitle: "单个报价平均金额",
    icon: BarChart3,
    color: "from-blue-500/10 to-indigo-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400"
  },
  {
    title: "转换率",
    value: `${keyMetrics.conversionRate}%`,
    subtitle: "报价转订单成功率",
    icon: Target,
    color: "from-purple-500/10 to-pink-500/5 border-purple-500/20",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400",
    progress: parseFloat(keyMetrics.conversionRate)
  },
  {
    title: "平均毛利率",
    value: `${keyMetrics.avgMargin}%`,
    subtitle: "报价利润水平",
    icon: Percent,
    color: "from-orange-500/10 to-red-500/5 border-orange-500/20",
    iconBg: "bg-orange-500/20",
    iconColor: "text-orange-400",
    progress: parseFloat(keyMetrics.avgMargin)
  }];


  // 状态分布数据
  const statusDistributionData = useMemo(() => {
    const statusData = [
    { name: "草稿", value: stats.draft || 0, color: "#64748b" },
    { name: "审批中", value: stats.inReview || 0, color: "#eab308" },
    { name: "已批准", value: stats.approved || 0, color: "#22c55e" },
    { name: "已发送", value: stats.sent || 0, color: "#a855f7" },
    { name: "已转换", value: stats.converted || 0, color: "#10b981" },
    { name: "被拒", value: stats.rejected || 0, color: "#ef4444" }];

    return statusData.filter((item) => item.value > 0);
  }, [stats]);

  // 月度趋势数据
  const monthlyTrendData = useMemo(() => {
    // 这里应该从API获取真实的月度数据
    return [
    { month: "1月", quotes: 12, amount: 1500000, converted: 8 },
    { month: "2月", quotes: 18, amount: 2300000, converted: 12 },
    { month: "3月", quotes: 15, amount: 1900000, converted: 10 },
    { month: "4月", quotes: 22, amount: 2800000, converted: 15 },
    { month: "5月", quotes: 20, amount: 2500000, converted: 14 },
    { month: "6月", quotes: keyMetrics.thisMonth, amount: stats.totalAmount || 0, converted: stats.converted || 0 }];

  }, [keyMetrics.thisMonth, stats.totalAmount, stats.converted]);

  // 渲染趋势指示器
  const renderTrendIndicator = (trend, value) => {
    if (trend === "neutral" || !value) return null;

    return (
      <div className={cn(
        "flex items-center gap-1 text-xs",
        trend === "up" ? "text-emerald-400" : "text-red-400"
      )}>
        {trend === "up" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        <span>{trend === "up" ? "+" : ""}{value}%</span>
      </div>);

  };

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

              <Eye className={cn("w-3 h-3 mr-1", loading && "animate-spin")} />
              刷新
            </Button>
          }
        </div>

        {onViewModeChange &&
        <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">视图模式:</span>
            {QUOTE_VIEW_MODES.map((mode) =>
          <Button
            key={mode.value}
            variant={viewMode === mode.value ? "default" : "outline"}
            size="sm"
            onClick={() => onViewModeChange(mode.value)}
            className="text-xs">

                <mode.icon className="w-3 h-3 mr-1" />
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

        {statsCards.map((card, index) => {
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

      {/* 财务指标 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        {financialCards.map((card, index) => {
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
        className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* 状态分布 */}
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              报价状态分布
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

        {/* 月度趋势 */}
        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-400" />
              月度趋势分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleLineChart
              data={monthlyTrendData}
              xKey="month"
              yKeys={['quotes', 'converted']}
              height={200} />

          </CardContent>
        </Card>
      </motion.div>

      {/* 快速统计 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}>

        <Card className="border border-slate-700/70 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Users className="w-4 h-4 text-purple-400" />
              快速统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-blue-400">{keyMetrics.thisMonth}</p>
                <p className="text-xs text-slate-500">本月报价</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-green-400">{stats.converted || 0}</p>
                <p className="text-xs text-slate-500">已转换</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-purple-400">{stats.expired || 0}</p>
                <p className="text-xs text-slate-500">已过期</p>
              </div>
              <div className="text-center p-3 bg-slate-800/60 rounded-lg">
                <p className="text-2xl font-bold text-amber-400">{keyMetrics.expiringSoonCount}</p>
                <p className="text-xs text-slate-500">即将过期</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>);

};

export default QuoteStatsOverview;