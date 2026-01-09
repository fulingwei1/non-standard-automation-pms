/**
 * 漏斗图组件 - 基于 @ant-design/plots
 * 用于转化率分析、销售漏斗
 */

import { Funnel } from '@ant-design/plots'
import { useMemo } from 'react'

/**
 * FunnelChart - 漏斗图
 * @param {Array} data - 数据源 [{ stage: '线索', value: 1000 }, { stage: '商机', value: 500 }, ...]
 * @param {string} xField - 阶段字段名
 * @param {string} yField - 值字段名
 * @param {number} height - 图表高度
 * @param {boolean} isTransposed - 是否横向漏斗
 * @param {boolean} dynamicHeight - 是否动态高度
 * @param {function} formatter - 值格式化函数
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 */
export default function FunnelChart({
  data = [],
  xField = 'stage',
  yField = 'value',
  height = 300,
  isTransposed = false,
  dynamicHeight = true,
  formatter,
  colors,
  title,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    return {
      data,
      xField,
      yField,
      height,
      isTransposed,
      dynamicHeight,
      label: {
        style: {
          fill: '#e2e8f0',
          fontSize: 12,
        },
        formatter: (datum) => {
          const value = formatter ? formatter(datum[yField]) : datum[yField]
          return `${datum[xField]}: ${value}`
        },
      },
      conversionTag: {
        style: {
          fill: '#94a3b8',
          fontSize: 11,
        },
        formatter: (datum) => {
          return `转化率: ${(datum.$$percentage$$ * 100).toFixed(1)}%`
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum[xField],
          value: formatter ? formatter(datum[yField]) : datum[yField],
        }),
      },
      legend: false,
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 800,
        },
      },
      ...rest,
    }
  }, [data, xField, yField, height, isTransposed, dynamicHeight, formatter, colors, rest])

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
      <Funnel {...config} />
    </div>
  )
}
