/**
 * 缺料趋势分析页面
 * Team 3 - Shortage Trend Analysis
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { getTrendAnalysis } from '@/services/api/shortage';
import { ALERT_COLORS, ALERT_LEVELS } from '../constants';
import TrendLineChart from './components/TrendLineChart';
import { BarChart3, Clock, CheckCircle, TrendingUp } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const TrendAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [dateRange, setDateRange] = useState({
    start_date: getDefaultStartDate(),
    end_date: getDefaultEndDate(),
  });

  // 加载趋势数据
  const loadTrendData = async () => {
    try {
      setLoading(true);
      const response = await getTrendAnalysis(dateRange);
      setData(response.data);
    } catch (error) {
      console.error('Failed to load trend data:', error);
      toast({
        title: '加载失败',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTrendData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!data) return null;

  // 准备级别分布饼图数据
  const levelPieData = Object.entries(data.by_level || {}).map(([level, count]) => ({
    name: ALERT_LEVELS[level]?.label || level,
    value: count,
    color: ALERT_COLORS[level],
  }));

  // 准备状态分布饼图数据
  const statusPieData = Object.entries(data.by_status || {}).map(([status, count]) => ({
    name: status,
    value: count,
    color:
      status === 'RESOLVED'
        ? '#22C55E'
        : status === 'PROCESSING'
        ? '#3B82F6'
        : '#6B7280',
  }));

  // 计算解决率
  const resolvedRate =
    data.total_alerts > 0
      ? ((data.by_status?.RESOLVED || 0) / data.total_alerts) * 100
      : 0;

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">缺料趋势分析</h1>
        <p className="text-gray-500 mt-1">
          分析预警趋势，识别问题模式
        </p>
      </div>

      {/* 日期筛选 */}
      <Card>
        <CardHeader>
          <CardTitle>时间范围</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-4">
            <div className="flex-1">
              <Label htmlFor="start_date">开始日期</Label>
              <Input
                id="start_date"
                type="date"
                value={dateRange.start_date}
                onChange={(e) =>
                  setDateRange({ ...dateRange, start_date: e.target.value })
                }
              />
            </div>
            <div className="flex-1">
              <Label htmlFor="end_date">结束日期</Label>
              <Input
                id="end_date"
                type="date"
                value={dateRange.end_date}
                onChange={(e) =>
                  setDateRange({ ...dateRange, end_date: e.target.value })
                }
              />
            </div>
            <Button onClick={loadTrendData} className="bg-blue-600 hover:bg-blue-700">
              <BarChart3 className="mr-2 h-4 w-4" />
              刷新数据
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 总体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <BarChart3 className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">总预警数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.total_alerts}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">解决率</p>
                <p className="text-2xl font-bold text-green-600">
                  {resolvedRate.toFixed(1)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Clock className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">平均响应时间</p>
                <p className="text-2xl font-bold text-orange-600">
                  {data.avg_resolution_hours?.toFixed(1) || 0}h
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">总成本影响</p>
                <p className="text-2xl font-bold text-red-600">
                  ¥{parseFloat(data.total_cost_impact || 0).toLocaleString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 分布图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 按级别分布 */}
        <Card>
          <CardHeader>
            <CardTitle>按预警级别分布</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={levelPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(levelPieData || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 按状态分布 */}
        <Card>
          <CardHeader>
            <CardTitle>按处理状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(statusPieData || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 趋势折线图 */}
      <TrendLineChart data={data.trend_data || []} />
    </div>
  );
};

// 获取默认开始日期（30天前）
function getDefaultStartDate() {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  return date.toISOString().split('T')[0];
}

// 获取默认结束日期（今天）
function getDefaultEndDate() {
  return new Date().toISOString().split('T')[0];
}

export default TrendAnalysis;
