import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Calendar,
  Download,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { alertApi } from '../services/api'
import { LoadingCard, ErrorMessage, LoadingSpinner } from '../components/common'

export default function AlertStatistics() {
  const [stats, setStats] = useState(null)
  const [topProjects, setTopProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [period, setPeriod] = useState('WEEKLY')

  useEffect(() => {
    loadStatistics()
  }, [period])

  const loadStatistics = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await alertApi.statistics({ period })
      const data = res.data || res
      setStats(data.summary || {})
      setTopProjects(data.top_projects || [])
    } catch (err) {
      console.error('Failed to load statistics:', err)
      const errorMessage = err.response?.data?.detail || err.message || '加载统计数据失败'
      setError(errorMessage)
      // 如果是演示账号，设置空数据而不是显示错误
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setStats({})
        setTopProjects([])
        setError(null) // Clear error for demo accounts
      }
    } finally {
      setLoading(false)
    }
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
        actions={
          <div className="flex gap-2">
            <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
              {['DAILY', 'WEEKLY', 'MONTHLY'].map((p) => (
                <Button
                  key={p}
                  variant={period === p ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setPeriod(p)}
                >
                  {p === 'DAILY' ? '今日' : p === 'WEEKLY' ? '本周' : '本月'}
                </Button>
              ))}
            </div>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
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
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardHeader>
              <CardTitle>响应时效统计</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-slate-500 mb-1">平均响应时间</p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.response_metrics?.avg_response_time
                      ? `${(stats.response_metrics.avg_response_time / 60).toFixed(1)}小时`
                      : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">平均解决时间</p>
                  <p className="text-2xl font-bold text-white">
                    {stats?.response_metrics?.avg_resolve_time
                      ? `${(stats.response_metrics.avg_resolve_time / 60).toFixed(1)}小时`
                      : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">响应达标率</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {stats?.response_metrics?.response_rate
                      ? `${(stats.response_metrics.response_rate * 100).toFixed(0)}%`
                      : '-'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">超时未处理</p>
                  <p className="text-2xl font-bold text-red-400">
                    {stats?.response_metrics?.timeout_count || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

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

