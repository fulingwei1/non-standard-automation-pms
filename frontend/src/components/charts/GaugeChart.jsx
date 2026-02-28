/**
 * 仪表盘组件 - 基于 @ant-design/plots
 * 用于KPI展示、目标完成度
 */

import { Gauge } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * GaugeChart - 仪表盘
 * @param {number} value - 当前值（0-100 或自定义范围）
 * @param {number} min - 最小值，默认 0
 * @param {number} max - 最大值，默认 100
 * @param {number} height - 图表高度
 * @param {string} title - 图表标题
 * @param {string} unit - 单位
 * @param {Array} thresholds - 阈值配置 [{ value: 30, color: 'red' }, { value: 70, color: 'yellow' }, { value: 100, color: 'green' }]
 */
export default function GaugeChart({
  value = 0,
  min = 0,
  max = 100,
  height = 200,
  title,
  unit = "%",
  thresholds,
  style,
  ...rest
}) {
  const percent = useMemo(() => {
    return (value - min) / (max - min);
  }, [value, min, max]);

  const config = useMemo(() => {
    const defaultThresholds = [
      { value: 0.3, color: "#ef4444" }, // 红色
      { value: 0.7, color: "#eab308" }, // 黄色
      { value: 1, color: "#22c55e" }, // 绿色
    ];

    const rangeColors = thresholds || defaultThresholds;

    return {
      percent,
      height,
      range: {
        ticks: (rangeColors || []).map((t) => t.value),
        color: (rangeColors || []).map((t) => t.color),
      },
      indicator: {
        pointer: {
          style: {
            stroke: "#64748b",
          },
        },
        pin: {
          style: {
            stroke: "#64748b",
          },
        },
      },
      axis: {
        label: {
          formatter(v) {
            return Math.round(Number(v) * (max - min) + min);
          },
          style: {
            fill: "#64748b",
            fontSize: 10,
          },
        },
        subTickLine: {
          count: 3,
        },
      },
      statistic: {
        title: {
          content: title || "",
          style: {
            fontSize: "14px",
            color: "#94a3b8",
          },
        },
        content: {
          formatter: () => `${value}${unit}`,
          style: {
            fontSize: "24px",
            fontWeight: "bold",
            color: "#e2e8f0",
          },
        },
      },
      animation: {
        appear: {
          animation: "fade-in",
          duration: 800,
        },
      },
      ...rest,
    };
  }, [percent, height, max, min, value, unit, title, thresholds, rest]);

  return (
    <div style={style}>
      <Gauge {...config} />
    </div>
  );
}
