/**
 * 双轴图组件 - 基于 @ant-design/plots
 * 用于不同量纲数据对比（如金额+百分比）
 */

import { DualAxes } from '@ant-design/plots'
import { useMemo } from 'react'

/**
 * DualAxesChart - 双轴图
 * @param {Array} data - 数据源（可以是单数组或双数组）
 * @param {string} xField - X轴字段名
 * @param {Array} yField - Y轴字段名数组 ['value1', 'value2']
 * @param {number} height - 图表高度
 * @param {Array} geometryOptions - 图形配置 [{ geometry: 'column' }, { geometry: 'line' }]
 * @param {function} leftFormatter - 左轴格式化
 * @param {function} rightFormatter - 右轴格式化
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 */
export default function DualAxesChart({
  data = [],
  xField = 'date',
  yField = ['value', 'rate'],
  height = 300,
  geometryOptions,
  leftFormatter,
  rightFormatter,
  colors,
  title,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const defaultGeometryOptions = [
      {
        geometry: 'column',
        columnWidthRatio: 0.4,
        color: colors?.[0] || '#5B8FF9',
      },
      {
        geometry: 'line',
        smooth: true,
        lineStyle: {
          lineWidth: 2,
        },
        point: {
          size: 4,
          shape: 'circle',
          style: {
            fill: 'white',
            stroke: colors?.[1] || '#5AD8A6',
            lineWidth: 2,
          },
        },
        color: colors?.[1] || '#5AD8A6',
      },
    ]

    return {
      data: [data, data],
      xField,
      yField,
      height,
      geometryOptions: geometryOptions || defaultGeometryOptions,
      xAxis: {
        label: {
          style: {
            fill: '#94a3b8',
            fontSize: 12,
          },
        },
        line: {
          style: {
            stroke: '#334155',
          },
        },
      },
      yAxis: {
        [yField[0]]: {
          label: {
            formatter: leftFormatter,
            style: {
              fill: '#94a3b8',
              fontSize: 12,
            },
          },
          grid: {
            line: {
              style: {
                stroke: '#334155',
                lineDash: [4, 4],
              },
            },
          },
        },
        [yField[1]]: {
          label: {
            formatter: rightFormatter,
            style: {
              fill: '#94a3b8',
              fontSize: 12,
            },
          },
        },
      },
      legend: {
        position: 'top-right',
        itemName: {
          style: {
            fill: '#94a3b8',
          },
        },
      },
      tooltip: {
        shared: true,
        showMarkers: true,
      },
      animation: {
        appear: {
          duration: 800,
        },
      },
      ...rest,
    }
  }, [data, xField, yField, height, geometryOptions, leftFormatter, rightFormatter, colors, rest])

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
      <DualAxes {...config} />
    </div>
  )
}
