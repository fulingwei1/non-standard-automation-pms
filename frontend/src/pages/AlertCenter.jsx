import { useState, useMemo, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  Search,
  Eye,
  Settings,
  Bell,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  FileText,
  RefreshCw,
  Download,
  CheckSquare,
  Square,
  ArrowUpDown,
  Filter,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  DialogDescription,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { alertApi, projectApi } from '../services/api'

// Alert level configuration
const alertLevelConfig = {
  URGENT: {
    label: '紧急',
    color: 'red',
    icon: AlertTriangle,
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
  },
  CRITICAL: {
    label: '严重',
    color: 'orange',
    icon: AlertCircle,
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    textColor: 'text-orange-400',
  },
  WARNING: {
    label: '注意',
    color: 'amber',
    icon: AlertCircle,
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    textColor: 'text-amber-400',
  },
  INFO: {
    label: '提示',
    color: 'blue',
    icon: AlertCircle,
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
  },
}

// Alert status configuration
const alertStatusConfig = {
  PENDING: { label: '待处理', color: 'amber', icon: Clock },
  ACTIVE: { label: '待处理', color: 'amber', icon: Clock },
  ACKNOWLEDGED: { label: '已确认', color: 'blue', icon: CheckCircle2 },
  RESOLVED: { label: '已解决', color: 'emerald', icon: CheckCircle2 },
  CLOSED: { label: '已关闭', color: 'slate', icon: XCircle },
  IGNORED: { label: '已忽略', color: 'slate', icon: XCircle },
}

// Alert type configuration
const alertTypeConfig = {
  PROJ_DELAY: { label: '项目进度延期预警', category: '项目' },
  PROJ_MILESTONE: { label: '里程碑逾期预警', category: '项目' },
  PO_DELIVERY: { label: '采购交期预警', category: '采购' },
  PO_SHORTAGE: { label: '物料短缺预警', category: '采购' },
  OS_DELIVERY: { label: '外协交期预警', category: '外协' },
  COST_OVERRUN: { label: '成本超支预警', category: '成本' },
  QA_INSPECTION: { label: '检验不合格预警', category: '质量' },
  TASK_OVERDUE: { label: '任务逾期预警', category: '任务' },
}

// Mock alert data
// Mock data - 已移除，使用真实API
// Statistics summary

export default function AlertCenter() {
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState({
    total: 0,
    urgent: 0,
    critical: 0,
    warning: 0,
    today_new: 0,
    today_closed: 0,
    urgent_change: 0,
    critical_change: 0,
    warning_change: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedLevel, setSelectedLevel] = useState('ALL')
  const [selectedStatus, setSelectedStatus] = useState('ALL')
  const [selectedProject, setSelectedProject] = useState('ALL')
  const [dateRange, setDateRange] = useState({ start: '', end: '' })
  const [showDetail, setShowDetail] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [showResolveDialog, setShowResolveDialog] = useState(false)
  const [showCloseDialog, setShowCloseDialog] = useState(false)
  const [resolveResult, setResolveResult] = useState('')
  const [closeReason, setCloseReason] = useState('')
  const [selectedAlerts, setSelectedAlerts] = useState(new Set())
  const [sortBy, setSortBy] = useState('triggered_at')
  const [sortOrder, setSortOrder] = useState('desc')
  const [projects, setProjects] = useState([])

  // Define functions first (before useEffect hooks that use them)
  const loadProjects = async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 1000 })
      const data = response.data || response
      const projectList = data.items || data || []
      
      // Transform to format needed by the component
      const transformedProjects = projectList.map(project => ({
        id: project.id || project.project_code,
        name: project.project_name || '',
      }))
      
      setProjects(transformedProjects)
    } catch (error) {
      console.error('Failed to load projects:', error)
      const mockProjects = [
        { id: 1, name: 'XX测试设备项目' },
        { id: 2, name: 'YY检测设备项目' },
        { id: 3, name: 'ZZ包装线项目' },
      ]
      setProjects(mockProjects)
    }
  }

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page,
        page_size: pageSize,
      }
      if (selectedLevel !== 'ALL') {
        params.alert_level = selectedLevel
      }
      if (selectedStatus !== 'ALL') {
        params.status = selectedStatus === 'ACTIVE' ? 'PENDING' : selectedStatus
      }
      if (selectedProject !== 'ALL') {
        params.project_id = parseInt(selectedProject)
      }
      if (dateRange.start) {
        params.date_from = dateRange.start
      }
      if (dateRange.end) {
        params.date_to = dateRange.end
      }
      if (searchQuery) {
        params.keyword = searchQuery
      }
      const response = await alertApi.list(params)
      const data = response.data?.data || response.data || response
      // Handle PaginatedResponse format
      if (data && typeof data === 'object' && 'items' in data) {
        setAlerts(data.items || [])
        setTotal(data.total || 0)
      } else if (Array.isArray(data)) {
        setAlerts(data)
        setTotal(data.length)
      } else {
        setAlerts([])
        setTotal(0)
      }
    } catch (err) {
      console.error('Failed to load alerts:', err)
      let errorMessage = '加载预警列表失败'
      if (err.response) {
        errorMessage = err.response.data?.detail || err.response.data?.message || errorMessage
      } else if (err.request) {
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      } else {
        errorMessage = err.message || errorMessage
      }
      setError(errorMessage)
      setAlerts([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, selectedLevel, selectedStatus, selectedProject, dateRange, searchQuery])

  const loadStatistics = useCallback(async () => {
    try {
      const response = await alertApi.dashboard()
      const data = response.data
      if (data) {
        setStats({
          total: data.active_alerts?.total || 0,
          urgent: data.active_alerts?.urgent || 0,
          critical: data.active_alerts?.critical || 0,
          warning: data.active_alerts?.warning || 0,
          today_new: data.today_new || 0,
          today_closed: data.today_closed || 0,
          urgent_change: 0,
          critical_change: 0,
          warning_change: 0,
        })
      }
    } catch (error) {
      console.error('Failed to load statistics:', error)
      // Calculate from loaded alerts as fallback
      setStats({
        total: alerts.length,
        urgent: alerts.filter(a => a.alert_level === 'URGENT').length,
        critical: alerts.filter(a => a.alert_level === 'CRITICAL').length,
        warning: alerts.filter(a => a.alert_level === 'WARNING').length,
        today_new: 0,
        today_closed: 0,
        urgent_change: 0,
        critical_change: 0,
        warning_change: 0,
      })
    }
  }, [])

  // Filter and sort alerts
  const filteredAlerts = useMemo(() => {
    let result = alerts

    // Client-side search
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase()
      result = result.filter((alert) => {
        return (
          alert.alert_no?.toLowerCase().includes(searchLower) ||
          alert.alert_title?.toLowerCase().includes(searchLower) ||
          alert.project_name?.toLowerCase().includes(searchLower) ||
          alert.target_name?.toLowerCase().includes(searchLower)
        )
      })
    }

    // Filter by project
    if (selectedProject !== 'ALL') {
      result = result.filter((alert) => {
        return alert.project_id === parseInt(selectedProject) || 
               alert.project_name === selectedProject
      })
    }

    // Filter by date range
    if (dateRange.start || dateRange.end) {
      result = result.filter((alert) => {
        if (!alert.triggered_at) return false
        const alertDate = new Date(alert.triggered_at)
        if (dateRange.start) {
          const startDate = new Date(dateRange.start)
          startDate.setHours(0, 0, 0, 0)
          if (alertDate < startDate) return false
        }
        if (dateRange.end) {
          const endDate = new Date(dateRange.end)
          endDate.setHours(23, 59, 59, 999)
          if (alertDate > endDate) return false
        }
        return true
      })
    }

    // Sort
    result = [...result].sort((a, b) => {
      let aValue = a[sortBy]
      let bValue = b[sortBy]

      if (sortBy === 'triggered_at') {
        aValue = new Date(aValue || 0).getTime()
        bValue = new Date(bValue || 0).getTime()
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

    return result
  }, [alerts, searchQuery, selectedProject, dateRange, sortBy, sortOrder])

  const navigate = useNavigate()

  const handleViewDetail = (alert) => {
    setSelectedAlert(alert)
    setShowDetail(true)
  }

  const handleViewFullDetail = (alert) => {
    navigate(`/alerts/${alert.id}`)
  }

  const handleAcknowledge = useCallback(async (alertId) => {
    try {
      await alertApi.acknowledge(alertId)
      await loadAlerts()
      await loadStatistics()
      toast.success('预警已确认')
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
      toast.error('确认失败，请稍后重试')
      // Update local state on error
      setAlerts((prev) =>
        prev.map((alert) =>
          alert.id === alertId
            ? { ...alert, status: 'ACKNOWLEDGED', acknowledged_at: new Date().toISOString() }
            : alert
        )
      )
    }
  }, [loadAlerts, loadStatistics])

  const handleResolve = useCallback(async (alertId, result) => {
    if (!result || !result.trim()) {
      toast.error('请输入处理结果')
      return
    }
    try {
      await alertApi.resolve(alertId, { handle_result: result })
      await loadAlerts()
      await loadStatistics()
      setShowDetail(false)
      setShowResolveDialog(false)
      setResolveResult('')
      toast.success('预警已标记为已解决')
    } catch (error) {
      console.error('Failed to resolve alert:', error)
      toast.error('操作失败，请稍后重试')
    }
  }, [loadAlerts, loadStatistics])

  const handleClose = useCallback(async (alertId, reason) => {
    if (!reason || !reason.trim()) {
      toast.error('请输入关闭原因')
      return
    }
    try {
      await alertApi.close(alertId, { handle_result: reason })
      await loadAlerts()
      await loadStatistics()
      setShowDetail(false)
      setShowCloseDialog(false)
      setCloseReason('')
      toast.success('预警已关闭')
    } catch (error) {
      console.error('Failed to close alert:', error)
      toast.error('关闭失败，请稍后重试')
    }
  }, [loadAlerts, loadStatistics])

  const openResolveDialog = () => {
    setShowResolveDialog(true)
    setResolveResult('')
  }

  const openCloseDialog = () => {
    setShowCloseDialog(true)
    setCloseReason('')
  }

  const handleSelectAlert = (alertId) => {
    const newSelected = new Set(selectedAlerts)
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId)
    } else {
      newSelected.add(alertId)
    }
    setSelectedAlerts(newSelected)
  }

  const handleSelectAll = useCallback(() => {
    if (selectedAlerts.size === filteredAlerts.length) {
      setSelectedAlerts(new Set())
    } else {
      setSelectedAlerts(new Set(filteredAlerts.map(alert => alert.id)))
    }
  }, [selectedAlerts, filteredAlerts])

  // useEffect hooks (after all function definitions)
  // Load alerts on mount and when dependencies change
  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  // Load statistics on mount and when filters change
  useEffect(() => {
    loadStatistics()
  }, [loadStatistics])

  // Load projects for filter
  useEffect(() => {
    loadProjects()
  }, [])

  // Load alerts with debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        loadAlerts()
      } else {
        setPage(1)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery, loadAlerts])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl/Cmd + F: Focus search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault()
        const searchInput = document.querySelector('input[placeholder*="搜索"]')
        if (searchInput) {
          searchInput.focus()
          searchInput.select()
        }
      }
      // Esc: Close dialogs
      if (e.key === 'Escape') {
        if (showDetail) setShowDetail(false)
        if (showResolveDialog) setShowResolveDialog(false)
        if (showCloseDialog) setShowCloseDialog(false)
      }
      // Ctrl/Cmd + A: Select all (when not in input)
      if ((e.ctrlKey || e.metaKey) && e.key === 'a' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault()
        handleSelectAll()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showDetail, showResolveDialog, showCloseDialog, filteredAlerts, handleSelectAll])

  const handleBatchAcknowledge = useCallback(async () => {
    if (selectedAlerts.size === 0) return
    
    try {
      const promises = Array.from(selectedAlerts).map(id => alertApi.acknowledge(id))
      await Promise.all(promises)
      await loadAlerts()
      await loadStatistics()
      const count = selectedAlerts.size
      setSelectedAlerts(new Set())
      toast.success(`已批量确认 ${count} 条预警`)
    } catch (error) {
      console.error('Failed to batch acknowledge:', error)
      toast.error('批量确认失败，请稍后重试')
    }
  }, [selectedAlerts, loadAlerts, loadStatistics])

  const handleExportExcel = async () => {
    try {
      const params = {
        project_id: filters.project_id || undefined,
        alert_level: filters.alert_level || undefined,
        status: filters.status || undefined,
        rule_type: filters.rule_type || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
        group_by: 'none', // 可选: 'none', 'level', 'type'
      }
      
      const response = await alertApi.exportExcel(params)
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `预警报表_${new Date().toISOString().split('T')[0]}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Excel导出成功')
    } catch (error) {
      console.error('Failed to export Excel:', error)
      toast.error('导出失败，请稍后重试')
    }
  }

  const handleExportPdf = async () => {
    try {
      const params = {
        project_id: filters.project_id || undefined,
        alert_level: filters.alert_level || undefined,
        status: filters.status || undefined,
        rule_type: filters.rule_type || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      }
      
      const response = await alertApi.exportPdf(params)
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `预警报表_${new Date().toISOString().split('T')[0]}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('PDF导出成功')
    } catch (error) {
      console.error('Failed to export PDF:', error)
      toast.error('导出失败，请稍后重试')
    }
  }

  const handleExport = () => {
    try {
      const csvContent = [
        ['预警编号', '预警级别', '预警类型', '标题', '项目名称', '负责人', '状态', '触发时间'].join(','),
        ...filteredAlerts.map(alert => [
          alert.alert_no || '',
          alertLevelConfig[alert.alert_level]?.label || '',
          alertTypeConfig[alert.alert_type]?.label || '',
          `"${(alert.alert_title || alert.title || '').replace(/"/g, '""')}"`,
          `"${(alert.project_name || '').replace(/"/g, '""')}"`,
          `"${(alert.handler_name || alert.assigned_to || '').replace(/"/g, '""')}"`,
          alertStatusConfig[alert.status]?.label || '',
          alert.triggered_at || '',
        ].join(','))
      ].join('\n')

      const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `预警列表_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      toast.success('导出成功')
    } catch (error) {
      console.error('Failed to export:', error)
      toast.error('导出失败，请稍后重试')
    }
  }

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const formatTimeAgo = (timeString) => {
    if (!timeString) return ''
    const now = new Date()
    const time = new Date(timeString)
    const diffMs = now - time
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    return `${diffDays}天前`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警中心"
        description="实时监控项目风险，及时处理异常情况"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {selectedAlerts.size > 0 && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={handleBatchAcknowledge}
                  disabled={loading}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  批量确认 ({selectedAlerts.size})
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={() => setSelectedAlerts(new Set())}
                >
                  <XCircle className="w-4 h-4" />
                  取消选择
                </Button>
              </>
            )}
            {filteredAlerts.length > 0 && (
              <div className="text-sm text-slate-400 hidden md:block px-2">
                显示 {filteredAlerts.length} / {total} 条
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExport}
              disabled={loading || filteredAlerts.length === 0}
            >
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {
                loadAlerts()
                loadStatistics()
                toast.success('数据已刷新')
              }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => navigate('/alert-rules')}
            >
              <Settings className="w-4 h-4" />
              规则配置
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics Overview */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-red-500/5 border-red-500/20 cursor-pointer hover:bg-red-500/10 transition-colors"
              onClick={() => {
                setSelectedLevel('URGENT')
                setSelectedStatus('ALL')
                // Scroll to list
                setTimeout(() => {
                  document.querySelector('.space-y-3')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }, 100)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">🔴 紧急</p>
                    <p className="text-2xl font-bold text-red-400">{stats.urgent}</p>
                    {stats.urgent_change > 0 && (
                      <p className="text-xs text-red-400 mt-1 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        +{stats.urgent_change}↑
                      </p>
                    )}
                  </div>
                  <AlertTriangle className="w-8 h-8 text-red-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card 
              className="bg-orange-500/5 border-orange-500/20 cursor-pointer hover:bg-orange-500/10 transition-colors"
              onClick={() => {
                setSelectedLevel('CRITICAL')
                setSelectedStatus('ALL')
                setTimeout(() => {
                  document.querySelector('.space-y-3')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }, 100)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">🟠 严重</p>
                    <p className="text-2xl font-bold text-orange-400">{stats.critical}</p>
                    {stats.critical_change > 0 && (
                      <p className="text-xs text-orange-400 mt-1 flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        +{stats.critical_change}↑
                      </p>
                    )}
                  </div>
                  <AlertCircle className="w-8 h-8 text-orange-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card 
              className="bg-amber-500/5 border-amber-500/20 cursor-pointer hover:bg-amber-500/10 transition-colors"
              onClick={() => {
                setSelectedLevel('WARNING')
                setSelectedStatus('ALL')
                setTimeout(() => {
                  document.querySelector('.space-y-3')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }, 100)
              }}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">🟡 注意</p>
                    <p className="text-2xl font-bold text-amber-400">{stats.warning}</p>
                    {stats.warning_change < 0 && (
                      <p className="text-xs text-amber-400 mt-1 flex items-center gap-1">
                        <TrendingDown className="w-3 h-3" />
                        {stats.warning_change}↓
                      </p>
                    )}
                  </div>
                  <AlertCircle className="w-8 h-8 text-amber-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/5 border-blue-500/20">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">📊 今日</p>
                    <p className="text-2xl font-bold text-blue-400">
                      处理 {stats.today_new}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">关闭 {stats.today_closed}</p>
                  </div>
                  <Calendar className="w-8 h-8 text-blue-400/50" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="space-y-4">
                {/* First Row: Search and Project Filter */}
                <div className="flex flex-col md:flex-row gap-4">
                  {/* Search */}
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        placeholder="搜索预警编号、标题或项目名称... (Ctrl+F)"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-slate-800/50 border-slate-700"
                      />
                    </div>
                  </div>

                  {/* Project Filter */}
                  <div className="w-full md:w-48">
                    <select
                      value={selectedProject}
                      onChange={(e) => setSelectedProject(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      <option value="ALL">全部项目</option>
                      {projects.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Date Range */}
                  <div className="flex gap-2">
                    <Input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                      className="w-full md:w-40 bg-slate-800/50 border-slate-700 text-sm"
                      placeholder="开始日期"
                    />
                    <Input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                      className="w-full md:w-40 bg-slate-800/50 border-slate-700 text-sm"
                      placeholder="结束日期"
                    />
                    {(dateRange.start || dateRange.end) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDateRange({ start: '', end: '' })}
                        className="text-slate-400 hover:text-white"
                      >
                        <XCircle className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>

                {/* Second Row: Level and Status Filters */}
                <div className="flex flex-wrap gap-4">
                  {/* Level Filter */}
                  <div className="flex gap-2">
                    {['ALL', 'URGENT', 'CRITICAL', 'WARNING'].map((level) => {
                      const config = level === 'ALL' 
                        ? { label: '全部', color: 'slate' }
                        : alertLevelConfig[level]
                      return (
                        <Button
                          key={level}
                          variant={selectedLevel === level ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setSelectedLevel(level)}
                          className={cn(
                            selectedLevel === level && config.color === 'red' && 'bg-red-500/20 border-red-500/50 text-red-400',
                            selectedLevel === level && config.color === 'orange' && 'bg-orange-500/20 border-orange-500/50 text-orange-400',
                            selectedLevel === level && config.color === 'amber' && 'bg-amber-500/20 border-amber-500/50 text-amber-400',
                          )}
                        >
                          {config.label}
                        </Button>
                      )
                    })}
                  </div>

                  {/* Status Filter */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">状态:</span>
                    <div className="flex gap-2">
                      {['ALL', 'PENDING', 'ACTIVE', 'ACKNOWLEDGED', 'CLOSED'].map((status) => {
                        const config = status === 'ALL'
                          ? { label: '全部状态', color: 'slate' }
                          : alertStatusConfig[status] || alertStatusConfig.ACTIVE
                        return (
                          <Button
                            key={status}
                            variant={selectedStatus === status ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSelectedStatus(status)}
                          >
                            {config.label}
                          </Button>
                        )
                      })}
                    </div>
                  </div>

                  {/* Clear Filters */}
                  {(selectedLevel !== 'ALL' || selectedStatus !== 'ALL' || selectedProject !== 'ALL' || dateRange.start || dateRange.end || searchQuery) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedLevel('ALL')
                        setSelectedStatus('ALL')
                        setSelectedProject('ALL')
                        setDateRange({ start: '', end: '' })
                        setSearchQuery('')
                      }}
                      className="text-slate-400 hover:text-white"
                    >
                      <XCircle className="w-4 h-4 mr-1" />
                      清除筛选
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Alert List */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-3"
        >
          {loading ? (
            <LoadingCard rows={5} />
          ) : error ? (
            <ErrorMessage error={error} onRetry={loadAlerts} />
          ) : filteredAlerts.length === 0 ? (
            <EmptyState
              icon={AlertCircle}
              title="暂无预警数据"
              description={
                searchQuery || selectedLevel !== 'ALL' || selectedStatus !== 'ALL' || selectedProject !== 'ALL' || dateRange.start || dateRange.end
                  ? "当前筛选条件下没有匹配的预警，请尝试调整筛选条件"
                  : "当前没有预警数据"
              }
              action={
                (searchQuery || selectedLevel !== 'ALL' || selectedStatus !== 'ALL' || selectedProject !== 'ALL' || dateRange.start || dateRange.end) && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelectedLevel('ALL')
                      setSelectedStatus('ALL')
                      setSelectedProject('ALL')
                      setDateRange({ start: '', end: '' })
                      setSearchQuery('')
                    }}
                  >
                    清除筛选
                  </Button>
                )
              }
            />
          ) : (
            <>
              {/* List Header with Sort */}
              <Card className="bg-slate-800/30">
                <CardContent className="p-3">
                  <div className="flex items-center gap-4 text-sm text-slate-400">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleSelectAll}
                        className="p-1 hover:text-white transition-colors"
                      >
                        {selectedAlerts.size === filteredAlerts.length ? (
                          <CheckSquare className="w-4 h-4" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>
                      <span>全选</span>
                    </div>
                    <div className="flex-1 flex items-center gap-4">
                      <button
                        onClick={() => handleSort('triggered_at')}
                        className="flex items-center gap-1 hover:text-white transition-colors"
                      >
                        <span>触发时间</span>
                        <ArrowUpDown className="w-3 h-3" />
                        {sortBy === 'triggered_at' && (
                          <span className="text-xs">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                      <button
                        onClick={() => handleSort('alert_level')}
                        className="flex items-center gap-1 hover:text-white transition-colors"
                      >
                        <span>级别</span>
                        <ArrowUpDown className="w-3 h-3" />
                        {sortBy === 'alert_level' && (
                          <span className="text-xs">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {filteredAlerts.map((alert) => {
                const levelConfig = alertLevelConfig[alert.alert_level] || alertLevelConfig.WARNING
                const LevelIcon = levelConfig.icon
                const isSelected = selectedAlerts.has(alert.id)

                return (
                <motion.div key={alert.id} variants={fadeIn}>
                  <Card
                    className={cn(
                      'hover:bg-slate-800/50 transition-colors',
                      levelConfig.bgColor,
                      levelConfig.borderColor,
                      'border',
                      isSelected && 'ring-2 ring-primary/50'
                    )}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3 flex-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleSelectAlert(alert.id)
                            }}
                            className="mt-1 p-1 hover:text-white transition-colors"
                          >
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-primary" />
                            ) : (
                              <Square className="w-4 h-4 text-slate-500" />
                            )}
                          </button>
                          <div 
                            className="flex-1 space-y-2 cursor-pointer"
                            onClick={() => handleViewDetail(alert)}
                          >
                            {/* Header */}
                            <div className="flex items-center gap-3">
                              <LevelIcon className={cn('w-5 h-5', levelConfig.textColor)} />
                              <span className="font-mono text-sm text-slate-300">
                                {alert.alert_no}
                              </span>
                              <Badge variant="outline" className={cn(levelConfig.textColor, levelConfig.borderColor)}>
                                {alert.rule_name || alert.target_type}
                              </Badge>
                              <Badge variant="secondary" className="ml-auto">
                                {formatTimeAgo(alert.triggered_at)}
                              </Badge>
                            </div>

                          {/* Title */}
                          <h3 className="text-white font-medium">{alert.alert_title}</h3>

                          {/* Content */}
                          {alert.alert_content && (
                            <p className="text-sm text-slate-400">{alert.alert_content}</p>
                          )}

                          {/* Footer */}
                          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                            {alert.handler_name && (
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                负责人: {alert.handler_name}
                              </span>
                            )}
                            {alert.project_name && (
                              <span 
                                className="flex items-center gap-1 hover:text-white transition-colors cursor-pointer"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  const project = projects.find(p => p.name === alert.project_name)
                                  if (project) {
                                    setSelectedProject(project.id.toString())
                                    setTimeout(() => {
                                      document.querySelector('.space-y-3')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                                    }, 100)
                                  }
                                }}
                              >
                                <FileText className="w-3 h-3" />
                                项目: {alert.project_name}
                              </span>
                            )}
                            {alert.acknowledged_at && (
                              <span className="flex items-center gap-1 text-emerald-400">
                                <CheckCircle2 className="w-3 h-3" />
                                已确认({formatTimeAgo(alert.acknowledged_at)})
                              </span>
                            )}
                            {alert.metric_value !== undefined && alert.threshold_value !== undefined && (
                              <span className="flex items-center gap-1 text-slate-400">
                                <span>指标: {alert.metric_value}</span>
                                <span className="text-slate-600">/</span>
                                <span>阈值: {alert.threshold_value}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                        <div className="flex items-center gap-2">
                          {(alert.status === 'PENDING' || alert.status === 'ACTIVE') && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleAcknowledge(alert.id)
                              }}
                              className="h-8"
                            >
                              确认
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleViewDetail(alert)
                            }}
                            className="h-8 gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            快速查看
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleViewFullDetail(alert)
                            }}
                            className="h-8"
                          >
                            详情页
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
                )
              })
            }

        {/* Pagination */}
        {!loading && filteredAlerts.length > 0 && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <span>共 {total} 条预警</span>
              {filteredAlerts.length < total && (
                <span className="text-slate-500">
                  (当前显示 {filteredAlerts.length} 条)
                </span>
              )}
            </div>
            {total > pageSize && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1 || loading}
                  onClick={() => setPage(page - 1)}
                >
                  上一页
                </Button>
                <span className="px-4">
                  第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= Math.ceil(total / pageSize) || loading}
                  onClick={() => setPage(page + 1)}
                >
                  下一页
                </Button>
              </div>
            )}
          </div>
        )}
            </>
          )}
        </motion.div>
      </div>

      {/* Alert Detail Dialog */}
      <AnimatePresence>
        {showDetail && selectedAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowDetail(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-slate-900 rounded-xl border border-slate-700 max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6 space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white mb-2">
                      {selectedAlert.alert_no}
                    </h2>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={cn(
                          alertLevelConfig[selectedAlert.alert_level].textColor,
                          alertLevelConfig[selectedAlert.alert_level].borderColor
                        )}
                      >
                        {alertLevelConfig[selectedAlert.alert_level].label}
                      </Badge>
                      <Badge variant="secondary">
                        {alertTypeConfig[selectedAlert.alert_type]?.label || selectedAlert.alert_type}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowDetail(false)}
                  >
                    <XCircle className="w-4 h-4" />
                  </Button>
                </div>

                {/* Content */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white mb-2">
                      {selectedAlert.alert_title || selectedAlert.title}
                    </h3>
                    <p className="text-slate-400">{selectedAlert.alert_content || selectedAlert.content}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-500 mb-1">触发时间</p>
                      <p className="text-white">{selectedAlert.triggered_at}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 mb-1">当前状态</p>
                      <Badge variant="secondary">
                        {alertStatusConfig[selectedAlert.status]?.label || selectedAlert.status}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 mb-1">负责人</p>
                      <p className="text-white">
                        {selectedAlert.assigned_to}({selectedAlert.assigned_to_role})
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 mb-1">关联项目</p>
                      <p className="text-white">{selectedAlert.project_name}</p>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-4 border-t border-slate-700">
                  {(selectedAlert.status === 'PENDING' || selectedAlert.status === 'ACTIVE') && (
                    <Button
                      onClick={() => {
                        handleAcknowledge(selectedAlert.id)
                        setShowDetail(false)
                      }}
                    >
                      确认预警
                    </Button>
                  )}
                  {selectedAlert.status !== 'RESOLVED' && (
                    <Button
                      variant="outline"
                      onClick={openResolveDialog}
                    >
                      标记已解决
                    </Button>
                  )}
                  {selectedAlert.status !== 'CLOSED' && (
                    <Button
                      variant="outline"
                      onClick={openCloseDialog}
                    >
                      关闭
                    </Button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Resolve Dialog */}
      <Dialog open={showResolveDialog} onOpenChange={setShowResolveDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>标记预警为已解决</DialogTitle>
            <DialogDescription>请输入处理结果，这将帮助其他团队成员了解问题解决过程。</DialogDescription>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 mb-2 block">
                  处理结果 <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={resolveResult}
                  onChange={(e) => setResolveResult(e.target.value)}
                  placeholder="请输入处理结果..."
                  rows={4}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent resize-none"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowResolveDialog(false)
                setResolveResult('')
              }}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                if (selectedAlert) {
                  handleResolve(selectedAlert.id, resolveResult)
                }
              }}
            >
              确认
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Close Dialog */}
      <Dialog open={showCloseDialog} onOpenChange={setShowCloseDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>关闭预警</DialogTitle>
            <DialogDescription>请输入关闭原因，这将记录预警的最终处理结果。</DialogDescription>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 mb-2 block">
                  关闭原因 <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={closeReason}
                  onChange={(e) => setCloseReason(e.target.value)}
                  placeholder="请输入关闭原因..."
                  rows={4}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent resize-none"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCloseDialog(false)
                setCloseReason('')
              }}
            >
              取消
            </Button>
            <Button
              onClick={() => {
                if (selectedAlert) {
                  handleClose(selectedAlert.id, closeReason)
                }
              }}
            >
              确认关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

