/**
 * Customer Service Engineer Dashboard
 * 客服工程师工作台 - 客户技术支持、问题处理、现场服务、客户沟通
 * 
 * 核心功能：
 * 1. 问题处理统计与待办
 * 2. 现场服务任务管理（S8阶段：现场交付）
 * 3. 质保期项目管理（S9阶段：质保结项）
 * 4. 客户问题跟踪
 * 5. 验收任务协调（SAT验收）
 * 6. 客户满意度跟踪
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Wrench,
  FileText,
  Phone,
  MapPin,
  Calendar,
  Star,
  ChevronRight,
  Plus,
  Search,
  AlertTriangle,
  CheckSquare,
  Package,
  Settings,
  MessageSquare,
  Send,
  UserPlus,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Input,
} from '../components/ui'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi, issueApi, projectApi, acceptanceApi } from '../services/api'

// 配置
const todoTypeConfig = {
  issue: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
  sat: { icon: CheckSquare, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  service: { icon: Wrench, color: 'text-purple-400', bg: 'bg-purple-500/20' },
  follow: { icon: Phone, color: 'text-green-400', bg: 'bg-green-500/20' },
  warranty: { icon: Package, color: 'text-amber-400', bg: 'bg-amber-500/20' },
}

const severityConfig = {
  low: { label: '低', color: 'bg-slate-500' },
  medium: { label: '中', color: 'bg-amber-500' },
  high: { label: '高', color: 'bg-orange-500' },
  critical: { label: '严重', color: 'bg-red-500' },
}

const priorityConfig = {
  low: { label: '低', color: 'text-slate-400' },
  medium: { label: '中', color: 'text-amber-400' },
  high: { label: '高', color: 'text-orange-400' },
  urgent: { label: '紧急', color: 'text-red-400' },
}

const issueStatusConfig = {
  open: { label: '待处理', color: 'bg-slate-500' },
  in_progress: { label: '处理中', color: 'bg-blue-500' },
  resolved: { label: '已解决', color: 'bg-emerald-500' },
  verified: { label: '已验证', color: 'bg-green-500' },
  closed: { label: '已关闭', color: 'bg-slate-600' },
}

const serviceTypeConfig = {
  installation: { label: '安装调试', icon: Settings },
  training: { label: '操作培训', icon: Users },
  maintenance: { label: '定期维护', icon: Wrench },
  repair: { label: '故障维修', icon: AlertTriangle },
}

const healthColors = {
  good: 'bg-emerald-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
}

export default function CustomerServiceDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState({})
  const [todos, setTodos] = useState([])
  const [activeProjects, setActiveProjects] = useState([])
  const [issues, setIssues] = useState([])
  const [serviceTasks, setServiceTasks] = useState([])
  const [warrantyProjects, setWarrantyProjects] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showCreateIssue, setShowCreateIssue] = useState(false)
  const [showAssignIssue, setShowAssignIssue] = useState(false)
  const [selectedIssue, setSelectedIssue] = useState(null)

  // Load customer service data
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Load service tickets statistics
      const statsResponse = await serviceApi.tickets.getStatistics()
      const ticketsStats = statsResponse.data || {}

      // Load pending issues
      const issuesResponse = await issueApi.list({
        page: 1,
        page_size: 20,
        status: 'PENDING,IN_PROGRESS',
        category: 'CUSTOMER',
      })
      const issuesData = issuesResponse.data?.items || issuesResponse.data || []

      // Load active projects (S8/S9 stages)
      const projectsResponse = await projectApi.list({
        page: 1,
        page_size: 50,
        stage: 'S8,S9',
      })
      const projectsData = projectsResponse.data?.items || projectsResponse.data || []

      // Load service tickets
      const ticketsResponse = await serviceApi.tickets.list({
        page: 1,
        page_size: 20,
        status: 'PENDING,IN_PROGRESS',
      })
      const ticketsData = ticketsResponse.data?.items || ticketsResponse.data || []

      // Load SAT acceptance orders
      const acceptanceResponse = await acceptanceApi.orders.list({
        page: 1,
        page_size: 20,
        acceptance_type: 'SAT',
        status: 'PENDING,IN_PROGRESS',
      })
      const acceptanceData = acceptanceResponse.data?.items || acceptanceResponse.data || []

      // Transform issues to todos
      const transformedTodos = [
        ...issuesData.slice(0, 3).map(issue => ({
          id: `issue-${issue.id}`,
          type: 'issue',
          title: '处理客户问题',
          target: `${issue.project_name || ''} - ${issue.customer_name || ''}`,
          issueNo: issue.issue_no || `ISS-${issue.id}`,
          priority: issue.priority?.toLowerCase() || 'medium',
          time: new Date(issue.created_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
          status: issue.status?.toLowerCase() || 'pending',
          done: false,
        })),
        ...acceptanceData.slice(0, 2).map(acc => ({
          id: `sat-${acc.id}`,
          type: 'sat',
          title: 'SAT验收协调',
          target: acc.project_name || '',
          projectId: acc.project_id?.toString() || '',
          time: acc.scheduled_date ? new Date(acc.scheduled_date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '待定',
          status: acc.status?.toLowerCase() || 'pending',
          done: false,
        })),
        ...ticketsData.slice(0, 2).map(ticket => ({
          id: `service-${ticket.id}`,
          type: 'service',
          title: '现场服务',
          target: ticket.project_name || ticket.customer_name || '',
          location: ticket.location || '',
          time: ticket.scheduled_time ? new Date(ticket.scheduled_time).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '待定',
          status: ticket.status?.toLowerCase() || 'pending',
          done: false,
        })),
      ]

      setTodos(transformedTodos)

      // Transform active projects
      const transformedProjects = projectsData.map(project => ({
        id: project.id?.toString() || project.project_code,
        name: project.project_name || '',
        customer: project.customer_name || '',
        stage: project.stage || '',
        stageLabel: project.stage === 'S8' ? '现场交付' : '质保结项',
        status: project.status || '',
        progress: project.progress || 0,
        location: project.location || '',
        contact: project.contact_person || '',
        contactPhone: project.contact_phone || '',
        scheduledDate: project.scheduled_date || '',
        issues: issuesData.filter(i => i.project_id === project.id).length,
        health: project.health_status?.toLowerCase() || 'normal',
      }))

      setActiveProjects(transformedProjects)

      // Transform issues
      const transformedIssues = issuesData.map(issue => ({
        id: issue.issue_no || `ISS-${issue.id}`,
        title: issue.title || issue.description || '',
        project: issue.project_name || '',
        customer: issue.customer_name || '',
        type: issue.issue_type || '',
        severity: issue.severity?.toLowerCase() || 'medium',
        priority: issue.priority?.toLowerCase() || 'medium',
        status: issue.status?.toLowerCase() || 'pending',
        reporter: issue.reporter_name || '',
        assignee: issue.assignee_name || '',
        createdAt: issue.created_at || '',
        updatedAt: issue.updated_at || '',
      }))

      setIssues(transformedIssues)

      // Transform service tasks
      const transformedServiceTasks = ticketsData.map(ticket => ({
        id: ticket.ticket_no || `SRV-${ticket.id}`,
        project: ticket.project_name || '',
        customer: ticket.customer_name || '',
        type: ticket.problem_type || '',
        urgency: ticket.urgency?.toLowerCase() || 'medium',
        status: ticket.status?.toLowerCase() || 'pending',
        reportedBy: ticket.reported_by || '',
        reportedTime: ticket.reported_time || '',
        scheduledTime: ticket.scheduled_time || '',
        location: ticket.location || '',
      }))

      setServiceTasks(transformedServiceTasks)

      // Filter warranty projects (S9 stage)
      const warrantyProjectsData = projectsData.filter(p => p.stage === 'S9')
      const transformedWarranty = warrantyProjectsData.map(project => ({
        id: project.id?.toString() || project.project_code,
        name: project.project_name || '',
        customer: project.customer_name || '',
        warrantyStart: project.warranty_start_date || '',
        warrantyEnd: project.warranty_end_date || '',
        status: project.status || '',
        issues: issuesData.filter(i => i.project_id === project.id).length,
      }))

      setWarrantyProjects(transformedWarranty)

      // Calculate stats
      const pendingIssues = issuesData.filter(i => i.status === 'PENDING').length
      const inProgressServices = ticketsData.filter(t => t.status === 'IN_PROGRESS').length
      const resolvedThisMonth = ticketsStats.resolved_this_month || 0
      const customerSatisfaction = ticketsStats.avg_satisfaction_score || 4.6
      const activeProjectsCount = projectsData.length
      const urgentIssues = issuesData.filter(i => i.priority === 'URGENT' || i.severity === 'CRITICAL').length
      const todayTasks = transformedTodos.length
      const warrantyProjectsCount = warrantyProjectsData.length

      setStats({
        pendingIssues,
        inProgressServices,
        resolvedThisMonth,
        customerSatisfaction: parseFloat(customerSatisfaction),
        activeProjects: activeProjectsCount,
        urgentIssues,
        todayTasks,
        warrantyProjects: warrantyProjectsCount,
      })

    } catch (err) {
      console.error('Failed to load customer service data:', err)
      setError(err.message || '加载数据失败')
      // Keep mock data as fallback
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const toggleTodo = (id) => {
    setTodos(prev => prev.map(t => t.id === id ? { ...t, done: !t.done } : t))
  }

  const handleCreateIssue = (issueData) => {
    // TODO: Call API to create issue
    setShowCreateIssue(false)
    // Refresh issue list
  }

  const handleAssignIssue = (issueId, assignData) => {
    // TODO: Call API to assign issue
    setShowAssignIssue(false)
    setSelectedIssue(null)
    // 刷新问题列表
  }

  const filteredIssues = useMemo(() => {
    if (!searchQuery) return issues
    const query = searchQuery.toLowerCase()
    return issues.filter(issue =>
      issue.title.toLowerCase().includes(query) ||
      issue.project.toLowerCase().includes(query) ||
      issue.customer.toLowerCase().includes(query) ||
      issue.id.toLowerCase().includes(query)
    )
  }, [searchQuery])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="客服工作台"
        description={`待处理问题: ${stats.pendingIssues} | 进行中服务: ${stats.inProgressServices} | 客户满意度: ${stats.customerSatisfaction}/5.0`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button 
              variant="outline" 
              className="flex items-center gap-2"
              onClick={() => setShowCreateIssue(true)}
            >
              <Plus className="w-4 h-4" />
              创建问题工单
            </Button>
            <Button className="flex items-center gap-2">
              <Wrench className="w-4 h-4" />
              安排服务
            </Button>
          </motion.div>
        }
      />

      {/* Stats Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 待处理问题 */}
        <Card className="bg-gradient-to-br from-red-500/10 to-orange-500/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">待处理问题</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.pendingIssues}</p>
                <div className="flex items-center gap-2 mt-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{stats.urgentIssues}个紧急</span>
                </div>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 进行中服务 */}
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">进行中服务</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.inProgressServices}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-blue-400" />
                  <span className="text-xs text-blue-400">今日任务 {stats.todayTasks}</span>
                </div>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Wrench className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 本月解决问题 */}
        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">本月解决</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.resolvedThisMonth}</p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+12%</span>
                  <span className="text-xs text-slate-500">vs 上月</span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 客户满意度 */}
        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">客户满意度</p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-2xl font-bold text-white">{stats.customerSatisfaction}</p>
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <Star
                        key={i}
                        className={cn(
                          'w-4 h-4',
                          i <= Math.floor(stats.customerSatisfaction)
                            ? 'fill-yellow-400 text-yellow-400'
                            : 'text-slate-600'
                        )}
                      />
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+0.2</span>
                  <span className="text-xs text-slate-500">vs 上月</span>
                </div>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Star className="w-5 h-5 text-purple-400 fill-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Todos & Active Projects */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* Today's Todos */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">今日待办</CardTitle>
                <Badge variant="secondary">{todos.filter(t => !t.done).length}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {todos.map((todo) => {
                const config = todoTypeConfig[todo.type]
                const Icon = config?.icon || Clock
                return (
                  <motion.div
                    key={todo.id}
                    variants={fadeIn}
                    onClick={() => toggleTodo(todo.id)}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all',
                      'hover:bg-surface-100',
                      todo.done && 'opacity-50'
                    )}
                  >
                    <div className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center',
                      config?.bg || 'bg-slate-500/20'
                    )}>
                      <Icon className={cn('w-4 h-4', config?.color || 'text-slate-400')} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          'font-medium text-sm',
                          todo.done ? 'line-through text-slate-500' : 'text-white'
                        )}>
                          {todo.title}
                        </span>
                        {todo.priority === 'urgent' && !todo.done && (
                          <AlertTriangle className="w-3 h-3 text-red-400" />
                        )}
                      </div>
                      <span className="text-xs text-slate-400">{todo.target}</span>
                    </div>
                    <span className="text-xs text-slate-500">{todo.time}</span>
                  </motion.div>
                )
              })}
            </CardContent>
          </Card>

          {/* Active Projects (S8/S9) */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">进行中项目</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  全部项目 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {activeProjects.map((project) => (
                <motion.div
                  key={project.id}
                  variants={fadeIn}
                  className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-white text-sm">{project.name}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-slate-400">{project.customer}</span>
                        <Badge variant="secondary" className="text-xs">
                          {project.stageLabel}
                        </Badge>
                      </div>
                    </div>
                    {project.issues > 0 && (
                      <Badge variant="destructive" className="text-xs">
                        {project.issues}个问题
                      </Badge>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2 mb-2">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    <span className="text-xs text-slate-400">{project.location}</span>
                    <span className="text-xs text-slate-500">|</span>
                    <span className="text-xs text-slate-400">{project.contact}</span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-full', healthColors[project.health])} />
                      <span className="text-slate-400">进度 {project.progress}%</span>
                    </div>
                    <span className="text-slate-400">{project.status}</span>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Middle Column - Issues & Service Tasks */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* Customer Issues */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">客户问题</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索问题..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="h-7 w-32 pl-8 text-xs"
                    />
                  </div>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {filteredIssues.map((issue) => (
                <motion.div
                  key={issue.id}
                  variants={fadeIn}
                  className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm text-white cursor-pointer hover:text-primary">
                          {issue.title}
                        </span>
                        <Badge
                          className={cn('text-xs', severityConfig[issue.severity]?.color || 'bg-slate-500')}
                        >
                          {severityConfig[issue.severity]?.label}
                        </Badge>
                        <span className={cn('text-xs', priorityConfig[issue.priority]?.color)}>
                          {priorityConfig[issue.priority]?.label}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400">
                        {issue.project} - {issue.customer}
                      </div>
                    </div>
                    <Badge
                      className={cn('text-xs', issueStatusConfig[issue.status]?.color || 'bg-slate-500')}
                    >
                      {issueStatusConfig[issue.status]?.label}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{issue.id}</span>
                    <div className="flex items-center gap-2">
                      <span>跟进 {issue.followUpCount} 次</span>
                      {issue.status === 'open' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-xs"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedIssue(issue)
                            setShowAssignIssue(true)
                          }}
                        >
                          <UserPlus className="w-3 h-3 mr-1" />
                          转派
                        </Button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Service Tasks */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">现场服务任务</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  全部任务 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {serviceTasks.map((task) => {
                const typeConfig = serviceTypeConfig[task.type]
                const TypeIcon = typeConfig?.icon || Wrench
                return (
                  <motion.div
                    key={task.id}
                    variants={fadeIn}
                    className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <TypeIcon className="w-4 h-4 text-blue-400" />
                        <span className="font-medium text-sm text-white">{task.title}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {typeConfig?.label}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-400 mb-1">
                      {task.project} - {task.customer}
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {task.location}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {task.scheduledDate}
                        </span>
                      </div>
                      <span>{task.estimatedHours}小时</span>
                    </div>
                  </motion.div>
                )
              })}
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Column - Warranty Projects & Quick Actions */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* Warranty Projects */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">质保期项目</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  全部 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {warrantyProjects.map((project) => (
                <motion.div
                  key={project.id}
                  variants={fadeIn}
                  className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h4 className="font-medium text-white text-sm">{project.name}</h4>
                      <span className="text-xs text-slate-400">{project.customer}</span>
                    </div>
                    {project.status === 'expiring' && (
                      <Badge variant="destructive" className="text-xs">
                        即将到期
                      </Badge>
                    )}
                  </div>
                  
                  <div className="mb-2">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">质保期</span>
                      <span className="text-slate-500">
                        {project.warrantyStartDate} ~ {project.warrantyEndDate}
                      </span>
                    </div>
                    <Progress
                      value={(project.daysRemaining / 365) * 100}
                      className="h-1.5"
                    />
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>剩余 {project.daysRemaining} 天</span>
                    {project.issues > 0 && (
                      <span className="text-red-400">{project.issues}个问题</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">快捷操作</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2">
              <Button 
                variant="outline" 
                className="h-auto py-3 flex flex-col gap-1"
                onClick={() => setShowCreateIssue(true)}
              >
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-xs">创建问题工单</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <FileText className="w-4 h-4 text-blue-400" />
                <span className="text-xs">服务报告</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <Wrench className="w-4 h-4 text-purple-400" />
                <span className="text-xs">安排服务</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <CheckSquare className="w-4 h-4 text-green-400" />
                <span className="text-xs">SAT验收</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <Phone className="w-4 h-4 text-amber-400" />
                <span className="text-xs">客户回访</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <MessageSquare className="w-4 h-4 text-cyan-400" />
                <span className="text-xs">满意度调查</span>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 创建问题工单对话框 */}
      <AnimatePresence>
        {showCreateIssue && (
          <CreateIssueDialog
            onClose={() => setShowCreateIssue(false)}
            onSubmit={handleCreateIssue}
          />
        )}
      </AnimatePresence>

      {/* 转派问题对话框 */}
      <AnimatePresence>
        {showAssignIssue && selectedIssue && (
          <AssignIssueDialog
            issue={selectedIssue}
            onClose={() => {
              setShowAssignIssue(false)
              setSelectedIssue(null)
            }}
            onSubmit={handleAssignIssue}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// 创建问题工单对话框组件
function CreateIssueDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    category: 'CUSTOMER',
    issue_type: 'DEFECT',
    severity: 'MEDIUM',
    priority: 'MEDIUM',
    project_id: '',
    machine_id: '',
    title: '',
    description: '',
    assignee_id: '',
    due_date: '',
    impact_scope: '',
    impact_level: 'MEDIUM',
    is_blocking: false,
    tags: [],
  })

    const mockProjects = [
    { id: 1, code: 'PJ250106002', name: 'EOL功能测试设备', customer: '东莞XX电子' },
    { id: 2, code: 'PJ250103003', name: 'ICT在线测试设备', customer: '惠州XX电池' },
    { id: 3, code: 'PJ250101001', name: 'BMS老化测试设备', customer: '深圳XX科技' },
  ]

  const mockMachines = formData.project_id
    ? [
        { id: 1, code: 'PN001', name: '设备1号' },
        { id: 2, code: 'PN002', name: '设备2号' },
      ]
    : []

  const mockUsers = [
    { id: 1, name: '李工程师', role: '机械工程师' },
    { id: 2, name: '王工程师', role: '电气工程师' },
    { id: 3, name: '张工程师', role: '测试工程师' },
    { id: 4, name: '赵经理', role: '项目经理' },
  ]

  const handleSubmit = () => {
    if (!formData.title || !formData.description) {
      alert('请填写问题标题和描述')
      return
    }
    onSubmit(formData)
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl bg-surface-50 border-white/10 text-white max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-400" />
            创建问题工单
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {/* 基本信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题分类 *</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="CUSTOMER">客户问题</option>
                <option value="PROJECT">项目问题</option>
                <option value="TASK">任务问题</option>
                <option value="ACCEPTANCE">验收问题</option>
                <option value="QUALITY">质量问题</option>
                <option value="TECHNICAL">技术问题</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">问题类型 *</label>
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
                <option value="QUESTION">疑问</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">严重程度 *</label>
              <select
                value={formData.severity}
                onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="LOW">低</option>
                <option value="MEDIUM">中</option>
                <option value="HIGH">高</option>
                <option value="CRITICAL">严重</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">优先级 *</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="LOW">低</option>
                <option value="MEDIUM">中</option>
                <option value="HIGH">高</option>
                <option value="URGENT">紧急</option>
              </select>
            </div>
          </div>

          {/* 关联信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">关联项目</label>
              <select
                value={formData.project_id}
                onChange={(e) => {
                  setFormData({ ...formData, project_id: e.target.value, machine_id: '' })
                }}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="">选择项目（可选）</option>
                {mockProjects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.code} - {project.name} ({project.customer})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">关联设备</label>
              <select
                value={formData.machine_id}
                onChange={(e) => setFormData({ ...formData, machine_id: e.target.value })}
                disabled={!formData.project_id}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white disabled:opacity-50"
              >
                <option value="">选择设备（可选）</option>
                {mockMachines.map((machine) => (
                  <option key={machine.id} value={machine.id}>
                    {machine.code} - {machine.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* 问题描述 */}
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
              placeholder="请详细描述问题情况、复现步骤、影响范围等"
              rows={5}
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white resize-none"
            />
          </div>

          {/* 转派信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">转派给</label>
              <select
                value={formData.assignee_id}
                onChange={(e) => setFormData({ ...formData, assignee_id: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="">选择处理人（可选）</option>
                {mockUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.role})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">要求完成日期</label>
              <Input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
          </div>

          {/* 影响评估 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">影响范围</label>
              <Input
                value={formData.impact_scope}
                onChange={(e) => setFormData({ ...formData, impact_scope: e.target.value })}
                placeholder="例如：影响FAT验收进度"
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
          <Button onClick={handleSubmit} className="bg-primary hover:bg-primary/90">
            <Send className="w-4 h-4 mr-2" />
            创建并转派
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// 转派问题对话框组件
function AssignIssueDialog({ issue, onClose, onSubmit }) {
  const [assignData, setAssignData] = useState({
    assignee_id: '',
    due_date: '',
    comment: '',
  })

    const mockUsers = [
    { id: 1, name: '李工程师', role: '机械工程师' },
    { id: 2, name: '王工程师', role: '电气工程师' },
    { id: 3, name: '张工程师', role: '测试工程师' },
    { id: 4, name: '赵经理', role: '项目经理' },
  ]

  const handleSubmit = () => {
    if (!assignData.assignee_id) {
      alert('请选择转派对象')
      return
    }
    onSubmit(issue.id, assignData)
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-surface-50 border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-blue-400" />
            转派问题
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {/* 问题信息 */}
          <div className="p-3 bg-surface-100 rounded-lg">
            <div className="text-sm text-slate-400 mb-1">问题编号</div>
            <div className="font-mono text-white">{issue.id}</div>
            <div className="text-sm text-slate-400 mt-2 mb-1">问题标题</div>
            <div className="text-white">{issue.title}</div>
          </div>

          {/* 转派信息 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-slate-400 mb-1 block">转派给 *</label>
              <select
                value={assignData.assignee_id}
                onChange={(e) => setAssignData({ ...assignData, assignee_id: e.target.value })}
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white"
              >
                <option value="">选择处理人</option>
                {mockUsers.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.role})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-400 mb-1 block">要求完成日期</label>
              <Input
                type="date"
                value={assignData.due_date}
                onChange={(e) => setAssignData({ ...assignData, due_date: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
              />
            </div>
          </div>

          {/* 转派说明 */}
          <div>
            <label className="text-sm text-slate-400 mb-1 block">转派说明</label>
            <textarea
              value={assignData.comment}
              onChange={(e) => setAssignData({ ...assignData, comment: e.target.value })}
              placeholder="请输入转派原因或说明"
              rows={3}
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-white resize-none"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} className="bg-primary hover:bg-primary/90">
            <Send className="w-4 h-4 mr-2" />
            确认转派
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

