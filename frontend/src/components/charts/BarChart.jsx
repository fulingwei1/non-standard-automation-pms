/**
 * 柱状图组件 - 基于 @ant-design/plots
 * 用于分类数据对比、排名展示
 */

import { Column, Bar } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * BarChart - 柱状图/条形图
 * @param {Array} data - 数据源 [{ category: 'A', value: 100 }, ...]
 * @param {string} xField - X轴字段名，默认 'category'
 * @param {string} yField - Y轴字段名，默认 'value'
 * @param {string} seriesField - 系列字段（分组/堆叠时使用）
 * @param {boolean} horizontal - 是否水平条形图
 * @param {boolean} isGroup - 是否分组柱状图
 * @param {boolean} isStack - 是否堆叠柱状图
 * @param {number} height - 图表高度
 * @param {function} onBarClick - 柱子点击事件
 * @param {function} formatter - 值格式化函数
 * @param {boolean} showLabel - 是否显示数据标签
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 */
export default function BarChart({
  data = [],
  xField = "category",
  yField = "value",
  seriesField,
  horizontal = false,
  isGroup = false,
  isStack = false,
  height = 300,
  onBarClick,
  formatter,
  showLabel = false,
  colors,
  title,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const cfg = {
      data,
      xField: horizontal ? yField : xField,
      yField: horizontal ? xField : yField,
      height,
      isGroup,
      isStack,
      columnWidthRatio: 0.6,
      tooltip: {
        formatter: formatter
          ? (datum) => ({
              name: datum[seriesField] || (horizontal ? xField : yField),
              value: formatter(datum[horizontal ? xField : yField]),
            })
          : undefined,
      },
      label: showLabel
        ? {
            position: horizontal ? "right" : "top",
            style: {
              fill: "#94a3b8",
              fontSize: 11,
            },
            formatter: formatter
              ? (datum) => formatter(datum[horizontal ? xField : yField])
              : undefined,
          }
        : false,
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 12,
          },
          autoRotate: true,
        },
        line: {
          style: {
            stroke: "#334155",
          },
        },
      },
      yAxis: {
        label: {
          formatter: horizontal ? undefined : formatter,
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
          animation: horizontal ? "scale-in-x" : "scale-in-y",
          duration: 800,
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
    horizontal,
    isGroup,
    isStack,
    height,
    formatter,
    showLabel,
    colors,
    rest,
  ]);

  const handleReady = (plot) => {
    if (onBarClick) {
      plot.on("element:click", (evt) => {
        onBarClick(evt.data?.data);
      });
    }
  };

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

  const ChartComponent = horizontal ? Bar : Column;

  return (
    <div style={style}>
      {title && (
        <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
      )}
      <ChartComponent {...config} onReady={handleReady} />
    </div>
  );
}
