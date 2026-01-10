/**
 * 折线图组件 - 基于 @ant-design/plots
 * 用于趋势分析、时间序列数据展示
 */

import { Line } from "@ant-design/plots";
import { useMemo } from "react";

const defaultConfig = {
  padding: "auto",
  xField: "date",
  yField: "value",
  smooth: true,
  animation: {
    appear: {
      animation: "path-in",
      duration: 1000,
    },
  },
  theme: {
    styleSheet: {
      backgroundColor: "transparent",
    },
  },
};

/**
 * LineChart - 折线图
 * @param {Array} data - 数据源 [{ date: '2024-01', value: 100, category: 'A' }, ...]
 * @param {string} xField - X轴字段名，默认 'date'
 * @param {string} yField - Y轴字段名，默认 'value'
 * @param {string} seriesField - 系列字段（多线条时使用）
 * @param {number} height - 图表高度，默认 300
 * @param {boolean} showPoint - 是否显示数据点
 * @param {boolean} showArea - 是否显示区域填充
 * @param {function} onPointClick - 数据点点击事件
 * @param {function} formatter - Y轴格式化函数
 * @param {string} title - 图表标题
 * @param {object} style - 自定义样式
 */
export default function LineChart({
  data = [],
  xField = "date",
  yField = "value",
  seriesField,
  height = 300,
  showPoint = true,
  showArea = false,
  onPointClick,
  formatter,
  title,
  colors,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const cfg = {
      ...defaultConfig,
      data,
      xField,
      yField,
      height,
      point: showPoint
        ? {
            size: 4,
            shape: "circle",
            style: {
              fill: "white",
              stroke: "#5B8FF9",
              lineWidth: 2,
            },
          }
        : false,
      area: showArea
        ? {
            style: {
              fillOpacity: 0.15,
            },
          }
        : false,
      tooltip: {
        showMarkers: true,
        shared: true,
        showCrosshairs: true,
        crosshairs: {
          type: "xy",
        },
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
        tickLine: {
          style: {
            stroke: "#334155",
          },
        },
      },
      yAxis: {
        label: {
          formatter: formatter,
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
    height,
    showPoint,
    showArea,
    formatter,
    colors,
    rest,
  ]);

  const handleReady = (plot) => {
    if (onPointClick) {
      plot.on("point:click", (evt) => {
        onPointClick(evt.data?.data);
      });
    }
  };

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
      <Line {...config} onReady={handleReady} />
    </div>
  );
}
