/**
 * Sales Workstation - Main dashboard for sales engineers
 * Features: Performance metrics, Sales funnel, Todo list, Project tracking, Payment schedule
 */

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Target,
  Users,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Phone,
  FileText,
  Send,
  Plus,
  ChevronRight,
  Building2,
  Briefcase,
  Receipt,
  ArrowUpRight,
  Flame,
  Filter,
  LayoutGrid,
  List,
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
import { fadeIn, staggerContainer } from '../lib/animations'
import { cn, formatDate } from '../lib/utils'
import { SalesFunnel, CustomerCard, OpportunityCard, PaymentTimeline, PaymentStats } from '../components/sales'
import {
  salesStatisticsApi,
  opportunityApi,
  customerApi,
  contractApi,
  invoiceApi,
  projectApi,
  quoteApi,
  taskCenterApi,
} from '../services/api'

const DEFAULT_STATS = {
  monthlyTarget: 1200000,
  monthlyAchieved: 0,
  opportunityCount: 0,
  hotOpportunities: 0,
  pendingPayment: 0,
  overduePayment: 0,
  customerCount: 0,
  newCustomers: 0,
}

const OPPORTUNITY_STAGE_MAP = {
  DISCOVERY: 'lead',
  QUALIFIED: 'contact',
  PROPOSAL: 'quote',
  NEGOTIATION: 'negotiate',
  WON: 'won',
  LOST: 'lost',
  ON_HOLD: 'contact',
}

const PROJECT_STAGE_LABELS = {
  INITIATION: '立项',
  PLAN: '计划',
  DESIGN: '设计',
  PRODUCTION: '生产',
  DELIVERY: '交付',
  ACCEPTANCE: '验收',
  CLOSED: '结项',
}

const HEALTH_MAP = {
  H1: 'good',
  HEALTH_GREEN: 'good',
  GREEN: 'good',
  H2: 'warning',
  HEALTH_YELLOW: 'warning',
  YELLOW: 'warning',
  H3: 'critical',
  HEALTH_RED: 'critical',
  RED: 'critical',
}

const mapOpportunityStage = (stage) => OPPORTUNITY_STAGE_MAP[stage?.toUpperCase?.()] || 'lead'

const mapOpportunityPriority = (priority) => {
  const value = (priority || '').toString().toLowerCase()
  if (value.includes('urgent')) return 'urgent'
  if (value.includes('high')) return 'high'
  if (value.includes('low')) return 'low'
  return 'medium'
}

const mapProjectStageLabel = (stage) => {
  if (!stage) return '进行中'
  const normalized = stage.toString().toUpperCase()
  return PROJECT_STAGE_LABELS[normalized] || stage
}

const mapProjectHealth = (health) => {
  if (!health) return 'warning'
  const normalized = health.toString().toUpperCase()
  return HEALTH_MAP[normalized] || 'warning'
}

const isCurrentMonth = (date) => {
  if (!date) return false
  const checkDate = new Date(date)
  if (isNaN(checkDate.getTime())) return false
  const now = new Date()
  return checkDate.getFullYear() === now.getFullYear() && checkDate.getMonth() === now.getMonth()
}

const mapTaskToTodoType = (task) => {
  const type = (task.task_type || task.source_type || '').toUpperCase()
  if (type.includes('QUOTE')) return 'quote'
  if (type.includes('PAY')) return 'payment'
  if (type.includes('VISIT')) return 'visit'
  if (type.includes('APPROVAL')) return 'approval'
  if (type.includes('FOLLOW')) return 'follow'
  return 'reminder'
}

const calculateDaysBetween = (date) => {
  if (!date) return 0
  const target = new Date(date)
  if (isNaN(target.getTime())) return 0
  const diff = Date.now() - target.getTime()
  return Math.max(Math.floor(diff / (1000 * 60 * 60 * 24)), 0)
}

const transformOpportunity = (opportunity) => {
  const stage = mapOpportunityStage(opportunity.stage || opportunity.opportunity_stage)
  const expectedCloseDate = opportunity.estimated_close_date || opportunity.expected_close_date || ''
  const probability = Number(opportunity.win_probability ?? opportunity.success_rate ?? 0)
  return {
    id: opportunity.id,
    name: opportunity.opportunity_name || opportunity.name || opportunity.opportunity_code || '未命名商机',
    customerName: opportunity.customer?.customer_name || opportunity.customer_name || '',
    customerShort: opportunity.customer?.short_name || opportunity.customer?.customer_name || opportunity.customer_name || '',
    stage,
    priority: mapOpportunityPriority(opportunity.priority),
    expectedAmount: parseFloat(opportunity.est_amount || opportunity.expected_amount || 0),
    expectedCloseDate: expectedCloseDate ? formatDate(expectedCloseDate) : '未设置',
    probability,
    owner: opportunity.owner?.real_name || opportunity.owner_name || opportunity.owner?.username || '未分配',
    daysInStage: calculateDaysBetween(opportunity.stage_updated_at || opportunity.updated_at),
    isHot: probability >= 70,
    isOverdue: expectedCloseDate ? new Date(expectedCloseDate) < new Date() && stage !== 'won' : false,
    tags: opportunity.industry ? [opportunity.industry] : [],
  }
}

const transformCustomer = (customer) => ({
  id: customer.id,
  name: customer.customer_name || customer.name || '未命名客户',
  shortName: customer.short_name || customer.customer_name || customer.name || '客户',
  grade: (customer.grade || customer.level || 'B').toUpperCase(),
  status: (customer.status || 'active').toLowerCase(),
  industry: customer.industry || customer.category || '未分类',
  location: [customer.region, customer.city, customer.address].filter(Boolean).slice(0, 2).join(' · ') || '未设置',
  contactPerson: customer.contact_person || customer.primary_contact?.name,
  phone: customer.contact_phone || customer.primary_contact?.phone,
  totalAmount: parseFloat(customer.total_contract_amount || 0),
  pendingAmount: parseFloat(customer.pending_payment || 0),
  projectCount: customer.project_count || 0,
  opportunityCount: customer.opportunity_count || 0,
  tags: customer.tags || [],
  lastContact: customer.last_follow_up_at ? formatDate(customer.last_follow_up_at) : '无记录',
  createdAt: customer.created_at,
})

const transformInvoiceToPayment = (invoice) => {
  const statusMap = {
    PAID: 'paid',
    PENDING: 'pending',
    ISSUED: 'invoiced',
    OVERDUE: 'overdue',
  }
  const backendStatus = invoice.payment_status || invoice.status
  const status = statusMap[backendStatus] || 'pending'
  return {
    id: invoice.id,
    type: (invoice.payment_type || 'progress').toLowerCase(),
    projectName: invoice.project_name || invoice.contract_name || '未关联项目',
    amount: parseFloat(invoice.amount || invoice.invoice_amount || 0),
    dueDate: invoice.due_date || invoice.payment_due_date || invoice.expected_payment_date || '',
    paidDate: invoice.paid_date || '',
    status,
    invoiceNo: invoice.invoice_code,
    notes: invoice.remark || '',
  }
}

const transformProject = (project) => ({
  id: project.id || project.project_id,
  name: project.project_name || project.name || project.project_code || '项目',
  customer: project.customer?.customer_name || project.customer_name || '未设置',
  stageLabel: mapProjectStageLabel(project.stage || project.project_stage || project.status),
  progress: Math.round(project.progress_pct ?? project.progress ?? 0),
  health: mapProjectHealth(project.health || project.health_status || project.health_level),
  acceptanceDate: project.acceptance_date || project.delivery_date || project.target_acceptance_date || project.expected_acceptance_date || '未设置',
})

const transformTaskToTodo = (task) => {
  const deadline = task.deadline || task.plan_end_date
  const priority = (task.priority || '').toLowerCase()
  return {
    id: `task-${task.id}`,
    type: mapTaskToTodoType(task),
    title: task.title,
    target: task.project_name || task.source_name || task.task_code,
    time: deadline ? formatDate(deadline) : '无截止',
    priority: priority === 'urgent' ? 'urgent' : priority === 'high' ? 'high' : 'normal',
    done: task.status === 'COMPLETED',
  }
}



const todoTypeConfig = {
  follow: { icon: Phone, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  quote: { icon: FileText, color: 'text-amber-400', bg: 'bg-amber-500/20' },
  payment: { icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
  visit: { icon: Building2, color: 'text-purple-400', bg: 'bg-purple-500/20' },
  acceptance: { icon: CheckCircle2, color: 'text-pink-400', bg: 'bg-pink-500/20' },
  approval: { icon: CheckCircle2, color: 'text-orange-400', bg: 'bg-orange-500/20' },
  reminder: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/20' },
}

const healthColors = {
  good: 'bg-emerald-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
}

export default function SalesWorkstation() {
  const [todos, setTodos] = useState([])
  const [stats, setStats] = useState({ ...DEFAULT_STATS })
  const [customers, setCustomers] = useState([])
  const [projects, setProjects] = useState([])
  const [payments, setPayments] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [funnelData, setFunnelData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load sales statistics
  const loadStatistics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const now = new Date()
      const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
      const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0]
      const params = { start_date: startDate, end_date: endDate }

      const [
        summaryResponse,
        funnelResponse,
        opportunitiesResponse,
        customersResponse,
        contractsResponse,
        invoicesResponse,
      ] = await Promise.all([
        salesStatisticsApi.summary(params),
        salesStatisticsApi.funnel(params),
        opportunityApi.list({ page: 1, page_size: 100 }),
        customerApi.list({ page: 1, page_size: 10 }),
        contractApi.list({ page: 1, page_size: 10, status: 'SIGNED' }),
        invoiceApi.list({ page: 1, page_size: 10 }),
      ])

      const summaryData = summaryResponse.data?.data || summaryResponse.data || summaryResponse
      const funnelPayload = funnelResponse.data?.data || funnelResponse.data || {}
      const oppsData = opportunitiesResponse.data?.items || opportunitiesResponse.data || []
      const customersData = customersResponse.data?.items || customersResponse.data || []
      const contractsData = contractsResponse.data?.items || contractsResponse.data || []
      const invoicesData = invoicesResponse.data?.items || invoicesResponse.data || []

      const normalizedOpportunities = oppsData.map(transformOpportunity)
      setOpportunities(normalizedOpportunities.slice(0, 5))
      const hotOpportunities = normalizedOpportunities.filter(opp => opp.isHot).length

      const normalizedCustomers = customersData.slice(0, 3).map(transformCustomer)
      setCustomers(normalizedCustomers)
      const newCustomerCount = normalizedCustomers.filter(c => isCurrentMonth(c.createdAt)).length
      const totalCustomers = customersResponse.data?.total ?? customersData.length

      const paymentEntries = invoicesData.map(transformInvoiceToPayment)
      setPayments(paymentEntries)
      const pendingPayment = paymentEntries
        .filter(p => p.status === 'pending' || p.status === 'invoiced')
        .reduce((sum, p) => sum + (p.amount || 0), 0)
      const overduePayment = paymentEntries
        .filter(p => {
          if (p.status === 'overdue') return true
          if (p.status !== 'paid' && p.dueDate) {
            return new Date(p.dueDate) < new Date()
          }
          return false
        })
        .reduce((sum, p) => sum + (p.amount || 0), 0)

      const projectIds = contractsData.map(c => c.project_id).filter(Boolean).slice(0, 3)
      const projectDetails = await Promise.all(
        projectIds.map(async (projectId) => {
          try {
            const projectResponse = await projectApi.get(projectId)
            const projectData = projectResponse.data || projectResponse
            return transformProject(projectData)
          } catch (err) {
            console.error(`Failed to load project ${projectId}:`, err)
            return null
          }
        })
      )
      setProjects(projectDetails.filter(Boolean))

      const funnelCounts = {
        lead: funnelPayload.leads || 0,
        contact: funnelPayload.opportunities || 0,
        quote: funnelPayload.quotes || 0,
        negotiate: Math.max((funnelPayload.contracts || 0) - (summaryData?.won_opportunities || 0), 0),
        won: summaryData?.won_opportunities || funnelPayload.contracts || 0,
      }
      setFunnelData(funnelCounts)

      setStats({
        monthlyTarget: summaryData?.monthly_target || DEFAULT_STATS.monthlyTarget,
        monthlyAchieved: summaryData?.total_contract_amount || 0,
        opportunityCount: summaryData?.total_opportunities || normalizedOpportunities.length,
        hotOpportunities,
        pendingPayment,
        overduePayment,
        customerCount: totalCustomers || summaryData?.total_leads || 0,
        newCustomers: newCustomerCount,
      })
    } catch (err) {
      console.error('Failed to load sales statistics:', err)
      setError(err.response?.data?.detail || err.message || '加载销售数据失败')
      setStats({ ...DEFAULT_STATS })
      setFunnelData(null)
      setOpportunities([])
      setCustomers([])
      setProjects([])
      setPayments([])
    } finally {
      setLoading(false)
    }
  }, [])

  const loadTodos = useCallback(async () => {
    try {
      const [tasksResponse, quotesResponse] = await Promise.all([
        taskCenterApi.myTasks({ page: 1, page_size: 10, status: 'IN_PROGRESS' }),
        quoteApi.list({ status: 'SUBMITTED', page_size: 5 }),
      ])

      const taskItems = tasksResponse.data?.items || tasksResponse.data || []
      const taskTodos = taskItems.map(transformTaskToTodo)

      const quotes = quotesResponse.data?.items || quotesResponse.data || []
      const approvalTodos = []
      await Promise.all(
        quotes.slice(0, 3).map(async (quote) => {
          try {
            const statusResponse = await quoteApi.getApprovalStatus(quote.id)
            const statusData = statusResponse.data?.data || statusResponse.data || statusResponse
            if ((statusData.status || statusData.approval_status) === 'PENDING') {
              approvalTodos.push({
                id: `approval-quote-${quote.id}`,
                type: 'approval',
                title: `报价审批 - ${quote.quote_code || quote.code}`,
                target: quote.customer?.customer_name || quote.customer_name || '',
                time: '待审批',
                priority: 'high',
                done: false,
              })
            }
          } catch (err) {
            console.error('Failed to load quote approval status:', err)
          }
        })
      )

      setTodos([...taskTodos, ...approvalTodos])
    } catch (err) {
      console.error('Failed to load todos:', err)
      setTodos([])
    }
  }, [])

  // Load data when component mounts
  useEffect(() => {
    loadStatistics()
    loadTodos()
  }, [loadStatistics, loadTodos])

  const achievementRate = stats.monthlyTarget > 0 
    ? (stats.monthlyAchieved / stats.monthlyTarget * 100).toFixed(1)
    : '0'

  const toggleTodo = (id) => {
    setTodos(prev => prev.map(t => t.id === id ? { ...t, done: !t.done } : t))
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="销售工作台"
        description={`业绩目标: ¥${(stats.monthlyTarget / 10000).toFixed(0)}万 | 已完成: ¥${(stats.monthlyAchieved / 10000).toFixed(0)}万 (${achievementRate}%)`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              新建客户
            </Button>
            <Button className="flex items-center gap-2">
              <Target className="w-4 h-4" />
              新建商机
            </Button>
          </motion.div>
        }
      />

      {/* Stats Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Monthly Sales */}
        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">本月签约</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  ¥{(stats.monthlyAchieved / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+15%</span>
                  <span className="text-xs text-slate-500">vs 上月</span>
                </div>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div className="mt-3">
              <Progress value={parseFloat(achievementRate)} className="h-1.5" />
              <p className="text-xs text-slate-500 mt-1">目标完成率 {achievementRate}%</p>
            </div>
          </CardContent>
        </Card>

        {/* Opportunities */}
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">商机总数</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.opportunityCount}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Flame className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-amber-400">{stats.hotOpportunities}个热门商机</span>
                </div>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pending Payment */}
        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">待回款</p>
                <p className="text-2xl font-bold text-white mt-1">
                  ¥{(stats.pendingPayment / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">
                    {(stats.overduePayment / 10000).toFixed(0)}万逾期
                  </span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <Receipt className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Customers */}
        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">客户总数</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.customerCount}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Plus className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">本月新增{stats.newCustomers}</span>
                </div>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Building2 className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Funnel & Todos */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* Sales Funnel */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">销售漏斗</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <SalesFunnel
                data={funnelData || undefined}
                onStageClick={() => {
                // Handle stage click if needed
                }}
              />
            </CardContent>
          </Card>

          {/* Today's Todos - Issue 5.3: 待办事项卡片 */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">今日待办</CardTitle>
                <Badge variant="secondary">{todos.filter(t => !t.done).length}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {todos.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  暂无待办事项
                </div>
              ) : (
                todos.map((todo) => {
                  const config = todoTypeConfig[todo.type] || { icon: Clock, color: 'text-slate-400', bg: 'bg-slate-500/20' }
                  const Icon = config.icon
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
                        config.bg
                      )}>
                        <Icon className={cn('w-4 h-4', config.color)} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            'font-medium text-sm',
                            todo.done ? 'line-through text-slate-500' : 'text-white'
                          )}>
                            {todo.title}
                          </span>
                          {todo.priority === 'high' && !todo.done && (
                            <AlertTriangle className="w-3 h-3 text-red-400" />
                          )}
                        </div>
                        <span className="text-xs text-slate-400">{todo.target}</span>
                      </div>
                      <span className="text-xs text-slate-500">{todo.time}</span>
                    </motion.div>
                  )
                })
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Middle Column - Projects & Payments */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* My Projects */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">我的项目进度</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  全部项目 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {projects.map((project) => (
                <motion.div
                  key={project.id}
                  variants={fadeIn}
                  className="p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-white text-sm">{project.name}</h4>
                      <span className="text-xs text-slate-400">{project.customer}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {project.stageLabel}
                    </Badge>
                  </div>
                  
                  {/* Progress Steps */}
                  <div className="flex items-center gap-1 mb-2">
                    {['方案', '设计', '采购', '装配', '验收'].map((step, index) => {
                      const stepProgress = index * 20 + 20
                      const isActive = project.progress >= stepProgress
                      const isCurrent = project.progress >= stepProgress - 20 && project.progress < stepProgress
                      return (
                        <div key={step} className="flex items-center">
                          <div className={cn(
                            'w-2 h-2 rounded-full',
                            isActive ? 'bg-primary' : isCurrent ? 'bg-amber-500' : 'bg-slate-600'
                          )} />
                          {index < 4 && (
                            <div className={cn(
                              'w-6 h-0.5',
                              isActive ? 'bg-primary' : 'bg-slate-600'
                            )} />
                          )}
                        </div>
                      )
                    })}
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className={cn('w-2 h-2 rounded-full', healthColors[project.health])} />
                      <span className="text-slate-400">进度 {project.progress}%</span>
                    </div>
                    <span className="text-slate-400">验收: {project.acceptanceDate}</span>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* Payment Schedule */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">近期回款计划</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  全部回款 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <PaymentTimeline payments={payments} compact />
            </CardContent>
          </Card>
        </motion.div>

        {/* Right Column - Customers */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* Quick Customer List */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">重点客户</CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  客户管理 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {customers.map((customer) => (
                <CustomerCard
                  key={customer.id}
                  customer={customer}
                  compact
                  onClick={() => {
                    // Handle customer click if needed
                  }}
                />
              ))}
            </CardContent>
          </Card>

          {/* Payment Stats */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">回款概览</CardTitle>
            </CardHeader>
            <CardContent>
              <PaymentStats payments={payments} />
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">快捷操作</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-2">
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <FileText className="w-4 h-4 text-amber-400" />
                <span className="text-xs">新建报价</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <Send className="w-4 h-4 text-blue-400" />
                <span className="text-xs">发送方案</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <Receipt className="w-4 h-4 text-emerald-400" />
                <span className="text-xs">申请开票</span>
              </Button>
              <Button variant="outline" className="h-auto py-3 flex flex-col gap-1">
                <Calendar className="w-4 h-4 text-purple-400" />
                <span className="text-xs">安排拜访</span>
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  )
}
