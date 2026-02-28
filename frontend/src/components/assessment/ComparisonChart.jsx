/**
 * Comparison Chart Component - 对比图组件
 * 用于对比多个评估的维度分数
 */

import { useMemo } from "react";

const dimensionLabels = {
  technology: "技术",
  business: "商务",
  resource: "资源",
  delivery: "交付",
  customer: "客户关系",
};

const colors = [
  "rgb(59, 130, 246)", // blue
  "rgb(34, 197, 94)", // green
  "rgb(251, 146, 60)", // orange
  "rgb(168, 85, 247)", // purple
  "rgb(236, 72, 153)", // pink
];

export function ComparisonChart({ data, height = 300 }) {
  // data格式: [{ name: '评估1', scores: { technology: 15, business: 18, ... } }, ...]

  const dimensions = useMemo(() => {
    return Object.keys(dimensionLabels);
  }, []);

  const maxScore = 20;
  const barWidth = 60;
  const barGap = 20;
  const chartWidth = dimensions.length * (barWidth + barGap);
  const padding = 60;

  return (
    <div className="overflow-x-auto">
      <div style={{ minWidth: `${chartWidth + padding * 2}px` }}>
        <svg width="100%" height={height} className="overflow-visible">
          {/* Y轴标签 */}
          <g>
            {[0, 5, 10, 15, 20].map((value) => {
              const y =
                padding +
                ((maxScore - value) / maxScore) * (height - padding * 2);
              return (
                <g key={value}>
                  <line
                    x1={padding}
                    y1={y}
                    x2={chartWidth + padding}
                    y2={y}
                    stroke="currentColor"
                    strokeWidth="1"
                    strokeDasharray="2 2"
                    opacity="0.2"
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

          {/* 维度分组 */}
          {(dimensions || []).map((dimension, dimIndex) => {
            const x = padding + dimIndex * (barWidth + barGap) + barGap / 2;

            return (
              <g key={dimension}>
                {/* 维度标签 */}
                <text
                  x={x + barWidth / 2}
                  y={height - padding + 20}
                  textAnchor="middle"
                  className="text-xs fill-gray-300"
                >
                  {dimensionLabels[dimension]}
                </text>

                {/* 每个评估的柱状图 */}
                {(data || []).map((assessment, assessIndex) => {
                  const score = assessment.scores[dimension] || 0;
                  const barHeight = (score / maxScore) * (height - padding * 2);
                  const barX = x + (assessIndex * barWidth) / data?.length;
                  const barY = height - padding - barHeight;
                  const color = colors[assessIndex % colors.length];

                  return (
                    <g key={`${dimension}-${assessIndex}`}>
                      <rect
                        x={barX}
                        y={barY}
                        width={barWidth / data?.length - 2}
                        height={barHeight}
                        fill={color}
                        className="transition-all hover:opacity-80"
                      />
                      {/* 数值标签 */}
                      {barHeight > 15 && (
                        <text
                          x={barX + barWidth / data?.length / 2}
                          y={barY - 5}
                          textAnchor="middle"
                          className="text-xs font-semibold fill-gray-300"
                        >
                          {score}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>

        {/* 图例 */}
        <div className="flex items-center justify-center gap-4 mt-4">
          {(data || []).map((assessment, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: colors[index % colors.length] }}
              />
              <span className="text-sm text-gray-300">{assessment.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
