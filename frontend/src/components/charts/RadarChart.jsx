/**
 * 雷达图组件 - 基于 @ant-design/plots
 * 用于多维度数据对比、能力评估
 */

import { Radar } from '@ant-design/plots'
import { useMemo } from 'react'

/**
 * RadarChart - 雷达图
 * @param {Array} data - 数据源 [{ item: '维度1', value: 80, user: 'A' }, ...]
 * @param {string} xField - 维度字段名，默认 'item'
 * @param {string} yField - 值字段名，默认 'value'
 * @param {string} seriesField - 系列字段（多系列对比时使用）
 * @param {number} height - 图表高度
 * @param {boolean} showArea - 是否显示填充区域
 * @param {boolean} showPoint - 是否显示数据点
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 */
export default function RadarChart({
  data = [],
  xField = 'item',
  yField = 'value',
  seriesField,
  height = 300,
  showArea = true,
  showPoint = true,
  colors,
  title,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const cfg = {
      data,
      xField,
      yField,
      height,
      area: showArea ? {
        style: {
          fillOpacity: 0.25,
        },
      } : false,
      point: showPoint ? {
        size: 3,
      } : false,
      xAxis: {
        label: {
          style: {
            fill: '#94a3b8',
            fontSize: 12,
          },
        },
        line: null,
        tickLine: null,
        grid: {
          line: {
            style: {
              stroke: '#334155',
            },
          },
        },
      },
      yAxis: {
        label: {
          style: {
            fill: '#64748b',
            fontSize: 10,
          },
        },
        grid: {
          line: {
            style: {
              stroke: '#334155',
            },
          },
          alternateColor: 'rgba(51, 65, 85, 0.2)',
        },
      },
      legend: seriesField ? {
        position: 'top-right',
        itemName: {
          style: {
            fill: '#94a3b8',
          },
        },
      } : false,
      tooltip: {
        showMarkers: false,
      },
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 800,
        },
      },
      ...rest,
    }

    if (seriesField) {
      cfg.seriesField = seriesField
    }

    if (colors) {
      cfg.color = colors
    }

    return cfg
  }, [data, xField, yField, seriesField, height, showArea, showPoint, colors, rest])

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-slate-400"
        style={{ height, ...style }}
      >
        暂无数据
      </div>
    )
  }

  return (
    <div style={style}>
      {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
      <Radar {...config} />
    </div>
  )
}
