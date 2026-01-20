/**
 * Trend Chart Component - 趋势图组件
 * 用于展示评估分数随时间的变化趋势
 */

import { useMemo } from "react";

export function TrendChart({ data, height = 250, showPoints = true }) {
  // data格式: [{ date: '2026-01-07', value: 75, label: '评估1' }, ...]

  const maxValue = useMemo(() => {
    return Math.max(...data.map((d) => d.value), 100);
  }, [data]);

  const minValue = useMemo(() => {
    return Math.min(...data.map((d) => d.value), 0);
  }, [data]);

  const valueRange = maxValue - minValue || 100;
  const padding = 40;

  const points = useMemo(() => {
    return data.map((item, index) => {
      const x =
        padding + (index / (data.length - 1 || 1)) * (height - padding * 2);
      const y =
        height -
        padding -
        ((item.value - minValue) / valueRange) * (height - padding * 2);
      return {
        x,
        y,
        value: item.value,
        label: item.label,
        date: item.date,
      };
    });
  }, [data, height, padding, minValue, valueRange]);

  const pathData = useMemo(() => {
    if (points.length === 0) {return "";}
    return points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");
  }, [points]);

  return (
    <div className="relative" style={{ height: `${height}px`, width: "100%" }}>
      <svg width="100%" height={height} className="overflow-visible">
        {/* 网格线 */}
        <g opacity="0.1">
          {[0, 25, 50, 75, 100].map((value) => {
            const y =
              height -
              padding -
              ((value - minValue) / valueRange) * (height - padding * 2);
            return (
              <g key={value}>
                <line
                  x1={padding}
                  y1={y}
                  x2={height - padding}
                  y2={y}
                  stroke="currentColor"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                  className="text-gray-400"
                />
                <text
                  x={padding - 10}
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

        {/* 趋势线 */}
        {points.length > 1 && (
          <path
            d={pathData}
            fill="none"
            stroke="rgb(59, 130, 246)"
            strokeWidth="2"
            className="transition-all"
          />
        )}

        {/* 填充区域 */}
        {points.length > 1 && (
          <path
            d={`${pathData} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`}
            fill="rgba(59, 130, 246, 0.1)"
          />
        )}

        {/* 数据点 */}
        {showPoints &&
          points.map((point, index) => (
            <g key={index}>
              <circle
                cx={point.x}
                cy={point.y}
                r="5"
                fill="rgb(59, 130, 246)"
                className="transition-all hover:r-7"
              />
              {/* 数值标签 */}
              <text
                x={point.x}
                y={point.y - 12}
                textAnchor="middle"
                className="text-xs font-semibold fill-blue-400"
              >
                {point.value}
              </text>
              {/* 日期标签 */}
              <text
                x={point.x}
                y={height - padding + 20}
                textAnchor="middle"
                className="text-xs fill-gray-400"
              >
                {point.date
                  ? new Date(point.date).toLocaleDateString("zh-CN", {
                      month: "short",
                      day: "numeric",
                    })
                  : point.label}
              </text>
            </g>
          ))}
      </svg>
    </div>
  );
}
