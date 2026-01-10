/**
 * 瀑布图组件 - 基于 @ant-design/plots
 * 用于财务分析、成本分解
 */

import { Waterfall } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * WaterfallChart - 瀑布图
 * @param {Array} data - 数据源 [{ type: '收入', value: 1000 }, { type: '成本', value: -500 }, ...]
 * @param {string} xField - X轴字段名
 * @param {string} yField - Y轴字段名
 * @param {number} height - 图表高度
 * @param {function} formatter - 值格式化函数
 * @param {object} colors - 颜色配置 { rising: '#22c55e', falling: '#ef4444', total: '#3b82f6' }
 * @param {string} title - 图表标题
 */
export default function WaterfallChart({
  data = [],
  xField = "type",
  yField = "value",
  height = 300,
  formatter,
  colors,
  title,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const defaultColors = {
      rising: "#22c55e",
      falling: "#ef4444",
      total: "#3b82f6",
    };
    const colorConfig = { ...defaultColors, ...colors };

    return {
      data,
      xField,
      yField,
      height,
      appendPadding: [20, 0, 0, 0],
      meta: {
        [xField]: {
          alias: "类型",
        },
        [yField]: {
          alias: "金额",
          formatter,
        },
      },
      total: {
        label: "合计",
        style: {
          fill: colorConfig.total,
        },
      },
      risingFill: colorConfig.rising,
      fallingFill: colorConfig.falling,
      label: {
        style: {
          fill: "#e2e8f0",
          fontSize: 11,
        },
        formatter: (datum) =>
          formatter ? formatter(datum[yField]) : datum[yField],
      },
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 12,
          },
        },
        line: {
          style: {
            stroke: "#334155",
          },
        },
      },
      yAxis: {
        label: {
          formatter,
          style: {
            fill: "#94a3b8",
            fontSize: 12,
          },
        },
        grid: {
          line: {
            style: {
              stroke: "#334155",
              lineDash: [4, 4],
            },
          },
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum[xField],
          value: formatter ? formatter(datum[yField]) : datum[yField],
        }),
      },
      animation: {
        appear: {
          animation: "scale-in-y",
          duration: 800,
        },
      },
      ...rest,
    };
  }, [data, xField, yField, height, formatter, colors, rest]);

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-slate-400"
        style={{ height, ...style }}
      >
        暂无数据
      </div>
    );
  }

  return (
    <div style={style}>
      {title && (
        <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
      )}
      <Waterfall {...config} />
    </div>
  );
}
