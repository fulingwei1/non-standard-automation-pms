/**
 * Radar Chart Component - 雷达图组件
 * 用于展示技术评估的五维评分
 *
 * NOTE: A general-purpose RadarChart exists at:
 * components/charts/RadarChart.jsx
 * That component wraps @ant-design/plots for flexible multi-series radar charts.
 * This component is a custom SVG implementation specialized for 5-dimension assessments.
 */

import { useMemo } from "react";

const dimensionLabels = {
  technology: "技术",
  business: "商务",
  resource: "资源",
  delivery: "交付",
  customer: "客户关系",
};

export function RadarChart({ data, size = 300, maxScore = 20 }) {
  const dimensions = useMemo(() => {
    return Object.keys(dimensionLabels).map((key) => ({
      key,
      label: dimensionLabels[key],
      score: data[key] || 0,
    }));
  }, [data]);

  const radius = size / 2 - 40;
  const centerX = size / 2;
  const centerY = size / 2;
  const angleStep = (2 * Math.PI) / dimensions.length;

  // 计算每个维度的坐标点
  const points = useMemo(() => {
    return dimensions.map((dim, index) => {
      const angle = index * angleStep - Math.PI / 2;
      const normalizedScore = dim.score / maxScore;
      const r = radius * normalizedScore;
      return {
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
        label: dim.label,
        score: dim.score,
        angle: angle + Math.PI / 2,
      };
    });
  }, [dimensions, radius, centerX, centerY, angleStep, maxScore]);

  // 生成网格线
  const gridLevels = 5;
  const gridLines = useMemo(() => {
    return Array.from({ length: gridLevels }, (_, i) => {
      const level = (i + 1) / gridLevels;
      const levelRadius = radius * level;
      return dimensions.map((_, index) => {
        const angle = index * angleStep - Math.PI / 2;
        return {
          x: centerX + levelRadius * Math.cos(angle),
          y: centerY + levelRadius * Math.sin(angle),
        };
      });
    });
  }, [dimensions.length, radius, centerX, centerY, angleStep]);

  // 生成数据区域路径
  const dataPath = useMemo(() => {
    return points.map((p) => `${p.x},${p.y}`).join(" ");
  }, [points]);

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* 网格线 */}
        <g opacity="0.2">
          {gridLines.map((line, i) => (
            <polygon
              key={i}
              points={line.map((p) => `${p.x},${p.y}`).join(" ")}
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              className="text-gray-400"
            />
          ))}
        </g>

        {/* 轴线 */}
        <g opacity="0.3">
          {dimensions.map((_, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const x2 = centerX + radius * Math.cos(angle);
            const y2 = centerY + radius * Math.sin(angle);
            return (
              <line
                key={index}
                x1={centerX}
                y1={centerY}
                x2={x2}
                y2={y2}
                stroke="currentColor"
                strokeWidth="1"
                className="text-gray-400"
              />
            );
          })}
        </g>

        {/* 数据区域 */}
        <polygon
          points={dataPath}
          fill="rgba(59, 130, 246, 0.2)"
          stroke="rgb(59, 130, 246)"
          strokeWidth="2"
        />

        {/* 数据点 */}
        {points.map((point, index) => (
          <g key={index}>
            <circle cx={point.x} cy={point.y} r="4" fill="rgb(59, 130, 246)" />
            {/* 标签 */}
            <text
              x={point.x + (point.x > centerX ? 10 : -10)}
              y={point.y + (point.y > centerY ? 15 : -5)}
              textAnchor={point.x > centerX ? "start" : "end"}
              className="text-xs fill-gray-300"
            >
              {point.label}
            </text>
            {/* 分数 */}
            <text
              x={point.x}
              y={point.y - 8}
              textAnchor="middle"
              className="text-xs font-bold fill-blue-400"
            >
              {point.score}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
