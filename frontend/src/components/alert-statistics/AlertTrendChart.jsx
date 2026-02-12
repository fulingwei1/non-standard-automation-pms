/**
 * Alert Trend Chart Component - 告警趋势图表组件
 * 用于展示告警随时间的变化趋势
 */

import React, { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  BarChart,
  Bar } from
"recharts";
import {
  TimeRangeSelector,
  DateRangePicker } from
"../../components/ui/time-range-selector";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  ALERT_LEVEL_STATS,
  TIME_DIMENSIONS,
  CHART_TYPES,
  generateTimeSeries as _generateTimeSeries,
  getTrendDirection,
  getTrendColor,
  getTrendIcon } from
"@/lib/constants/alert";

export function AlertTrendChart({
  data,
  height = 400,
  showGrid = true,
  showPoints = true,
  showLegend = true,
  showTooltip = true,
  timeDimension = 'DAILY',
  className = ""
}) {
  const [activeTab, setActiveTab] = useState("trends");
  const [chartType, setChartType] = useState("line");
  const [timeRange, setTimeRange] = useState("month");

  // 处理数据
  const processedData = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}

    // 根据时间维度聚合数据
    const groupedData = {};

    data.forEach((alert) => {
      if (!alert.created_at) {return;}

      const date = new Date(alert.created_at);
      let key;

      switch (timeDimension) {
        case 'HOURLY':
          key = `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:00`;
          break;
        case 'DAILY':
          key = `${date.getMonth() + 1}/${date.getDate()}`;
          break;
        case 'WEEKLY':
          {
            const weekNumber = getWeekNumber(date);
            key = `第${weekNumber}周`;
          }
          break;
        case 'MONTHLY':
          key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          break;
        default:
          key = `${date.getMonth() + 1}/${date.getDate()}`;
      }

      if (!groupedData[key]) {
        groupedData[key] = {
          date: key,
          total: 0,
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          info: 0,
          resolved: 0,
          pending: 0
        };
      }

      groupedData[key].total += 1;

      // 按级别统计
      const level = alert.alert_level || 'INFO';
      groupedData[key][level.toLowerCase()] += 1;

      // 按状态统计
      const status = alert.status || 'PENDING';
      if (status === 'RESOLVED') {
        groupedData[key].resolved += 1;
      } else if (status === 'PENDING') {
        groupedData[key].pending += 1;
      }
    });

    return Object.values(groupedData).sort((a, b) =>
    new Date(a.date) - new Date(b.date)
    );
  }, [data, timeDimension]);

  // 计算趋势指标
  const trendMetrics = useMemo(() => {
    if (processedData.length < 2) {return null;}

    const latest = processedData[processedData.length - 1];
    const previous = processedData[processedData.length - 2];

    return {
      total: {
        current: latest.total,
        previous: previous.total,
        change: getTrendDirection(latest.total, previous.total)
      },
      critical: {
        current: latest.critical,
        previous: previous.critical,
        change: getTrendDirection(latest.critical, previous.critical)
      },
      resolved: {
        current: latest.resolved,
        previous: previous.resolved,
        change: getTrendDirection(latest.resolved, previous.resolved)
      }
    };
  }, [processedData]);

  // 渲染趋势图
  const renderTrendChart = () => {
    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={processedData}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              <YAxis
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              {showTooltip &&
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }} />

              }
              {showLegend &&
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle" />

              }
              <Line
                type="monotone"
                dataKey="critical"
                stroke={ALERT_LEVEL_STATS.CRITICAL.color}
                strokeWidth={2}
                dot={showPoints ? { r: 4 } : false}
                name="严重" />

              <Line
                type="monotone"
                dataKey="high"
                stroke={ALERT_LEVEL_STATS.HIGH.color}
                strokeWidth={2}
                dot={showPoints ? { r: 4 } : false}
                name="高" />

              <Line
                type="monotone"
                dataKey="medium"
                stroke={ALERT_LEVEL_STATS.MEDIUM.color}
                strokeWidth={2}
                dot={showPoints ? { r: 4 } : false}
                name="中" />

              <Line
                type="monotone"
                dataKey="low"
                stroke={ALERT_LEVEL_STATS.LOW.color}
                strokeWidth={2}
                dot={showPoints ? { r: 4 } : false}
                name="低" />

              <Line
                type="monotone"
                dataKey="info"
                stroke={ALERT_LEVEL_STATS.INFO.color}
                strokeWidth={2}
                dot={showPoints ? { r: 4 } : false}
                name="信息" />

            </LineChart>
          </ResponsiveContainer>);


      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={processedData}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              <YAxis
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              {showTooltip &&
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }} />

              }
              {showLegend &&
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle" />

              }
              <Area
                type="monotone"
                dataKey="critical"
                stackId="1"
                stroke={ALERT_LEVEL_STATS.CRITICAL.color}
                fill={ALERT_LEVEL_STATS.CRITICAL.bgColor}
                name="严重" />

              <Area
                type="monotone"
                dataKey="high"
                stackId="1"
                stroke={ALERT_LEVEL_STATS.HIGH.color}
                fill={ALERT_LEVEL_STATS.HIGH.bgColor}
                name="高" />

              <Area
                type="monotone"
                dataKey="medium"
                stackId="1"
                stroke={ALERT_LEVEL_STATS.MEDIUM.color}
                fill={ALERT_LEVEL_STATS.MEDIUM.bgColor}
                name="中" />

              <Area
                type="monotone"
                dataKey="low"
                stackId="1"
                stroke={ALERT_LEVEL_STATS.LOW.color}
                fill={ALERT_LEVEL_STATS.LOW.bgColor}
                name="低" />

              <Area
                type="monotone"
                dataKey="info"
                stackId="1"
                stroke={ALERT_LEVEL_STATS.INFO.color}
                fill={ALERT_LEVEL_STATS.INFO.bgColor}
                name="信息" />

            </AreaChart>
          </ResponsiveContainer>);


      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={processedData}>
              {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              <YAxis
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false} />

              {showTooltip &&
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }} />

              }
              {showLegend &&
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle" />

              }
              <Bar
                dataKey="critical"
                fill={ALERT_LEVEL_STATS.CRITICAL.color}
                name="严重" />

              <Bar
                dataKey="high"
                fill={ALERT_LEVEL_STATS.HIGH.color}
                name="高" />

              <Bar
                dataKey="medium"
                fill={ALERT_LEVEL_STATS.MEDIUM.color}
                name="中" />

              <Bar
                dataKey="low"
                fill={ALERT_LEVEL_STATS.LOW.color}
                name="低" />

              <Bar
                dataKey="info"
                fill={ALERT_LEVEL_STATS.INFO.color}
                name="信息" />

            </BarChart>
          </ResponsiveContainer>);


      default:
        return null;
    }
  };

  // 渲染解决率趋势
  const renderResolutionTrend = () => {
    const resolutionData = processedData.map((item) => ({
      ...item,
      resolutionRate: item.total > 0 ? (item.resolved / item.total * 100).toFixed(1) : 0
    }));

    return (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={resolutionData}>
          {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false} />

          <YAxis
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            domain={[0, 100]} />

          {showTooltip &&
          <Tooltip
            formatter={(value) => [`${value}%`, '解决率']}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }} />

          }
          {showLegend &&
          <Legend
            wrapperStyle={{ paddingTop: '20px' }} />

          }
          <Line
            type="monotone"
            dataKey="resolutionRate"
            stroke="#22c55e"
            strokeWidth={2}
            dot={showPoints ? { r: 4 } : false}
            name="解决率" />

        </LineChart>
      </ResponsiveContainer>);

  };

  // 获取周数
  const getWeekNumber = (date) => {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date - firstDayOfYear) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
  };

  // 无数据时的显示
  if (processedData.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <p className="text-lg mb-2">暂无告警趋势数据</p>
            <p className="text-sm">请选择其他时间范围或检查数据源</p>
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <CardTitle className="text-lg font-semibold">告警趋势分析</CardTitle>

          <div className="flex items-center space-x-2">
            <TimeRangeSelector
              value={timeRange}
              onChange={setTimeRange}
              className="w-32" />


            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="trends">告警趋势</TabsTrigger>
                <TabsTrigger value="resolution">解决率</TabsTrigger>
              </TabsList>

              <TabsContent value="trends" className="mt-4">
                <div className="flex items-center space-x-2">
                  <Button
                    variant={chartType === 'line' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('line')}>

                    折线图
                  </Button>
                  <Button
                    variant={chartType === 'area' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('area')}>

                    面积图
                  </Button>
                  <Button
                    variant={chartType === 'bar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('bar')}>

                    柱状图
                  </Button>
                </div>

                {renderTrendChart()}

                {/* 趋势指标 */}
                {trendMetrics &&
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">总告警数</span>
                        <span className="text-xs text-gray-500">
                          {getTrendIcon(trendMetrics.total.change)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-2xl font-bold">
                          {trendMetrics.total.current}
                        </span>
                        <span className={`text-sm ${getTrendColor(trendMetrics.total.change)}`}>
                          {trendMetrics.total.change === 'up' ? '+' : ''}
                          {trendMetrics.total.previous > 0 ?
                        Math.round((trendMetrics.total.current - trendMetrics.total.previous) / trendMetrics.total.previous * 100) :
                        0}%
                        </span>
                      </div>
                    </div>

                    <div className="bg-red-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-red-600">严重告警</span>
                        <span className="text-xs text-red-500">
                          {getTrendIcon(trendMetrics.critical.change)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-2xl font-bold text-red-600">
                          {trendMetrics.critical.current}
                        </span>
                        <span className={`text-sm ${getTrendColor(trendMetrics.critical.change)}`}>
                          {trendMetrics.critical.change === 'up' ? '+' : ''}
                          {trendMetrics.critical.previous > 0 ?
                        Math.round((trendMetrics.critical.current - trendMetrics.critical.previous) / trendMetrics.critical.previous * 100) :
                        0}%
                        </span>
                      </div>
                    </div>

                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-green-600">已解决</span>
                        <span className="text-xs text-green-500">
                          {getTrendIcon(trendMetrics.resolved.change)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className="text-2xl font-bold text-green-600">
                          {trendMetrics.resolved.current}
                        </span>
                        <span className={`text-sm ${getTrendColor(trendMetrics.resolved.change)}`}>
                          {trendMetrics.resolved.change === 'up' ? '+' : ''}
                          {trendMetrics.resolved.previous > 0 ?
                        Math.round((trendMetrics.resolved.current - trendMetrics.resolved.previous) / trendMetrics.resolved.previous * 100) :
                        0}%
                        </span>
                      </div>
                    </div>
                </div>
                }
              </TabsContent>

              <TabsContent value="resolution" className="mt-4">
                {renderResolutionTrend()}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </CardHeader>
    </Card>);

}
