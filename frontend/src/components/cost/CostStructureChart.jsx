/**
 * Cost Structure Chart Component - 成本结构图表组件
 * 用于展示成本按分类的占比（饼图）
 */

import { useMemo } from 'react'
import { formatCurrency } from '../../lib/utils'

export function CostStructureChart({ 
  data, 
  size = 300,
  showLegend = true 
}) {
  // data格式: [{ category: '硬件成本', amount: 80000, percentage: 50 }, ...]
  
  const total = useMemo(() => {
    return data.reduce((sum, item) => sum + (item.amount || 0), 0)
  }, [data])
  
  if (!data || data.length === 0 || total === 0) {
    return (
      <div className="flex items-center justify-center" style={{ height: `${size}px` }}>
        <div className="text-slate-400">暂无数据</div>
      </div>
    )
  }
  
  const radius = size / 2 - 20
  const centerX = size / 2
  const centerY = size / 2
  
  const segments = useMemo(() => {
    let currentAngle = -90 // Start from top
    
    return data.map((item, index) => {
      const amount = item.amount || 0
      const percentage = (amount / total) * 100
      const angle = (amount / total) * 360
      
      const startAngle = currentAngle
      const endAngle = currentAngle + angle
      currentAngle = endAngle
      
      const startAngleRad = (startAngle * Math.PI) / 180
      const endAngleRad = (endAngle * Math.PI) / 180
      
      const x1 = centerX + radius * Math.cos(startAngleRad)
      const y1 = centerY + radius * Math.sin(startAngleRad)
      const x2 = centerX + radius * Math.cos(endAngleRad)
      const y2 = centerY + radius * Math.sin(endAngleRad)
      
      const largeArcFlag = angle > 180 ? 1 : 0
      
      const pathData = [
        `M ${centerX} ${centerY}`,
        `L ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
        'Z',
      ].join(' ')
      
      // Generate color based on index
      const hue = (index * 360) / data.length
      const color = `hsl(${hue}, 70%, 50%)`
      
      return {
        pathData,
        percentage,
        color,
        label: item.category,
        amount,
        startAngle,
        endAngle,
      }
    })
  }, [data, total, radius, centerX, centerY])
  
  return (
    <div className="flex items-center gap-8">
      {/* Pie Chart */}
      <div className="relative" style={{ width: `${size}px`, height: `${size}px` }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {segments.map((segment, index) => (
            <g key={index}>
              <path
                d={segment.pathData}
                fill={segment.color}
                stroke="rgb(15 23 42)"
                strokeWidth="2"
                className="transition-opacity hover:opacity-80 cursor-pointer"
              />
            </g>
          ))}
        </svg>
        
        {/* Center label */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">
              {formatCurrency(total)}
            </div>
            <div className="text-xs text-slate-400">总成本</div>
          </div>
        </div>
      </div>
      
      {/* Legend */}
      {showLegend && (
        <div className="flex-1 space-y-3">
          {segments.map((segment, index) => (
            <div key={index} className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: segment.color }}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-300 truncate">{segment.label}</span>
                  <span className="text-white font-medium ml-2">
                    {formatCurrency(segment.amount)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all"
                      style={{
                        width: `${segment.percentage}%`,
                        backgroundColor: segment.color,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-500 w-12 text-right">
                    {segment.percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
