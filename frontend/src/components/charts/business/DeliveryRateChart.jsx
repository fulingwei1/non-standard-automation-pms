/**
 * 交付准时率图表 - 业务专用组件
 * 展示项目交付准时率趋势和分布
 */

import { Line, Column, Gauge } from "@ant-design/plots";

/**
 * DeliveryRateChart - 交付准时率图表
 * @param {Array|object} data - 数据
 * @param {string} chartType - 图表类型 'gauge' | 'trend' | 'comparison'
 * @param {number} height - 图表高度
 * @param {string} title - 图表标题
 */
export default function DeliveryRateChart({
  data,
  chartType = "gauge",
  height = 250,
  title,
  style,
}) {
  // 仪表盘（单一准时率）
  if (chartType === "gauge") {
    const rate =
      typeof data === "number" ? data : data?.rate || data?.onTimeRate || 0;
    const percent = rate / 100;

    const gaugeConfig = {
      percent,
      height,
      range: {
        ticks: [0, 0.6, 0.8, 1],
        color: ["#ef4444", "#eab308", "#22c55e"],
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
            return `${Math.round(Number(v) * 100)}%`;
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
          content: "准时率",
          style: {
            fontSize: "14px",
            color: "#94a3b8",
          },
        },
        content: {
          formatter: () => `${rate.toFixed(1)}%`,
          style: {
            fontSize: "24px",
            fontWeight: "bold",
            color: rate >= 80 ? "#22c55e" : rate >= 60 ? "#eab308" : "#ef4444",
          },
        },
      },
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Gauge {...gaugeConfig} />
      </div>
    );
  }

  // 趋势图
  if (chartType === "trend") {
    const trendData = Array.isArray(data) ? data : [];

    const lineConfig = {
      data: trendData,
      xField: "month" in (trendData[0] || {}) ? "month" : "date",
      yField: "rate" in (trendData[0] || {}) ? "rate" : "value",
      height,
      smooth: true,
      point: {
        size: 4,
        shape: "circle",
        style: {
          fill: "white",
          stroke: "#22c55e",
          lineWidth: 2,
        },
      },
      color: "#22c55e",
      areaStyle: {
        fillOpacity: 0.15,
      },
      annotations: [
        {
          type: "line",
          start: ["min", 80],
          end: ["max", 80],
          style: {
            stroke: "#eab308",
            lineDash: [4, 4],
          },
          text: {
            content: "目标 80%",
            position: "end",
            style: {
              fill: "#eab308",
              fontSize: 10,
            },
          },
        },
      ],
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
          },
        },
        line: {
          style: {
            stroke: "#334155",
          },
        },
      },
      yAxis: {
        min: 0,
        max: 100,
        label: {
          formatter: (v) => `${v}%`,
          style: {
            fill: "#94a3b8",
            fontSize: 11,
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
          name: "准时率",
          value: `${datum.rate || datum.value}%`,
        }),
      },
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Line {...lineConfig} />
      </div>
    );
  }

  // 部门/项目对比图
  if (chartType === "comparison") {
    const compData = Array.isArray(data) ? data : [];

    const barConfig = {
      data: compData.sort(
        (a, b) => (b.rate || b.value || 0) - (a.rate || a.value || 0),
      ),
      xField: "name" in (compData[0] || {}) ? "name" : "category",
      yField: "rate" in (compData[0] || {}) ? "rate" : "value",
      height,
      columnWidthRatio: 0.5,
      color: ({ rate, value }) => {
        const r = rate || value || 0;
        return r >= 80 ? "#22c55e" : r >= 60 ? "#eab308" : "#ef4444";
      },
      label: {
        position: "top",
        formatter: (datum) => `${(datum.rate || datum.value || 0).toFixed(1)}%`,
        style: {
          fill: "#94a3b8",
          fontSize: 11,
        },
      },
      annotations: [
        {
          type: "line",
          start: ["min", 80],
          end: ["max", 80],
          style: {
            stroke: "#eab308",
            lineDash: [4, 4],
          },
        },
      ],
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
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
        min: 0,
        max: 100,
        label: {
          formatter: (v) => `${v}%`,
          style: {
            fill: "#94a3b8",
            fontSize: 11,
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
          name: datum.name || datum.category,
          value: `${(datum.rate || datum.value || 0).toFixed(1)}%`,
        }),
      },
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Column {...barConfig} />
      </div>
    );
  }

  return (
    <div
      className="flex items-center justify-center text-slate-400"
      style={{ height, ...style }}
    >
      暂无数据
    </div>
  );
}
