/**
 * Scheduler Monitoring Dashboard
 * 调度器监控仪表盘
 * Features: Task execution metrics, Failure heatmap, Notification chain metrics, Prometheus export
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  Server,
  Zap,
  Timer,
  Target,
  XCircle,
  Info,
  Filter,
  Search,
  Calendar,
  Bell,
  Send,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Progress,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  LoadingCard,
  ErrorMessage,
  EmptyState,
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { schedulerApi } from '../services/api'

export default function SchedulerMonitoringDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [metrics, setMetrics] = useState([])
  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [services, setServices] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30) // seconds

  // Fetch all data
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [metricsRes, statusRes, servicesRes] = await Promise.all([
        schedulerApi.metrics(),
        schedulerApi.status(),
        schedulerApi.listServices(),
      ])

      if (metricsRes.data?.code === 200) {
        setMetrics(metricsRes.data.data?.metrics || [])
      }

      if (statusRes.data?.code === 200) {
        setSchedulerStatus(statusRes.data.data)
      }

      if (servicesRes.data?.code === 200) {
        setServices(servicesRes.data.data?.services || [])
      }
    } catch (err) {
      console.error('Failed to fetch scheduler data:', err)
      setError(err.message || '获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchData()
    }, refreshInterval * 1000)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  // Filtered metrics
  const filteredMetrics = useMemo(() => {
    let filtered = metrics

    if (searchTerm) {
      filtered = filtered.filter(
        (m) =>
          m.job_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          m.job_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          m.owner?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    if (filterCategory !== 'all') {
      filtered = filtered.filter((m) => m.category === filterCategory)
    }

    return filtered
  }, [metrics, searchTerm, filterCategory])

  // Statistics
  const stats = useMemo(() => {
    const total = metrics.length
    const totalSuccess = metrics.reduce((sum, m) => sum + (m.success_count || 0), 0)
    const totalFailure = metrics.reduce((sum, m) => sum + (m.failure_count || 0), 0)
    const totalRuns = totalSuccess + totalFailure
    const successRate = totalRuns > 0 ? ((totalSuccess / totalRuns) * 100).toFixed(1) : 0
    const avgDuration = metrics.reduce((sum, m) => sum + (m.avg_duration_ms || 0), 0) / (total || 1)
    const jobsWithFailures = metrics.filter((m) => (m.failure_count || 0) > 0).length

    return {
      total,
      totalSuccess,
      totalFailure,
      totalRuns,
      successRate: parseFloat(successRate),
      avgDuration: avgDuration.toFixed(2),
      jobsWithFailures,
    }
  }, [metrics])

  // Categories
  const categories = useMemo(() => {
    const cats = new Set(metrics.map((m) => m.category).filter(Boolean))
    return Array.from(cats).sort()
  }, [metrics])

  // Failure heatmap data (group by category)
  const failureHeatmap = useMemo(() => {
    const heatmap = {}
    metrics.forEach((m) => {
      const cat = m.category || 'Unknown'
      if (!heatmap[cat]) {
        heatmap[cat] = {
          category: cat,
          totalFailures: 0,
          jobs: [],
        }
      }
      heatmap[cat].totalFailures += m.failure_count || 0
      if ((m.failure_count || 0) > 0) {
        heatmap[cat].jobs.push({
          job_id: m.job_id,
          job_name: m.job_name,
          failure_count: m.failure_count,
        })
      }
    })
    return Object.values(heatmap).sort((a, b) => b.totalFailures - a.totalFailures)
  }, [metrics])

  // Notification chain metrics (find send_alert_notifications job)
  const notificationMetrics = useMemo(() => {
    return metrics.find((m) => m.job_id === 'send_alert_notifications') || null
  }, [metrics])

  // Export Prometheus metrics
  const handleExportPrometheus = async () => {
    try {
      const res = await schedulerApi.metricsPrometheus()
      const blob = new Blob([res.data], { type: 'text/plain' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scheduler_metrics_${new Date().toISOString().split('T')[0]}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export Prometheus metrics:', err)
      alert('导出失败: ' + (err.message || '未知错误'))
    }
  }

  if (loading && metrics.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="调度器监控仪表盘" description="实时监控调度任务执行情况" />
        <LoadingCard />
      </div>
    )
  }

  if (error && metrics.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="调度器监控仪表盘" description="实时监控调度任务执行情况" />
        <ErrorMessage message={error} onRetry={fetchData} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="调度器监控仪表盘"
        description="实时监控调度任务执行情况、失败热力图和通知链路指标"
      >
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={loading}
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', loading && 'animate-spin')} />
            刷新
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportPrometheus}>
            <Download className="h-4 w-4 mr-2" />
            Prometheus 导出
          </Button>
        </div>
      </PageHeader>

      {/* Statistics Cards */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">总任务数</p>
                  <p className="text-2xl font-bold mt-1">{stats.total}</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-blue-500/10 flex items-center justify-center">
                  <Activity className="h-6 w-6 text-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">成功率</p>
                  <p className="text-2xl font-bold mt-1">{stats.successRate}%</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stats.totalSuccess} / {stats.totalRuns} 次执行
                  </p>
                </div>
                <div className="h-12 w-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">平均耗时</p>
                  <p className="text-2xl font-bold mt-1">{stats.avgDuration}ms</p>
                </div>
                <div className="h-12 w-12 rounded-full bg-purple-500/10 flex items-center justify-center">
                  <Timer className="h-6 w-6 text-purple-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">失败任务数</p>
                  <p className="text-2xl font-bold mt-1">{stats.jobsWithFailures}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    总失败次数: {stats.totalFailure}
                  </p>
                </div>
                <div className="h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center">
                  <XCircle className="h-6 w-6 text-red-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Scheduler Status */}
      {schedulerStatus && (
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                调度器状态
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Badge variant={schedulerStatus.running ? 'success' : 'destructive'}>
                  {schedulerStatus.running ? '运行中' : '已停止'}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  已注册任务: {schedulerStatus.job_count || 0}
                </span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Notification Chain Metrics */}
      {notificationMetrics && (
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                通知链路指标
              </CardTitle>
              <CardDescription>消息推送服务 (send_alert_notifications) 执行情况</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">成功次数</p>
                  <p className="text-2xl font-bold">{notificationMetrics.success_count || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">失败次数</p>
                  <p className="text-2xl font-bold text-red-500">
                    {notificationMetrics.failure_count || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">平均耗时</p>
                  <p className="text-2xl font-bold">
                    {notificationMetrics.avg_duration_ms
                      ? `${notificationMetrics.avg_duration_ms.toFixed(2)}ms`
                      : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">P95 耗时</p>
                  <p className="text-2xl font-bold">
                    {notificationMetrics.p95_duration_ms
                      ? `${notificationMetrics.p95_duration_ms.toFixed(2)}ms`
                      : 'N/A'}
                  </p>
                </div>
              </div>
              {notificationMetrics.last_timestamp && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    最后执行时间: {formatDate(notificationMetrics.last_timestamp)}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="tasks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="tasks">任务运行表</TabsTrigger>
          <TabsTrigger value="heatmap">失败热力图</TabsTrigger>
        </TabsList>

        {/* Task Execution Table */}
        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>任务运行表</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="搜索任务..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-64"
                    />
                  </div>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  >
                    <option value="all">所有类别</option>
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredMetrics.length === 0 ? (
                <EmptyState message="没有找到匹配的任务" />
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>任务ID</TableHead>
                        <TableHead>任务名称</TableHead>
                        <TableHead>负责人</TableHead>
                        <TableHead>类别</TableHead>
                        <TableHead>成功次数</TableHead>
                        <TableHead>失败次数</TableHead>
                        <TableHead>成功率</TableHead>
                        <TableHead>平均耗时</TableHead>
                        <TableHead>P95 耗时</TableHead>
                        <TableHead>最后执行时间</TableHead>
                        <TableHead>状态</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredMetrics.map((metric) => {
                        const totalRuns = (metric.success_count || 0) + (metric.failure_count || 0)
                        const successRate =
                          totalRuns > 0
                            ? ((metric.success_count / totalRuns) * 100).toFixed(1)
                            : 0

                        return (
                          <TableRow key={metric.job_id}>
                            <TableCell className="font-mono text-sm">{metric.job_id}</TableCell>
                            <TableCell className="font-medium">{metric.job_name || '-'}</TableCell>
                            <TableCell>{metric.owner || '-'}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{metric.category || 'Unknown'}</Badge>
                            </TableCell>
                            <TableCell>
                              <span className="text-emerald-600 font-medium">
                                {metric.success_count || 0}
                              </span>
                            </TableCell>
                            <TableCell>
                              <span className="text-red-600 font-medium">
                                {metric.failure_count || 0}
                              </span>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <span>{successRate}%</span>
                                <Progress value={parseFloat(successRate)} className="w-16 h-2" />
                              </div>
                            </TableCell>
                            <TableCell>
                              {metric.avg_duration_ms
                                ? `${metric.avg_duration_ms.toFixed(2)}ms`
                                : '-'}
                            </TableCell>
                            <TableCell>
                              {metric.p95_duration_ms
                                ? `${metric.p95_duration_ms.toFixed(2)}ms`
                                : '-'}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {metric.last_timestamp
                                ? formatDate(metric.last_timestamp)
                                : '-'}
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  metric.last_status === 'success' ? 'success' : 'destructive'
                                }
                              >
                                {metric.last_status === 'success' ? '成功' : '失败'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Failure Heatmap */}
        <TabsContent value="heatmap" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>失败热力图</CardTitle>
              <CardDescription>按类别统计任务失败情况</CardDescription>
            </CardHeader>
            <CardContent>
              {failureHeatmap.length === 0 ? (
                <EmptyState message="暂无失败记录" />
              ) : (
                <div className="space-y-4">
                  {failureHeatmap.map((item) => {
                    const maxFailures = Math.max(
                      ...failureHeatmap.map((i) => i.totalFailures),
                      1
                    )
                    const intensity = (item.totalFailures / maxFailures) * 100

                    return (
                      <div key={item.category} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{item.category}</Badge>
                            <span className="text-sm text-muted-foreground">
                              失败次数: {item.totalFailures}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                              <div
                                className={cn(
                                  'h-full transition-all',
                                  intensity > 70
                                    ? 'bg-red-500'
                                    : intensity > 40
                                    ? 'bg-amber-500'
                                    : 'bg-yellow-500'
                                )}
                                style={{ width: `${intensity}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground w-12 text-right">
                              {intensity.toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        {item.jobs.length > 0 && (
                          <div className="ml-6 space-y-1">
                            {item.jobs.map((job) => (
                              <div
                                key={job.job_id}
                                className="text-sm text-muted-foreground flex items-center gap-2"
                              >
                                <span className="font-mono text-xs">{job.job_id}</span>
                                <span className="text-red-600">({job.failure_count} 次失败)</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}



