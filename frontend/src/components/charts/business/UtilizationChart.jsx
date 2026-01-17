/**
 * 人员利用率图表 - 业务专用组件
 * 展示人员工时利用率、部门负荷分布
 */

import { Bar, Radar, Heatmap } from "@ant-design/plots";
import { useMemo } from "react";

/**
 * UtilizationChart - 人员利用率图表
 * @param {Array} data - 利用率数据
 * @param {string} chartType - 图表类型 'bar' | 'radar' | 'heatmap'
 * @param {number} height - 图表高度
 * @param {function} onPersonClick - 人员点击回调
 * @param {string} title - 图表标题
 */
export default function UtilizationChart({
  data = [],
  chartType = "bar",
  height = 300,
  onPersonClick,
  title,
  style,
}) {
  const sortedData = useMemo(() => {
    return [...data]
      .sort(
        (a, b) =>
          (b.rate || b.utilization || 0) - (a.rate || a.utilization || 0),
      )
      .slice(0, 15);
  }, [data]);

  // 水平条形图（人员排名）
  if (chartType === "bar") {
    const barConfig = {
      data: sortedData,
      xField: "rate" in (sortedData[0] || {}) ? "rate" : "utilization",
      yField: "name" in (sortedData[0] || {}) ? "name" : "user",
      height,
      color: ({ rate, utilization }) => {
        const r = rate || utilization || 0;
        if (r >= 100) return "#ef4444"; // 过载
        if (r >= 80) return "#22c55e"; // 饱和
        if (r >= 60) return "#3b82f6"; // 正常
        return "#64748b"; // 空闲
      },
      barWidthRatio: 0.6,
      label: {
        position: "right",
        formatter: (datum) =>
          `${(datum.rate || datum.utilization || 0).toFixed(0)}%`,
        style: {
          fill: "#e2e8f0",
          fontSize: 11,
        },
      },
      annotations: [
        {
          type: "line",
          start: [80, "min"],
          end: [80, "max"],
          style: {
            stroke: "#22c55e",
            lineDash: [4, 4],
          },
        },
        {
          type: "line",
          start: [100, "min"],
          end: [100, "max"],
          style: {
            stroke: "#ef4444",
            lineDash: [4, 4],
          },
        },
      ],
      xAxis: {
        min: 0,
        max: 120,
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
      yAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
          },
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.name || datum.user,
          value: `${(datum.rate || datum.utilization || 0).toFixed(1)}%`,
        }),
      },
    };

    const handleReady = (plot) => {
      if (onPersonClick) {
        plot.on("element:click", (evt) => {
          onPersonClick(evt.data?.data);
        });
      }
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Bar {...barConfig} onReady={handleReady} />
      </div>
    );
  }

  // 雷达图（部门对比）
  if (chartType === "radar") {
    const radarConfig = {
      data,
      xField: "department" in (data[0] || {}) ? "department" : "item",
      yField: "rate" in (data[0] || {}) ? "rate" : "value",
      seriesField: "period" in (data[0] || {}) ? "period" : undefined,
      height,
      area: {
        style: {
          fillOpacity: 0.25,
        },
      },
      point: {
        size: 3,
      },
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
          },
        },
        line: null,
        tickLine: null,
        grid: {
          line: {
            style: {
              stroke: "#334155",
            },
          },
        },
      },
      yAxis: {
        label: {
          formatter: (v) => `${v}%`,
          style: {
            fill: "#64748b",
            fontSize: 10,
          },
        },
        grid: {
          line: {
            style: {
              stroke: "#334155",
            },
          },
          alternateColor: "rgba(51, 65, 85, 0.2)",
        },
      },
      legend: {
        position: "top-right",
        itemName: {
          style: {
            fill: "#94a3b8",
          },
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.department || datum.item,
          value: `${(datum.rate || datum.value || 0).toFixed(1)}%`,
        }),
      },
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Radar {...radarConfig} />
      </div>
    );
  }

  // 热力图（时间×人员）
  if (chartType === "heatmap") {
    const heatmapConfig = {
      data,
      xField: "week" in (data[0] || {}) ? "week" : "date",
      yField: "name" in (data[0] || {}) ? "name" : "user",
      colorField: "hours" in (data[0] || {}) ? "hours" : "value",
      height,
      color: [
        "#1e40af",
        "#3b82f6",
        "#60a5fa",
        "#93c5fd",
        "#22c55e",
        "#eab308",
        "#ef4444",
      ],
      meta: {
        hours: {
          alias: "工时",
        },
        value: {
          alias: "工时",
        },
      },
      label: {
        style: {
          fill: "#e2e8f0",
          fontSize: 10,
        },
      },
      xAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
          },
        },
      },
      yAxis: {
        label: {
          style: {
            fill: "#94a3b8",
            fontSize: 11,
          },
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: `${datum.name || datum.user} - ${datum.week || datum.date}`,
          value: `${datum.hours || datum.value || 0} 小时`,
        }),
      },
    };

    return (
      <div style={style}>
        {title && (
          <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>
        )}
        <Heatmap {...heatmapConfig} />
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
