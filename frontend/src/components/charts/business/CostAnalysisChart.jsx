/**
 * 成本分析图表 - 业务专用组件
 * 展示成本构成、预算执行、成本趋势等
 */

import { Pie, Column, DualAxes, Waterfall } from '@ant-design/plots'
import { formatCurrency } from '../../../lib/utils'

/**
 * CostAnalysisChart - 成本分析图表
 * @param {Array} data - 成本数据
 * @param {string} chartType - 图表类型 'structure' | 'budget' | 'trend' | 'waterfall'
 * @param {number} height - 图表高度
 * @param {function} onCategoryClick - 分类点击回调
 * @param {string} title - 图表标题
 */
export default function CostAnalysisChart({
  data = [],
  chartType = 'structure',
  height = 300,
  onCategoryClick,
  title,
  style,
}) {
  // 成本构成饼图
  if (chartType === 'structure') {
    const total = data.reduce((sum, item) => sum + (item.amount || item.value || 0), 0)

    const pieConfig = {
      data: data.map(item => ({
        ...item,
        type: item.category || item.type || item.name,
        value: item.amount || item.value || 0,
      })),
      angleField: 'value',
      colorField: 'type',
      height,
      radius: 0.85,
      innerRadius: 0.55,
      label: {
        type: 'spider',
        content: ({ percent, type }) => `${type}\n${(percent * 100).toFixed(1)}%`,
        style: {
          fill: '#94a3b8',
          fontSize: 11,
        },
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.type,
          value: `${formatCurrency(datum.value)} (${((datum.value / total) * 100).toFixed(1)}%)`,
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
      statistic: {
        title: {
          content: '总成本',
          style: {
            color: '#94a3b8',
            fontSize: '12px',
          },
        },
        content: {
          content: formatCurrency(total),
          style: {
            color: '#e2e8f0',
            fontSize: '20px',
            fontWeight: 'bold',
          },
        },
      },
      interactions: [
        { type: 'element-active' },
      ],
    }

    const handleReady = (plot) => {
      if (onCategoryClick) {
        plot.on('element:click', (evt) => {
          onCategoryClick(evt.data?.data)
        })
      }
    }

    return (
      <div style={style}>
        {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
        <Pie {...pieConfig} onReady={handleReady} />
      </div>
    )
  }

  // 预算执行柱状图
  if (chartType === 'budget') {
    const barConfig = {
      data: data.flatMap(item => [
        { category: item.category || item.name, type: '预算', value: item.budget || 0 },
        { category: item.category || item.name, type: '实际', value: item.actual || item.amount || 0 },
      ]),
      isGroup: true,
      xField: 'category',
      yField: 'value',
      seriesField: 'type',
      height,
      columnWidthRatio: 0.6,
      color: ['#3b82f6', '#22c55e'],
      label: {
        position: 'top',
        style: {
          fill: '#94a3b8',
          fontSize: 10,
        },
        formatter: (datum) => formatCurrency(datum.value),
      },
      tooltip: {
        formatter: (datum) => ({
          name: datum.type,
          value: formatCurrency(datum.value),
        }),
      },
      xAxis: {
        label: {
          style: {
            fill: '#94a3b8',
            fontSize: 11,
          },
          autoRotate: true,
        },
        line: {
          style: {
            stroke: '#334155',
          },
        },
      },
      yAxis: {
        label: {
          formatter: (v) => formatCurrency(v),
          style: {
            fill: '#94a3b8',
            fontSize: 11,
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
      legend: {
        position: 'top-right',
        itemName: {
          style: {
            fill: '#94a3b8',
          },
        },
      },
    }

    return (
      <div style={style}>
        {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
        <Column {...barConfig} />
      </div>
    )
  }

  // 成本趋势双轴图
  if (chartType === 'trend') {
    const dualConfig = {
      data: [data, data],
      xField: 'month' in (data[0] || {}) ? 'month' : 'date',
      yField: ['cost', 'rate'],
      height,
      geometryOptions: [
        {
          geometry: 'column',
          columnWidthRatio: 0.4,
          color: '#3b82f6',
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
              stroke: '#22c55e',
              lineWidth: 2,
            },
          },
          color: '#22c55e',
        },
      ],
      xAxis: {
        label: {
          style: {
            fill: '#94a3b8',
            fontSize: 11,
          },
        },
        line: {
          style: {
            stroke: '#334155',
          },
        },
      },
      yAxis: {
        cost: {
          label: {
            formatter: (v) => formatCurrency(v),
            style: {
              fill: '#94a3b8',
              fontSize: 11,
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
        rate: {
          label: {
            formatter: (v) => `${(v * 100).toFixed(0)}%`,
            style: {
              fill: '#94a3b8',
              fontSize: 11,
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
        custom: true,
        items: [
          { name: '成本', marker: { symbol: 'square', style: { fill: '#3b82f6' } } },
          { name: '成本率', marker: { symbol: 'line', style: { stroke: '#22c55e' } } },
        ],
      },
      tooltip: {
        shared: true,
      },
    }

    return (
      <div style={style}>
        {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
        <DualAxes {...dualConfig} />
      </div>
    )
  }

  // 成本瀑布图
  if (chartType === 'waterfall') {
    const waterfallConfig = {
      data,
      xField: 'type' in (data[0] || {}) ? 'type' : 'category',
      yField: 'value' in (data[0] || {}) ? 'value' : 'amount',
      height,
      total: {
        label: '合计',
        style: {
          fill: '#3b82f6',
        },
      },
      risingFill: '#22c55e',
      fallingFill: '#ef4444',
      label: {
        style: {
          fill: '#e2e8f0',
          fontSize: 11,
        },
        formatter: (datum) => formatCurrency(datum.value || datum.amount),
      },
      xAxis: {
        label: {
          style: {
            fill: '#94a3b8',
            fontSize: 11,
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
          formatter: (v) => formatCurrency(v),
          style: {
            fill: '#94a3b8',
            fontSize: 11,
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
    }

    return (
      <div style={style}>
        {title && <div className="text-sm font-medium text-slate-300 mb-3">{title}</div>}
        <Waterfall {...waterfallConfig} />
      </div>
    )
  }

  return (
    <div
      className="flex items-center justify-center text-slate-400"
      style={{ height, ...style }}
    >
      不支持的图表类型
    </div>
  )
}
