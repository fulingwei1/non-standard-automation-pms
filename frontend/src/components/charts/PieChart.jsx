/**
 * 饼图/环形图组件 - 基于 @ant-design/plots
 * 用于占比分析、构成展示
 */

import { Pie } from '@ant-design/plots'
import { useMemo } from 'react'

/**
 * PieChart - 饼图/环形图
 * @param {Array} data - 数据源 [{ type: 'A', value: 100 }, ...]
 * @param {string} angleField - 角度字段（值字段），默认 'value'
 * @param {string} colorField - 颜色字段（分类字段），默认 'type'
 * @param {boolean} donut - 是否环形图
 * @param {number} innerRadius - 内圆半径比例（环形图时有效）
 * @param {number} height - 图表高度
 * @param {function} onSliceClick - 扇区点击事件
 * @param {function} formatter - 值格式化函数
 * @param {boolean} showLabel - 是否显示标签
 * @param {string} labelType - 标签类型：'inner' | 'outer' | 'spider'
 * @param {Array} colors - 自定义颜色
 * @param {string} title - 图表标题
 * @param {object} statistic - 中心统计文本配置（环形图）
 */
export default function PieChart({
  data = [],
  angleField = 'value',
  colorField = 'type',
  donut = false,
  innerRadius = 0.6,
  height = 300,
  onSliceClick,
  formatter,
  showLabel = true,
  labelType = 'outer',
  colors,
  title,
  statistic,
  style,
  ...rest
}) {
  const config = useMemo(() => {
    const cfg = {
      data,
      angleField,
      colorField,
      height,
      radius: 0.9,
      innerRadius: donut ? innerRadius : 0,
      label: showLabel ? {
        type: labelType,
        content: ({ percent }) => `${(percent * 100).toFixed(1)}%`,
        style: {
          fill: '#94a3b8',
          fontSize: 12,
        },
      } : false,
      tooltip: {
        formatter: (datum) => ({
          name: datum[colorField],
          value: formatter ? formatter(datum[angleField]) : datum[angleField],
        }),
      },
      legend: {
        position: 'right',
        itemName: {
          style: {
            fill: '#94a3b8',
          },
        },
      },
      interactions: [
        { type: 'element-active' },
        { type: 'pie-legend-active' },
      ],
      animation: {
        appear: {
          animation: 'fade-in',
          duration: 800,
        },
      },
      statistic: donut && statistic ? {
        title: statistic.title ? {
          content: statistic.title,
          style: {
            color: '#94a3b8',
            fontSize: '14px',
          },
        } : false,
        content: statistic.content ? {
          content: statistic.content,
          style: {
            color: '#e2e8f0',
            fontSize: '24px',
            fontWeight: 'bold',
          },
        } : false,
      } : false,
      ...rest,
    }

    if (colors) {
      cfg.color = colors
    }

    return cfg
  }, [data, angleField, colorField, donut, innerRadius, height, formatter, showLabel, labelType, colors, statistic, rest])

  const handleReady = (plot) => {
    if (onSliceClick) {
      plot.on('element:click', (evt) => {
        onSliceClick(evt.data?.data)
      })
    }
  }

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
      <Pie {...config} onReady={handleReady} />
    </div>
  )
}
