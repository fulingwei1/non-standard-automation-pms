import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Target, Users, DollarSign } from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesStatisticsApi } from '../services/api'

const stages = [
  { key: 'inquiry', label: '询价', color: 'slate' },
  { key: 'quotation', label: '报价', color: 'blue' },
  { key: 'negotiation', label: '谈判', color: 'amber' },
  { key: 'contract', label: '合同', color: 'purple' },
  { key: 'won', label: '成交', color: 'emerald' },
]

export default function SalesFunnel() {
  const [funnelData, setFunnelData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFunnelData()
  }, [])

  const loadFunnelData = async () => {
    try {
      setLoading(true)
      const res = await salesStatisticsApi.funnel({})
      setFunnelData(res.data || [])
    } catch (error) {
      console.error('Failed to load funnel data:', error)
      // Mock data
      setFunnelData([
        { stage: 'inquiry', count: 120, value: 12000000, conversion: 100 },
        { stage: 'quotation', count: 80, value: 8000000, conversion: 66.7 },
        { stage: 'negotiation', count: 45, value: 4500000, conversion: 37.5 },
        { stage: 'contract', count: 25, value: 2500000, conversion: 20.8 },
        { stage: 'won', count: 15, value: 1500000, conversion: 12.5 },
      ])
    } finally {
      setLoading(false)
    }
  }

  const maxCount = Math.max(...funnelData.map((d) => d.count), 1)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader title="销售漏斗" />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Funnel Visualization */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle>销售漏斗分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {funnelData.map((data, index) => {
                  const stageConfig = stages.find((s) => s.key === data.stage) || stages[0]
                  const width = (data.count / maxCount) * 100
                  const prevData = index > 0 ? funnelData[index - 1] : null
                  const dropRate = prevData
                    ? ((prevData.count - data.count) / prevData.count) * 100
                    : 0

                  return (
                    <div key={data.stage} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Badge
                            variant="outline"
                            className={cn(
                              `bg-${stageConfig.color}-500/10`,
                              `border-${stageConfig.color}-500/30`,
                              `text-${stageConfig.color}-400`
                            )}
                          >
                            {stageConfig.label}
                          </Badge>
                          <span className="text-white font-medium">{data.count}个</span>
                          <span className="text-slate-400 text-sm">
                            ¥{(data.value / 10000).toFixed(0)}万
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <span className="text-slate-400">
                            转化率: <span className="text-white">{data.conversion.toFixed(1)}%</span>
                          </span>
                          {prevData && (
                            <span className={cn(
                              'flex items-center gap-1',
                              dropRate > 50 ? 'text-red-400' : 'text-slate-400'
                            )}>
                              {dropRate > 50 ? (
                                <TrendingDown className="w-4 h-4" />
                              ) : (
                                <TrendingUp className="w-4 h-4" />
                              )}
                              流失 {dropRate.toFixed(1)}%
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="relative">
                        <Progress
                          value={width}
                          className={cn(`bg-${stageConfig.color}-500/20`)}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">总线索数</p>
                    <p className="text-2xl font-bold text-white">
                      {funnelData[0]?.count || 0}
                    </p>
                  </div>
                  <Target className="w-8 h-8 text-blue-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">成交数</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {funnelData[funnelData.length - 1]?.count || 0}
                    </p>
                  </div>
                  <Users className="w-8 h-8 text-emerald-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">总成交额</p>
                    <p className="text-2xl font-bold text-purple-400">
                      ¥{(funnelData.reduce((sum, d) => sum + (d.value || 0), 0) / 10000).toFixed(0)}万
                    </p>
                  </div>
                  <DollarSign className="w-8 h-8 text-purple-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}



