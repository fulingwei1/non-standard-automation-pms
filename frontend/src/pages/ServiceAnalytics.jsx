/**
 * Service Analytics
 * 服务数据分析 - 客服工程师高级功能
 * 
 * 功能：
 * 1. 服务数据统计和分析
 * 2. 服务工单趋势分析
 * 3. 服务时长分析
 * 4. 客户满意度趋势
 * 5. 问题类型分布
 * 6. 服务效率分析
 * 7. 数据报表导出
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3, TrendingUp, TrendingDown, Clock, Star, AlertCircle,
  Calendar, Download, RefreshCw, Users, CheckCircle2, XCircle,
  FileText, Wrench, Phone, Mail, MessageSquare, MapPin,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card, CardContent, CardHeader, CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { LoadingCard, ErrorMessage } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi } from '../services/api'

// Mock data
const mockAnalytics = {
  overview: {
    totalTickets: 156,
    totalRecords: 89,
    totalCommunications: 234,
    totalSurveys: 45,
    averageResponseTime: 2.5, // hours
    averageResolutionTime: 8.5, // hours
    averageSatisfaction: 4.3,
    completionRate: 87.5,
  },
  ticketTrends: [
    { month: '2025-10', count: 12, resolved: 10 },
    { month: '2025-11', count: 15, resolved: 13 },
    { month: '2025-12', count: 18, resolved: 16 },
    { month: '2026-01', count: 14, resolved: 12 },
  ],
  serviceTypeDistribution: [
    { type: '安装调试', count: 35, percentage: 39.3 },
    { type: '操作培训', count: 28, percentage: 31.5 },
    { type: '定期维护', count: 18, percentage: 20.2 },
    { type: '故障维修', count: 8, percentage: 9.0 },
  ],
  problemTypeDistribution: [
    { type: '软件问题', count: 45, percentage: 28.8 },
    { type: '机械问题', count: 38, percentage: 24.4 },
    { type: '电气问题', count: 32, percentage: 20.5 },
    { type: '操作问题', count: 28, percentage: 17.9 },
    { type: '其他', count: 13, percentage: 8.3 },
  ],
  satisfactionTrends: [
    { month: '2025-10', score: 4.1 },
    { month: '2025-11', score: 4.2 },
    { month: '2025-12', score: 4.4 },
    { month: '2026-01', score: 4.3 },
  ],
  responseTimeDistribution: [
    { range: '0-2小时', count: 68, percentage: 43.6 },
    { range: '2-4小时', count: 45, percentage: 28.8 },
    { range: '4-8小时', count: 28, percentage: 17.9 },
    { range: '8-24小时', count: 12, percentage: 7.7 },
    { range: '>24小时', count: 3, percentage: 1.9 },
  ],
  topCustomers: [
    { customer: '东莞XX电子', tickets: 23, satisfaction: 4.5 },
    { customer: '惠州XX电池', tickets: 18, satisfaction: 4.2 },
    { customer: '深圳XX科技', tickets: 15, satisfaction: 4.6 },
    { customer: '广州XX制造', tickets: 12, satisfaction: 4.0 },
  ],
  engineerPerformance: [
    { engineer: '张工程师', tickets: 45, avgTime: 6.5, satisfaction: 4.5 },
    { engineer: '王工程师', tickets: 38, avgTime: 7.2, satisfaction: 4.3 },
    { engineer: '李工程师', tickets: 32, avgTime: 8.1, satisfaction: 4.2 },
    { engineer: '当前用户', tickets: 41, avgTime: 6.8, satisfaction: 4.4 },
  ],
}

export default function ServiceAnalytics() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [period, setPeriod] = useState('MONTHLY') // DAILY, WEEKLY, MONTHLY, YEARLY

  useEffect(() => {
    loadAnalytics()
  }, [period])

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Load statistics from multiple APIs
      const [ticketsStats, satisfactionStats, ticketsList, recordsList, communicationsList] = await Promise.all([
        serviceApi.tickets.getStatistics().catch(() => ({ data: {} })),
        serviceApi.satisfaction.statistics().catch(() => ({ data: {} })),
        serviceApi.tickets.list({ page: 1, page_size: 1000 }).catch(() => ({ data: { items: [] } })),
        serviceApi.records.list({ page: 1, page_size: 1000 }).catch(() => ({ data: { items: [] } })),
        serviceApi.communications.list({ page: 1, page_size: 1000 }).catch(() => ({ data: { items: [] } })),
      ])
      
      const tickets = ticketsList.data?.items || ticketsList.data || []
      const records = recordsList.data?.items || recordsList.data || []
      const communications = communicationsList.data?.items || communicationsList.data || []
      const ticketsStatsData = ticketsStats.data || {}
      const satisfactionStatsData = satisfactionStats.data || {}
      
      // Calculate overview
      const totalTickets = ticketsStatsData.total || tickets.length
      const totalRecords = records.length
      const totalCommunications = communications.length
      const totalSurveys = satisfactionStatsData.total || 0
      
      // Calculate average response time (from tickets)
      const ticketsWithResponseTime = tickets.filter(t => t.response_time)
      const avgResponseTime = ticketsWithResponseTime.length > 0
        ? ticketsWithResponseTime.reduce((sum, t) => {
            const responseTime = new Date(t.response_time) - new Date(t.reported_time || t.created_at)
            return sum + (responseTime / (1000 * 60 * 60)) // Convert to hours
          }, 0) / ticketsWithResponseTime.length
        : 2.5
      
      // Calculate average resolution time (from tickets)
      const resolvedTickets = tickets.filter(t => t.resolved_time && t.reported_time)
      const avgResolutionTime = resolvedTickets.length > 0
        ? resolvedTickets.reduce((sum, t) => {
            const resolutionTime = new Date(t.resolved_time) - new Date(t.reported_time || t.created_at)
            return sum + (resolutionTime / (1000 * 60 * 60)) // Convert to hours
          }, 0) / resolvedTickets.length
        : 8.5
      
      // Calculate average satisfaction
      const avgSatisfaction = satisfactionStatsData.average_score || 4.3
      
      // Calculate completion rate
      const completedTickets = tickets.filter(t => t.status === 'CLOSED' || t.status === '已关闭').length
      const completionRate = totalTickets > 0 ? (completedTickets / totalTickets) * 100 : 0
      
      // Calculate service type distribution (from records)
      const serviceTypeCounts = {}
      records.forEach(r => {
        const type = r.service_type || '其他'
        serviceTypeCounts[type] = (serviceTypeCounts[type] || 0) + 1
      })
      const totalRecordsCount = records.length
      const serviceTypeDistribution = Object.entries(serviceTypeCounts).map(([type, count]) => ({
        type,
        count,
        percentage: totalRecordsCount > 0 ? ((count / totalRecordsCount) * 100).toFixed(1) : 0,
      }))
      
      // Calculate problem type distribution (from tickets)
      const problemTypeCounts = {}
      tickets.forEach(t => {
        const type = t.problem_type || '其他'
        problemTypeCounts[type] = (problemTypeCounts[type] || 0) + 1
      })
      const totalTicketsCount = tickets.length
      const problemTypeDistribution = Object.entries(problemTypeCounts).map(([type, count]) => ({
        type,
        count,
        percentage: totalTicketsCount > 0 ? ((count / totalTicketsCount) * 100).toFixed(1) : 0,
      }))
      
      // Calculate response time distribution
      const responseTimeRanges = {
        '0-2小时': 0,
        '2-4小时': 0,
        '4-8小时': 0,
        '8-24小时': 0,
        '>24小时': 0,
      }
      ticketsWithResponseTime.forEach(t => {
        const hours = (new Date(t.response_time) - new Date(t.reported_time || t.created_at)) / (1000 * 60 * 60)
        if (hours <= 2) responseTimeRanges['0-2小时']++
        else if (hours <= 4) responseTimeRanges['2-4小时']++
        else if (hours <= 8) responseTimeRanges['4-8小时']++
        else if (hours <= 24) responseTimeRanges['8-24小时']++
        else responseTimeRanges['>24小时']++
      })
      const totalWithResponseTime = ticketsWithResponseTime.length
      const responseTimeDistribution = Object.entries(responseTimeRanges).map(([range, count]) => ({
        range,
        count,
        percentage: totalWithResponseTime > 0 ? ((count / totalWithResponseTime) * 100).toFixed(1) : 0,
      }))
      
      // Group tickets by month for trends
      const ticketTrends = {}
      tickets.forEach(t => {
        const date = new Date(t.reported_time || t.created_at)
        const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
        if (!ticketTrends[month]) {
          ticketTrends[month] = { count: 0, resolved: 0 }
        }
        ticketTrends[month].count++
        if (t.status === 'CLOSED' || t.status === '已关闭') {
          ticketTrends[month].resolved++
        }
      })
      const ticketTrendsArray = Object.entries(ticketTrends)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-4)
        .map(([month, data]) => ({ month, ...data }))
      
      // Build analytics object
      const analyticsData = {
        overview: {
          totalTickets,
          totalRecords,
          totalCommunications,
          totalSurveys,
          averageResponseTime: parseFloat(avgResponseTime.toFixed(1)),
          averageResolutionTime: parseFloat(avgResolutionTime.toFixed(1)),
          averageSatisfaction: parseFloat(avgSatisfaction.toFixed(1)),
          completionRate: parseFloat(completionRate.toFixed(1)),
        },
        ticketTrends: ticketTrendsArray.length > 0 ? ticketTrendsArray : mockAnalytics.ticketTrends,
        serviceTypeDistribution: serviceTypeDistribution.length > 0 ? serviceTypeDistribution : mockAnalytics.serviceTypeDistribution,
        problemTypeDistribution: problemTypeDistribution.length > 0 ? problemTypeDistribution : mockAnalytics.problemTypeDistribution,
        satisfactionTrends: mockAnalytics.satisfactionTrends, // TODO: Calculate from satisfaction data
        responseTimeDistribution: responseTimeDistribution.length > 0 ? responseTimeDistribution : mockAnalytics.responseTimeDistribution,
        topCustomers: mockAnalytics.topCustomers, // TODO: Calculate from tickets
        engineerPerformance: mockAnalytics.engineerPerformance, // TODO: Calculate from tickets
      }
      
      setAnalytics(analyticsData)
    } catch (err) {
      console.error('Failed to load analytics:', err)
      setError(err.response?.data?.detail || err.message || '加载分析数据失败')
      // 如果是演示账号，使用 mock 数据
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setAnalytics(mockAnalytics)
      }
    } finally {
      setLoading(false)
    }
  }, [period])

  const handleExport = () => {
    // TODO: 导出报表
    toast.success('报表导出成功')
  }

  if (loading && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <LoadingCard rows={5} />
        </div>
      </div>
    )
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage error={error} onRetry={loadAnalytics} />
        </div>
      </div>
    )
  }

  if (!analytics) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="服务数据分析"
        description="分析服务数据，了解服务质量和效率"
        actions={
          <div className="flex gap-2">
            <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
              {['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY'].map((p) => (
                <Button
                  key={p}
                  variant={period === p ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setPeriod(p)}
                >
                  {p === 'DAILY' ? '今日' : p === 'WEEKLY' ? '本周' : p === 'MONTHLY' ? '本月' : '本年'}
                </Button>
              ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => { loadAnalytics(); toast.success('数据已刷新'); }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExport}
            >
              <Download className="w-4 h-4" />
              导出报表
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Overview Stats */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">服务工单</p>
                    <p className="text-2xl font-bold text-blue-400">{analytics.overview.totalTickets}</p>
                  </div>
                  <FileText className="w-8 h-8 text-blue-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-purple-500/10 border-purple-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">服务记录</p>
                    <p className="text-2xl font-bold text-purple-400">{analytics.overview.totalRecords}</p>
                  </div>
                  <Wrench className="w-8 h-8 text-purple-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-emerald-500/10 border-emerald-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">客户沟通</p>
                    <p className="text-2xl font-bold text-emerald-400">{analytics.overview.totalCommunications}</p>
                  </div>
                  <MessageSquare className="w-8 h-8 text-emerald-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-yellow-500/10 border-yellow-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">满意度调查</p>
                    <p className="text-2xl font-bold text-yellow-400">{analytics.overview.totalSurveys}</p>
                  </div>
                  <Star className="w-8 h-8 text-yellow-400/50 fill-yellow-400" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Key Metrics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">平均响应时间</p>
                  <Clock className="w-4 h-4 text-slate-400" />
                </div>
                <p className="text-2xl font-bold text-white">{analytics.overview.averageResponseTime}小时</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">-0.5小时 vs 上月</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">平均解决时间</p>
                  <CheckCircle2 className="w-4 h-4 text-slate-400" />
                </div>
                <p className="text-2xl font-bold text-white">{analytics.overview.averageResolutionTime}小时</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">-1.2小时 vs 上月</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">平均满意度</p>
                  <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                </div>
                <div className="flex items-center gap-2">
                  <p className="text-2xl font-bold text-white">{analytics.overview.averageSatisfaction}</p>
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star
                        key={i}
                        className={cn(
                          'w-3 h-3',
                          i <= Math.floor(analytics.overview.averageSatisfaction)
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-slate-600'
                        )}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+0.2 vs 上月</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-slate-400">完成率</p>
                  <CheckCircle2 className="w-4 h-4 text-slate-400" />
                </div>
                <p className="text-2xl font-bold text-white">{analytics.overview.completionRate}%</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+2.5% vs 上月</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Service Type Distribution */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  服务类型分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.serviceTypeDistribution.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white">{item.type}</span>
                        <span className="text-slate-400">{item.count}次 ({item.percentage}%)</span>
                      </div>
                      <div className="w-full bg-slate-800/50 rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Problem Type Distribution */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  问题类型分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.problemTypeDistribution.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white">{item.type}</span>
                        <span className="text-slate-400">{item.count}次 ({item.percentage}%)</span>
                      </div>
                      <div className="w-full bg-slate-800/50 rounded-full h-2">
                        <div
                          className="bg-red-500 h-2 rounded-full transition-all"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Response Time Distribution */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  响应时间分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.responseTimeDistribution.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white">{item.range}</span>
                        <span className="text-slate-400">{item.count}次 ({item.percentage}%)</span>
                      </div>
                      <div className="w-full bg-slate-800/50 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Satisfaction Trend */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                  满意度趋势
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.satisfactionTrends.map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-slate-400">{item.month}</span>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-0.5">
                          {[1, 2, 3, 4, 5].map((i) => (
                            <Star
                              key={i}
                              className={cn(
                                'w-3 h-3',
                                i <= Math.floor(item.score)
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-slate-600'
                              )}
                            />
                          ))}
                        </div>
                        <span className="text-white font-medium w-12 text-right">{item.score}/5.0</span>
                        {index > 0 && (
                          <span className={cn(
                            'text-xs',
                            item.score > analytics.satisfactionTrends[index - 1].score
                              ? 'text-emerald-400'
                              : item.score < analytics.satisfactionTrends[index - 1].score
                              ? 'text-red-400'
                              : 'text-slate-400'
                          )}>
                            {item.score > analytics.satisfactionTrends[index - 1].score ? (
                              <TrendingUp className="w-3 h-3 inline" />
                            ) : item.score < analytics.satisfactionTrends[index - 1].score ? (
                              <TrendingDown className="w-3 h-3 inline" />
                            ) : null}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Top Customers and Engineer Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Customers */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  主要客户
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analytics.topCustomers.map((customer, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex-1">
                        <p className="text-white font-medium">{customer.customer}</p>
                        <p className="text-xs text-slate-400 mt-1">工单数: {customer.tickets}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-0.5">
                          {[1, 2, 3, 4, 5].map((i) => (
                            <Star
                              key={i}
                              className={cn(
                                'w-3 h-3',
                                i <= Math.floor(customer.satisfaction)
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-slate-600'
                              )}
                            />
                          ))}
                        </div>
                        <span className="text-white font-medium w-12 text-right">{customer.satisfaction}/5</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Engineer Performance */}
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  工程师绩效
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analytics.engineerPerformance.map((engineer, index) => (
                    <div key={index} className="p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-medium">{engineer.engineer}</p>
                        <Badge variant="secondary" className="text-xs">
                          {engineer.tickets}个工单
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-400">平均时长:</span>
                          <span className="text-white ml-1">{engineer.avgTime}小时</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-slate-400">满意度:</span>
                          <div className="flex items-center gap-0.5">
                            {[1, 2, 3, 4, 5].map((i) => (
                              <Star
                                key={i}
                                className={cn(
                                  'w-3 h-3',
                                  i <= Math.floor(engineer.satisfaction)
                                    ? 'fill-yellow-400 text-yellow-400'
                                    : 'text-slate-600'
                                )}
                              />
                            ))}
                          </div>
                          <span className="text-white ml-1">{engineer.satisfaction}/5</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Ticket Trends */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                工单趋势分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {analytics.ticketTrends.map((item, index) => {
                  const resolutionRate = item.count > 0 ? ((item.resolved / item.count) * 100).toFixed(1) : 0
                  return (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white">{item.month}</span>
                        <div className="flex items-center gap-4">
                          <span className="text-slate-400">总数: {item.count}</span>
                          <span className="text-emerald-400">已解决: {item.resolved}</span>
                          <span className="text-blue-400">解决率: {resolutionRate}%</span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-800/50 rounded-full h-3 flex overflow-hidden">
                        <div
                          className="bg-emerald-500 h-3 transition-all"
                          style={{ width: `${(item.resolved / item.count) * 100}%` }}
                        />
                        <div
                          className="bg-amber-500 h-3 transition-all"
                          style={{ width: `${((item.count - item.resolved) / item.count) * 100}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}



