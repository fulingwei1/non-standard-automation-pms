/**
 * Qualification Trend Chart - 任职资格趋势图组件
 * 用于展示员工任职资格评估分数随时间的变化趋势
 */
import { useMemo } from "react";
import { format } from "date-fns";

export function QualificationTrendChart({
  data,
  height = 300,
  width = "100%",
  showPoints = true,
  showGrid = true,
}) {
  // data格式: [{ date: '2024-01-15', total_score: 85, period: '2024-Q1' }, ...]

  const sortedData = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}
    return [...data].sort((a, b) => {
      const dateA = new Date(a.date || a.assessed_at || a.period || 0);
      const dateB = new Date(b.date || b.assessed_at || b.period || 0);
      return dateA - dateB;
    });
  }, [data]);

  const maxValue = useMemo(() => {
    if (sortedData.length === 0) {return 100;}
    const scores = sortedData.map((d) => d.total_score || d.score || 0);
    return Math.max(...scores, 100);
  }, [sortedData]);

  const minValue = useMemo(() => {
    if (sortedData.length === 0) {return 0;}
    const scores = sortedData.map((d) => d.total_score || d.score || 0);
    return Math.min(...scores, 0);
  }, [sortedData]);

  const valueRange = maxValue - minValue || 100;
  const padding = { top: 20, right: 40, bottom: 60, left: 50 };
  const chartWidth = typeof width === "number" ? width : 600;
  const chartHeight = height;

  const points = useMemo(() => {
    if (sortedData.length === 0) {return [];}
    return sortedData.map((item, index) => {
      const score = item.total_score || item.score || 0;
      const x =
        padding.left +
        (index / (sortedData.length - 1 || 1)) *
          (chartWidth - padding.left - padding.right);
      const y =
        padding.top +
        ((maxValue - score) / valueRange) *
          (chartHeight - padding.top - padding.bottom);
      return {
        x,
        y,
        value: score,
        label: item.period || item.assessment_period || `评估${index + 1}`,
        date: item.date || item.assessed_at || item.period,
        result: item.result,
      };
    });
  }, [sortedData, chartWidth, chartHeight, padding, maxValue, valueRange]);

  const pathData = useMemo(() => {
    if (points.length === 0) {return "";}
    return points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");
  }, [points]);

  if (sortedData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        暂无评估数据
      </div>
    );
  }

  const getResultColor = (result) => {
    const colors = {
      PASS: "rgb(34, 197, 94)", // green
      PARTIAL: "rgb(251, 191, 36)", // yellow
      FAIL: "rgb(239, 68, 68)", // red
    };
    return colors[result] || "rgb(59, 130, 246)"; // blue
  };

  return (
    <div className="relative w-full" style={{ height: `${height}px` }}>
      <svg width="100%" height={height} className="overflow-visible">
        {/* 网格线 */}
        {showGrid && (
          <g opacity="0.1">
            {[0, 20, 40, 60, 80, 100].map((value) => {
              if (value < minValue || value > maxValue) {return null;}
              const y =
                padding.top +
                ((maxValue - value) / valueRange) *
                  (chartHeight - padding.top - padding.bottom);
              return (
                <g key={value}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={chartWidth - padding.right}
                    y2={y}
                    stroke="currentColor"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                    className="text-gray-400"
                  />
                  <text
                    x={padding.left - 10}
                    y={y + 4}
                    textAnchor="end"
                    className="text-xs fill-gray-500"
                  >
                    {value}
                  </text>
                </g>
              );
            })}
          </g>
        )}

        {/* 趋势线 */}
        {points.length > 1 && (
          <path
            d={pathData}
            fill="none"
            stroke="rgb(59, 130, 246)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="transition-all"
          />
        )}

        {/* 填充区域 */}
        {points.length > 1 && (
          <path
            d={`${pathData} L ${points[points.length - 1].x} ${chartHeight - padding.bottom} L ${points[0].x} ${chartHeight - padding.bottom} Z`}
            fill="rgba(59, 130, 246, 0.1)"
          />
        )}

        {/* 数据点 */}
        {showPoints &&
          points.map((point, index) => {
            const color = getResultColor(point.result);
            return (
              <g key={index}>
                <circle
                  cx={point.x}
                  cy={point.y}
                  r="6"
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                  className="transition-all hover:r-8 cursor-pointer"
                />
                {/* 数值标签 */}
                <text
                  x={point.x}
                  y={point.y - 15}
                  textAnchor="middle"
                  className="text-sm font-semibold fill-blue-600"
                >
                  {point.value.toFixed(1)}
                </text>
                {/* 日期标签 */}
                <text
                  x={point.x}
                  y={chartHeight - padding.bottom + 20}
                  textAnchor="middle"
                  className="text-xs fill-gray-500"
                >
                  {point.date
                    ? format(new Date(point.date), "MM/dd")
                    : point.label}
                </text>
                {/* 周期标签 */}
                {point.label && (
                  <text
                    x={point.x}
                    y={chartHeight - padding.bottom + 35}
                    textAnchor="middle"
                    className="text-xs fill-gray-400"
                  >
                    {point.label}
                  </text>
                )}
              </g>
            );
          })}
      </svg>
    </div>
  );
}
