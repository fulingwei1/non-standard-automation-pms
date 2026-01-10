import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDraggable,
  useDroppable,
  DragOverlay,
} from '@dnd-kit/core'
import {
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable'
import {
  CSS,
} from '@dnd-kit/utilities'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Plus,
  Search,
  Filter,
  Eye,
  Edit3,
  User,
  Calendar,
  Tag,
  FileText,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Download,
  Upload,
  List,
  Kanban,
  BarChart3,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { issueApi, issueTemplateApi } from '../services/api'
import { SimpleBarChart, SimpleLineChart, SimplePieChart } from '../components/administrative/StatisticsCharts'

// Mock issue data
// Mock data - 已移除，使用真实API
const severityColors = {
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/30',
  MAJOR: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  MINOR: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
}

const priorityColors = {
  URGENT: 'bg-red-500/20 text-red-400',
  HIGH: 'bg-orange-500/20 text-orange-400',
  MEDIUM: 'bg-blue-500/20 text-blue-400',
  LOW: 'bg-gray-500/20 text-gray-400',
}

const statusColors = {
  OPEN: 'bg-blue-500/20 text-blue-400',
  PROCESSING: 'bg-yellow-500/20 text-yellow-400',
  RESOLVED: 'bg-green-500/20 text-green-400',
  CLOSED: 'bg-gray-500/20 text-gray-400',
  DEFERRED: 'bg-purple-500/20 text-purple-400',
}

const statusIcons = {
  OPEN: AlertCircle,
  PROCESSING: Clock,
  RESOLVED: CheckCircle2,
  CLOSED: CheckCircle2,
  DEFERRED: XCircle,
}

export default function IssueManagement() {
  const [issues, setIssues] = useState([])
  const [filteredIssues, setFilteredIssues] = useState([])
  const [selectedIssue, setSelectedIssue] = useState(null)
  const [showDetail, setShowDetail] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterSeverity, setFilterSeverity] = useState('all')
  const [filterCategory, setFilterCategory] = useState('all')
  const [selectedIssues, setSelectedIssues] = useState([])
  const [viewMode, setViewMode] = useState('list') // 'list' | 'board' | 'statistics'
  const [showFollowUps, setShowFollowUps] = useState(false)
  const [showRelated, setShowRelated] = useState(false)
  const [statistics, setStatistics] = useState({
    total: 0,
    open: 0,
    processing: 0,
    resolved: 0,
    closed: 0,
    blocking: 0,
    overdue: 0,
  })

  // Load issues from API
  const loadIssues = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Build query parameters
      const params = {
        page: 1,
        page_size: 100,
      }

      // Apply filters
      if (filterStatus !== 'all') {
        params.status = filterStatus
      }
      if (filterSeverity !== 'all') {
        params.severity = filterSeverity
      }
      if (filterCategory !== 'all') {
        params.category = filterCategory
      }
      if (searchKeyword) {
        params.keyword = searchKeyword
      }

      const response = await issueApi.list(params)
      // Handle PaginatedResponse format
      const data = response.data?.data || response.data || response
      if (data && typeof data === 'object' && 'items' in data) {
        setIssues(data.items || [])
      } else if (Array.isArray(data)) {
        setIssues(data)
      } else {
        setIssues([])
      }
    } catch (err) {
      console.error('Failed to load issues:', err)
      // 更详细的错误信息
      let errorMessage = '加载问题列表失败'
      if (err.response) {
        errorMessage = err.response.data?.detail || err.response.data?.message || errorMessage
      } else if (err.request) {
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      } else {
        errorMessage = err.message || errorMessage
      }
      setError(errorMessage)
      setIssues([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterSeverity, filterCategory, searchKeyword])

  // Load statistics
  const loadStatistics = useCallback(async () => {
    try {
      const response = await issueApi.getStatistics({})
      // Handle response format
      const data = response.data?.data || response.data || response
      const stats = data || {}
      setStatistics({
        total: stats.total || 0,
        open: stats.open || 0,
        processing: stats.processing || 0,
        resolved: stats.resolved || 0,
        closed: stats.closed || 0,
        blocking: stats.blocking || 0,
        overdue: stats.overdue || 0,
      })
    } catch (err) {
      console.error('Failed to load statistics:', err)
      // Calculate from local issues as fallback
      setStatistics({
        total: issues.length,
        open: issues.filter((i) => i.status === 'OPEN').length,
        processing: issues.filter((i) => i.status === 'PROCESSING').length,
        resolved: issues.filter((i) => i.status === 'RESOLVED').length,
        closed: issues.filter((i) => i.status === 'CLOSED').length,
        blocking: issues.filter((i) => i.is_blocking).length,
        overdue: issues.filter(
          (i) =>
            i.due_date &&
            new Date(i.due_date) < new Date() &&
            ['OPEN', 'PROCESSING'].includes(i.status)
        ).length,
      })
    }
  }, [issues])

  // Load issues when component mounts or filters change
  useEffect(() => {
    loadIssues()
  }, [loadIssues])

  // Load statistics when issues change
  useEffect(() => {
    if (issues.length > 0) {
      loadStatistics()
    }
  }, [issues, loadStatistics])

  // Client-side filtering (for additional filtering beyond API)
  useEffect(() => {
    let filtered = issues

    // Additional client-side search (if API doesn't support it)
    if (searchKeyword && !params?.keyword) {
      filtered = filtered.filter(
        (issue) =>
          issue.title?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
          issue.issue_no?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
          issue.description?.toLowerCase().includes(searchKeyword.toLowerCase())
      )
    }

    setFilteredIssues(filtered)
  }, [issues, searchKeyword])

  const handleCreateIssue = async (issueData) => {
    try {
      const response = await issueApi.create(issueData)
      const newIssue = response.data || response
      
      // Refresh issues list
      await loadIssues()
      setShowCreate(false)
    } catch (err) {
      console.error('Failed to create issue:', err)
      alert('创建问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleUpdateIssue = async (issueId, updateData) => {
    try {
      await issueApi.update(issueId, updateData)
      await loadIssues()
      setShowDetail(false)
      setSelectedIssue(null)
    } catch (err) {
      console.error('Failed to update issue:', err)
      alert('更新问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleAssignIssue = async (issueId, assigneeId) => {
    try {
      await issueApi.assign(issueId, { assignee_id: assigneeId })
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
    } catch (err) {
      console.error('Failed to assign issue:', err)
      alert('分配问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleResolveIssue = async (issueId, solution) => {
    try {
      await issueApi.resolve(issueId, { solution })
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
    } catch (err) {
      console.error('Failed to resolve issue:', err)
      alert('解决问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleStatusChange = async (issueId, newStatus) => {
    try {
      await issueApi.changeStatus(issueId, { status: newStatus })
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
    } catch (err) {
      console.error('Failed to change issue status:', err)
      alert('更新问题状态失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleCloseIssue = async (issueId, data = {}) => {
    try {
      await issueApi.close(issueId, data)
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
      alert('问题已关闭')
    } catch (err) {
      console.error('Failed to close issue:', err)
      alert('关闭问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleCancelIssue = async (issueId, data = {}) => {
    try {
      await issueApi.cancel(issueId, data)
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
      alert('问题已取消')
    } catch (err) {
      console.error('Failed to cancel issue:', err)
      alert('取消问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeleteIssue = async (issueId) => {
    if (!confirm('确定要删除此问题吗？删除后无法恢复。')) {
      return
    }
    try {
      await issueApi.delete(issueId)
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        setShowDetail(false)
        setSelectedIssue(null)
      }
      alert('问题已删除')
    } catch (err) {
      console.error('Failed to delete issue:', err)
      alert('删除问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleVerifyIssue = async (issueId, verifiedResult) => {
    try {
      await issueApi.verify(issueId, { verified_result: verifiedResult })
      await loadIssues()
      if (selectedIssue?.id === issueId) {
        const updated = await issueApi.get(issueId)
        setSelectedIssue(updated.data || updated)
      }
      alert('问题验证完成')
    } catch (err) {
      console.error('Failed to verify issue:', err)
      alert('验证问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleBatchAssign = async (issueIds, assigneeId, dueDate) => {
    try {
      await issueApi.batchAssign({ issue_ids: issueIds, assignee_id: assigneeId, due_date: dueDate })
      await loadIssues()
      alert(`成功批量分配 ${issueIds.length} 个问题`)
    } catch (err) {
      console.error('Failed to batch assign:', err)
      alert('批量分配失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleBatchStatus = async (issueIds, newStatus) => {
    try {
      await issueApi.batchStatus({ issue_ids: issueIds, new_status: newStatus })
      await loadIssues()
      alert(`成功批量变更 ${issueIds.length} 个问题状态`)
    } catch (err) {
      console.error('Failed to batch change status:', err)
      alert('批量状态变更失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleBatchClose = async (issueIds) => {
    try {
      await issueApi.batchClose({ issue_ids: issueIds })
      await loadIssues()
      alert(`成功批量关闭 ${issueIds.length} 个问题`)
    } catch (err) {
      console.error('Failed to batch close:', err)
      alert('批量关闭失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleExport = async () => {
    try {
      const params = {}
      if (filterStatus !== 'all') params.status = filterStatus
      if (filterSeverity !== 'all') params.severity = filterSeverity
      if (filterCategory !== 'all') params.category = filterCategory
      if (searchKeyword) params.keyword = searchKeyword

      const response = await issueApi.export(params)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `问题列表_${new Date().toISOString().split('T')[0]}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      alert('导出成功')
    } catch (err) {
      console.error('Failed to export:', err)
      alert('导出失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleImport = async (file) => {
    try {
      await issueApi.import(file)
      await loadIssues()
      alert('导入成功')
    } catch (err) {
      console.error('Failed to import:', err)
      alert('导入失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  // Calculate statistics from current issues as fallback
  // (statistics state is loaded from API, but we calculate from local issues as backup)
  const calculatedStats = {
    total: issues.length,
    open: issues.filter((i) => i.status === 'OPEN').length,
    processing: issues.filter((i) => i.status === 'PROCESSING').length,
    resolved: issues.filter((i) => i.status === 'RESOLVED').length,
    closed: issues.filter((i) => i.status === 'CLOSED').length,
    blocking: issues.filter((i) => i.is_blocking).length,
    overdue: issues.filter(
      (i) =>
        i.due_date &&
        new Date(i.due_date) < new Date() &&
        ['OPEN', 'PROCESSING'].includes(i.status)
    ).length,
  }
  
  // Use state statistics if available, otherwise use calculated
  const displayStats = statistics.total > 0 ? statistics : calculatedStats

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题管理中心"
        description="统一管理项目问题、任务问题、验收问题等"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4"
        >
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">总问题数</div>
              <div className="text-2xl font-bold text-white">{displayStats.total}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">待处理</div>
              <div className="text-2xl font-bold text-blue-400">{displayStats.open}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">处理中</div>
              <div className="text-2xl font-bold text-yellow-400">{displayStats.processing}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已解决</div>
              <div className="text-2xl font-bold text-green-400">{displayStats.resolved}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已关闭</div>
              <div className="text-2xl font-bold text-gray-400">{displayStats.closed}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">阻塞问题</div>
              <div className="text-2xl font-bold text-red-400">{displayStats.blocking}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已逾期</div>
              <div className="text-2xl font-bold text-red-400">{displayStats.overdue}</div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 搜索和筛选 */}
        <Card className="bg-surface-50 border-white/5">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  placeholder="搜索问题编号、标题、描述..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-surface-100 border-white/10 text-white"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部状态</option>
                  <option value="OPEN">待处理</option>
                  <option value="PROCESSING">处理中</option>
                  <option value="RESOLVED">已解决</option>
                  <option value="CLOSED">已关闭</option>
                </select>
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部严重程度</option>
                  <option value="CRITICAL">严重</option>
                  <option value="MAJOR">主要</option>
                  <option value="MINOR">次要</option>
                </select>
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
                >
                  <option value="all">全部分类</option>
                  <option value="PROJECT">项目问题</option>
                  <option value="TASK">任务问题</option>
                  <option value="ACCEPTANCE">验收问题</option>
                  <option value="QUALITY">质量问题</option>
                  <option value="TECHNICAL">技术问题</option>
                </select>
                <Button
                  onClick={() => setShowCreate(true)}
                  className="bg-primary hover:bg-primary/90"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  新建问题
                </Button>
                <Button
                  onClick={handleExport}
                  variant="outline"
                  className="border-white/10"
                >
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
                <label className="cursor-pointer">
                  <Button
                    variant="outline"
                    className="border-white/10"
                    as="span"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    导入
                  </Button>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleImport(file)
                    }}
                  />
                </label>
                <div className="flex gap-1 border border-white/10 rounded-lg p-1">
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                    className={viewMode === 'list' ? 'bg-primary' : ''}
                  >
                    <List className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'board' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('board')}
                    className={viewMode === 'board' ? 'bg-primary' : ''}
                  >
                    <Kanban className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={viewMode === 'statistics' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('statistics')}
                    className={viewMode === 'statistics' ? 'bg-primary' : ''}
                  >
                    <BarChart3 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 加载状态 */}
        {loading && (
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-8 text-center">
              <div className="text-slate-400">加载中...</div>
            </CardContent>
          </Card>
        )}

        {/* 错误状态 */}
        {error && !loading && (
          <Card className="bg-red-500/10 border-red-500/30">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="font-semibold text-red-400 mb-1">加载失败</div>
                  <div className="text-sm text-red-300 mb-3">{error}</div>
                  <Button
                    onClick={() => {
                      setError(null)
                      loadIssues()
                    }}
                    variant="outline"
                    size="sm"
                    className="border-red-500/30 text-red-400 hover:bg-red-500/20"
                  >
                    重试
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 批量操作栏 */}
        {selectedIssues.length > 0 && (
          <Card className="bg-primary/10 border-primary/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="text-white">
                  已选择 <span className="font-bold">{selectedIssues.length}</span> 个问题
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const assigneeId = prompt('请输入处理人ID:')
                      if (assigneeId) {
                        handleBatchAssign(selectedIssues, parseInt(assigneeId))
                        setSelectedIssues([])
                      }
                    }}
                  >
                    <User className="w-4 h-4 mr-1" />
                    批量分配
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newStatus = prompt('请输入新状态 (OPEN/PROCESSING/RESOLVED/CLOSED):')
                      if (newStatus) {
                        handleBatchStatus(selectedIssues, newStatus)
                        setSelectedIssues([])
                      }
                    }}
                  >
                    <Edit3 className="w-4 h-4 mr-1" />
                    批量状态
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (confirm('确定要批量关闭选中的问题吗？')) {
                        handleBatchClose(selectedIssues)
                        setSelectedIssues([])
                      }
                    }}
                  >
                    <XCircle className="w-4 h-4 mr-1" />
                    批量关闭
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedIssues([])}
                  >
                    取消选择
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 问题列表/看板/统计视图 */}
        {!loading && !error && viewMode === 'list' && (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-3"
          >
            {filteredIssues.length === 0 ? (
              <Card className="bg-surface-50 border-white/5">
                <CardContent className="p-8 text-center">
                  <div className="text-slate-400">暂无问题</div>
                </CardContent>
              </Card>
            ) : (
              filteredIssues.map((issue) => {
                const StatusIcon = statusIcons[issue.status] || AlertCircle
                const isOverdue =
                  issue.due_date &&
                  new Date(issue.due_date) < new Date() &&
                  ['OPEN', 'PROCESSING'].includes(issue.status)

                return (
              <motion.div
                key={issue.id}
                variants={fadeIn}
                onClick={() => {
                  setSelectedIssue(issue)
                  setShowDetail(true)
                }}
                className="cursor-pointer"
              >
                <Card className="bg-surface-50 border-white/5 hover:border-primary/50 transition-all">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="font-mono text-sm text-slate-400">{issue.issue_no}</span>
                          <Badge className={cn('border', severityColors[issue.severity])}>
                            {issue.severity}
                          </Badge>
                          <Badge className={cn(priorityColors[issue.priority])}>
                            {issue.priority}
                          </Badge>
                          <Badge className={cn(statusColors[issue.status])}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {issue.status}
                          </Badge>
                          {issue.is_blocking && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                              阻塞
                            </Badge>
                          )}
                          {isOverdue && (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                              逾期
                            </Badge>
                          )}
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-2">{issue.title}</h3>
                        <p className="text-sm text-slate-400 mb-3 line-clamp-2">
                          {issue.description}
                        </p>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <span className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            {issue.reporter_name}
                          </span>
                          {issue.assignee_name && (
                            <span className="flex items-center gap-1">
                              <User className="w-4 h-4" />
                              负责人: {issue.assignee_name}
                            </span>
                          )}
                          {issue.due_date && (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              {issue.due_date}
                            </span>
                          )}
                          {issue.project_name && (
                            <span className="text-primary">{issue.project_name}</span>
                          )}
                        </div>
                        {issue.tags && issue.tags.length > 0 && (
                          <div className="flex items-center gap-2 mt-2">
                            {issue.tags.map((tag, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs text-slate-400 border-slate-600"
                              >
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedIssue(issue)
                          setShowDetail(true)
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
                )
              })
            )}
          </motion.div>
        )}

        {filteredIssues.length === 0 && viewMode === 'list' && (
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-12 text-center">
              <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">暂无问题数据</p>
            </CardContent>
          </Card>
        )}

        {/* 看板视图 */}
        {!loading && !error && viewMode === 'board' && (
          <IssueBoardView 
            issues={filteredIssues} 
            onIssueClick={(issue) => {
              setSelectedIssue(issue)
              setShowDetail(true)
            }}
            onStatusChange={handleStatusChange}
            onRefresh={loadIssues}
          />
        )}

        {/* 统计视图 */}
        {!loading && !error && viewMode === 'statistics' && (
          <IssueStatisticsView />
        )}
      </div>

      {/* 问题详情对话框 */}
      <AnimatePresence>
        {showDetail && selectedIssue && (
          <IssueDetailDialog
            issue={selectedIssue}
            onClose={() => {
              setShowDetail(false)
              setSelectedIssue(null)
            }}
            onAssign={handleAssignIssue}
            onResolve={handleResolveIssue}
            onVerify={handleVerifyIssue}
            onCloseIssue={handleCloseIssue}
            onCancel={handleCancelIssue}
            onDelete={handleDeleteIssue}
            onStatusChange={handleStatusChange}
            onRefresh={loadIssues}
          />
        )}
      </AnimatePresence>

      {/* 创建问题对话框 */}
      <AnimatePresence>
        {showCreate && (
          <CreateIssueDialog
            onClose={() => setShowCreate(false)}
            onSubmit={handleCreateIssue}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// 问题详情对话框组件
function IssueDetailDialog({ 
  issue, 
  onClose, 
  onAssign,
  onResolve,
  onVerify,
  onCloseIssue,
  onCancel,
  onDelete,
  onStatusChange,
  onRefresh,
}) {
  const [showFollowUps, setShowFollowUps] = useState(false)
  const [showRelated, setShowRelated] = useState(false)
  const [followUps, setFollowUps] = useState([])
  const [relatedIssues, setRelatedIssues] = useState([])
  const [loadingFollowUps, setLoadingFollowUps] = useState(false)
  const [loadingRelated, setLoadingRelated] = useState(false)
  const [showAssignDialog, setShowAssignDialog] = useState(false)
  const [showResolveDialog, setShowResolveDialog] = useState(false)
  const [showVerifyDialog, setShowVerifyDialog] = useState(false)
  const [assigneeId, setAssigneeId] = useState(issue.assignee_id || '')
  const [solution, setSolution] = useState(issue.solution || '')
  const [verifiedResult, setVerifiedResult] = useState('VERIFIED')

  const loadFollowUps = async () => {
    try {
      setLoadingFollowUps(true)
      const response = await issueApi.getFollowUps(issue.id)
      const data = response.data?.data || response.data || response
      setFollowUps(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load follow-ups:', err)
      setFollowUps([])
    } finally {
      setLoadingFollowUps(false)
    }
  }

  const loadRelated = async () => {
    try {
      setLoadingRelated(true)
      const response = await issueApi.getRelated(issue.id)
      const data = response.data?.data || response.data || response
      setRelatedIssues(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Failed to load related issues:', err)
      setRelatedIssues([])
    } finally {
      setLoadingRelated(false)
    }
  }

  useEffect(() => {
    if (showFollowUps) {
      loadFollowUps()
    }
  }, [showFollowUps, issue.id])

  useEffect(() => {
    if (showRelated) {
      loadRelated()
    }
  }, [showRelated, issue.id])

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-surface-50 border-white/10 text-white max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-primary" />
            {issue.title}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-slate-400 mb-1">问题编号</div>
              <div className="font-mono text-white">{issue.issue_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">状态</div>
              <Badge className={cn(statusColors[issue.status])}>{issue.status}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">严重程度</div>
              <Badge className={cn(severityColors[issue.severity])}>{issue.severity}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">优先级</div>
              <Badge className={cn(priorityColors[issue.priority])}>{issue.priority}</Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">提出人</div>
              <div className="text-white">{issue.reporter_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">负责人</div>
              <div className="text-white">{issue.assignee_name || '未分配'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">要求完成日期</div>
              <div className="text-white">{issue.due_date || '未设置'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">提出时间</div>
              <div className="text-white">{issue.report_date}</div>
            </div>
          </div>

          {/* 问题描述 */}
          <div>
            <div className="text-sm text-slate-400 mb-2">问题描述</div>
            <div className="text-white bg-surface-100 p-3 rounded-lg">{issue.description}</div>
          </div>

          {/* 解决方案 */}
          {issue.solution && (
            <div>
              <div className="text-sm text-slate-400 mb-2">解决方案</div>
              <div className="text-white bg-surface-100 p-3 rounded-lg">{issue.solution}</div>
            </div>
          )}

          {/* 影响评估 */}
          {issue.impact_scope && (
            <div>
              <div className="text-sm text-slate-400 mb-2">影响范围</div>
              <div className="text-white">{issue.impact_scope}</div>
            </div>
          )}

          {/* 标签 */}
          {issue.tags && issue.tags.length > 0 && (
            <div>
              <div className="text-sm text-slate-400 mb-2">标签</div>
              <div className="flex items-center gap-2">
                {issue.tags.map((tag, idx) => (
                  <Badge
                    key={idx}
                    variant="outline"
                    className="text-slate-400 border-slate-600"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// 创建问题对话框组件
function CreateIssueDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    category: 'PROJECT',
    issue_type: 'DEFECT',
    severity: 'MAJOR',
    priority: 'MEDIUM',
    title: '',
    description: '',
    assignee_id: null,
    due_date: '',
    impact_scope: '',
    impact_level: 'MEDIUM',
    is_blocking: false,
    tags: [],
  })
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [showTemplateSelector, setShowTemplateSelector] = useState(false)
  const [loadingTemplates, setLoadingTemplates] = useState(false)

  // Load templates
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        setLoadingTemplates(true)
        const response = await issueTemplateApi.list({ page_size: 100 })
        const templatesData = response.data?.items || response.data || []
        setTemplates(templatesData)
      } catch (err) {
        console.error('Failed to load templates:', err)
      } finally {
        setLoadingTemplates(false)
      }
    }
    loadTemplates()
  }, [])

  // Apply template
  const handleSelectTemplate = (template) => {
    if (template) {
      setFormData({
        ...formData,
        category: template.category || formData.category,
        issue_type: template.issue_type || formData.issue_type,
        severity: template.severity || formData.severity,
        priority: template.priority || formData.priority,
        title: template.title || formData.title,
        description: template.description || formData.description,
        impact_scope: template.impact_scope || formData.impact_scope,
        impact_level: template.impact_level || formData.impact_level,
        is_blocking: template.is_blocking ?? formData.is_blocking,
        tags: template.tags || formData.tags,
      })
      setSelectedTemplate(template)
      setShowTemplateSelector(false)
    }
  }

  // Create from template
  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate) {
      alert('请先选择模板')
      return
    }
    try {
      const templateData = {
        project_id: formData.project_id,
        machine_id: formData.machine_id,
        task_id: formData.task_id,
        acceptance_order_id: formData.acceptance_order_id,
        assignee_id: formData.assignee_id,
        due_date: formData.due_date,
      }
      const response = await issueTemplateApi.createIssue(selectedTemplate.id, templateData)
      const newIssue = response.data || response
      onSubmit(newIssue)
    } catch (err) {
      console.error('Failed to create issue from template:', err)
      alert('从模板创建问题失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleSubmit = () => {
    if (!formData.title || !formData.description) {
      alert('请填写问题标题和描述')
      return
    }
    onSubmit(formData)
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-surface-50 border-white/10 text-white">
        <DialogHeader>
          <DialogTitle>新建问题</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题分类</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="PROJECT">项目问题</option>
                <option value="TASK">任务问题</option>
                <option value="ACCEPTANCE">验收问题</option>
                <option value="QUALITY">质量问题</option>
                <option value="TECHNICAL">技术问题</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题类型</label>
              <select
                value={formData.issue_type}
                onChange={(e) => setFormData({ ...formData, issue_type: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="DEFECT">缺陷</option>
                <option value="DEVIATION">偏差</option>
                <option value="RISK">风险</option>
                <option value="BLOCKER">阻塞</option>
                <option value="SUGGESTION">建议</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">严重程度</label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="CRITICAL">严重</option>
                <option value="MAJOR">主要</option>
                <option value="MINOR">次要</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">优先级</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="URGENT">紧急</option>
                <option value="HIGH">高</option>
                <option value="MEDIUM">中</option>
                <option value="LOW">低</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">问题标题 *</label>
            <Input
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="请输入问题标题"
              className="bg-surface-100 border-white/10 text-white"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">问题描述 *</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="请详细描述问题情况"
              rows={4}
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">要求完成日期</label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                checked={formData.is_blocking}
                onChange={(e) => setFormData({ ...formData, is_blocking: e.target.checked })}
                className="w-4 h-4"
              />
              <label className="text-sm text-slate-400">是否阻塞项目/任务</label>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          {selectedTemplate ? (
            <Button onClick={handleCreateFromTemplate} className="bg-primary hover:bg-primary/90">
              从模板创建
            </Button>
          ) : (
            <Button onClick={handleSubmit} className="bg-primary hover:bg-primary/90">
              创建问题
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// 看板视图组件（支持拖拽）
function IssueBoardView({ issues, onIssueClick, onStatusChange, onRefresh }) {
  const [activeId, setActiveId] = useState(null)
  const [localIssues, setLocalIssues] = useState(issues)
  
  // 同步外部issues变化
  useEffect(() => {
    setLocalIssues(issues)
  }, [issues])

  const columns = [
    { key: 'OPEN', label: '待处理', color: 'bg-blue-500/20 border-blue-500/30' },
    { key: 'PROCESSING', label: '处理中', color: 'bg-yellow-500/20 border-yellow-500/30' },
    { key: 'RESOLVED', label: '已解决', color: 'bg-green-500/20 border-green-500/30' },
    { key: 'VERIFIED', label: '待验证', color: 'bg-purple-500/20 border-purple-500/30' },
    { key: 'CLOSED', label: '已关闭', color: 'bg-gray-500/20 border-gray-500/30' },
    { key: 'CANCELLED', label: '已取消', color: 'bg-red-500/20 border-red-500/30' },
  ]

  const getIssuesByStatus = (status) => {
    return localIssues.filter(issue => issue.status === status)
  }

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  const handleDragStart = (event) => {
    setActiveId(event.active.id)
  }

  const handleDragEnd = async (event) => {
    const { active, over } = event
    setActiveId(null)

    if (!over) return

    const issueId = parseInt(active.id.toString().replace('issue-', ''))
    const newStatus = over.id.toString().replace('column-', '')

    // 找到问题
    const issue = localIssues.find(i => i.id === issueId)
    if (!issue || issue.status === newStatus) return

    // 乐观更新UI
    setLocalIssues(prev => 
      prev.map(i => 
        i.id === issueId ? { ...i, status: newStatus } : i
      )
    )

    // 调用API更新状态
    try {
      await onStatusChange(issueId, newStatus)
      // 刷新数据
      if (onRefresh) {
        await onRefresh()
      }
    } catch (error) {
      console.error('Failed to update issue status:', error)
      // 恢复原状态
      setLocalIssues(issues)
      alert('更新问题状态失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const draggedIssue = activeId ? localIssues.find(i => `issue-${i.id}` === activeId) : null

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {columns.map((column) => {
          const columnIssues = getIssuesByStatus(column.key)
          return (
            <DroppableColumn
              key={column.key}
              column={column}
              issues={columnIssues}
              onIssueClick={onIssueClick}
              activeId={activeId}
            />
          )
        })}
      </div>
      <DragOverlay>
        {draggedIssue ? (
          <Card className="bg-surface-50/90 border-primary/50 shadow-xl w-64">
            <CardContent className="p-3">
              <div className="text-sm font-medium text-white mb-1 line-clamp-2">
                {draggedIssue.title}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge className={cn('text-xs', severityColors[draggedIssue.severity])}>
                  {draggedIssue.severity}
                </Badge>
                <Badge className={cn('text-xs', priorityColors[draggedIssue.priority])}>
                  {draggedIssue.priority}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}

// 可拖拽的列组件
function DroppableColumn({ column, issues, onIssueClick, activeId }) {
  const { setNodeRef } = useDroppable({
    id: `column-${column.key}`,
  })

  return (
    <Card ref={setNodeRef} className={`${column.color} border`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
          <span>{column.label}</span>
          <Badge variant="outline" className="text-xs">
            {issues.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 max-h-[70vh] overflow-y-auto">
        {issues.length === 0 ? (
          <div className="text-slate-400 text-sm text-center py-4">暂无问题</div>
        ) : (
          issues.map((issue) => (
            <DraggableIssueCard
              key={issue.id}
              issue={issue}
              onIssueClick={onIssueClick}
              isActive={activeId === `issue-${issue.id}`}
            />
          ))
        )}
      </CardContent>
    </Card>
  )
}

// 可拖拽的问题卡片组件
function DraggableIssueCard({ issue, onIssueClick, isActive }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useDraggable({
    id: `issue-${issue.id}`,
  })

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <Card
        className={cn(
          "bg-surface-50/50 border-white/10 cursor-grab active:cursor-grabbing transition-all",
          isActive && "ring-2 ring-primary/50",
          isDragging && "shadow-lg scale-105"
        )}
        onClick={() => onIssueClick(issue)}
      >
        <CardContent className="p-3">
          <div className="text-sm font-medium text-white mb-1 line-clamp-2">
            {issue.title}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge className={cn('text-xs', severityColors[issue.severity])}>
              {issue.severity}
            </Badge>
            <Badge className={cn('text-xs', priorityColors[issue.priority])}>
              {issue.priority}
            </Badge>
            {issue.is_blocking && (
              <Badge className="text-xs bg-red-500/20 text-red-400">
                阻塞
              </Badge>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            {issue.assignee_name || '未分配'}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 统计视图组件
function IssueStatisticsView() {
  const [trendData, setTrendData] = useState([])
  const [causeData, setCauseData] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [engineerStats, setEngineerStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [groupBy, setGroupBy] = useState('day')
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])

  useEffect(() => {
    loadAllData()
  }, [groupBy, startDate, endDate])

  const loadAllData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        loadTrendData(),
        loadCauseAnalysis(),
        loadStatistics(),
        loadEngineerStatistics(),
      ])
    } finally {
      setLoading(false)
    }
  }

  const loadTrendData = async () => {
    try {
      const response = await issueApi.getTrend({
        group_by: groupBy,
        start_date: startDate,
        end_date: endDate,
      })
      setTrendData(response.data?.trend || response.trend || [])
    } catch (err) {
      console.error('Failed to load trend data:', err)
    }
  }

  const loadCauseAnalysis = async () => {
    try {
      const response = await issueApi.getCauseAnalysis({
        start_date: startDate,
        end_date: endDate,
        top_n: 10,
      })
      setCauseData(response.data || response)
    } catch (err) {
      console.error('Failed to load cause analysis:', err)
    }
  }

  const loadStatistics = async () => {
    try {
      const response = await issueApi.getStatistics({})
      setStatistics(response.data?.data || response.data || response)
    } catch (err) {
      console.error('Failed to load statistics:', err)
    }
  }

  const loadEngineerStatistics = async () => {
    try {
      const response = await issueApi.getEngineerStatistics({
        start_date: startDate,
        end_date: endDate,
      })
      setEngineerStats(response.data?.engineers || response.engineers || [])
    } catch (err) {
      console.error('Failed to load engineer statistics:', err)
    }
  }

  return (
    <div className="space-y-6">
      {/* 时间范围选择 */}
      <Card className="bg-surface-50 border-white/5">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">开始日期</label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">结束日期</label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">分组方式</label>
              <select
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
                className="px-4 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="day">按日</option>
                <option value="week">按周</option>
                <option value="month">按月</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 总体统计卡片 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">总问题数</div>
              <div className="text-2xl font-bold text-white">{statistics.total || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">待处理</div>
              <div className="text-2xl font-bold text-blue-400">{statistics.open || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">处理中</div>
              <div className="text-2xl font-bold text-yellow-400">{statistics.processing || 0}</div>
            </CardContent>
          </Card>
          <Card className="bg-surface-50 border-white/5">
            <CardContent className="p-4">
              <div className="text-sm text-slate-400 mb-1">已解决</div>
              <div className="text-2xl font-bold text-green-400">{statistics.resolved || 0}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 状态分布饼图 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-surface-50 border-white/5">
            <CardHeader>
              <CardTitle>问题状态分布</CardTitle>
            </CardHeader>
            <CardContent>
              <SimplePieChart
                data={[
                  { label: '待处理', value: statistics.open || 0, color: '#3b82f6' },
                  { label: '处理中', value: statistics.processing || 0, color: '#eab308' },
                  { label: '已解决', value: statistics.resolved || 0, color: '#22c55e' },
                  { label: '已关闭', value: statistics.closed || 0, color: '#6b7280' },
                  { label: '已取消', value: statistics.cancelled || 0, color: '#ef4444' },
                ].filter(item => item.value > 0)}
                size={250}
              />
            </CardContent>
          </Card>

          {/* 严重程度分布 */}
          <Card className="bg-surface-50 border-white/5">
            <CardHeader>
              <CardTitle>严重程度分布</CardTitle>
            </CardHeader>
            <CardContent>
              <SimplePieChart
                data={[
                  { label: '严重', value: statistics.critical || 0, color: '#ef4444' },
                  { label: '重要', value: statistics.major || 0, color: '#f59e0b' },
                  { label: '一般', value: statistics.minor || 0, color: '#3b82f6' },
                ].filter(item => item.value > 0)}
                size={250}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* 趋势图表 */}
      <Card className="bg-surface-50 border-white/5">
        <CardHeader>
          <CardTitle>问题趋势分析</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-slate-400 text-center py-8">加载中...</div>
          ) : trendData.length === 0 ? (
            <div className="text-slate-400 text-center py-8">暂无数据</div>
          ) : (
            <div className="space-y-6">
              {/* 创建趋势 */}
              <div>
                <div className="text-sm text-slate-400 mb-2">创建数量趋势</div>
                <SimpleLineChart
                  data={trendData.map(item => ({
                    label: item.date,
                    value: item.created || 0,
                  }))}
                  height={200}
                  color="text-blue-400"
                />
              </div>
              {/* 解决趋势 */}
              <div>
                <div className="text-sm text-slate-400 mb-2">解决数量趋势</div>
                <SimpleLineChart
                  data={trendData.map(item => ({
                    label: item.date,
                    value: item.resolved || 0,
                  }))}
                  height={200}
                  color="text-green-400"
                />
              </div>
              {/* 对比柱状图 */}
              <div>
                <div className="text-sm text-slate-400 mb-2">创建 vs 解决对比</div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-blue-400 mb-1">创建</div>
                    <SimpleBarChart
                      data={trendData.map(item => ({
                        label: item.date,
                        value: item.created || 0,
                      }))}
                      height={150}
                      color="bg-blue-500"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-green-400 mb-1">解决</div>
                    <SimpleBarChart
                      data={trendData.map(item => ({
                        label: item.date,
                        value: item.resolved || 0,
                      }))}
                      height={150}
                      color="bg-green-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 工程师问题统计 */}
      {engineerStats.length > 0 && (
        <Card className="bg-surface-50 border-white/5">
          <CardHeader>
            <CardTitle>工程师问题统计</CardTitle>
          </CardHeader>
          <CardContent>
            <SimpleBarChart
              data={engineerStats.slice(0, 10).map(eng => ({
                label: eng.engineer_name || '未知',
                value: eng.total_issues || 0,
              }))}
              height={200}
              color="bg-purple-500"
            />
          </CardContent>
        </Card>
      )}

      {/* 原因分析 - 增强可视化 */}
      {causeData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="bg-surface-50 border-white/5">
            <CardHeader>
              <CardTitle>问题原因分布</CardTitle>
            </CardHeader>
            <CardContent>
              <SimplePieChart
                data={causeData.top_causes?.slice(0, 10).map((cause, idx) => ({
                  label: cause.cause || '未知',
                  value: cause.count || 0,
                  color: `hsl(${idx * 36}, 70%, 50%)`,
                })) || []}
                size={250}
              />
            </CardContent>
          </Card>

          <Card className="bg-surface-50 border-white/5">
            <CardHeader>
              <CardTitle>Top {causeData.top_causes?.length || 0} 问题原因</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {causeData.top_causes?.map((cause, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className="w-32 text-sm text-white truncate" title={cause.cause}>
                      {cause.cause || '未知'}
                    </div>
                    <div className="flex-1 bg-surface-100 rounded-full h-6 relative">
                      <div
                        className="bg-primary h-6 rounded-full flex items-center justify-end pr-2 transition-all"
                        style={{ width: `${cause.percentage}%` }}
                      >
                        <span className="text-xs text-white">{cause.percentage}%</span>
                      </div>
                    </div>
                    <div className="w-16 text-sm text-slate-400 text-right">{cause.count}个</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 原因趋势（如果有历史数据） */}
          {causeData.trend && causeData.trend.length > 0 && (
            <Card className="bg-surface-50 border-white/5 md:col-span-2">
              <CardHeader>
                <CardTitle>问题原因趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBarChart
                  data={causeData.trend.map((item, idx) => ({
                    label: item.date || `第${idx + 1}期`,
                    value: item.count || 0,
                  }))}
                  height={200}
                  color="bg-purple-500"
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

