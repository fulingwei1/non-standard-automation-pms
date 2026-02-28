/**
 * Revenue Chart Component
 * 收入图表组件
 * 用于展示收入趋势、结构和分析
 */

import { useMemo } from "react";
import { motion } from "framer-motion";
import {
  LineChart,
  PieChart } from
"../../components/charts";
import { Card, CardContent } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { cn } from "../../lib/utils";
import {
  formatCurrency,
  formatPercentage,
  revenueTypes } from
"@/lib/constants/finance";

// 收入概览卡片组件
const RevenueOverviewCard = ({ revenueData, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-8 bg-slate-700 rounded w-1/3" />
            <div className="grid grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) =>
              <div key={i} className="space-y-2">
                  <div className="h-4 bg-slate-700 rounded w-1/2" />
                  <div className="h-6 bg-slate-700 rounded" />
              </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">收入概览</h3>
          <Badge variant="outline" className="text-green-400 border-green-400">
            {revenueData.growth >= 0 ? "增长" : "下降"}
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {formatCurrency(revenueData.totalRevenue)}
            </div>
            <div className="text-sm text-slate-400">总收入</div>
            {revenueData.growth !== undefined &&
            <div className={cn(
              "text-xs mt-1 flex items-center justify-center gap-1",
              revenueData.growth >= 0 ? "text-green-400" : "text-red-400"
            )}>
                {revenueData.growth >= 0 ? "↑" : "↓"}
                {Math.abs(revenueData.growth)}%
                <span className="text-slate-500">较上月</span>
            </div>
            }
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {formatCurrency(revenueData.targetRevenue)}
            </div>
            <div className="text-sm text-slate-400">目标收入</div>
            <div className="text-xs text-slate-500 mt-1">
              完成率 {formatPercentage(revenueData.achievementRate)}
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-white mb-1">
              {revenueData.customerCount || 0}
            </div>
            <div className="text-sm text-slate-400">活跃客户</div>
            <div className="text-xs text-slate-500 mt-1">
              新增 {revenueData.newCustomers || 0}
            </div>
          </div>
        </div>

        {/* 收入趋势进度条 */}
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-400">目标完成进度</span>
            <span className="text-sm font-medium text-white">
              {formatPercentage(revenueData.achievementRate)}
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(revenueData.achievementRate, 100)}%` }} />
          </div>
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
            <span>150%</span>
          </div>
        </div>
      </CardContent>
    </Card>);

};

// 收入类型饼图
const RevenueTypeDistribution = ({ revenueByType, loading }) => {
  const chartData = useMemo(() => {
    if (!revenueByType || revenueByType.length === 0) {return [];}
    return revenueByType.map((item) => ({
      type: item.type,
      value: item.value,
      percentage: item.value / revenueByType.reduce((sum, d) => sum + d.value, 0) * 100
    }));
  }, [revenueByType]);

  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="h-40 bg-slate-700 rounded" />
          </div>
        </CardContent>
      </Card>);

  }

  if (!chartData || chartData.length === 0) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-40 text-slate-400">
            暂无收入类型数据
          </div>
        </CardContent>
      </Card>);

  }

  const colors = [
  '#4ade80', // 产品销售
  '#60a5fa', // 服务收入
  '#a78bfa', // 咨询收入
  '#9ca3af' // 其他收入
  ];

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">收入类型分布</h3>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 饼图 */}
          <div>
            <PieChart
              data={chartData}
              height={300}
              showPoint={false}
              showLegend={false}
              tooltip={{
                showMarkers: false,
                formatter: (datum) => ({
                  name: revenueTypes[datum.type]?.label || datum.type,
                  value: formatCurrency(datum.value)
                })
              }} />

          </div>

          {/* 图例和明细 */}
          <div className="space-y-4">
            {chartData.map((item, index) => {
              const revenueType = revenueTypes[item.type];
              return (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: colors[index] }} />
                    <div>
                      <div className="text-sm font-medium text-white">
                        {revenueType?.label || item.type}
                      </div>
                      <div className="text-xs text-slate-400">
                        {revenueType?.description}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-white">
                      {formatCurrency(item.value)}
                    </div>
                    <div className="text-xs text-slate-500">
                      {formatPercentage(item.percentage)}
                    </div>
                  </div>
                </div>);

            })}
          </div>
        </div>
      </CardContent>
    </Card>);

};

// 收入趋势图
const RevenueTrendChart = ({ revenueByMonth, loading, timeRange }) => {
  const chartData = useMemo(() => {
    if (!revenueByMonth || revenueByMonth.length === 0) {return [];}
    return revenueByMonth.map((item) => ({
      month: item.month,
      actual: item.actual,
      target: item.target,
      growth: item.growth
    }));
  }, [revenueByMonth]);

  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="h-64 bg-slate-700 rounded" />
          </div>
        </CardContent>
      </Card>);

  }

  if (!chartData || chartData.length === 0) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64 text-slate-400">
            暂无收入趋势数据
          </div>
        </CardContent>
      </Card>);

  }

  const formatter = (value) => formatCurrency(value);

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">收入趋势</h3>
          <Select value={timeRange} onValueChange={(_value) => {}}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3m">近3个月</SelectItem>
              <SelectItem value="6m">近6个月</SelectItem>
              <SelectItem value="1y">近1年</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <LineChart
          data={chartData}
          xField="month"
          yField="actual"
          seriesField="type"
          height={300}
          showPoint
          showArea
          formatter={formatter}
          colors={['#4ade80']}
          tooltip={{
            showMarkers: true,
            shared: true,
            showCrosshairs: true,
            crosshairs: {
              type: 'xy'
            },
            formatter: (datum) => ({
              name: datum.target !== undefined ? '实际收入' : '收入',
              value: formatter(datum.actual || datum.value)
            })
          }}
          style={{ width: '100%' }} />

      </CardContent>
    </Card>);

};

// 客户收入分析
const CustomerRevenueAnalysis = ({ revenueByCustomer, loading }) => {
  const chartData = useMemo(() => {
    if (!revenueByCustomer || revenueByCustomer.length === 0) {return [];}
    return revenueByCustomer.
    sort((a, b) => b.value - a.value).
    slice(0, 10).
    map((item, index) => ({
      name: item.customer,
      revenue: item.value,
      growth: item.growth,
      rank: index + 1
    }));
  }, [revenueByCustomer]);

  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            <div className="space-y-2">
              {[...Array(5)].map((_, i) =>
              <div key={i} className="h-3 bg-slate-700 rounded w-full" />
              )}
            </div>
          </div>
        </CardContent>
      </Card>);

  }

  if (!chartData || chartData.length === 0) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-40 text-slate-400">
            暂无客户收入数据
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">客户收入TOP10</h3>

        <div className="space-y-3">
          {chartData.map((item, index) =>
          <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                index < 3 ? "bg-amber-500 text-white" : "bg-slate-700 text-slate-400"
              )}>
                  {item.rank}
                </div>
                <div className="text-sm text-white">
                  {item.customer}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className={cn(
                "text-sm font-medium",
                item.growth >= 0 ? "text-green-400" : "text-red-400"
              )}>
                  {item.growth >= 0 ? "↑" : "↓"}
                  {Math.abs(item.growth)}%
                </div>
                <div className="text-sm font-medium text-white">
                  {formatCurrency(item.revenue)}
                </div>
              </div>
          </div>
          )}
        </div>

        <div className="mt-4 pt-4 border-t border-slate-700">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">累计客户收入</span>
            <span className="text-white font-medium">
              {formatCurrency(chartData.reduce((sum, item) => sum + item.revenue, 0))}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>);

};

export function RevenueChart({
  revenueData,
  timeRange = "3m",
  loading = false
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6">

      {/* 收入概览 */}
      <RevenueOverviewCard revenueData={revenueData} loading={loading} />

      {/* 图表选项卡 */}
      <Tabs defaultValue="trend" className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800 p-1">
          <TabsTrigger value="trend" className="text-xs">收入趋势</TabsTrigger>
          <TabsTrigger value="type" className="text-xs">收入结构</TabsTrigger>
          <TabsTrigger value="customer" className="text-xs">客户分析</TabsTrigger>
          <TabsTrigger value="forecast" className="text-xs">预测分析</TabsTrigger>
        </TabsList>

        <TabsContent value="trend" className="mt-4">
          <RevenueTrendChart
            revenueByMonth={revenueData.byMonth}
            loading={loading}
            timeRange={timeRange} />

        </TabsContent>

        <TabsContent value="type" className="mt-4">
          <RevenueTypeDistribution
            revenueByType={revenueData.byType}
            loading={loading} />

        </TabsContent>

        <TabsContent value="customer" className="mt-4">
          <CustomerRevenueAnalysis
            revenueByCustomer={revenueData.byCustomer}
            loading={loading} />

        </TabsContent>

        <TabsContent value="forecast" className="mt-4">
          <Card className="bg-surface-50 border-white/10">
            <CardContent className="p-6">
              <div className="flex items-center justify-center h-64 text-slate-400">
                预测分析功能开发中...
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>);

}

export default RevenueChart;