/**
 * Sales Statistics Page - Sales analytics and reporting
 * Features: Sales funnel, revenue forecast, opportunity analysis
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Users,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  ArrowUpRight,
  ArrowDownRight,
  Download,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesStatisticsApi } from '../services/api'

export default function SalesStatistics() {
  const [loading, setLoading] = useState(false)
  const [timeRange, setTimeRange] = useState('month') // month, quarter, year
  const [funnelData, setFunnelData] = useState(null)
  const [revenueForecast, setRevenueForecast] = useState(null)
  const [opportunitiesByStage, setOpportunitiesByStage] = useState([])
  const [summary, setSummary] = useState(null)

  const loadStatistics = async () => {
    setLoading(true)
    try {
      // Calculate date range based on timeRange
      const today = new Date()
      let startDate = null
      let endDate = today.toISOString().split('T')[0]

      if (timeRange === 'month') {
        startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
      } else if (timeRange === 'quarter') {
        const quarter = Math.floor(today.getMonth() / 3)
        startDate = new Date(today.getFullYear(), quarter * 3, 1).toISOString().split('T')[0]
      } else if (timeRange === 'year') {
        startDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0]
      }

      const params = startDate ? { start_date: startDate, end_date: endDate } : {}

      // Load sales funnel
      const funnelResponse = await salesStatisticsApi.funnel(params)
      if (funnelResponse.data && funnelResponse.data.data) {
        // Transform backend data to frontend format
        const funnel = funnelResponse.data.data
        setFunnelData({
          stages: [
            { stage: 'leads', stage_label: '线索', count: funnel.leads || 0, amount: 0 },
            { stage: 'opportunities', stage_label: '商机', count: funnel.opportunities || 0, amount: funnel.total_opportunity_amount || 0 },
            { stage: 'quotes', stage_label: '报价', count: funnel.quotes || 0, amount: 0 },
            { stage: 'contracts', stage_label: '合同', count: funnel.contracts || 0, amount: funnel.total_contract_amount || 0 },
          ]
        })
      }

      // Load revenue forecast
      const forecastResponse = await salesStatisticsApi.revenueForecast({ months: 3 })
      if (forecastResponse.data && forecastResponse.data.data) {
        const forecast = forecastResponse.data.data
        const totalForecast = forecast.forecast ? forecast.forecast.reduce((sum, f) => sum + (parseFloat(f.estimated_revenue) || 0), 0) : 0
        setRevenueForecast({
          forecast_amount: totalForecast,
          confirmed_amount: forecast.confirmed_amount || 0,
          completion_rate: 0,
          breakdown: forecast.forecast || []
        })
      }

      // Load opportunities by stage
      const stageResponse = await salesStatisticsApi.opportunitiesByStage()
      if (stageResponse.data && stageResponse.data.data) {
        const stages = stageResponse.data.data
        const stageList = Object.entries(stages).map(([stage, data]) => ({
          stage,
          stage_label: {
            'DISCOVERY': '发现',
            'QUALIFIED': '已确认',
            'PROPOSAL': '提案',
            'NEGOTIATION': '谈判',
            'WON': '已成交',
            'LOST': '已丢失',
            'ON_HOLD': '暂停'
          }[stage] || stage,
          count: data.count || 0,
          amount: data.total_amount || 0
        }))
        setOpportunitiesByStage(stageList)
      }

      // Load summary stats from API
      try {
        const summaryResponse = await salesStatisticsApi.summary(params)
        if (summaryResponse.data && summaryResponse.data.data) {
          const summaryData = summaryResponse.data.data
          setSummary({
            total_leads: summaryData.total_leads || 0,
            converted_leads: summaryData.converted_leads || 0,
            total_opportunities: summaryData.total_opportunities || 0,
            won_opportunities: summaryData.won_opportunities || 0,
            total_contract_amount: summaryData.total_contract_amount || 0,
            paid_amount: summaryData.paid_amount || 0,
            conversion_rate: summaryData.conversion_rate || 0,
            win_rate: summaryData.win_rate || 0,
          })
        } else if (funnelResponse.data && funnelResponse.data.data) {
          // Fallback: calculate from funnel data if summary API not available
          const funnel = funnelResponse.data.data
          setSummary({
            total_leads: funnel.leads || 0,
            converted_leads: 0,
            total_opportunities: funnel.opportunities || 0,
            won_opportunities: 0,
            total_contract_amount: funnel.total_contract_amount || 0,
            paid_amount: 0,
            conversion_rate: 0,
            win_rate: 0,
          })
        }
      } catch (summaryError) {
        // Fallback to funnel data
        if (funnelResponse.data && funnelResponse.data.data) {
          const funnel = funnelResponse.data.data
          setSummary({
            total_leads: funnel.leads || 0,
            converted_leads: 0,
            total_opportunities: funnel.opportunities || 0,
            won_opportunities: 0,
            total_contract_amount: funnel.total_contract_amount || 0,
            paid_amount: 0,
            conversion_rate: 0,
            win_rate: 0,
          })
        }
      }
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatistics()
  }, [timeRange])

  const formatCurrency = (value) => {
    if (!value) return '0'
    const num = parseFloat(value)
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万'
    }
    return num.toLocaleString()
  }

  const formatPercent = (value) => {
    if (!value) return '0%'
    return parseFloat(value).toFixed(1) + '%'
  }

  // 导出报表
  const handleExport = () => {
    try {
      const exportData = {
        统计周期: timeRange === 'month' ? '本月' : timeRange === 'quarter' ? '本季度' : '本年',
        导出日期: new Date().toLocaleDateString('zh-CN'),
        线索总数: summary?.total_leads || 0,
        已转化线索: summary?.converted_leads || 0,
        商机总数: summary?.total_opportunities || 0,
        已成交商机: summary?.won_opportunities || 0,
        合同总额: formatCurrency(summary?.total_contract_amount || 0),
        已收款: formatCurrency(summary?.paid_amount || 0),
        成交率: formatPercent(summary?.win_rate || 0),
        转化率: formatPercent(summary?.conversion_rate || 0),
      }

      // 转换为CSV格式
      const csvContent = [
        '项目,数值',
        ...Object.entries(exportData).map(([key, value]) => `"${key}","${value}"`),
      ].join('\n')

      // 添加BOM以支持中文
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute(
        'download',
        `销售统计报表_${timeRange}_${new Date().toISOString().split('T')[0]}.csv`
      )
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      alert('导出失败: ' + error.message)
    }
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="销售统计"
        description="销售数据分析与报表"
        action={
          <div className="flex gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Calendar className="mr-2 h-4 w-4" />
                  {timeRange === 'month' ? '本月' : timeRange === 'quarter' ? '本季度' : '本年'}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setTimeRange('month')}>本月</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTimeRange('quarter')}>本季度</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTimeRange('year')}>本年</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="outline" onClick={handleExport}>
              <Download className="mr-2 h-4 w-4" />
              导出报表
            </Button>
          </div>
        }
      />

      {/* 汇总统计 */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">线索总数</p>
                  <p className="text-2xl font-bold text-white">{summary.total_leads || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {summary.converted_leads || 0} 已转化
                  </p>
                </div>
                <Users className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">商机总数</p>
                  <p className="text-2xl font-bold text-white">{summary.total_opportunities || 0}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {summary.won_opportunities || 0} 已成交
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">合同总额</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(summary.total_contract_amount || 0)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    已收款 {formatCurrency(summary.paid_amount || 0)}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-emerald-400" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">成交率</p>
                  <p className="text-2xl font-bold text-white">
                    {formatPercent(summary.win_rate || 0)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    转化率 {formatPercent(summary.conversion_rate || 0)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 销售漏斗 */}
      {funnelData && (
        <Card>
          <CardHeader>
            <CardTitle>销售漏斗</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {funnelData.stages && funnelData.stages.length > 0 ? (
                <>
                  {/* 漏斗可视化 */}
                  <div className="relative">
                    {funnelData.stages.map((stage, index) => {
                      const prevCount = index > 0 ? funnelData.stages[index - 1].count : stage.count
                      const conversionRate =
                        prevCount > 0 ? ((stage.count / prevCount) * 100).toFixed(1) : 0
                      const isIncreasing = index === 0 || stage.count >= prevCount
                      const maxCount = Math.max(...funnelData.stages.map((s) => s.count || 0), 1)
                      const widthPercent = ((stage.count || 0) / maxCount) * 100

                      return (
                        <div key={stage.stage || index} className="space-y-2 mb-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-white">
                                {stage.stage_label || stage.stage}
                              </span>
                              <Badge className="bg-blue-500">{stage.count || 0} 个</Badge>
                              {stage.amount && (
                                <span className="text-sm text-slate-400">
                                  {formatCurrency(stage.amount)}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              {index > 0 && (
                                <>
                                  {isIncreasing ? (
                                    <ArrowUpRight className="h-4 w-4 text-emerald-400" />
                                  ) : (
                                    <ArrowDownRight className="h-4 w-4 text-red-400" />
                                  )}
                                  <span className="text-sm text-slate-400">
                                    {conversionRate}% 转化率
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                          {/* 漏斗形状 */}
                          <div className="relative">
                            <div
                              className="h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded transition-all hover:opacity-80"
                              style={{
                                width: `${Math.max(widthPercent, 10)}%`,
                                marginLeft: `${(100 - Math.max(widthPercent, 10)) / 2}%`,
                                clipPath: index === 0 
                                  ? 'polygon(10% 0%, 90% 0%, 100% 100%, 0% 100%)'
                                  : index === funnelData.stages.length - 1
                                  ? 'polygon(0% 0%, 100% 0%, 90% 100%, 10% 100%)'
                                  : 'polygon(10% 0%, 90% 0%, 100% 100%, 0% 100%)',
                              }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : (
                <p className="text-center text-slate-400 py-8">暂无漏斗数据</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 商机阶段分布 */}
      {opportunitiesByStage && opportunitiesByStage.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>商机阶段分布</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {opportunitiesByStage.map((item) => {
                  const total = opportunitiesByStage.reduce(
                    (sum, i) => sum + (parseFloat(i.count) || 0),
                    0
                  )
                  const percentage = total > 0 ? ((item.count / total) * 100).toFixed(1) : 0

                  return (
                    <div key={item.stage} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-300">{item.stage_label || item.stage}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-white">{item.count || 0}</span>
                          <span className="text-xs text-slate-400">{percentage}%</span>
                        </div>
                      </div>
                      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* 收入预测 */}
          {revenueForecast && (
            <Card>
              <CardHeader>
                <CardTitle>收入预测</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">预计收入</span>
                      <span className="text-lg font-bold text-emerald-400">
                        {formatCurrency(revenueForecast.forecast_amount || 0)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">已确认收入</span>
                      <span className="text-lg font-bold text-blue-400">
                        {formatCurrency(revenueForecast.confirmed_amount || 0)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">完成度</span>
                      <span className="text-lg font-bold text-amber-400">
                        {formatPercent(revenueForecast.completion_rate || 0)}
                      </span>
                    </div>
                  </div>
                  {revenueForecast.breakdown && revenueForecast.breakdown.length > 0 && (
                    <div className="border-t border-slate-700 pt-4">
                      <p className="text-sm text-slate-400 mb-2">按阶段分解:</p>
                      <div className="space-y-2">
                        {revenueForecast.breakdown.map((item) => {
                          const total = revenueForecast.breakdown.reduce(
                            (sum, i) => sum + (parseFloat(i.amount) || 0),
                            0
                          )
                          const percentage = total > 0 ? ((item.amount || 0) / total) * 100 : 0
                          return (
                            <div key={item.stage} className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-300">
                                  {item.stage_label || item.stage}
                                </span>
                                <div className="flex items-center gap-2">
                                  <span className="text-white">{formatCurrency(item.amount || 0)}</span>
                                  <span className="text-xs text-slate-500">
                                    {percentage.toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      )}
    </motion.div>
  )
}

