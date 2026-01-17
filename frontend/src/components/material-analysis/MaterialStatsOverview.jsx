import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Package,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Truck,
  BarChart3,
  Activity,
  Target,
  Zap,
  RefreshCw } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import { SimpleBarChart, SimplePieChart, SimpleLineChart } from "../../components/administrative/StatisticsCharts";
import {
  MATERIAL_STATUS,
  MATERIAL_TYPES,
  IMPACT_LEVELS,
  ANALYSIS_METRICS,
  getMaterialStatus,
  getMaterialType,
  getImpactLevel,
  calculateReadinessRate,
  calculateAnalysisScore as _calculateAnalysisScore } from
"./materialAnalysisConstants";
import { cn } from "../../lib/utils";

/**
 * 📊 材料统计概览组件
 * 展示材料分析的关键指标和统计信息
 */
export function MaterialStatsOverview({
  projects = [],
  materials = [],
  loading = false,
  refreshInterval = 30000,
  onRefresh
}) {
  const [trendData, setTrendData] = useState([]);
  const [trendPeriod, setTrendPeriod] = useState('weekly');
  const [lastRefreshTime, setLastRefreshTime] = useState(new Date());

  // 计算总体统计数据
  const overallStats = useMemo(() => {
    if (projects.length === 0) {
      return {
        totalProjects: 0,
        totalMaterials: 0,
        readyRate: 100,
        onTimeDelivery: 0,
        qualityRate: 0,
        riskCount: 0,
        criticalMaterials: 0,
        materialCost: 0
      };
    }

    const stats = projects.reduce(
      (acc, project) => {
        const materialStats = project.materialStats || {};
        acc.totalMaterials += materialStats.total || 0;
        acc.arrived += materialStats.arrived || 0;
        acc.delayed += materialStats.delayed || 0;
        acc.inTransit += materialStats.inTransit || 0;
        return acc;
      },
      {
        totalMaterials: 0,
        arrived: 0,
        delayed: 0,
        inTransit: 0
      }
    );

    // 计算关键指标
    const readyRate = calculateReadinessRate(stats.arrived, stats.totalMaterials);
    const onTimeDelivery = stats.totalMaterials > 0 ?
    Math.round((stats.arrived + stats.inTransit) / stats.totalMaterials * 100) :
    0;

    // 计算风险项目数量
    const riskCount = projects.filter(
      (p) => p.readyRate < 80 || (p.materialStats?.delayed || 0) > 5
    ).length;

    // 计算关键物料数量
    const criticalMaterials = projects.reduce(
      (acc, project) => acc + (project.criticalMaterials?.length || 0),
      0
    );

    return {
      totalProjects: projects.length,
      totalMaterials: stats.totalMaterials,
      readyRate,
      onTimeDelivery,
      qualityRate: 95, // 模拟数据，实际应从质量系统获取
      riskCount,
      criticalMaterials,
      materialCost: Math.round(stats.totalMaterials * 1500) // 模拟成本
    };
  }, [projects]);

  // 材料状态分布数据
  const statusDistribution = useMemo(() => {
    const statusCount = {};

    projects.forEach((project) => {
      const stats = project.materialStats || {};
      statusCount.arrived = (statusCount.arrived || 0) + (stats.arrived || 0);
      statusCount.delayed = (statusCount.delayed || 0) + (stats.delayed || 0);
      statusCount.inTransit = (statusCount.inTransit || 0) + (stats.inTransit || 0);
      statusCount.notOrdered = (statusCount.notOrdered || 0) + (stats.notOrdered || 0);
    });

    return Object.entries(statusCount).map(([status, count]) => ({
      name: getMaterialStatus(status).label,
      value: count,
      color: getMaterialStatus(status).color.replace('bg-', '#').replace('500', '')
    }));
  }, [projects]);

  // 材料类型分布数据
  const typeDistribution = useMemo(() => {
    const typeCount = {};

    materials.forEach((material) => {
      const type = getMaterialType(material.type);
      typeCount[type.label] = (typeCount[type.label] || 0) + 1;
    });

    return Object.entries(typeCount).map(([type, count]) => ({
      name: type,
      value: count,
      color: getMaterialType(type).color.replace('bg-', '#').replace('500', '')
    }));
  }, [materials]);

  // 风险分析数据
  const riskAnalysis = useMemo(() => {
    const risks = projects.map((project) => {
      const riskScore = 100 - project.readyRate;
      const riskLevel = riskScore > 30 ? 'high' : riskScore > 15 ? 'medium' : 'low';

      return {
        name: project.name || project.id,
        riskScore,
        riskLevel,
        delayedMaterials: project.materialStats?.delayed || 0,
        criticalCount: project.criticalMaterials?.length || 0
      };
    }).sort((a, b) => b.riskScore - a.riskScore).slice(0, 10);

    return risks;
  }, [projects]);

  // 性能趋势数据
  useEffect(() => {
    const loadTrendData = async () => {
      try {
        // 模拟趋势数据 - 实际应从API获取
        const days = trendPeriod === 'daily' ? 7 : trendPeriod === 'weekly' ? 8 : 12;
        const mockTrend = Array.from({ length: days }, (_, i) => ({
          date: new Date(Date.now() - (days - i - 1) * 24 * 60 * 60 * 1000).toLocaleDateString(),
          readinessRate: Math.floor(Math.random() * 15) + 80,
          onTimeDelivery: Math.floor(Math.random() * 20) + 75,
          qualityRate: Math.floor(Math.random() * 10) + 90
        }));
        setTrendData(mockTrend);
      } catch (error) {
        console.error('加载趋势数据失败:', error);
      }
    };

    loadTrendData();
  }, [trendPeriod]);

  // 自动刷新
  useEffect(() => {
    const interval = setInterval(() => {
      setLastRefreshTime(new Date());
      if (onRefresh) onRefresh();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, onRefresh]);

  // 关键指标卡片
  const MetricCard = ({ title, value, icon: Icon, trend, trendValue, color, description }) =>
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    whileHover={{ scale: 1.02 }}
    className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className={cn("p-2 rounded-lg", color)}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-400">{title}</h3>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
          </div>
          {trend &&
        <div className="flex items-center gap-1 mt-2">
              {trend === 'up' ?
          <TrendingUp className="w-4 h-4 text-green-400" /> :

          <TrendingDown className="w-4 h-4 text-red-400" />
          }
              <span className={cn(
            "text-sm font-medium",
            trend === 'up' ? 'text-green-400' : 'text-red-400'
          )}>
                {trendValue}%
              </span>
            </div>
        }
          {description &&
        <p className="text-xs text-slate-500 mt-2">{description}</p>
        }
        </div>
      </div>
    </motion.div>;


  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) =>
        <div key={i} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 animate-pulse">
            <div className="h-20 bg-slate-700/50 rounded-lg"></div>
          </div>
        )}
      </div>);

  }

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="齐套率"
          value={`${overallStats.readyRate}%`}
          icon={Package}
          trend={overallStats.readyRate >= 90 ? 'up' : 'down'}
          trendValue={Math.abs(overallStats.readyRate - 90)}
          color="bg-blue-500"
          description="材料到货齐套率" />

        
        <MetricCard
          title="准时交付"
          value={`${overallStats.onTimeDelivery}%`}
          icon={Truck}
          trend={overallStats.onTimeDelivery >= 85 ? 'up' : 'down'}
          trendValue={Math.abs(overallStats.onTimeDelivery - 85)}
          color="bg-green-500"
          description="准时交付率" />

        
        <MetricCard
          title="质量合格率"
          value={`${overallStats.qualityRate}%`}
          icon={CheckCircle2}
          trend="up"
          trendValue="2.5"
          color="bg-purple-500"
          description="材料检验合格率" />

        
        <MetricCard
          title="风险项目"
          value={overallStats.riskCount}
          icon={AlertTriangle}
          trend={overallStats.riskCount <= 3 ? 'up' : 'down'}
          trendValue={overallStats.riskCount}
          color="bg-red-500"
          description="需要关注的项目数量" />

      </div>

      {/* 详细的统计信息 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 材料状态分布 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <BarChart3 className="w-5 h-5" />
              材料状态分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimplePieChart
                data={statusDistribution}
                valueKey="value"
                nameKey="name"
                colors={statusDistribution.map((d) => d.color)} />

            </div>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {statusDistribution.map((item, index) =>
              <div key={index} className="flex items-center gap-2">
                  <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }} />

                  <span className="text-sm text-slate-300">
                    {item.name}: {item.value}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 材料类型分布 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Package className="w-5 h-5" />
              材料类型分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <SimpleBarChart
                data={typeDistribution}
                xAxisKey="name"
                yAxisKey="value"
                color="#3b82f6" />

            </div>
          </CardContent>
        </Card>

        {/* 风险分析 */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <AlertTriangle className="w-5 h-5" />
              风险分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {riskAnalysis.map((risk, index) =>
              <div key={index} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white truncate">
                        {risk.name}
                      </span>
                      <Badge variant={risk.riskLevel === 'high' ? 'destructive' : 'secondary'}>
                        {getImpactLevel(risk.riskLevel).label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-slate-400">
                      <span>延期: {risk.delayedMaterials}</span>
                      <span>关键: {risk.criticalCount}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">{risk.riskScore}%</div>
                    <Progress
                    value={risk.riskScore}
                    className="w-16 h-2 mt-1" />

                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 性能趋势图 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white">
              <Activity className="w-5 h-5" />
              性能趋势
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={trendPeriod}
                onChange={(e) => setTrendPeriod(e.target.value)}
                className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm">

                <option value="daily">每日</option>
                <option value="weekly">每周</option>
                <option value="monthly">每月</option>
              </select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRefresh && onRefresh()}
                className="flex items-center gap-2">

                <RefreshCw className="w-4 h-4" />
                刷新
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <SimpleLineChart
              data={trendData}
              xAxisKey="date"
              yAxisKeys={['readinessRate', 'onTimeDelivery', 'qualityRate']}
              colors={['#3b82f6', '#10b981', '#8b5cf6']}
              labels={['齐套率', '准时交付', '质量合格']} />

          </div>
          <div className="flex items-center justify-between mt-4 text-xs text-slate-400">
            <span>最后更新: {lastRefreshTime.toLocaleTimeString()}</span>
            <span>自动刷新间隔: {refreshInterval / 1000}秒</span>
          </div>
        </CardContent>
      </Card>
    </div>);

}

export default MaterialStatsOverview;