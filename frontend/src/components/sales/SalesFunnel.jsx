/**
 * Sales Funnel Component - Visualizes sales pipeline stages
 */

import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'
import { fadeIn } from '../../lib/animations'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const funnelStages = [
  { key: 'lead', label: '潜在客户', color: 'from-violet-500 to-purple-600' },
  { key: 'contact', label: '意向洽谈', color: 'from-blue-500 to-cyan-500' },
  { key: 'quote', label: '报价阶段', color: 'from-amber-500 to-orange-500' },
  { key: 'negotiate', label: '合同谈判', color: 'from-pink-500 to-rose-500' },
  { key: 'won', label: '签约赢单', color: 'from-emerald-500 to-green-500' },
]

export default function SalesFunnel({ data = {}, onStageClick }) {
  // Default mock data if not provided
  const funnelData = {
    lead: data.lead ?? 12,
    contact: data.contact ?? 8,
    quote: data.quote ?? 5,
    negotiate: data.negotiate ?? 3,
    won: data.won ?? 2,
  }

  const maxValue = Math.max(...Object.values(funnelData), 1)

  const getTrend = (stage) => {
    // Mock trend data
    const trends = {
      lead: { value: 15, direction: 'up' },
      contact: { value: 8, direction: 'up' },
      quote: { value: 5, direction: 'down' },
      negotiate: { value: 0, direction: 'flat' },
      won: { value: 25, direction: 'up' },
    }
    return trends[stage] || { value: 0, direction: 'flat' }
  }

  return (
    <motion.div variants={fadeIn} className="space-y-3">
      {funnelStages.map((stage, index) => {
        const count = funnelData[stage.key]
        const widthPercent = Math.max((count / maxValue) * 100, 20)
        const trend = getTrend(stage.key)

        return (
          <motion.div
            key={stage.key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onStageClick?.(stage.key)}
            className="cursor-pointer group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
                {stage.label}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-white">{count}</span>
                {trend.direction === 'up' && (
                  <span className="flex items-center text-xs text-emerald-400">
                    <TrendingUp className="w-3 h-3 mr-0.5" />
                    {trend.value}%
                  </span>
                )}
                {trend.direction === 'down' && (
                  <span className="flex items-center text-xs text-red-400">
                    <TrendingDown className="w-3 h-3 mr-0.5" />
                    {trend.value}%
                  </span>
                )}
                {trend.direction === 'flat' && (
                  <span className="flex items-center text-xs text-slate-500">
                    <Minus className="w-3 h-3" />
                  </span>
                )}
              </div>
            </div>
            <div className="relative h-8 bg-surface-50 rounded-lg overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${widthPercent}%` }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={cn(
                  'absolute inset-y-0 left-0 rounded-lg bg-gradient-to-r',
                  stage.color,
                  'group-hover:shadow-lg transition-shadow'
                )}
              />
              <div className="absolute inset-0 flex items-center px-3">
                <span className="text-sm font-medium text-white drop-shadow">
                  {stage.label}
                </span>
              </div>
            </div>
          </motion.div>
        )
      })}

      {/* Conversion rates */}
      <div className="mt-4 pt-4 border-t border-white/5">
        <div className="flex justify-between text-xs text-slate-400">
          <span>整体转化率</span>
          <span className="text-emerald-400 font-medium">
            {((funnelData.won / funnelData.lead) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between text-xs text-slate-400 mt-1">
          <span>平均成交周期</span>
          <span className="text-white font-medium">32 天</span>
        </div>
      </div>
    </motion.div>
  )
}

