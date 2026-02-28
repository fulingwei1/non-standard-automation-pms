/**
 * Sales Director Statistics Overview Component
 * 销售总监统计概览组件
 */

import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  DollarSign,
  Users,
  Target,
  Briefcase,
  BarChart3,
  Activity,
  CheckCircle2,
  AlertTriangle } from
'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui';
import { Progress } from '../../components/ui';
import StatCard from "../common/StatCard";
import { cn } from '../../lib/utils';
import {
  DEFAULT_STATS,
  TIME_PERIODS,
  calculateTrend,
  formatCurrency,
  formatPercentage } from
'@/lib/constants/sales';

export default function SalesDirectorStatsOverview({
  overallStats = null,
  selectedPeriod = 'month',
  onPeriodChange,
  loading = false,
  onRefresh
}) {
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // 自动刷新时间戳
  useEffect(() => {
    const timer = setInterval(() => {
      setLastUpdated(new Date());
    }, 60000);

    return () => clearInterval(timer);
  }, []);

  // 计算统计数据
  const statsData = useMemo(() => {
    if (!overallStats) {
      return {
        monthlyRevenue: { current: 0, target: DEFAULT_STATS.monthlyTarget, trend: 'stable' },
        yearlyRevenue: { current: 0, target: DEFAULT_STATS.yearTarget, trend: 'stable' },
        teamSize: { current: 0, growth: 0, trend: 'stable' },
        activeDeals: { current: 0, trend: 'stable' },
        conversionRate: { current: 0, trend: 'stable' },
        avgDealSize: { current: 0, trend: 'stable' }
      };
    }

    return {
      monthlyRevenue: {
        current: overallStats.monthlyRevenue || 0,
        target: DEFAULT_STATS.monthlyTarget,
        trend: calculateTrend(overallStats.monthlyRevenue || 0, overallStats.lastMonthRevenue || 0),
        completion: (overallStats.monthlyRevenue || 0) / DEFAULT_STATS.monthlyTarget * 100
      },
      yearlyRevenue: {
        current: overallStats.yearlyRevenue || 0,
        target: DEFAULT_STATS.yearTarget,
        trend: calculateTrend(overallStats.yearlyRevenue || 0, overallStats.lastYearRevenue || 0),
        completion: (overallStats.yearlyRevenue || 0) / DEFAULT_STATS.yearTarget * 100
      },
      teamSize: {
        current: overallStats.teamSize || 0,
        growth: overallStats.teamGrowth || 0,
        trend: overallStats.teamGrowth > 0 ? 'upward' : overallStats.teamGrowth < 0 ? 'downward' : 'stable'
      },
      activeDeals: {
        current: overallStats.activeDeals || 0,
        trend: calculateTrend(overallStats.activeDeals || 0, overallStats.lastPeriodDeals || 0)
      },
      conversionRate: {
        current: overallStats.conversionRate || 0,
        trend: calculateTrend(overallStats.conversionRate || 0, overallStats.lastConversionRate || 0)
      },
      avgDealSize: {
        current: overallStats.avgDealSize || 0,
        trend: calculateTrend(overallStats.avgDealSize || 0, overallStats.lastAvgDealSize || 0)
      }
    };
  }, [overallStats]);

  // 主要统计卡片配置
  const mainStatsCards = [
  {
    title: '本月收入',
    value: formatCurrency(statsData.monthlyRevenue.current),
    subtitle: `目标: ${formatCurrency(statsData.monthlyRevenue.target)}`,
    icon: DollarSign,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    trend: statsData.monthlyRevenue.trend,
    progress: statsData.monthlyRevenue.completion,
    showProgress: true
  },
  {
    title: '年度收入',
    value: formatCurrency(statsData.yearlyRevenue.current),
    subtitle: `目标: ${formatCurrency(statsData.yearlyRevenue.target)}`,
    icon: TrendingUp,
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    trend: statsData.yearlyRevenue.trend,
    progress: statsData.yearlyRevenue.completion,
    showProgress: true
  },
  {
    title: '团队规模',
    value: statsData.teamSize.current.toString(),
    subtitle: `增长率: ${formatPercentage(statsData.teamSize.growth)}`,
    icon: Users,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    trend: statsData.teamSize.trend
  },
  {
    title: '活跃商机',
    value: statsData.activeDeals.current.toString(),
    subtitle: '进行中的商机数量',
    icon: Briefcase,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    trend: statsData.activeDeals.trend
  },
  {
    title: '转化率',
    value: formatPercentage(statsData.conversionRate.current),
    subtitle: '线索到成交转化',
    icon: Target,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    trend: statsData.conversionRate.trend
  },
  {
    title: '平均订单额',
    value: formatCurrency(statsData.avgDealSize.current),
    subtitle: '每单平均金额',
    icon: BarChart3,
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/10',
    trend: statsData.avgDealSize.trend
  }];


  // 渲染统计卡片
  const renderStatCard = (stat, index) => {
    const trendValue =
      stat.trend && typeof stat.trend === "object"
        ? stat.trend.trend === "upward"
          ? stat.trend.value
          : stat.trend.trend === "downward"
            ? -stat.trend.value
            : undefined
        : undefined;

    return (
      <motion.div
        key={stat.title}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.1 }}>

        <StatCard
          title={stat.title}
          value={stat.value}
          subtitle={stat.subtitle}
          icon={stat.icon}
          color={stat.color}
          iconColor={stat.color}
          valueColor="text-slate-100"
          bg={stat.bgColor}
          trend={trendValue}
          trendLabel=""
          trendShowSign={false}
          trendSuffix="%"
          showDecoration={false}
          cardClassName="h-full p-6"
          iconWrapperClassName="bg-opacity-10"
        >
          {stat.showProgress && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-500">
                <span>完成进度</span>
                <span>{formatPercentage(stat.progress || 0)}</span>
              </div>
              <Progress
                value={stat.progress || 0}
                className="h-2"
              />

              <div className="flex justify-between text-xs text-slate-500">
                <span>0</span>
                <span>{formatPercentage(100)}</span>
              </div>
            </div>
          )}
        </StatCard>
      </motion.div>);

  };

  // 渲染加载状态
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) =>
          <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-slate-700 rounded-lg" />
                  <div className="flex-1">
                    <div className="h-4 bg-slate-700 rounded mb-2" />
                    <div className="h-6 bg-slate-700 rounded w-3/4" />
                  </div>
                </div>
                <div className="mt-4 h-2 bg-slate-700 rounded" />
              </CardContent>
          </Card>
          )}
        </div>
      </div>);

  }

  return (
    <div className="space-y-6">
      {/* 时间选择器 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-slate-100">销售概览</h3>
          <div className="flex gap-2">
            {Object.values(TIME_PERIODS).map((period) =>
            <button
              key={period.value}
              onClick={() => onPeriodChange?.(period.value)}
              className={cn(
                'px-3 py-1 text-sm rounded-md transition-colors',
                selectedPeriod === period.value ?
                'bg-blue-500 text-white' :
                'bg-slate-700 text-slate-300 hover:bg-slate-600'
              )}>

                {period.label}
            </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">
            最后更新: {lastUpdated.toLocaleTimeString()}
          </span>
          {onRefresh &&
          <button
            onClick={onRefresh}
            className="text-xs bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600 transition-colors">

              刷新
          </button>
          }
        </div>
      </div>

      {/* 主要统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {mainStatsCards.map(renderStatCard)}
      </div>

      {/* 快速洞察 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" />
            快速洞察
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 表现最佳指标 */}
            <div className="bg-green-500/10 p-4 rounded-lg border border-green-500/30">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-5 h-5 text-green-400" />
                <span className="font-medium text-green-400">表现最佳</span>
              </div>
              <div className="text-sm text-green-300">
                {statsData.monthlyRevenue.completion >= 80 ?
                `本月收入完成率 ${formatPercentage(statsData.monthlyRevenue.completion)}` :
                statsData.conversionRate.current >= 20 ?
                `转化率 ${formatPercentage(statsData.conversionRate.current)}` :
                '各项指标正常'
                }
              </div>
            </div>

            {/* 需要关注的指标 */}
            <div className="bg-orange-500/10 p-4 rounded-lg border border-orange-500/30">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                <span className="font-medium text-orange-400">需要关注</span>
              </div>
              <div className="text-sm text-orange-300">
                {statsData.monthlyRevenue.completion < 50 ?
                `本月收入完成率仅 ${formatPercentage(statsData.monthlyRevenue.completion)}` :
                statsData.conversionRate.current < 10 ?
                `转化率偏低 ${formatPercentage(statsData.conversionRate.current)}` :
                '暂无特别关注项'
                }
              </div>
            </div>

            {/* 团队状态 */}
            <div className="bg-blue-500/10 p-4 rounded-lg border border-blue-500/30">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-5 h-5 text-blue-400" />
                <span className="font-medium text-blue-400">团队状态</span>
              </div>
              <div className="text-sm text-blue-300">
                团队规模 {statsData.teamSize.current} 人
                {statsData.teamSize.growth > 0 &&
                <span className="ml-1">
                    (增长 {formatPercentage(statsData.teamSize.growth)})
                </span>
                }
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>);

}
