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
  const normalized = useMemo(() => {
    const numericMin = Number.isFinite(Number(min)) ? Number(min) : 0;
    const rawMax = Number.isFinite(Number(max)) ? Number(max) : 100;
    const numericMax = rawMax === numericMin ? numericMin + 1 : rawMax;
    const numericValue = Number.isFinite(Number(value)) ? Number(value) : numericMin;
    const clampedValue = Math.min(Math.max(numericValue, numericMin), numericMax);
    const percent = (clampedValue - numericMin) / (numericMax - numericMin);

    return {
      value: clampedValue,
      percent: Math.min(Math.max(percent, 0), 1),
    };
  }, [value, min, max]);

  const displayValue = useMemo(() => {
    const rounded = Math.round(normalized.value * 10) / 10;
    return Number.isInteger(rounded) ? String(rounded) : String(rounded);
  }, [normalized.value]);

  const config = useMemo(() => {
    const defaultThresholds = [
      { value: 0.3, color: "#ef4444" }, // 红色
      { value: 0.7, color: "#eab308" }, // 黄色
      { value: 1, color: "#22c55e" }, // 绿色
    ];

    const rangeColors = thresholds || defaultThresholds;
    const thresholdValues = rangeColors.map((t) =>
      Math.min(Math.max(Number(t.value) || 0, 0), 1)
    );
    const thresholdColors = rangeColors.map((t) => t.color);
    const { children: _children, ...rootOptions } = rest;

    return {
      height,
      ...rootOptions,
      children: [
        {
          type: "gauge",
          data: {
            target: normalized.percent,
            total: 1,
            thresholds: thresholdValues,
          },
          scale: {
            color: {
              range: thresholdColors,
            },
          },
          style: {
            pointerStroke: "#64748b",
            pinStroke: "#64748b",
            textContent: () => `${displayValue}${unit}`,
            textFontSize: 24,
            textFontWeight: "bold",
            textFill: "#e2e8f0",
          },
          animate: {
            enter: {
              type: "fadeIn",
              duration: 800,
            },
          },
        },
      ],
    };
  }, [height, normalized.percent, displayValue, unit, thresholds, rest]);

  return (
    <div style={style}>
      {title && (
        <div className="text-center text-sm text-slate-400 mb-2">{title}</div>
      )}
      <Gauge {...config} />
    </div>
  );
}
