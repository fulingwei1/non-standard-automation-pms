/**
 * 项目健康度图表 - 业务专用组件
 * 展示项目健康度分布：H1正常、H2有风险、H3阻塞、H4已完结
 */

import { Pie, Column } from '@ant-design/plots'
import { useMemo, useState } from 'react'

const HEALTH_CONFIG = {
  H1: { label: '正常', color: '#22c55e', description: '项目进展顺利' },
  H2: { label: '有风险', color: '#eab308', description: '存在潜在风险需关注' },
  H3: { label: '阻塞', color: '#ef4444', description: '项目遇到阻塞问题' },
  H4: { label: '已完结', color: '#64748b', description: '项目已结束' },
}

/**
 * ProjectHealthChart - 项目健康度图表
 * @param {object} data - 健康度数据 { H1: 10, H2: 5, H3: 2, H4: 3 }
 * @param {string} chartType - 图表类型 'pie' | 'bar' | 'donut'
 * @param {number} height - 图表高度
 * @param {function} onHealthClick - 点击回调，返回健康度类型
 * @param {string} title - 图表标题
 */
export default function ProjectHealthChart({
  data = {},
  chartType = 'donut',
  height = 280,
  onHealthClick,
  title = '项目健康度分布',
  style,
}) {
  const [activeHealth, setActiveHealth] = useState(null)

  const chartData = useMemo(() => {
    return Object.entries(HEALTH_CONFIG).map(([key, config]) => ({
      type: config.label,
      value: data[key] || 0,
      healthCode: key,
      color: config.color,
    })).filter(item => item.value > 0)
  }, [data])

  const total = useMemo(() => {
    return chartData.reduce((sum, item) => sum + item.value, 0)
  }, [chartData])

  const handleReady = (plot) => {
    plot.on('element:click', (evt) => {
      const healthCode = evt.data?.data?.healthCode
      if (healthCode && onHealthClick) {
        onHealthClick(healthCode)
      }
      setActiveHealth(healthCode)
    })
  }

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-slate-400"
        style={{ height, ...style }}
      >
        暂无项目数据
      </div>
    )
  }

  // 饼图/环形图配置
  if (chartType === 'pie' || chartType === 'donut') {
    const pieConfig = {
      data: chartData,
      angleField: 'value',
      colorField: 'type',
      height,
      radius: 0.85,
      innerRadius: chartType === 'donut' ? 0.6 : 0,
      color: chartData.map(d => d.color),
      label: {
        type: 'outer',
        content: ({ percent, type }) => `${type} ${(percent * 100).toFixed(0)}%`,
        style: {
          fill: '#94a3b8',
          fontSize: 12,
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.type,
          value: `${datum.value} 个项目 (${((datum.value / total) * 100).toFixed(1)}%)`,
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
      statistic: chartType === 'donut' ? {
        title: {
          content: '总项目',
          style: {
            color: '#94a3b8',
            fontSize: '14px',
          },
        },
        content: {
          content: `${total}`,
          style: {
            color: '#e2e8f0',
            fontSize: '28px',
            fontWeight: 'bold',
          },
        },
      } : false,
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
    }

    return (
      <div style={style}>
        {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
        <Pie {...pieConfig} onReady={handleReady} />
      </div>
    )
  }

  // 柱状图配置
  const barConfig = {
    data: chartData,
    xField: 'type',
    yField: 'value',
    height,
    color: ({ type }) => {
      const item = chartData.find(d => d.type === type)
      return item?.color || '#64748b'
    },
    columnWidthRatio: 0.5,
    label: {
      position: 'top',
      style: {
        fill: '#94a3b8',
        fontSize: 12,
      },
    },
    tooltip: {
      formatter: (datum) => ({
        name: datum.type,
        value: `${datum.value} 个项目`,
      }),
    },
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
      label: {
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
    animation: {
      appear: {
        animation: 'scale-in-y',
        duration: 800,
      },
    },
  }

  return (
    <div style={style}>
      {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
      <Column {...barConfig} onReady={handleReady} />
    </div>
  )
}
