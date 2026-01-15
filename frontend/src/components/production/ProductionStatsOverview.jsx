/**
 * Production Statistics Overview Component
 * 生产统计概览组件
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Users,
  Activity,
  Target,
  Package,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Zap,
  Factory,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui';
import { Progress } from '../../components/ui';
import { cn } from '../../lib/utils';
import {
  PRODUCTION_METRICS,
  calculateCompletionRate,
  calculateQualityRate,
  formatProductionData,
} from './productionConstants';

export default function ProductionStatsOverview({
  productionStats,
  productionDaily,
  loading = false,
  onRefresh,
}) {
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // 自动刷新
  useEffect(() => {
    const timer = setInterval(() => {
      setLastUpdated(new Date());
    }, 60000); // 每分钟更新时间戳

    return () => clearInterval(timer);
  }, []);

  // 计算趋势数据
  const getTrendData = (current, previous) => {
    if (!previous || previous === 0) return { trend: 'up', value: 0 };
    const change = ((current - previous) / previous) * 100;
    return {
      trend: change >= 0 ? 'up' : 'down',
      value: Math.abs(change).toFixed(1),
    };
  };

  const statsCards = [
    {
      title: '生产中项目',
      value: productionStats?.inProductionProjects || 0,
      icon: Factory,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      trend: getTrendData(
        productionStats?.inProductionProjects || 0,
        productionDaily?.yesterdayProjects || 0
      ),
    },
    {
      title: '今日产量',
      value: productionStats?.todayOutput || 0,
      icon: Package,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      unit: '件',
      trend: getTrendData(
        productionStats?.todayOutput || 0,
        productionDaily?.yesterdayOutput || 0
      ),
    },
    {
      title: '完成率',
      value: productionStats?.completionRate || 0,
      icon: Target,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      unit: '%',
      isPercentage: true,
      trend: getTrendData(
        productionStats?.completionRate || 0,
        productionDaily?.yesterdayCompletionRate || 0
      ),
    },
    {
      title: '准时交付率',
      value: productionStats?.onTimeDeliveryRate || 0,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      unit: '%',
      isPercentage: true,
      trend: getTrendData(
        productionStats?.onTimeDeliveryRate || 0,
        productionDaily?.yesterdayOnTimeDeliveryRate || 0
      ),
    },
    {
      title: '在岗工人',
      value: `${productionStats?.activeWorkers || 0}/${productionStats?.totalWorkers || 0}`,
      icon: Users,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50',
      isRatio: true,
      trend: getTrendData(
        productionStats?.activeWorkers || 0,
        productionDaily?.yesterdayActiveWorkers || 0
      ),
    },
    {
      title: '运行工位',
      value: `${productionStats?.activeWorkstations || 0}/${productionStats?.totalWorkstations || 0}`,
      icon: Activity,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      isRatio: true,
      trend: getTrendData(
        productionStats?.activeWorkstations || 0,
        productionDaily?.yesterdayActiveWorkstations || 0
      ),
    },
  ];

  // 性能指标数据
  const performanceMetrics = [
    {
      title: '生产效率',
      value: productionStats?.efficiency || 85,
      target: 90,
      icon: Zap,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      title: '设备利用率',
      value: productionStats?.equipmentUtilization || 78,
      target: 85,
      icon: Factory,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: '质量合格率',
      value: productionStats?.qualityRate || 92,
      target: 95,
      icon: CheckCircle2,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: '安全指数',
      value: productionStats?.safetyIndex || 96,
      target: 98,
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
  ];

  // 渲染统计卡片
  const renderStatsCard = (stat, index) => {
    const Icon = stat.icon;
    const isPositive = stat.trend?.trend === 'up';
    
    return (
      <motion.div
        key={stat.title}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.1 }}
      >
        <Card className="h-full hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className={cn('p-3 rounded-lg', stat.bgColor)}>
                  <Icon className={cn('w-6 h-6', stat.color)} />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                    {stat.unit && <span className="text-lg text-gray-600 ml-1">{stat.unit}</span>}
                  </p>
                </div>
              </div>
              
              {stat.trend && (
                <div className="flex items-center space-x-1">
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4 text-green-500" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-500" />
                  )}
                  <span className={cn('text-sm font-medium', 
                    isPositive ? 'text-green-600' : 'text-red-600'
                  )}>
                    {stat.trend.value}%
                  </span>
                </div>
              )}
            </div>
            
            {stat.isRatio && (
              <div className="mt-3">
                <Progress 
                  value={stat.value ? (parseInt(stat.value.split('/')[0]) / parseInt(stat.value.split('/')[1])) * 100 : 0}
                  className="h-2"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  // 渲染性能指标
  const renderPerformanceMetric = (metric, index) => {
    const Icon = metric.icon;
    const progress = Math.min(metric.value / metric.target * 100, 100);
    const isGood = metric.value >= metric.target;
    
    return (
      <motion.div
        key={metric.title}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: index * 0.1 }}
      >
        <Card className="h-full">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className={cn('p-2 rounded-lg', stat.bgColor)}>
                  <Icon className={cn('w-4 h-4', metric.color)} />
                </div>
                <span className="text-sm font-medium text-gray-700">{metric.title}</span>
              </div>
              <span className={cn('text-sm font-bold', 
                isGood ? 'text-green-600' : 'text-red-600'
              )}>
                {metric.value}%
              </span>
            </div>
            
            <div className="space-y-2">
              <Progress value={progress} className="h-2" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>当前: {metric.value}%</span>
                <span>目标: {metric.target}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-gray-200 rounded-lg"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 rounded mb-2"></div>
                    <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 统计卡片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {statsCards.map(renderStatsCard)}
      </div>

      {/* 性能指标 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {performanceMetrics.map(renderPerformanceMetric)}
      </div>

      {/* 快速统计面板 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              今日生产活动
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                最后更新: {lastUpdated.toLocaleTimeString()}
              </span>
              {onRefresh && (
                <button
                  onClick={onRefresh}
                  className="text-xs bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600 transition-colors"
                >
                  刷新
                </button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {productionDaily?.todayPlans || 0}
              </div>
              <div className="text-sm text-gray-600">今日计划</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {productionDaily?.completedPlans || 0}
              </div>
              <div className="text-sm text-gray-600">已完成</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {productionDaily?.inProgressPlans || 0}
              </div>
              <div className="text-sm text-gray-600">进行中</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {productionDaily?.delayedPlans || 0}
              </div>
              <div className="text-sm text-gray-600">已延期</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}