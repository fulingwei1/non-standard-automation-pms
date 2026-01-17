import { useMemo } from "react";
import {
  BarChart3,
  TrendingUp,
  PieChart as PieChartIcon,
  Calendar } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

/**
 * 工时数据可视化组件集合
 * 使用简单的SVG和Canvas绘制图表（不依赖外部图表库）
 */

// 简单的柱状图组件
export function BarChart({
  data,
  width = 400,
  height = 200,
  color = "#3b82f6"
}) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        暂无数据
      </div>);

  }

  const maxValue = Math.max(...data.map((d) => d.value));
  const barWidth = width / data.length - 10;
  const scale = (height - 40) / maxValue;

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Y轴标签 */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const value = Math.round(maxValue * ratio);
        const y = height - 30 - ratio * (height - 40);
        return (
          <g key={ratio}>
            <line
              x1={30}
              y1={y}
              x2={width}
              y2={y}
              stroke="#334155"
              strokeWidth={1}
              strokeDasharray="2,2" />

            <text
              x={25}
              y={y + 4}
              textAnchor="end"
              className="text-xs fill-slate-400">

              {value}
            </text>
          </g>);

      })}

      {/* 柱状图 */}
      {data.map((item, index) => {
        const barHeight = item.value * scale;
        const x = 40 + index * (barWidth + 10);
        const y = height - 30 - barHeight;

        return (
          <g key={index}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={color}
              rx={4}
              className="hover:opacity-80 transition-opacity" />

            <text
              x={x + barWidth / 2}
              y={height - 10}
              textAnchor="middle"
              className="text-xs fill-slate-400">

              {item.label}
            </text>
            <text
              x={x + barWidth / 2}
              y={y - 5}
              textAnchor="middle"
              className="text-xs fill-slate-300 font-medium">

              {item.value.toFixed(1)}
            </text>
          </g>);

      })}
    </svg>);

}

// 简单的折线图组件
export function LineChart({
  data,
  width = 400,
  height = 200,
  color = "#10b981"
}) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        暂无数据
      </div>);

  }

  const maxValue = Math.max(...data.map((d) => d.value));
  const minValue = Math.min(...data.map((d) => d.value));
  const range = maxValue - minValue || 1;
  const scale = (height - 60) / range;
  const stepX = (width - 60) / (data.length - 1 || 1);

  const points = data.
  map((item, index) => {
    const x = 40 + index * stepX;
    const y = height - 30 - (item.value - minValue) * scale;
    return `${x},${y}`;
  }).
  join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      {/* Y轴标签 */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
        const value = Math.round(minValue + range * ratio);
        const y = height - 30 - ratio * (height - 60);
        return (
          <g key={ratio}>
            <line
              x1={30}
              y1={y}
              x2={width}
              y2={y}
              stroke="#334155"
              strokeWidth={1}
              strokeDasharray="2,2" />

            <text
              x={25}
              y={y + 4}
              textAnchor="end"
              className="text-xs fill-slate-400">

              {value}
            </text>
          </g>);

      })}

      {/* 折线 */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={2}
        className="drop-shadow-sm" />


      {/* 数据点 */}
      {data.map((item, index) => {
        const x = 40 + index * stepX;
        const y = height - 30 - (item.value - minValue) * scale;
        return (
          <g key={index}>
            <circle
              cx={x}
              cy={y}
              r={4}
              fill={color}
              className="hover:r-6 transition-all" />

            <text
              x={x}
              y={height - 10}
              textAnchor="middle"
              className="text-xs fill-slate-400">

              {item.label}
            </text>
          </g>);

      })}
    </svg>);

}

// 简单的饼图组件
export function PieChart({ data, width = 200, height = 200 }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        暂无数据
      </div>);

  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const colors = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899"];


  let currentAngle = -90;
  const radius = Math.min(width, height) / 2 - 20;
  const centerX = width / 2;
  const centerY = height / 2;

  return (
    <div className="relative">
      <svg width={width} height={height} className="overflow-visible">
        {data.map((item, index) => {
          const percentage = item.value / total;
          const angle = percentage * 360;
          const startAngle = currentAngle;
          const endAngle = currentAngle + angle;

          const startAngleRad = startAngle * Math.PI / 180;
          const endAngleRad = endAngle * Math.PI / 180;

          const x1 = centerX + radius * Math.cos(startAngleRad);
          const y1 = centerY + radius * Math.sin(startAngleRad);
          const x2 = centerX + radius * Math.cos(endAngleRad);
          const y2 = centerY + radius * Math.sin(endAngleRad);

          const largeArcFlag = angle > 180 ? 1 : 0;

          const pathData = [
          `M ${centerX} ${centerY}`,
          `L ${x1} ${y1}`,
          `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
          "Z"].
          join(" ");

          currentAngle = endAngle;

          return (
            <g key={index}>
              <path
                d={pathData}
                fill={colors[index % colors.length]}
                className="hover:opacity-80 transition-opacity cursor-pointer" />

            </g>);

        })}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">
            {total.toFixed(1)}
          </div>
          <div className="text-xs text-slate-400">总工时</div>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {data.map((item, index) => {
          const percentage = (item.value / total * 100).toFixed(1);
          return (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded"
                style={{
                  backgroundColor: colors[index % colors.length]
                }} />

              <span className="text-slate-300">{item.label}</span>
              <span className="text-slate-400 ml-auto">
                {item.value.toFixed(1)}h ({percentage}%)
              </span>
            </div>);

        })}
      </div>
    </div>);

}

// 工时趋势图卡片
export function TimesheetTrendChart({ data, title = "工时趋势" }) {
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.map((item) => ({
      label: item.date || item.label || "",
      value: parseFloat(item.hours || item.value || 0)
    }));
  }, [data]);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          <CardTitle className="text-white">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center">
          <LineChart data={chartData} width={600} height={250} />
        </div>
      </CardContent>
    </Card>);

}

// 部门对比图卡片
export function DepartmentComparisonChart({ data, title = "部门工时对比" }) {
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.map((item) => ({
      label: item.department_name || item.label || "",
      value: parseFloat(item.total_hours || item.value || 0)
    }));
  }, [data]);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-green-500" />
          <CardTitle className="text-white">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center">
          <BarChart data={chartData} width={600} height={250} color="#10b981" />
        </div>
      </CardContent>
    </Card>);

}

// 项目工时分布图卡片
export function ProjectDistributionChart({ data, title = "项目工时分布" }) {
  const chartData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    return data.
    slice(0, 6) // 只显示前6个项目
    .map((item) => ({
      label: item.project_name || item.label || "",
      value: parseFloat(item.total_hours || item.value || 0)
    }));
  }, [data]);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center gap-2">
          <PieChartIcon className="w-5 h-5 text-purple-500" />
          <CardTitle className="text-white">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center">
          <PieChart data={chartData} width={300} height={300} />
        </div>
      </CardContent>
    </Card>);

}

// 日历热力图（简化版）
export function CalendarHeatmap({ data: _data, title = "工时日历" }) {
  // 这里实现一个简化的日历视图
  // 完整的热力图需要更复杂的实现

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-orange-500" />
          <CardTitle className="text-white">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center text-slate-400 py-8">
          日历热力图功能开发中...
          <br />
          <span className="text-xs">将显示每日工时分布</span>
        </div>
      </CardContent>
    </Card>);

}