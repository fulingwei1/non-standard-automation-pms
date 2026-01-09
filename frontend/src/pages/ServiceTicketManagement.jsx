/**
 * Service Ticket Management
 * 服务工单管理系统 - 客服工程师高级功能
 * 
 * 功能：
 * 1. 服务工单创建、编辑、查看
 * 2. 工单状态跟踪（待分配/处理中/待验证/已关闭）
 * 3. 工单转派和分配
 * 4. 工单搜索和筛选
 * 5. 工单统计分析
 * 6. 客户满意度记录
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Search, Filter, Eye, Edit, Send, CheckCircle2, Clock,
  AlertTriangle, User, Calendar, Phone, MapPin, Star, FileText,
  TrendingUp, Download, RefreshCw, XCircle, ChevronRight,
  ArrowUpDown, ArrowUp, ArrowDown,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card, CardContent, CardHeader, CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogBody
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi, userApi } from '../services/api'
import { formatDate } from '../lib/utils'

const statusConfig = {
  '待分配': { label: '待分配', color: 'bg-slate-500', textColor: 'text-slate-400' },
  '处理中': { label: '处理中', color: 'bg-blue-500', textColor: 'text-blue-400' },
  '待验证': { label: '待验证', color: 'bg-amber-500', textColor: 'text-amber-400' },
  '已关闭': { label: '已关闭', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
}

const urgencyConfig = {
  '紧急': { label: '紧急', color: 'text-red-400', bg: 'bg-red-500/20' },
  '普通': { label: '普通', color: 'text-slate-400', bg: 'bg-slate-500/20' },
}

const problemTypeConfig = {
  '软件问题': { label: '软件问题', icon: '💻' },
  '机械问题': { label: '机械问题', icon: '⚙️' },
  '电气问题': { label: '电气问题', icon: '⚡' },
  '操作问题': { label: '操作问题', icon: '👤' },
  '其他': { label: '其他', icon: '📋' },
}

export default function ServiceTicketManagement() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [urgencyFilter, setUrgencyFilter] = useState('ALL')
  const [sortBy, setSortBy] = useState('reported_time') // reported_time, status, urgency
  const [sortOrder, setSortOrder] = useState('desc') // asc, desc
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0,
  })
  const [dateRange, setDateRange] = useState({
    start: '',
    end: '',
  })
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showBatchAssignDialog, setShowBatchAssignDialog] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [selectedTickets, setSelectedTickets] = useState(new Set())
  const [exporting, setExporting] = useState(false)
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    inProgress: 0,
    pendingVerify: 0,
    closed: 0,
    urgent: 0,
  })

  useEffect(() => {
    loadTickets()
    loadStatistics()
  }, [])

  // 快捷键支持
  useEffect(() => {
    const handleKeyDown = (e) => {
      // ESC 关闭对话框
      if (e.key === 'Escape') {
        if (showCreateDialog) setShowCreateDialog(false)
        if (showDetailDialog) {
          setShowDetailDialog(false)
          setSelectedTicket(null)
        }
      }
      // Ctrl/Cmd + K 聚焦搜索框
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        // 搜索框会自动聚焦
      }
      // F5 刷新
      if (e.key === 'F5') {
        e.preventDefault()
        loadTickets()
        loadStatistics()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showCreateDialog, showDetailDialog, loadTickets, loadStatistics])

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      'PENDING': '待分配',
      'ASSIGNED': '处理中',
      'IN_PROGRESS': '处理中',
      'PENDING_VERIFY': '待验证',
      'CLOSED': '已关闭',
    }
    return statusMap[backendStatus] || backendStatus
  }

  // Map backend urgency to frontend urgency
  const mapBackendUrgency = (backendUrgency) => {
    const urgencyMap = {
      'URGENT': '紧急',
      'HIGH': '高',
      'MEDIUM': '中',
      'LOW': '低',
    }
    return urgencyMap[backendUrgency] || backendUrgency
  }

  const loadTickets = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
      }
      
      if (statusFilter !== 'ALL') {
        const statusMap = {
          '待分配': 'PENDING',
          '处理中': 'IN_PROGRESS',
          '待验证': 'PENDING_VERIFY',
          '已关闭': 'CLOSED',
        }
        params.status = statusMap[statusFilter] || statusFilter
      }
      
      if (urgencyFilter !== 'ALL') {
        const urgencyMap = {
          '紧急': 'URGENT',
          '高': 'HIGH',
          '中': 'MEDIUM',
          '低': 'LOW',
        }
        params.urgency = urgencyMap[urgencyFilter] || urgencyFilter
      }
      
      if (searchQuery) {
        params.keyword = searchQuery
      }
      
      if (dateRange.start) {
        params.date_from = dateRange.start
      }
      if (dateRange.end) {
        params.date_to = dateRange.end
      }
      
      const response = await serviceApi.tickets.list(params)
      const data = response.data || response
      
      // Handle PaginatedResponse format
      let ticketsData = []
      if (data && typeof data === 'object' && 'items' in data) {
        ticketsData = data.items || []
        setPagination(prev => ({
          ...prev,
          total: data.total || 0,
          pages: data.pages || 0,
          page: data.page || prev.page,
          page_size: data.page_size || prev.page_size,
        }))
      } else if (Array.isArray(data)) {
        ticketsData = data
        setPagination(prev => ({
          ...prev,
          total: data.length,
          pages: Math.ceil(data.length / prev.page_size),
        }))
      }
      
      // Transform backend data to frontend format
      const transformedTickets = ticketsData.map(ticket => ({
        id: ticket.id,
        ticket_no: ticket.ticket_no || '',
        project_code: ticket.project_code || '',
        project_name: ticket.project_name || '',
        machine_no: ticket.machine_no || '',
        customer_name: ticket.customer_name || '',
        problem_type: ticket.problem_type || '',
        problem_desc: ticket.problem_desc || ticket.description || '',
        urgency: mapBackendUrgency(ticket.urgency),
        reported_by: ticket.reported_by_name || ticket.reported_by || '',
        reported_phone: ticket.reported_phone || '',
        reported_time: ticket.reported_time || ticket.created_at || '',
        assigned_to: ticket.assigned_to,
        assigned_name: ticket.assigned_to_name || '',
        assigned_time: ticket.assigned_time || '',
        status: mapBackendStatus(ticket.status),
        response_time: ticket.response_time || '',
        resolved_time: ticket.resolved_time || '',
        solution: ticket.solution || '',
        satisfaction: ticket.satisfaction_score || null,
        timeline: ticket.timeline || null,
      }))
      
      setTickets(transformedTickets)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载服务工单失败')
      setTickets([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [statusFilter, urgencyFilter, searchQuery, pagination.page, pagination.page_size, dateRange])

  const loadStatistics = useCallback(async () => {
    try {
      const response = await serviceApi.tickets.getStatistics()
      const statsData = response.data || {}
      
      setStats({
        total: statsData.total || 0,
        pending: statsData.pending || 0,
        inProgress: statsData.in_progress || 0,
        pendingVerify: statsData.pending_verify || 0,
        closed: statsData.closed || 0,
        urgent: statsData.urgent || 0,
      })
    } catch (err) {
      // Calculate from local tickets as fallback
      setStats({
        total: tickets.length,
        pending: tickets.filter(t => t.status === '待分配').length,
        inProgress: tickets.filter(t => t.status === '处理中').length,
        pendingVerify: tickets.filter(t => t.status === '待验证').length,
        closed: tickets.filter(t => t.status === '已关闭').length,
        urgent: tickets.filter(t => t.urgency === '紧急').length,
      })
    }
  }, [tickets])

  // 由于后端已经处理了筛选和分页，前端只需要排序
  const sortedTickets = useMemo(() => {
    let result = [...tickets]

    // Sort
    result.sort((a, b) => {
      let aValue, bValue
      
      switch (sortBy) {
        case 'reported_time':
          aValue = new Date(a.reported_time || 0).getTime()
          bValue = new Date(b.reported_time || 0).getTime()
          break
        case 'status':
          const statusOrder = { '待分配': 1, '处理中': 2, '待验证': 3, '已关闭': 4 }
          aValue = statusOrder[a.status] || 0
          bValue = statusOrder[b.status] || 0
          break
        case 'urgency':
          const urgencyOrder = { '紧急': 1, '高': 2, '中': 3, '低': 4, '普通': 5 }
          aValue = urgencyOrder[a.urgency] || 0
          bValue = urgencyOrder[b.urgency] || 0
          break
        default:
          return 0
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
      }
    })

    return result
  }, [tickets, sortBy, sortOrder])

  // 处理选择
  const handleSelectTicket = (ticketId) => {
    setSelectedTickets(prev => {
      const newSet = new Set(prev)
      if (newSet.has(ticketId)) {
        newSet.delete(ticketId)
      } else {
        newSet.add(ticketId)
      }
      return newSet
    })
  }

  const handleSelectAll = () => {
    if (selectedTickets.size === sortedTickets.length) {
      setSelectedTickets(new Set())
    } else {
      setSelectedTickets(new Set(sortedTickets.map(t => t.id)))
    }
  }

  // 导出功能
  const handleExport = async (ticketIds = null) => {
    if (exporting) return
    
    try {
      setExporting(true)
      
      // 获取要导出的工单数据
      let ticketsToExport = []
      if (ticketIds && ticketIds.length > 0) {
        // 导出选中的工单
        ticketsToExport = sortedTickets.filter(t => ticketIds.includes(t.id))
      } else {
        // 导出当前筛选条件下的所有工单
        const params = {
          page: 1,
          page_size: 1000, // 导出时获取更多数据
        }
        
        if (statusFilter !== 'ALL') {
          const statusMap = {
            '待分配': 'PENDING',
            '处理中': 'IN_PROGRESS',
            '待验证': 'PENDING_VERIFY',
            '已关闭': 'CLOSED',
          }
          params.status = statusMap[statusFilter] || statusFilter
        }
        
        if (urgencyFilter !== 'ALL') {
          const urgencyMap = {
            '紧急': 'URGENT',
            '高': 'HIGH',
            '中': 'MEDIUM',
            '低': 'LOW',
          }
          params.urgency = urgencyMap[urgencyFilter] || urgencyFilter
        }
        
        if (searchQuery) {
          params.keyword = searchQuery
        }
        
        if (dateRange.start) {
          params.date_from = dateRange.start
        }
        if (dateRange.end) {
          params.date_to = dateRange.end
        }
        
        const response = await serviceApi.tickets.list(params)
        const data = response.data || response
        ticketsToExport = data.items || data || []
      }
      
      // 转换为 CSV 格式
      const headers = ['工单号', '项目编码', '项目名称', '机台号', '客户名称', '问题类型', '问题描述', 
                      '紧急程度', '报告人', '报告人电话', '报告时间', '负责人', '分配时间', 
                      '状态', '响应时间', '解决时间', '解决方案', '满意度', '客户反馈']
      
      const csvRows = [
        headers.join(','),
        ...ticketsToExport.map(ticket => [
          ticket.ticket_no || '',
          ticket.project_code || '',
          ticket.project_name || '',
          ticket.machine_no || '',
          ticket.customer_name || '',
          ticket.problem_type || '',
          `"${(ticket.problem_desc || '').replace(/"/g, '""')}"`,
          ticket.urgency || '',
          ticket.reported_by || '',
          ticket.reported_phone || '',
          ticket.reported_time ? formatDate(ticket.reported_time) : '',
          ticket.assigned_name || '',
          ticket.assigned_time ? formatDate(ticket.assigned_time) : '',
          ticket.status || '',
          ticket.response_time ? formatDate(ticket.response_time) : '',
          ticket.resolved_time ? formatDate(ticket.resolved_time) : '',
          `"${(ticket.solution || '').replace(/"/g, '""')}"`,
          ticket.satisfaction || '',
          `"${(ticket.feedback || '').replace(/"/g, '""')}"`,
        ].join(','))
      ]
      
      const csvContent = csvRows.join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `服务工单_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      
      toast.success(`成功导出 ${ticketsToExport.length} 条工单记录`)
    } catch (error) {
      toast.error('导出失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    } finally {
      setExporting(false)
    }
  }

  const handleViewDetail = (ticket) => {
    setSelectedTicket(ticket)
    setShowDetailDialog(true)
  }

  const handleCreateTicket = async (ticketData) => {
    if (submitting) return
    
    try {
      setSubmitting(true)
      await serviceApi.tickets.create(ticketData)
      toast.success('服务工单创建成功')
      setShowCreateDialog(false)
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleAssignTicket = async (ticketId, assignData) => {
    if (submitting) return
    
    try {
      setSubmitting(true)
      await serviceApi.tickets.assign(ticketId, assignData)
      toast.success('工单分配成功')
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      toast.error('分配失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleCloseTicket = async (ticketId, closeData) => {
    if (submitting) return
    
    // 验证必填字段
    if (!closeData.solution || !closeData.solution.trim()) {
      toast.warning('请填写解决方案')
      return
    }
    
    if (!closeData.satisfaction) {
      toast.warning('请选择客户满意度')
      return
    }
    
    try {
      setSubmitting(true)
      await serviceApi.tickets.close(ticketId, closeData)
      toast.success('工单已关闭')
      setShowDetailDialog(false)
      setSelectedTicket(null)
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      toast.error('关闭失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    } finally {
      setSubmitting(false)
    }
  }

  const handleBatchAssign = async (assignData) => {
    if (submitting) return
    
    if (selectedTickets.size === 0) {
      toast.warning('请选择要分配的工单')
      return
    }
    
    if (!assignData.assignee_id) {
      toast.warning('请选择负责人')
      return
    }
    
    try {
      setSubmitting(true)
      const ticketIds = Array.from(selectedTickets)
      
      // 尝试使用批量分配API，如果不存在则循环调用单个分配
      try {
        await serviceApi.tickets.batchAssign({
          ticket_ids: ticketIds,
          assignee_id: assignData.assignee_id,
          comment: assignData.comment || '',
        })
        toast.success(`成功分配 ${ticketIds.length} 个工单`)
      } catch (batchError) {
        // 如果批量API不存在，则循环调用单个分配
        if (batchError.response?.status === 404) {
          let successCount = 0
          let failCount = 0
          for (const ticketId of ticketIds) {
            try {
              await serviceApi.tickets.assign(ticketId, {
                assignee_id: assignData.assignee_id,
                comment: assignData.comment || '',
              })
              successCount++
            } catch (err) {
              failCount++
            }
          }
          if (failCount === 0) {
            toast.success(`成功分配 ${successCount} 个工单`)
          } else {
            toast.warn(`分配完成：成功 ${successCount} 个，失败 ${failCount} 个`)
          }
        } else {
          throw batchError
        }
      }
      
      setShowBatchAssignDialog(false)
      setSelectedTickets(new Set())
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      toast.error('批量分配失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="服务工单管理"
        description="管理客户服务工单，跟踪问题处理进度"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={async () => { 
                await loadTickets()
                await loadStatistics()
                toast.success('数据已刷新')
              }}
              disabled={loading}
              title="刷新数据 (F5)"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              刷新
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
              title="创建新的服务工单"
            >
              <Plus className="w-4 h-4" />
              创建工单
            </Button>
            {selectedTickets.size > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => handleExport(Array.from(selectedTickets))}
                disabled={exporting}
              >
                <Download className={cn("w-4 h-4", exporting && "animate-spin")} />
                {exporting ? '导出中...' : `导出选中 (${selectedTickets.size})`}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => handleExport()}
              disabled={exporting}
              title="导出当前筛选条件下的所有工单"
            >
              <Download className={cn("w-4 h-4", exporting && "animate-spin")} />
              {exporting ? '导出中...' : '导出全部'}
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-slate-800/30 border-slate-700 cursor-pointer hover:bg-slate-800/50 transition-colors"
              onClick={() => {
                setStatusFilter('ALL')
                setUrgencyFilter('ALL')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总工单数</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-slate-800/30 border-slate-700 cursor-pointer hover:bg-slate-800/50 transition-colors"
              onClick={() => {
                setStatusFilter('待分配')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待分配</div>
                <div className="text-2xl font-bold text-slate-400">{stats.pending}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-blue-500/10 border-blue-500/20 cursor-pointer hover:bg-blue-500/20 transition-colors"
              onClick={() => {
                setStatusFilter('处理中')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">处理中</div>
                <div className="text-2xl font-bold text-blue-400">{stats.inProgress}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-amber-500/10 border-amber-500/20 cursor-pointer hover:bg-amber-500/20 transition-colors"
              onClick={() => {
                setStatusFilter('待验证')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待验证</div>
                <div className="text-2xl font-bold text-amber-400">{stats.pendingVerify}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-emerald-500/10 border-emerald-500/20 cursor-pointer hover:bg-emerald-500/20 transition-colors"
              onClick={() => {
                setStatusFilter('已关闭')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已关闭</div>
                <div className="text-2xl font-bold text-emerald-400">{stats.closed}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card 
              className="bg-red-500/10 border-red-500/20 cursor-pointer hover:bg-red-500/20 transition-colors"
              onClick={() => {
                setUrgencyFilter('紧急')
                setPagination(prev => ({ ...prev, page: 1 }))
              }}
            >
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">紧急工单</div>
                <div className="text-2xl font-bold text-red-400">{stats.urgent}</div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索工单号、项目名称、客户名称... (Ctrl+K)"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                      onKeyDown={(e) => {
                        if (e.key === 'Escape') {
                          setSearchQuery('')
                        }
                      }}
                    />
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <select
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value)
                      setPagination(prev => ({ ...prev, page: 1 }))
                    }}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white min-w-[120px]"
                  >
                    <option value="ALL">全部状态</option>
                    <option value="待分配">待分配</option>
                    <option value="处理中">处理中</option>
                    <option value="待验证">待验证</option>
                    <option value="已关闭">已关闭</option>
                  </select>
                  <select
                    value={urgencyFilter}
                    onChange={(e) => {
                      setUrgencyFilter(e.target.value)
                      setPagination(prev => ({ ...prev, page: 1 }))
                    }}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white min-w-[120px]"
                  >
                    <option value="ALL">全部紧急度</option>
                    <option value="紧急">紧急</option>
                    <option value="普通">普通</option>
                  </select>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-32 bg-slate-800/50 border-slate-700">
                      <SelectValue placeholder="排序" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="reported_time">报告时间</SelectItem>
                      <SelectItem value="status">状态</SelectItem>
                      <SelectItem value="urgency">紧急度</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    title={sortOrder === 'asc' ? '升序' : '降序'}
                    className="bg-slate-800/50 border-slate-700"
                  >
                    {sortOrder === 'asc' ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                  </Button>
                      <div className="flex gap-2 items-center flex-wrap">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400" />
                      <Input
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => {
                          setDateRange(prev => ({ ...prev, start: e.target.value }))
                          setPagination(prev => ({ ...prev, page: 1 }))
                        }}
                        className="w-36 bg-slate-800/50 border-slate-700 text-sm"
                        placeholder="开始日期"
                        title="开始日期"
                      />
                    </div>
                    <span className="text-slate-400 hidden sm:inline">至</span>
                    <Input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => {
                        setDateRange(prev => ({ ...prev, end: e.target.value }))
                        setPagination(prev => ({ ...prev, page: 1 }))
                      }}
                      className="w-36 bg-slate-800/50 border-slate-700 text-sm"
                      placeholder="结束日期"
                      title="结束日期"
                    />
                  </div>
                  {(searchQuery || statusFilter !== 'ALL' || urgencyFilter !== 'ALL' || dateRange.start || dateRange.end) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setStatusFilter('ALL')
                        setUrgencyFilter('ALL')
                        setDateRange({ start: '', end: '' })
                        setPagination(prev => ({ ...prev, page: 1 }))
                      }}
                      className="gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      清除
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Ticket List */}
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
          {loading ? (
            <LoadingCard rows={5} />
          ) : error && tickets.length === 0 ? (
            <ErrorMessage error={error} onRetry={loadTickets} />
          ) : sortedTickets.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="暂无服务工单"
              description={
                searchQuery || statusFilter !== 'ALL' || urgencyFilter !== 'ALL' || dateRange.start || dateRange.end
                  ? "当前筛选条件下没有匹配的工单，请尝试调整筛选条件或清除筛选"
                  : "当前没有服务工单数据，点击右上角「创建工单」按钮创建新的服务工单"
              }
              action={
                (searchQuery || statusFilter !== 'ALL' || urgencyFilter !== 'ALL' || dateRange.start || dateRange.end) ? (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchQuery('')
                      setStatusFilter('ALL')
                      setUrgencyFilter('ALL')
                      setDateRange({ start: '', end: '' })
                      setPagination(prev => ({ ...prev, page: 1 }))
                    }}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    清除筛选
                  </Button>
                ) : (
                  <Button onClick={() => setShowCreateDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    创建工单
                  </Button>
                )
              }
            />
          ) : (
            <>
              {/* Select All */}
              {sortedTickets.length > 0 && (
                <Card className="bg-slate-800/30 border-slate-700">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedTickets.size === sortedTickets.length && sortedTickets.length > 0}
                        onChange={handleSelectAll}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
                      />
                      <span className="text-sm text-slate-400">
                        {selectedTickets.size === sortedTickets.length ? '取消全选' : '全选当前页'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}
              {selectedTickets.size > 0 && (
                <Card className="bg-blue-500/10 border-blue-500/20">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-blue-400">
                        已选择 {selectedTickets.size} 个工单
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedTickets(new Set())}
                        >
                          取消选择
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowBatchAssignDialog(true)}
                          disabled={submitting}
                        >
                          批量分配
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleExport(Array.from(selectedTickets))}
                          disabled={exporting}
                        >
                          <Download className={cn("w-4 h-4 mr-1", exporting && "animate-spin")} />
                          {exporting ? '导出中...' : '导出选中'}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              {sortedTickets.map((ticket) => {
                const status = statusConfig[ticket.status] || statusConfig['待分配']
                const urgency = urgencyConfig[ticket.urgency] || urgencyConfig['普通']
                const problemType = problemTypeConfig[ticket.problem_type] || problemTypeConfig['其他']

                return (
                  <motion.div key={ticket.id} variants={fadeIn}>
                    <Card className={cn(
                      "hover:bg-slate-800/50 transition-colors",
                      selectedTickets.has(ticket.id) && "ring-2 ring-blue-500"
                    )}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3 flex-1">
                            <input
                              type="checkbox"
                              checked={selectedTickets.has(ticket.id)}
                              onChange={() => handleSelectTicket(ticket.id)}
                              className="mt-1 w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500"
                            />
                            <div className="flex-1 space-y-3">
                          {/* Header */}
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm text-slate-300">{ticket.ticket_no}</span>
                            <Badge className={cn(status.color, 'text-xs')}>
                              {status.label}
                            </Badge>
                            <Badge className={cn(urgency.bg, urgency.textColor, 'text-xs')}>
                              {urgency.label}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {problemType.icon} {problemType.label}
                            </Badge>
                          </div>

                          {/* Content */}
                          <div>
                            <h3 className="text-white font-medium mb-1">{ticket.problem_desc}</h3>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {ticket.project_code} - {ticket.project_name}
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {ticket.customer_name}
                              </span>
                              <span className="flex items-center gap-1">
                                <Phone className="w-3 h-3" />
                                {ticket.reported_by} ({ticket.reported_phone})
                              </span>
                              {ticket.assigned_name && (
                                <span className="flex items-center gap-1">
                                  <User className="w-3 h-3" />
                                  负责人: {ticket.assigned_name}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Footer */}
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              报告时间: {ticket.reported_time ? formatDate(ticket.reported_time) : '-'}
                            </span>
                            {ticket.response_time && (
                              <span className="flex items-center gap-1 text-blue-400">
                                <CheckCircle2 className="w-3 h-3" />
                                响应: {formatDate(ticket.response_time)}
                              </span>
                            )}
                            {ticket.resolved_time && (
                              <span className="flex items-center gap-1 text-emerald-400">
                                <CheckCircle2 className="w-3 h-3" />
                                解决: {formatDate(ticket.resolved_time)}
                              </span>
                            )}
                            {ticket.satisfaction && (
                              <span className="flex items-center gap-1 text-yellow-400">
                                <Star className="w-3 h-3 fill-yellow-400" />
                                满意度: {ticket.satisfaction}/5
                              </span>
                            )}
                            </div>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(ticket)}
                            className="gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
                )
              })}
            </>
          )}
          
          {/* Pagination */}
          {!loading && pagination.total > pagination.page_size && (
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="flex items-center justify-between p-4">
                <div className="text-sm text-slate-400">
                  共 {pagination.total} 条记录，第 {pagination.page} / {pagination.pages} 页
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                    disabled={pagination.page === 1 || loading}
                    className="bg-slate-800/50 border-slate-700"
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPagination(prev => ({ ...prev, page: Math.min(prev.pages, prev.page + 1) }))}
                    disabled={pagination.page >= pagination.pages || loading}
                    className="bg-slate-800/50 border-slate-700"
                  >
                    下一页
                  </Button>
                  <Select
                    value={pagination.page_size.toString()}
                    onValueChange={(value) => {
                      setPagination(prev => ({
                        ...prev,
                        page_size: parseInt(value),
                        page: 1, // Reset to first page when changing page size
                      }))
                    }}
                  >
                    <SelectTrigger className="w-24 bg-slate-800/50 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10 条/页</SelectItem>
                      <SelectItem value="20">20 条/页</SelectItem>
                      <SelectItem value="50">50 条/页</SelectItem>
                      <SelectItem value="100">100 条/页</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>

      {/* Create Ticket Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <CreateTicketDialog
            onClose={() => setShowCreateDialog(false)}
            onSubmit={handleCreateTicket}
          />
        )}
      </AnimatePresence>

      {/* Detail Dialog */}
      <AnimatePresence>
        {showDetailDialog && selectedTicket && (
          <TicketDetailDialog
            ticket={selectedTicket}
            onClose={() => {
              setShowDetailDialog(false)
              setSelectedTicket(null)
            }}
            onAssign={handleAssignTicket}
            onCloseTicket={handleCloseTicket}
          />
        )}
      </AnimatePresence>

      {/* Batch Assign Dialog */}
      {showBatchAssignDialog && (
        <BatchAssignDialog
          ticketCount={selectedTickets.size}
          onClose={() => setShowBatchAssignDialog(false)}
          onSubmit={handleBatchAssign}
        />
      )}
    </div>
  )
}

// Create Ticket Dialog Component
function CreateTicketDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    project_id: '',
    machine_no: '',
    customer_id: '',
    customer_name: '',
    problem_type: '软件问题',
    problem_desc: '',
    urgency: '普通',
    reported_by: '',
    reported_phone: '',
    remark: '',
  })

  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    // 表单验证
    if (!formData.problem_desc || !formData.problem_desc.trim()) {
      toast.warning('请填写问题描述')
      return
    }
    if (!formData.reported_by || !formData.reported_by.trim()) {
      toast.warning('请填写报告人信息')
      return
    }
    if (!formData.customer_name || !formData.customer_name.trim()) {
      toast.warning('请填写客户名称')
      return
    }
    
    // 验证电话号码格式（如果填写了）
    if (formData.reported_phone && !/^1[3-9]\d{9}$/.test(formData.reported_phone.replace(/\s+/g, ''))) {
      toast.warning('请输入正确的手机号码')
      return
    }
    
    if (submitting) return
    
    try {
      setSubmitting(true)
      await onSubmit(formData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建服务工单</DialogTitle>
          <DialogDescription>填写工单信息，系统将自动生成工单号</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">关联项目 *</label>
                <Input
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                  placeholder="选择或输入项目编号"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">机台号</label>
                <Input
                  value={formData.machine_no}
                  onChange={(e) => setFormData({ ...formData, machine_no: e.target.value })}
                  placeholder="输入机台号"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">客户名称 *</label>
                <Input
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  placeholder="输入客户名称"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">问题类型 *</label>
                <select
                  value={formData.problem_type}
                  onChange={(e) => setFormData({ ...formData, problem_type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="软件问题">软件问题</option>
                  <option value="机械问题">机械问题</option>
                  <option value="电气问题">电气问题</option>
                  <option value="操作问题">操作问题</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题描述 *</label>
              <Textarea
                value={formData.problem_desc}
                onChange={(e) => setFormData({ ...formData, problem_desc: e.target.value })}
                placeholder="请详细描述问题情况..."
                rows={5}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">紧急程度 *</label>
                <select
                  value={formData.urgency}
                  onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="普通">普通</option>
                  <option value="紧急">紧急</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">报告人 *</label>
                <Input
                  value={formData.reported_by}
                  onChange={(e) => setFormData({ ...formData, reported_by: e.target.value })}
                  placeholder="输入报告人姓名"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">报告人电话</label>
              <Input
                value={formData.reported_phone}
                onChange={(e) => setFormData({ ...formData, reported_phone: e.target.value })}
                placeholder="输入报告人电话"
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">备注</label>
              <Textarea
                value={formData.remark}
                onChange={(e) => setFormData({ ...formData, remark: e.target.value })}
                placeholder="其他备注信息..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>取消</Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            <Send className="w-4 h-4 mr-2" />
            {submitting ? '创建中...' : '创建工单'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Ticket Detail Dialog Component
function TicketDetailDialog({ ticket, onClose, onAssign, onCloseTicket }) {
  const [showAssignDialog, setShowAssignDialog] = useState(false)
  const [showCloseDialog, setShowCloseDialog] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [closeData, setCloseData] = useState({
    solution: '',
    root_cause: '',
    preventive_action: '',
    satisfaction: '',
    feedback: '',
  })

  const status = statusConfig[ticket.status] || statusConfig['待分配']
  const urgency = urgencyConfig[ticket.urgency] || urgencyConfig['普通']
  const problemType = problemTypeConfig[ticket.problem_type] || problemTypeConfig['其他']

  const handleClose = async () => {
    if (!closeData.solution || !closeData.solution.trim()) {
      toast.warning('请填写解决方案')
      return
    }
    if (!closeData.satisfaction) {
      toast.warning('请选择客户满意度评分')
      return
    }
    
    if (submitting) return
    
    try {
      setSubmitting(true)
      await onCloseTicket(ticket.id, closeData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="font-mono">{ticket.ticket_no}</span>
              <Badge className={cn(status.color, 'text-xs')}>{status.label}</Badge>
              <Badge className={cn(urgency.bg, urgency.textColor, 'text-xs')}>{urgency.label}</Badge>
            </DialogTitle>
            <DialogDescription>服务工单详情</DialogDescription>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目信息</p>
                  <p className="text-white">{ticket.project_code} - {ticket.project_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">机台号</p>
                  <p className="text-white">{ticket.machine_no || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户名称</p>
                  <p className="text-white">{ticket.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">问题类型</p>
                  <p className="text-white">{problemType.icon} {problemType.label}</p>
                </div>
              </div>

              {/* Problem Description */}
              <div>
                <p className="text-sm text-slate-400 mb-1">问题描述</p>
                <p className="text-white bg-slate-800/50 p-3 rounded-lg">{ticket.problem_desc}</p>
              </div>

              {/* Reporter Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">报告人</p>
                  <p className="text-white">{ticket.reported_by}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">报告人电话</p>
                  <p className="text-white">{ticket.reported_phone}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">报告时间</p>
                  <p className="text-white">{ticket.reported_time ? formatDate(ticket.reported_time) : '-'}</p>
                </div>
                {ticket.assigned_name && (
                  <div>
                    <p className="text-sm text-slate-400 mb-1">负责人</p>
                    <p className="text-white">{ticket.assigned_name}</p>
                  </div>
                )}
              </div>

              {/* Timeline - Enhanced Visualization */}
              <div>
                <p className="text-sm text-slate-400 mb-3 font-medium">处理时间线</p>
                <div className="relative">
                  {/* Timeline Line */}
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-700"></div>
                  
                  <div className="space-y-4 relative">
                    {/* Timeline from backend */}
                    {ticket.timeline && Array.isArray(ticket.timeline) && ticket.timeline.length > 0 ? (
                      ticket.timeline.map((item, index) => {
                        const getIcon = (type) => {
                          switch (type) {
                            case 'REPORTED':
                              return <Clock className="w-4 h-4 text-slate-400" />
                            case 'ASSIGNED':
                              return <User className="w-4 h-4 text-blue-400" />
                            case 'STATUS_CHANGE':
                              return <ArrowUpDown className="w-4 h-4 text-amber-400" />
                            case 'CLOSED':
                              return <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            default:
                              return <FileText className="w-4 h-4 text-slate-400" />
                          }
                        }
                        
                        const getColor = (type) => {
                          switch (type) {
                            case 'REPORTED':
                              return 'bg-slate-500'
                            case 'ASSIGNED':
                              return 'bg-blue-500'
                            case 'STATUS_CHANGE':
                              return 'bg-amber-500'
                            case 'CLOSED':
                              return 'bg-emerald-500'
                            default:
                              return 'bg-slate-500'
                          }
                        }
                        
                        return (
                          <div key={index} className="flex items-start gap-3 relative">
                            {/* Timeline Dot */}
                            <div className={cn(
                              "relative z-10 w-8 h-8 rounded-full flex items-center justify-center",
                              getColor(item.type)
                            )}>
                              {getIcon(item.type)}
                            </div>
                            
                            {/* Timeline Content */}
                            <div className="flex-1 pb-4">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium text-white">
                                  {item.type === 'REPORTED' && '工单创建'}
                                  {item.type === 'ASSIGNED' && '工单分配'}
                                  {item.type === 'STATUS_CHANGE' && '状态变更'}
                                  {item.type === 'CLOSED' && '工单关闭'}
                                  {!['REPORTED', 'ASSIGNED', 'STATUS_CHANGE', 'CLOSED'].includes(item.type) && '操作记录'}
                                </span>
                                <span className="text-xs text-slate-500">
                                  {item.timestamp ? formatDate(item.timestamp) : '-'}
                                </span>
                              </div>
                              {item.user && (
                                <div className="text-xs text-slate-400 mb-1">
                                  操作人: {item.user}
                                </div>
                              )}
                              {item.description && (
                                <div className="text-sm text-slate-300 bg-slate-800/50 p-2 rounded">
                                  {item.description}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })
                    ) : (
                      // Fallback to basic timeline if no timeline data
                      <>
                        <div className="flex items-start gap-3 relative">
                          <div className="relative z-10 w-8 h-8 rounded-full bg-slate-500 flex items-center justify-center">
                            <Clock className="w-4 h-4 text-white" />
                          </div>
                          <div className="flex-1 pb-4">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-white">工单创建</span>
                              <span className="text-xs text-slate-500">
                                {ticket.reported_time ? formatDate(ticket.reported_time) : '-'}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400">
                              报告人: {ticket.reported_by}
                            </div>
                          </div>
                        </div>
                        {ticket.assigned_time && (
                          <div className="flex items-start gap-3 relative">
                            <div className="relative z-10 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                              <User className="w-4 h-4 text-white" />
                            </div>
                            <div className="flex-1 pb-4">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium text-white">工单分配</span>
                                <span className="text-xs text-slate-500">
                                  {formatDate(ticket.assigned_time)}
                                </span>
                              </div>
                              {ticket.assigned_name && (
                                <div className="text-xs text-slate-400">
                                  分配给: {ticket.assigned_name}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                        {ticket.response_time && (
                          <div className="flex items-start gap-3 relative">
                            <div className="relative z-10 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                              <CheckCircle2 className="w-4 h-4 text-white" />
                            </div>
                            <div className="flex-1 pb-4">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium text-white">响应</span>
                                <span className="text-xs text-slate-500">
                                  {formatDate(ticket.response_time)}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                        {ticket.resolved_time && (
                          <div className="flex items-start gap-3 relative">
                            <div className="relative z-10 w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center">
                              <CheckCircle2 className="w-4 h-4 text-white" />
                            </div>
                            <div className="flex-1 pb-4">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium text-white">工单解决</span>
                                <span className="text-xs text-slate-500">
                                  {formatDate(ticket.resolved_time)}
                                </span>
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Solution */}
              {ticket.solution && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">解决方案</p>
                  <p className="text-white bg-slate-800/50 p-3 rounded-lg">{ticket.solution}</p>
                </div>
              )}

              {/* Satisfaction */}
              {ticket.satisfaction && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户满意度</p>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                          key={i}
                          className={cn(
                            'w-5 h-5',
                            i <= ticket.satisfaction
                              ? 'fill-yellow-400 text-yellow-400'
                              : 'text-slate-600'
                          )}
                        />
                      ))}
                    </div>
                    <span className="text-white">{ticket.satisfaction}/5</span>
                  </div>
                  {ticket.feedback && (
                    <p className="text-slate-400 text-sm mt-2 bg-slate-800/50 p-3 rounded-lg">
                      {ticket.feedback}
                    </p>
                  )}
                </div>
              )}

              {/* Action Buttons Info */}
              <div className="border-t border-slate-700 pt-4">
                <p className="text-sm text-slate-400 mb-2">操作提示</p>
                <div className="text-xs text-slate-500 space-y-1">
                  {ticket.status === '待分配' && (
                    <p>• 点击"分配工单"按钮，将此工单分配给负责的工程师</p>
                  )}
                  {ticket.status === '待验证' && (
                    <p>• 点击"关闭工单"按钮，填写解决方案和客户反馈后关闭工单</p>
                  )}
                  {ticket.status === '处理中' && (
                    <p>• 工单正在处理中，等待工程师完成处理</p>
                  )}
                  {ticket.status === '已关闭' && (
                    <p>• 工单已关闭，如需重新打开请联系管理员</p>
                  )}
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <div className="flex items-center justify-between w-full">
              <div className="text-xs text-slate-400">
                提示：按 ESC 键可关闭对话框
              </div>
              <div className="flex gap-2">
                {ticket.status === '待分配' && (
                  <Button 
                    variant="outline" 
                    onClick={() => setShowAssignDialog(true)}
                    disabled={submitting}
                  >
                    分配工单
                  </Button>
                )}
                {ticket.status === '待验证' && (
                  <Button 
                    onClick={() => setShowCloseDialog(true)}
                    disabled={submitting}
                  >
                    关闭工单
                  </Button>
                )}
                <Button variant="outline" onClick={onClose} disabled={submitting}>
                  关闭
                </Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Dialog */}
      {showAssignDialog && (
        <AssignTicketDialog
          ticket={ticket}
          onClose={() => setShowAssignDialog(false)}
          onSubmit={(assignData) => {
            onAssign(ticket.id, assignData)
            setShowAssignDialog(false)
          }}
        />
      )}

      {/* Close Dialog */}
      {showCloseDialog && (
        <CloseTicketDialog
          ticket={ticket}
          closeData={closeData}
          setCloseData={setCloseData}
          onClose={() => setShowCloseDialog(false)}
          onSubmit={handleClose}
        />
      )}
    </>
  )
}

// Assign Ticket Dialog
function AssignTicketDialog({ ticket, onClose, onSubmit }) {
  const [assignData, setAssignData] = useState({
    assignee_id: '',
    comment: '',
  })
  const [users, setUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Load users for assignment
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoadingUsers(true)
        // Get active users, preferably from service department
        const response = await userApi.list({
          is_active: true,
          page_size: 100,
          // Optionally filter by department: department: '售后服务部'
        })
        const userList = response.data?.items || response.data || []
        setUsers(userList.map(u => ({
          id: u.id,
          name: u.real_name || u.username,
          role: u.position || u.roles?.[0] || '工程师'
        })))
      } catch (err) {
        // Fallback to empty list or mock data if needed
        setUsers([])
      } finally {
        setLoadingUsers(false)
      }
    }
    loadUsers()
  }, [])

  const handleSubmit = async () => {
    if (!assignData.assignee_id) {
      toast.warning('请选择负责人')
      return
    }
    
    if (submitting) return
    
    try {
      setSubmitting(true)
      await onSubmit(ticket.id, assignData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle>分配工单</DialogTitle>
          <DialogDescription>选择负责人处理此工单</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">负责人 *</label>
              <select
                value={assignData.assignee_id}
                onChange={(e) => setAssignData({ ...assignData, assignee_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                disabled={loadingUsers}
              >
                <option value="">{loadingUsers ? '加载中...' : '选择负责人'}</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.role})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">分配说明</label>
              <Textarea
                value={assignData.comment}
                onChange={(e) => setAssignData({ ...assignData, comment: e.target.value })}
                placeholder="输入分配说明..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>取消</Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? '提交中...' : '确认分配'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Close Ticket Dialog
function CloseTicketDialog({ ticket, closeData, setCloseData, submitting, onClose, onSubmit }) {
  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>关闭工单</DialogTitle>
          <DialogDescription>填写解决方案和客户反馈信息</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">解决方案 *</label>
              <Textarea
                value={closeData.solution}
                onChange={(e) => setCloseData({ ...closeData, solution: e.target.value })}
                placeholder="详细描述解决方案..."
                rows={4}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">根本原因</label>
              <Textarea
                value={closeData.root_cause}
                onChange={(e) => setCloseData({ ...closeData, root_cause: e.target.value })}
                placeholder="分析问题的根本原因..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">预防措施</label>
              <Textarea
                value={closeData.preventive_action}
                onChange={(e) => setCloseData({ ...closeData, preventive_action: e.target.value })}
                placeholder="描述预防类似问题的措施..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">客户满意度 *</label>
              <select
                value={closeData.satisfaction}
                onChange={(e) => setCloseData({ ...closeData, satisfaction: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
              >
                <option value="">选择满意度</option>
                <option value="1">1分 - 非常不满意</option>
                <option value="2">2分 - 不满意</option>
                <option value="3">3分 - 一般</option>
                <option value="4">4分 - 满意</option>
                <option value="5">5分 - 非常满意</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">客户反馈</label>
              <Textarea
                value={closeData.feedback}
                onChange={(e) => setCloseData({ ...closeData, feedback: e.target.value })}
                placeholder="记录客户反馈意见..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>取消</Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting ? '提交中...' : '确认关闭'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Batch Assign Dialog
function BatchAssignDialog({ ticketCount, onClose, onSubmit }) {
  const [assignData, setAssignData] = useState({
    assignee_id: '',
    comment: '',
  })
  const [users, setUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Load users for assignment
  useEffect(() => {
    const loadUsers = async () => {
      try {
        setLoadingUsers(true)
        const response = await userApi.list({
          is_active: true,
          page_size: 100,
        })
        const userList = response.data?.items || response.data || []
        setUsers(userList.map(u => ({
          id: u.id,
          name: u.real_name || u.username,
          role: u.position || u.roles?.[0] || '工程师'
        })))
      } catch (err) {
        setUsers([])
      } finally {
        setLoadingUsers(false)
      }
    }
    loadUsers()
  }, [])

  const handleSubmit = async () => {
    if (!assignData.assignee_id) {
      toast.warning('请选择负责人')
      return
    }
    
    if (submitting) return
    
    try {
      setSubmitting(true)
      await onSubmit(assignData)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-md bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle>批量分配工单</DialogTitle>
          <DialogDescription>将 {ticketCount} 个工单分配给负责人</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">负责人 *</label>
              <select
                value={assignData.assignee_id}
                onChange={(e) => setAssignData({ ...assignData, assignee_id: e.target.value })}
                className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                disabled={loadingUsers}
              >
                <option value="">{loadingUsers ? '加载中...' : '选择负责人'}</option>
                {users.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.role})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">分配说明</label>
              <Textarea
                value={assignData.comment}
                onChange={(e) => setAssignData({ ...assignData, comment: e.target.value })}
                placeholder="输入分配说明（将应用于所有选中的工单）..."
                rows={3}
                className="bg-slate-800/50 border-slate-700"
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>取消</Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? '分配中...' : `确认分配 ${ticketCount} 个工单`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}