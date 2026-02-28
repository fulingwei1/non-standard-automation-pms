/**
 * Alert Distribution Component - 告警分布组件
 * 用于展示告警在各维度上的分布情况
 */

import { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar } from
"recharts";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  ALERT_LEVEL_STATS,
  ALERT_STATUS_STATS,
  ALERT_TYPE_STATS } from
"@/lib/constants/alert";

export function AlertDistribution({
  data,
  height = 400,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  className = ""
}) {
  const [activeTab, setActiveTab] = useState("level");
  const [chartType, setChartType] = useState("pie");

  // 计算告警级别分布
  const levelDistribution = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}

    const distribution = {
      CRITICAL: { ...ALERT_LEVEL_STATS.CRITICAL, count: 0 },
      HIGH: { ...ALERT_LEVEL_STATS.HIGH, count: 0 },
      MEDIUM: { ...ALERT_LEVEL_STATS.MEDIUM, count: 0 },
      LOW: { ...ALERT_LEVEL_STATS.LOW, count: 0 },
      INFO: { ...ALERT_LEVEL_STATS.INFO, count: 0 }
    };

    data.forEach((alert) => {
      const level = alert.alert_level || 'INFO';
      if (distribution[level]) {
        distribution[level].count += 1;
      }
    });

    return Object.values(distribution).
    filter((item) => item.count > 0).
    sort((a, b) => b.count - a.count);
  }, [data]);

  // 计算告警状态分布
  const statusDistribution = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}

    const distribution = {
      PENDING: { ...ALERT_STATUS_STATS.PENDING, count: 0 },
      ACKNOWLEDGED: { ...ALERT_STATUS_STATS.ACKNOWLEDGED, count: 0 },
      ASSIGNED: { ...ALERT_STATUS_STATS.ASSIGNED, count: 0 },
      IN_PROGRESS: { ...ALERT_STATUS_STATS.IN_PROGRESS, count: 0 },
      RESOLVED: { ...ALERT_STATUS_STATS.RESOLVED, count: 0 },
      CLOSED: { ...ALERT_STATUS_STATS.CLOSED, count: 0 },
      IGNORED: { ...ALERT_STATUS_STATS.IGNORED, count: 0 }
    };

    data.forEach((alert) => {
      const status = alert.status || 'PENDING';
      if (distribution[status]) {
        distribution[status].count += 1;
      }
    });

    return Object.values(distribution).
    filter((item) => item.count > 0).
    sort((a, b) => b.count - a.count);
  }, [data]);

  // 计算告警类型分布
  const typeDistribution = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}

    const distribution = {};
    const subtypes = {};

    data.forEach((alert) => {
      const type = alert.alert_type || 'SYSTEM';
      const subtype = alert.alert_subtype || 'OTHER';

      // 统计主类型
      if (!distribution[type]) {
        distribution[type] = {
          ...ALERT_TYPE_STATS[type],
          count: 0,
          subtypes: {}
        };
      }
      distribution[type].count += 1;

      // 统计子类型
      if (!subtypes[type]) {
        subtypes[type] = {};
      }
      if (!subtypes[type][subtype]) {
        subtypes[type][subtype] = { count: 0 };
      }
      subtypes[type][subtype].count += 1;
    });

    // 合并子类型数据
    Object.keys(distribution).forEach((type) => {
      distribution[type].subtypes = subtypes[type] || {};
    });

    return Object.values(distribution).
    filter((item) => item.count > 0).
    sort((a, b) => b.count - a.count);
  }, [data]);

  // 计算项目分布
  const projectDistribution = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}

    const distribution = {};

    data.forEach((alert) => {
      const project = alert.project_name || alert.project_id || '未分类';

      if (!distribution[project]) {
        distribution[project] = {
          name: project,
          count: 0,
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          info: 0
        };
      }
      distribution[project].count += 1;

      // 按级别统计
      const level = alert.alert_level || 'INFO';
      if (distribution[project][level.toLowerCase()] !== undefined) {
        distribution[project][level.toLowerCase()] += 1;
      }
    });

    return Object.values(distribution).
    filter((item) => item.count > 0).
    sort((a, b) => b.count - a.count).
    slice(0, 10); // 只显示前10个项目
  }, [data]);

  // 计算雷达图数据
  const radarData = useMemo(() => {
    if (!data || data.length === 0) {return [];}

    return [
    {
      subject: '严重告警',
      A: (levelDistribution.find((d) => d.label === '严重')?.count || 0) / data.length * 100,
      fullMark: 100
    },
    {
      subject: '高优先级',
      A: (levelDistribution.find((d) => d.label === '高')?.count || 0) / data.length * 100,
      fullMark: 100
    },
    {
      subject: '待处理',
      A: (statusDistribution.find((d) => d.label === '待处理')?.count || 0) / data.length * 100,
      fullMark: 100
    },
    {
      subject: '已解决',
      A: (statusDistribution.find((d) => d.label === '已解决')?.count || 0) / data.length * 100,
      fullMark: 100
    },
    {
      subject: '系统告警',
      A: (typeDistribution.find((d) => d.label === '系统告警')?.count || 0) / data.length * 100,
      fullMark: 100
    },
    {
      subject: '项目告警',
      A: (typeDistribution.find((d) => d.label === '项目预警')?.count || 0) / data.length * 100,
      fullMark: 100
    }];

  }, [data, levelDistribution, statusDistribution, typeDistribution]);

  // 渲染饼图
  const renderPieChart = (data, _title) => {
    const COLORS = data.map((item) => item.color || item.bgColor);

    return (
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
            outerRadius={height / 2 - 40}
            fill="#8884d8"
            dataKey="count">

            {data.map((entry, index) =>
            <Cell key={`cell-${index}`} fill={COLORS[index]} />
            )}
          </Pie>
          {showTooltip &&
          <Tooltip
            formatter={(value) => [value, '数量']}
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }} />

          }
          {showLegend &&
          <Legend
            layout="vertical"
            verticalAlign="middle"
            align="right"
            wrapperStyle={{ paddingLeft: '20px' }} />

          }
        </PieChart>
      </ResponsiveContainer>);

  };

  // 渲染柱状图
  const renderBarChart = (data, _title) =>
  <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />}
        <XAxis
        dataKey="name"
        tick={{ fontSize: 12 }}
        axisLine={false}
        tickLine={false} />

        <YAxis
        tick={{ fontSize: 12 }}
        axisLine={false}
        tickLine={false} />

        {showTooltip &&
      <Tooltip
        formatter={(value) => [value, '数量']}
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
        dataKey="count"
        fill="#8884d8"
        name="数量" />

      </BarChart>
  </ResponsiveContainer>;


  // 渲染雷达图
  const renderRadarChart = () =>
  <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={radarData}>
        <PolarGrid />
        <PolarAngleAxis
        dataKey="subject"
        tick={{ fontSize: 12 }} />

        <PolarRadiusAxis
        angle={30}
        domain={[0, 100]}
        tick={{ fontSize: 12 }} />

        <Radar
        name="告警分布"
        dataKey="A"
        stroke="#8884d8"
        fill="#8884d8"
        fillOpacity={0.3} />

        {showTooltip &&
      <Tooltip
        formatter={(value) => [`${value.toFixed(1)}%`, '占比']}
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
      </RadarChart>
  </ResponsiveContainer>;


  // 渲染类型分布详细视图
  const renderTypeDetail = () =>
  <div className="space-y-6">
      {typeDistribution.map((typeData, index) =>
    <Card key={index}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <span className="text-xl">{typeData.icon}</span>
              {typeData.label}
              <Badge variant="secondary">{typeData.count} 个</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              {Object.entries(typeData.subtypes).map(([subtype, subtypeData]) =>
          <div key={subtype} className="text-center">
                  <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-gray-100 flex items-center justify-center">
                    <div className={`w-3 h-3 rounded-full ${ALERT_TYPE_STATS[typeData.category]?.subtypes[subtype]?.color || 'bg-gray-400'}`} />
                  </div>
                  <div className="text-sm font-medium text-gray-700">
                    {subtypeData.label || subtype}
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {subtypeData.count}
                  </div>
          </div>
          )}
            </div>
          </CardContent>
    </Card>
    )}
  </div>;


  // 无数据时的显示
  if (!data || data.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <p className="text-lg mb-2">暂无告警分布数据</p>
            <p className="text-sm">请检查数据源或选择其他时间范围</p>
          </div>
        </CardContent>
      </Card>);

  }

  // 获取当前分布数据
  const getCurrentData = () => {
    switch (activeTab) {
      case 'level':
        return levelDistribution;
      case 'status':
        return statusDistribution;
      case 'type':
        return typeDistribution;
      case 'project':
        return projectDistribution;
      default:
        return levelDistribution;
    }
  };

  // 渲染当前图表
  const renderCurrentChart = () => {
    const currentData = getCurrentData();

    if (activeTab === 'radar') {
      return renderRadarChart();
    }

    switch (chartType) {
      case 'pie':
        return renderPieChart(currentData);
      case 'bar':
        return renderBarChart(currentData);
      default:
        return renderPieChart(currentData);
    }
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex flex-col space-y-3 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <CardTitle className="text-lg font-semibold">告警分布分析</CardTitle>

          <div className="flex items-center space-x-2">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="level">级别</TabsTrigger>
                <TabsTrigger value="status">状态</TabsTrigger>
                <TabsTrigger value="type">类型</TabsTrigger>
                <TabsTrigger value="project">项目</TabsTrigger>
                <TabsTrigger value="radar">综合</TabsTrigger>
              </TabsList>

              <TabsContent value="level" className="mt-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Button
                    variant={chartType === 'pie' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('pie')}>

                    饼图
                  </Button>
                  <Button
                    variant={chartType === 'bar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('bar')}>

                    柱状图
                  </Button>
                </div>
                {renderCurrentChart()}
              </TabsContent>

              <TabsContent value="status" className="mt-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Button
                    variant={chartType === 'pie' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('pie')}>

                    饼图
                  </Button>
                  <Button
                    variant={chartType === 'bar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('bar')}>

                    柱状图
                  </Button>
                </div>
                {renderCurrentChart()}
              </TabsContent>

              <TabsContent value="type" className="mt-4">
                <div className="mb-4">
                  <div className="flex items-center space-x-2">
                    <Button
                      variant={chartType === 'pie' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setChartType('pie')}>

                      饼图
                    </Button>
                    <Button
                      variant={chartType === 'bar' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setChartType('bar')}>

                      柱状图
                    </Button>
                  </div>
                </div>
                {chartType === 'pie' || chartType === 'bar' ?
                renderCurrentChart() :

                renderTypeDetail()
                }
              </TabsContent>

              <TabsContent value="project" className="mt-4">
                <div className="flex items-center space-x-2 mb-4">
                  <Button
                    variant={chartType === 'bar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('bar')}
                    disabled>

                    柱状图
                  </Button>
                </div>
                {renderBarChart(projectDistribution, "项目告警分布")}
              </TabsContent>

              <TabsContent value="radar" className="mt-4">
                {renderRadarChart()}
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </CardHeader>
    </Card>);

}

export default AlertDistribution;