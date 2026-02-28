/**
 * 面积图组件 - 基于 @ant-design/plots
 * 用于趋势展示、数据量变化
 */

import { Area } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * AreaChart - 面积图
 * @param {Array} data - 数据源
 * @param {string} xField - X轴字段名
 * @param {string} yField - Y轴字段名
 * @param {string} seriesField - 系列字段（堆叠时使用）
 * @param {boolean} isStack - 是否堆叠
 * @param {boolean} isPercent - 是否百分比堆叠
 * @param {number} height - 图表高度
 * @param {function} formatter - 值格式化函数
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 */
export default function AreaChart({
  data = [],
  xField = "date",
  yField = "value",
  seriesField,
  isStack = false,
  isPercent = false,
  height = 300,
  formatter,
  colors,
  title,
  smooth = true,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const cfg = {
      data,
      xField,
      yField,
      height,
      smooth,
      isStack,
      isPercent,
      areaStyle: {
        fillOpacity: 0.6,
      },
      line: {
        style: {
          lineWidth: 2,
        },
      },
      tooltip: {
        showMarkers: true,
        shared: true,
        formatter: formatter
          ? (datum) => ({
              name: datum[seriesField] || yField,
              value: formatter(datum[yField]),
            })
          : undefined,
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
          formatter: isPercent ? (v) => `${(v * 100).toFixed(0)}%` : formatter,
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
      legend: seriesField
        ? {
            position: "top-right",
            itemName: {
              style: {
                fill: "#94a3b8",
              },
            },
          }
        : false,
      animation: {
        appear: {
          animation: "wave-in",
          duration: 1000,
        },
      },
      ...rest,
    };

    if (seriesField) {
      cfg.seriesField = seriesField;
    }

    if (colors) {
      cfg.color = colors;
    }

    return cfg;
  }, [
    data,
    xField,
    yField,
    seriesField,
    isStack,
    isPercent,
    height,
    smooth,
    formatter,
    colors,
    rest,
  ]);

  if (!data || data?.length === 0) {
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
      <Area {...config} />
    </div>
  );
}
