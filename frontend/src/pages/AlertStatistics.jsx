import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  Download,
  Filter,
  FileText,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { alertApi } from '../services/api'
import { LoadingCard, ErrorMessage, LoadingSpinner } from '../components/common'
import {
  SimpleLineChart,
  SimpleBarChart,
  SimplePieChart,
} from '../components/administrative/StatisticsCharts'

// 响应时效分析组件
function ResponseMetricsSection({ dateRange, selectedProject }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [dateRange, selectedProject])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end,
      }
      if (selectedProject) {
        params.project_id = selectedProject
      }
      const res = await alertApi.responseMetrics(params)
      const data = res.data || res
      setMetrics(data)
    } catch (err) {
      console.error('Failed to load response metrics:', err)
      setMetrics(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardContent className="p-8">
            <LoadingSpinner text="加载响应时效数据..." />
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  if (!metrics) {
    return null
  }

  // 响应时效分布数据
  const distributionData = metrics.response_distribution ? [
    { label: '<1小时', value: metrics.response_distribution['<1小时'] || 0, color: 'hsl(120, 70%, 50%)' },
    { label: '1-4小时', value: metrics.response_distribution['1-4小时'] || 0, color: 'hsl(60, 70%, 50%)' },
    { label: '4-8小时', value: metrics.response_distribution['4-8小时'] || 0, color: 'hsl(30, 70%, 50%)' },
    { label: '>8小时', value: metrics.response_distribution['>8小时'] || 0, color: 'hsl(0, 70%, 50%)' },
  ] : []

  return (
    <div className="space-y-6">
      {/* 汇总指标 */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle>响应时效统计</CardTitle>
            <CardDescription>预警响应和解决时效分析</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-slate-500 mb-1">平均响应时间</p>
                <p className="text-2xl font-bold text-white">
                  {metrics.summary?.avg_response_time_hours
                    ? `${metrics.summary.avg_response_time_hours.toFixed(2)}小时`
                    : '-'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {metrics.summary?.total_acknowledged || 0} 个已确认预警
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">平均解决时间</p>
                <p className="text-2xl font-bold text-white">
                  {metrics.summary?.avg_resolve_time_hours
                    ? `${metrics.summary.avg_resolve_time_hours.toFixed(2)}小时`
                    : '-'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {metrics.summary?.total_resolved || 0} 个已解决预警
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">快速响应率</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {metrics.response_distribution && metrics.summary?.total_acknowledged
                    ? `${((metrics.response_distribution['<1小时'] / metrics.summary.total_acknowledged) * 100).toFixed(0)}%`
                    : '-'}
                </p>
                <p className="text-xs text-slate-500 mt-1">1小时内响应</p>
              </div>
              <div>
                <p className="text-sm text-slate-500 mb-1">超时响应</p>
                <p className="text-2xl font-bold text-red-400">
                  {metrics.response_distribution?.['>8小时'] || 0}
                </p>
                <p className="text-xs text-slate-500 mt-1">超过8小时</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 响应时效分布和排行榜 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 响应时效分布 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card className="bg-surface-1/50">
            <CardHeader>
              <CardTitle>响应时效分布</CardTitle>
              <CardDescription>按响应时间区间统计</CardDescription>
            </CardHeader>
            <CardContent>
              {distributionData.length > 0 ? (
                <SimplePieChart data={distributionData} size={250} />
              ) : (
                <div className="h-[250px] flex items-center justify-center text-slate-500">
                  暂无数据
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* 响应时效排行榜 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card className="bg-surface-1/50">
            <CardHeader>
              <CardTitle>响应时效排行榜</CardTitle>
              <CardDescription>最快/最慢的项目和责任人</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* 最快的项目 */}
                {metrics.rankings?.fastest_projects?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-emerald-400 mb-3">响应最快的项目 TOP5</h4>
                    <div className="space-y-2">
                      {metrics.rankings.fastest_projects.map((project, index) => (
                        <div
                          key={project.project_id}
                          className="flex items-center justify-between p-2 bg-slate-800/50 rounded"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-500 w-6">{index + 1}</span>
                            <span className="text-sm text-white">{project.project_name}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-medium text-emerald-400">
                              {project.avg_hours.toFixed(2)}h
                            </span>
                            <span className="text-xs text-slate-500 ml-2">
                              ({project.count}个)
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 最慢的项目 */}
                {metrics.rankings?.slowest_projects?.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-red-400 mb-3">响应最慢的项目 TOP5</h4>
                    <div className="space-y-2">
                      {metrics.rankings.slowest_projects.map((project, index) => (
                        <div
                          key={project.project_id}
                          className="flex items-center justify-between p-2 bg-slate-800/50 rounded"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-slate-500 w-6">{index + 1}</span>
                            <span className="text-sm text-white">{project.project_name}</span>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-medium text-red-400">
                              {project.avg_hours.toFixed(2)}h
                            </span>
                            <span className="text-xs text-slate-500 ml-2">
                              ({project.count}个)
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 按级别和类型统计 */}
      {(metrics.by_level || metrics.by_type) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 按级别统计 */}
          {metrics.by_level && Object.keys(metrics.by_level).length > 0 && (
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <CardTitle>按级别统计响应时效</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(metrics.by_level).map(([level, data]) => (
                      <div key={level} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-300">{level}</span>
                          <span className="text-white font-medium">
                            {data.avg_hours.toFixed(2)}h
                          </span>
                        </div>
                        <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 transition-all"
                            style={{ width: `${Math.min((data.avg_hours / 24) * 100, 100)}%` }}
                          />
                        </div>
                        <div className="text-xs text-slate-500">
                          最小: {data.min_hours.toFixed(2)}h | 最大: {data.max_hours.toFixed(2)}h | 数量: {data.count}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 按类型统计 */}
          {metrics.by_type && Object.keys(metrics.by_type).length > 0 && (
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <CardTitle>按类型统计响应时效</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(metrics.by_type)
                      .sort((a, b) => b[1].avg_hours - a[1].avg_hours)
                      .slice(0, 10)
                      .map(([type, data]) => (
                        <div key={type} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-300">{type}</span>
                            <span className="text-white font-medium">
                              {data.avg_hours.toFixed(2)}h
                            </span>
                          </div>
                          <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-amber-500 transition-all"
                              style={{ width: `${Math.min((data.avg_hours / 24) * 100, 100)}%` }}
                            />
                          </div>
                          <div className="text-xs text-slate-500">
                            最小: {data.min_hours.toFixed(2)}h | 最大: {data.max_hours.toFixed(2)}h | 数量: {data.count}
                          </div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      )}
    </div>
  )
}

export default function AlertStatistics() {
  const [stats, setStats] = useState(null)
  const [trends, setTrends] = useState(null)
  const [topProjects, setTopProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [period, setPeriod] = useState('DAILY')
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  })
  const [selectedProject, setSelectedProject] = useState(null)

  useEffect(() => {
    loadStatistics()
    loadTrends()
  }, [period, dateRange, selectedProject])

  const loadStatistics = async () => {
    try {
      setError(null)
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end,
      }
      if (selectedProject) {
        params.project_id = selectedProject
      }
      const res = await alertApi.statistics(params)
      const data = res.data || res
      setStats(data)
    } catch (err) {
      console.error('Failed to load statistics:', err)
      const errorMessage = err.response?.data?.detail || err.message || '加载统计数据失败'
      setError(errorMessage)
    }
  }

  const loadTrends = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        period,
        start_date: dateRange.start,
        end_date: dateRange.end,
      }
      if (selectedProject) {
        params.project_id = selectedProject
      }
      const res = await alertApi.trends(params)
      const data = res.data || res
      setTrends(data)
    } catch (err) {
      console.error('Failed to load trends:', err)
      const errorMessage = err.response?.data?.detail || err.message || '加载趋势数据失败'
      setError(errorMessage)
      // 如果是演示账号，设置空数据而不是显示错误
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setTrends(null)
        setError(null) // Clear error for demo accounts
      }
    } finally {
      setLoading(false)
    }
  }

  const handleQuickRange = (days) => {
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - days)
    setDateRange({
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    })
  }

  // 准备图表数据
  const trendLineData = useMemo(() => {
    if (!trends?.trends) return []
    return trends.trends.map(item => ({
      label: item.date,
      value: item.total,
    }))
  }, [trends])

  const levelPieData = useMemo(() => {
    if (!trends?.summary?.by_level) return []
    const colors = {
      URGENT: 'hsl(0, 70%, 50%)',
      CRITICAL: 'hsl(30, 70%, 50%)',
      WARNING: 'hsl(45, 70%, 50%)',
      INFO: 'hsl(200, 70%, 50%)',
    }
    const labels = {
      URGENT: '紧急',
      CRITICAL: '严重',
      WARNING: '注意',
      INFO: '提示',
    }
    return Object.entries(trends.summary.by_level).map(([level, count]) => ({
      label: labels[level] || level,
      value: count,
      color: colors[level] || 'hsl(0, 0%, 50%)',
    }))
  }, [trends])

  const typeBarData = useMemo(() => {
    if (!trends?.summary?.by_type) return []
    return Object.entries(trends.summary.by_type)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([type, count]) => ({
        label: type,
        value: count,
      }))
  }, [trends])

  const statusAreaData = useMemo(() => {
    if (!trends?.trends) return []
    const statuses = ['PENDING', 'ACKNOWLEDGED', 'RESOLVED', 'CLOSED']
    const labels = {
      PENDING: '待处理',
      ACKNOWLEDGED: '已确认',
      RESOLVED: '已解决',
      CLOSED: '已关闭',
    }
    return trends.trends.map(item => ({
      date: item.date,
      ...Object.fromEntries(
        statuses.map(status => [
          status,
          item.by_status?.[status] || 0,
        ])
      ),
    }))
  }, [trends])

  const handleExportChart = (chartId, format = 'png') => {
    // 简单的图表导出功能（实际实现需要使用 html2canvas 或类似库）
    const element = document.getElementById(chartId)
    if (!element) return
    // TODO: 实现图表导出功能
    alert('图表导出功能开发中...')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="预警统计分析" />
        <div className="container mx-auto px-4 py-6">
          <LoadingSpinner text="加载统计数据..." />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="预警统计分析" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage
            error={error}
            onRetry={loadStatistics}
            title="加载统计失败"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警统计分析"
        description="多维度预警趋势分析和统计报表"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportExcel}
              className="gap-2"
            >
              <Download className="w-4 h-4" />
              导出Excel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportPdf}
              className="gap-2"
            >
              <FileText className="w-4 h-4" />
              导出PDF
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 时间范围选择 */}
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <Label className="text-sm text-slate-400">统计周期:</Label>
                <Select value={period} onValueChange={setPeriod}>
                  <SelectTrigger className="w-32 bg-surface-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="DAILY">按日</SelectItem>
                    <SelectItem value="WEEKLY">按周</SelectItem>
                    <SelectItem value="MONTHLY">按月</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-sm text-slate-400">日期范围:</Label>
                <Input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="w-40 bg-surface-2"
                />
                <span className="text-slate-400">至</span>
                <Input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="w-40 bg-surface-2"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickRange(7)}
                >
                  最近7天
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickRange(30)}
                >
                  最近30天
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickRange(90)}
                >
                  最近90天
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-red-500/5 border-red-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">紧急预警</p>
                    <p className="text-2xl font-bold text-red-400">
                      {stats?.by_level?.URGENT || 0}
                    </p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-red-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-orange-500/5 border-orange-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">严重预警</p>
                    <p className="text-2xl font-bold text-orange-400">
                      {stats?.by_level?.CRITICAL || 0}
                    </p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-orange-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-amber-500/5 border-amber-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">注意预警</p>
                    <p className="text-2xl font-bold text-amber-400">
                      {stats?.by_level?.WARNING || 0}
                    </p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-amber-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/5 border-blue-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">总计</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {stats?.total || 0}
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-blue-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Response Metrics */}
        <ResponseMetricsSection dateRange={dateRange} selectedProject={selectedProject} />

        {/* 趋势分析图表 */}
        {trends && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 预警数量趋势折线图 */}
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>预警数量趋势</CardTitle>
                      <CardDescription>按{period === 'DAILY' ? '日' : period === 'WEEKLY' ? '周' : '月'}统计预警数量变化</CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleExportChart('trend-line-chart')}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div id="trend-line-chart">
                    {trendLineData.length > 0 ? (
                      <SimpleLineChart
                        data={trendLineData}
                        height={250}
                        color="text-blue-400"
                      />
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-slate-500">
                        暂无数据
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* 预警级别分布饼图 */}
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>预警级别分布</CardTitle>
                      <CardDescription>各级别预警数量占比</CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleExportChart('level-pie-chart')}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div id="level-pie-chart">
                    {levelPieData.length > 0 ? (
                      <SimplePieChart data={levelPieData} size={250} />
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-slate-500">
                        暂无数据
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* 预警类型分布柱状图 */}
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>预警类型分布</CardTitle>
                      <CardDescription>各类型预警数量统计（TOP10）</CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleExportChart('type-bar-chart')}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div id="type-bar-chart">
                    {typeBarData.length > 0 ? (
                      <SimpleBarChart
                        data={typeBarData}
                        height={300}
                        color="bg-blue-500"
                      />
                    ) : (
                      <div className="h-[300px] flex items-center justify-center text-slate-500">
                        暂无数据
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* 预警状态变化面积图 */}
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>预警状态变化</CardTitle>
                      <CardDescription>各状态预警数量趋势</CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleExportChart('status-area-chart')}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div id="status-area-chart">
                    {statusAreaData.length > 0 ? (
                      <div className="space-y-4">
                        <div className="flex gap-4 text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-blue-500 rounded" />
                            <span className="text-slate-400">待处理</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-amber-500 rounded" />
                            <span className="text-slate-400">已确认</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-emerald-500 rounded" />
                            <span className="text-slate-400">已解决</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-slate-500 rounded" />
                            <span className="text-slate-400">已关闭</span>
                          </div>
                        </div>
                        <SimpleLineChart
                          data={statusAreaData.map(item => ({
                            label: item.date,
                            value: item.PENDING + item.ACKNOWLEDGED + item.RESOLVED + item.CLOSED,
                          }))}
                          height={200}
                          color="text-blue-400"
                        />
                      </div>
                    ) : (
                      <div className="h-[250px] flex items-center justify-center text-slate-500">
                        暂无数据
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        )}

        {/* 处理效率分析 */}
        <EfficiencyMetricsSection dateRange={dateRange} selectedProject={selectedProject} />

        {/* Top Projects */}
        {topProjects.length > 0 && (
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle>预警高发项目 TOP5</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topProjects.map((project, index) => (
                    <div
                      key={project.project_id}
                      className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-slate-500 w-8">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-white font-medium">{project.project_name}</p>
                          <p className="text-xs text-slate-500">
                            {project.alert_count}个预警
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {project.by_type && Object.entries(project.by_type).map(([type, count]) => (
                          <Badge key={type} variant="outline">
                            {type}: {count}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  )
}

// 处理效率分析组件
function EfficiencyMetricsSection({ dateRange, selectedProject }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [dateRange, selectedProject])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end,
      }
      if (selectedProject) {
        params.project_id = selectedProject
      }
      const res = await alertApi.efficiencyMetrics(params)
      const data = res.data || res
      setMetrics(data)
    } catch (err) {
      console.error('Failed to load efficiency metrics:', err)
      setMetrics(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card>
          <CardContent className="p-8">
            <LoadingSpinner text="加载处理效率数据..." />
          </CardContent>
        </Card>
      </motion.div>
    )
  }

  if (!metrics || !metrics.summary) {
    return null
  }

  // 效率指标数据
  const efficiencyData = [
    {
      label: '处理率',
      value: metrics.summary.processing_rate || 0,
      color: 'hsl(200, 70%, 50%)',
      description: '已处理预警 / 总预警数',
    },
    {
      label: '及时处理率',
      value: metrics.summary.timely_processing_rate || 0,
      color: 'hsl(120, 70%, 50%)',
      description: '在响应时限内处理的比例',
    },
    {
      label: '升级率',
      value: metrics.summary.escalation_rate || 0,
      color: 'hsl(30, 70%, 50%)',
      description: '升级预警 / 总预警数',
    },
    {
      label: '重复预警率',
      value: metrics.summary.duplicate_rate || 0,
      color: 'hsl(0, 70%, 50%)',
      description: '重复预警 / 总预警数',
    },
  ]

  return (
    <div className="space-y-6">
      {/* 汇总指标 */}
      <motion.div variants={fadeIn} initial="hidden" animate="visible">
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle>处理效率统计</CardTitle>
            <CardDescription>预警处理效率分析</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {efficiencyData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <p className="text-sm text-slate-500 mb-1">{item.label}</p>
                  <p className="text-2xl font-bold text-white">
                    {(item.value * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500">{item.description}</p>
                  <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden mt-2">
                    <div
                      className="h-full transition-all"
                      style={{
                        width: `${item.value * 100}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 处理效率排行榜 */}
      {metrics.rankings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 效率最高的项目 */}
          {metrics.rankings.best_projects?.length > 0 && (
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <CardTitle className="text-emerald-400">效率最高的项目 TOP5</CardTitle>
                  <CardDescription>处理效率得分最高的项目</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {metrics.rankings.best_projects.map((project, index) => (
                      <div
                        key={project.project_id}
                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-emerald-400 w-6">
                            {index + 1}
                          </span>
                          <div>
                            <p className="text-white font-medium">{project.project_name}</p>
                            <p className="text-xs text-slate-500">
                              处理率: {(project.processing_rate * 100).toFixed(1)}% | 
                              及时率: {(project.timely_processing_rate * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-lg font-bold text-emerald-400">
                            {project.efficiency_score.toFixed(1)}
                          </span>
                          <p className="text-xs text-slate-500">效率得分</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 效率最低的项目 */}
          {metrics.rankings.worst_projects?.length > 0 && (
            <motion.div variants={fadeIn} initial="hidden" animate="visible">
              <Card className="bg-surface-1/50">
                <CardHeader>
                  <CardTitle className="text-red-400">效率最低的项目 TOP5</CardTitle>
                  <CardDescription>需要关注和改进的项目</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {metrics.rankings.worst_projects.map((project, index) => (
                      <div
                        key={project.project_id}
                        className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-lg font-bold text-red-400 w-6">
                            {index + 1}
                          </span>
                          <div>
                            <p className="text-white font-medium">{project.project_name}</p>
                            <p className="text-xs text-slate-500">
                              处理率: {(project.processing_rate * 100).toFixed(1)}% | 
                              及时率: {(project.timely_processing_rate * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="text-lg font-bold text-red-400">
                            {project.efficiency_score.toFixed(1)}
                          </span>
                          <p className="text-xs text-slate-500">效率得分</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      )}

      {/* 按类型统计 */}
      {metrics.by_type && Object.keys(metrics.by_type).length > 0 && (
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card className="bg-surface-1/50">
            <CardHeader>
              <CardTitle>按类型统计处理效率</CardTitle>
              <CardDescription>各类型预警的处理效率对比</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(metrics.by_type)
                  .sort((a, b) => b[1].processing_rate - a[1].processing_rate)
                  .map(([type, data]) => (
                    <div key={type} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-300 font-medium">{type}</span>
                        <div className="flex gap-4 text-xs text-slate-400">
                          <span>处理率: {(data.processing_rate * 100).toFixed(1)}%</span>
                          <span>及时率: {(data.timely_processing_rate * 100).toFixed(1)}%</span>
                          <span>升级率: {(data.escalation_rate * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500 transition-all"
                              style={{ width: `${data.processing_rate * 100}%` }}
                            />
                          </div>
                          <p className="text-xs text-slate-500 mt-1">处理率</p>
                        </div>
                        <div>
                          <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 transition-all"
                              style={{ width: `${data.timely_processing_rate * 100}%` }}
                            />
                          </div>
                          <p className="text-xs text-slate-500 mt-1">及时率</p>
                        </div>
                        <div>
                          <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-orange-500 transition-all"
                              style={{ width: `${data.escalation_rate * 100}%` }}
                            />
                          </div>
                          <p className="text-xs text-slate-500 mt-1">升级率</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">
                        总预警数: {data.total}
                      </p>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}