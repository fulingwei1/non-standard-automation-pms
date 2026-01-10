/**
 * 矩形树图组件 - 基于 @ant-design/plots
 * 用于层级数据展示、占比分析
 */

import { Treemap } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * TreemapChart - 矩形树图
 * @param {object} data - 层级数据源 { name: 'root', children: [{ name: 'A', value: 100 }, ...] }
 * @param {number} height - 图表高度
 * @param {function} formatter - 值格式化函数
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 * @param {function} onDrillDown - 下钻回调
 */
export default function TreemapChart({
  data = {},
  height = 300,
  formatter,
  colors,
  title,
  onDrillDown,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    return {
      data,
      colorField: "name",
      height,
      label: {
        style: {
          fill: "#e2e8f0",
          fontSize: 12,
        },
        formatter: (datum) => {
          const value = formatter ? formatter(datum.value) : datum.value;
          return `${datum.name}\n${value}`;
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.name,
          value: formatter ? formatter(datum.value) : datum.value,
        }),
      },
      legend: {
        position: "top-right",
        itemName: {
          style: {
            fill: "#94a3b8",
          },
        },
      },
      interactions: [
        { type: "element-active" },
        { type: "treemap-drill-down" },
      ],
      drilldown: {
        enabled: true,
        breadCrumb: {
          textStyle: {
            fill: "#94a3b8",
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
  }, [data, height, formatter, colors, rest]);

  const handleReady = (plot) => {
    if (onDrillDown) {
      plot.on("element:click", (evt) => {
        const nodeData = evt.data?.data;
        if (nodeData?.children?.length > 0) {
          onDrillDown(nodeData);
        }
      });
    }
  };

  if (!data || !data.children || data.children.length === 0) {
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
      <Treemap {...config} onReady={handleReady} />
    </div>
  );
}
