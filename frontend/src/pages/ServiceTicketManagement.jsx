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
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card, CardContent, CardHeader, CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogBody
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi } from '../services/api'

// Mock data
const mockTickets = [
  {
    id: 1,
    ticket_no: 'SR-20260106-001',
    project_code: 'PJ250106002',
    project_name: 'EOL功能测试设备',
    machine_no: 'PN001',
    customer_name: '东莞XX电子',
    problem_type: '软件问题',
    problem_desc: '设备运行过程中出现程序崩溃，需要技术支持',
    urgency: '紧急',
    reported_by: '李工',
    reported_phone: '138****5678',
    reported_time: '2026-01-06 08:30:00',
    assigned_to: 1,
    assigned_name: '张工程师',
    assigned_time: '2026-01-06 09:00:00',
    status: '处理中',
    response_time: '2026-01-06 09:15:00',
    resolved_time: null,
    solution: null,
    satisfaction: null,
    feedback: null,
  },
  {
    id: 2,
    ticket_no: 'SR-20260105-002',
    project_code: 'PJ250103003',
    project_name: 'ICT在线测试设备',
    machine_no: 'PN002',
    customer_name: '惠州XX电池',
    problem_type: '机械问题',
    problem_desc: '设备运行时有异响，需要检查',
    urgency: '普通',
    reported_by: '张工',
    reported_phone: '139****9012',
    reported_time: '2026-01-05 14:20:00',
    assigned_to: 2,
    assigned_name: '王工程师',
    assigned_time: '2026-01-05 15:00:00',
    status: '待验证',
    response_time: '2026-01-05 15:10:00',
    resolved_time: '2026-01-06 10:00:00',
    solution: '已更换故障部件，设备运行正常',
    satisfaction: 5,
    feedback: '服务及时，问题解决迅速',
  },
  {
    id: 3,
    ticket_no: 'SR-20260104-003',
    project_code: 'PJ250101001',
    project_name: 'BMS老化测试设备',
    machine_no: 'PN003',
    customer_name: '深圳XX科技',
    problem_type: '操作问题',
    problem_desc: '操作人员需要培训',
    urgency: '普通',
    reported_by: '王工',
    reported_phone: '137****3456',
    reported_time: '2026-01-04 10:15:00',
    assigned_to: 1,
    assigned_name: '当前用户',
    assigned_time: '2026-01-04 11:00:00',
    status: '已关闭',
    response_time: '2026-01-04 11:30:00',
    resolved_time: '2026-01-05 16:00:00',
    solution: '已完成操作培训，客户已掌握操作方法',
    satisfaction: 4,
    feedback: '培训内容详细，但希望有更多实操练习',
  },
]

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
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState(null)
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
        page: 1,
        page_size: 100,
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
      
      const response = await serviceApi.tickets.list(params)
      const ticketsData = response.data?.items || response.data || []
      
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
      }))
      
      setTickets(transformedTickets)
    } catch (err) {
      console.error('Failed to load tickets:', err)
      setError(err.response?.data?.detail || err.message || '加载服务工单失败')
      setTickets([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [statusFilter, urgencyFilter, searchQuery])

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
      console.error('Failed to load statistics:', err)
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

  const filteredTickets = useMemo(() => {
    let result = tickets

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(ticket =>
        ticket.ticket_no.toLowerCase().includes(query) ||
        ticket.project_name.toLowerCase().includes(query) ||
        ticket.customer_name.toLowerCase().includes(query) ||
        ticket.problem_desc.toLowerCase().includes(query) ||
        ticket.reported_by.toLowerCase().includes(query)
      )
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      result = result.filter(ticket => ticket.status === statusFilter)
    }

    // Urgency filter
    if (urgencyFilter !== 'ALL') {
      result = result.filter(ticket => ticket.urgency === urgencyFilter)
    }

    return result
  }, [tickets, searchQuery, statusFilter, urgencyFilter])

  const handleViewDetail = (ticket) => {
    setSelectedTicket(ticket)
    setShowDetailDialog(true)
  }

  const handleCreateTicket = async (ticketData) => {
    try {
      await serviceApi.tickets.create(ticketData)
      toast.success('服务工单创建成功')
      setShowCreateDialog(false)
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      console.error('Failed to create ticket:', error)
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleAssignTicket = async (ticketId, assignData) => {
    try {
      await serviceApi.tickets.assign(ticketId, assignData)
      toast.success('工单分配成功')
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      console.error('Failed to assign ticket:', error)
      toast.error('分配失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleCloseTicket = async (ticketId, closeData) => {
    try {
      await serviceApi.tickets.close(ticketId, closeData)
      toast.success('工单已关闭')
      setShowDetailDialog(false)
      await loadTickets()
      await loadStatistics()
    } catch (error) {
      console.error('Failed to close ticket:', error)
      toast.error('关闭失败，请稍后重试')
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
              onClick={() => { loadTickets(); loadStatistics(); toast.success('数据已刷新'); }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              创建工单
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
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总工单数</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待分配</div>
                <div className="text-2xl font-bold text-slate-400">{stats.pending}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">处理中</div>
                <div className="text-2xl font-bold text-blue-400">{stats.inProgress}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-amber-500/10 border-amber-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待验证</div>
                <div className="text-2xl font-bold text-amber-400">{stats.pendingVerify}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-emerald-500/10 border-emerald-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已关闭</div>
                <div className="text-2xl font-bold text-emerald-400">{stats.closed}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-red-500/10 border-red-500/20">
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
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索工单号、项目名称、客户名称..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部状态</option>
                    <option value="待分配">待分配</option>
                    <option value="处理中">处理中</option>
                    <option value="待验证">待验证</option>
                    <option value="已关闭">已关闭</option>
                  </select>
                  <select
                    value={urgencyFilter}
                    onChange={(e) => setUrgencyFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部紧急度</option>
                    <option value="紧急">紧急</option>
                    <option value="普通">普通</option>
                  </select>
                  {(searchQuery || statusFilter !== 'ALL' || urgencyFilter !== 'ALL') && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setStatusFilter('ALL')
                        setUrgencyFilter('ALL')
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
          ) : filteredTickets.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="暂无服务工单"
              description={
                searchQuery || statusFilter !== 'ALL' || urgencyFilter !== 'ALL'
                  ? "当前筛选条件下没有匹配的工单，请尝试调整筛选条件"
                  : "当前没有服务工单数据"
              }
            />
          ) : (
            filteredTickets.map((ticket) => {
              const status = statusConfig[ticket.status] || statusConfig['待分配']
              const urgency = urgencyConfig[ticket.urgency] || urgencyConfig['普通']
              const problemType = problemTypeConfig[ticket.problem_type] || problemTypeConfig['其他']

              return (
                <motion.div key={ticket.id} variants={fadeIn}>
                  <Card className="hover:bg-slate-800/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
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
                              报告时间: {ticket.reported_time}
                            </span>
                            {ticket.response_time && (
                              <span className="flex items-center gap-1 text-blue-400">
                                <CheckCircle2 className="w-3 h-3" />
                                响应: {ticket.response_time}
                              </span>
                            )}
                            {ticket.resolved_time && (
                              <span className="flex items-center gap-1 text-emerald-400">
                                <CheckCircle2 className="w-3 h-3" />
                                解决: {ticket.resolved_time}
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
            })
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

  const handleSubmit = () => {
    if (!formData.problem_desc || !formData.reported_by) {
      toast.error('请填写问题描述和报告人信息')
      return
    }
    onSubmit(formData)
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
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>
            <Send className="w-4 h-4 mr-2" />
            创建工单
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

  const handleClose = () => {
    if (!closeData.solution || !closeData.satisfaction) {
      toast.error('请填写解决方案和满意度评分')
      return
    }
    onCloseTicket(ticket.id, closeData)
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
                  <p className="text-white">{ticket.reported_time}</p>
                </div>
                {ticket.assigned_name && (
                  <div>
                    <p className="text-sm text-slate-400 mb-1">负责人</p>
                    <p className="text-white">{ticket.assigned_name}</p>
                  </div>
                )}
              </div>

              {/* Timeline */}
              <div>
                <p className="text-sm text-slate-400 mb-2">处理时间线</p>
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-400">报告时间:</span>
                    <span className="text-white">{ticket.reported_time}</span>
                  </div>
                  {ticket.assigned_time && (
                    <div className="flex items-center gap-2 text-sm">
                      <User className="w-4 h-4 text-blue-400" />
                      <span className="text-slate-400">分配时间:</span>
                      <span className="text-white">{ticket.assigned_time}</span>
                    </div>
                  )}
                  {ticket.response_time && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-blue-400" />
                      <span className="text-slate-400">响应时间:</span>
                      <span className="text-white">{ticket.response_time}</span>
                    </div>
                  )}
                  {ticket.resolved_time && (
                    <div className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      <span className="text-slate-400">解决时间:</span>
                      <span className="text-white">{ticket.resolved_time}</span>
                    </div>
                  )}
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
                    <p className="text-slate-400 text-sm mt-2">{ticket.feedback}</p>
                  )}
                </div>
              )}
            </div>
          </DialogBody>
          <DialogFooter>
            {ticket.status === '待分配' && (
              <Button variant="outline" onClick={() => setShowAssignDialog(true)}>
                分配工单
              </Button>
            )}
            {ticket.status === '待验证' && (
              <Button onClick={() => setShowCloseDialog(true)}>
                关闭工单
              </Button>
            )}
            <Button variant="outline" onClick={onClose}>关闭</Button>
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

  const mockUsers = [
    { id: 1, name: '张工程师', role: '软件工程师' },
    { id: 2, name: '王工程师', role: '机械工程师' },
    { id: 3, name: '李工程师', role: '电气工程师' },
  ]

  const handleSubmit = () => {
    if (!assignData.assignee_id) {
      toast.error('请选择负责人')
      return
    }
    onSubmit(assignData)
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
              >
                <option value="">选择负责人</option>
                {mockUsers.map((user) => (
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
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>确认分配</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Close Ticket Dialog
function CloseTicketDialog({ ticket, closeData, setCloseData, onClose, onSubmit }) {
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
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={onSubmit}>确认关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

