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
import { cn } from '../lib/utils'
import { SalesFunnel, CustomerCard, OpportunityCard, PaymentTimeline, PaymentStats } from '../components/sales'
import { salesStatisticsApi, opportunityApi, customerApi, contractApi, invoiceApi, projectApi, quoteApi } from '../services/api'

// Mock data
const mockStats = {
  monthlyTarget: 1200000,
  monthlyAchieved: 856000,
  opportunityCount: 23,
  hotOpportunities: 8,
  pendingPayment: 320000,
  overduePayment: 85000,
  customerCount: 45,
  newCustomers: 5,
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
  const [stats, setStats] = useState(mockStats)
  const [customers, setCustomers] = useState([])
  const [projects, setProjects] = useState([])
  const [payments, setPayments] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load sales statistics
  const loadStatistics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Get current month date range
      const now = new Date()
      const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
      const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0]

      // Load sales summary
      const summaryResponse = await salesStatisticsApi.summary({ start_date: startDate, end_date: endDate })
      const summaryData = summaryResponse.data || {}

      // Load sales performance
      const performanceResponse = await salesStatisticsApi.performance({ start_date: startDate, end_date: endDate })
      const performanceData = performanceResponse.data || {}

      // Load funnel data
      await salesStatisticsApi.funnel({ start_date: startDate, end_date: endDate })

      // Load opportunities
      const opportunitiesResponse = await opportunityApi.list({ page: 1, page_size: 100 })
      const oppsData = opportunitiesResponse.data?.items || opportunitiesResponse.data || []

      // Calculate stats
      const monthlyTarget = 1200000 // Default target, can be configured
      const monthlyAchieved = performanceData.total_contract_amount || performanceData.paid_amount || 0
      const opportunityCount = summaryData.total_opportunities || oppsData.length
      const hotOpportunities = oppsData.filter(opp => {
        const stage = opp.stage || opp.opportunity_stage || ''
        return stage === 'QUALIFICATION' || stage === 'PROPOSAL' || stage === 'QUALIFYING'
      }).length
      
      setOpportunities(oppsData.slice(0, 5))

      // Load customers
      const customersResponse = await customerApi.list({ page: 1, page_size: 10 })
      const customersData = customersResponse.data?.items || customersResponse.data || []
      setCustomers(customersData.slice(0, 3))

      // Load projects (from contracts)
      const contractsResponse = await contractApi.list({ page: 1, page_size: 10, status: 'SIGNED' })
      const contractsData = contractsResponse.data?.items || contractsResponse.data || []
      
      // Get projects for these contracts
      const projectIds = contractsData.map(c => c.project_id).filter(Boolean)
      const projectsData = []
      for (const projectId of projectIds.slice(0, 3)) {
        try {
          const projectResponse = await projectApi.get(projectId)
          projectsData.push(projectResponse.data || projectResponse)
        } catch (err) {
          console.error(`Failed to load project ${projectId}:`, err)
        }
      }
      setProjects(projectsData)

      // Load invoices for payment tracking
      const invoicesResponse = await invoiceApi.list({ page: 1, page_size: 10 })
      const invoicesData = invoicesResponse.data?.items || invoicesResponse.data || []
      const paymentsData = invoicesData.map(inv => ({
        id: inv.id,
        type: 'progress', // Default type
        projectName: inv.project_name || '',
        amount: parseFloat(inv.amount || 0),
        dueDate: inv.due_date || '',
        paidDate: inv.paid_date || '',
        status: inv.status?.toLowerCase() || 'pending',
      }))
      setPayments(paymentsData.slice(0, 4))

      // Calculate pending and overdue payments
      const pendingPayment = paymentsData
        .filter(p => p.status === 'pending' || p.status === 'issued')
        .reduce((sum, p) => sum + p.amount, 0)
      const overduePayment = paymentsData
        .filter(p => p.status === 'overdue' || (p.dueDate && new Date(p.dueDate) < new Date() && p.status !== 'paid'))
        .reduce((sum, p) => sum + p.amount, 0)

      // Load todos (Sprint 3: Reminders)
      // TODO: Load from notifications API
      const todosData = []
      
      // Load pending approvals
      try {
        const approvalStatuses = []
        // Check quotes with pending approvals
        const quotesResponse = await quoteApi.list({ status: 'SUBMITTED', page_size: 10 })
        const quotes = quotesResponse.data?.items || quotesResponse.data || []
        for (const quote of quotes) {
          try {
            const approvalStatus = await quoteApi.getApprovalStatus(quote.id)
            if (approvalStatus?.status === 'PENDING') {
              todosData.push({
                id: `approval-quote-${quote.id}`,
                type: 'approval',
                title: `报价审批 - ${quote.quote_code}`,
                target: quote.customer?.customer_name || '',
                time: '待审批',
                priority: 'high',
                done: false,
              })
            }
          } catch (err) {
            // Ignore errors
          }
        }
      } catch (err) {
        console.error('Failed to load approval todos:', err)
      }

      // Load overdue reminders
      // TODO: Load from reminders API

      setTodos(todosData)

      setStats({
        monthlyTarget,
        monthlyAchieved,
        opportunityCount,
        hotOpportunities,
        pendingPayment,
        overduePayment,
        customerCount: summaryData.total_leads || customersData.length,
        newCustomers: customersData.filter(c => {
          const createdDate = new Date(c.created_at || c.createdAt || '')
          return createdDate >= new Date(startDate)
        }).length,
      })
    } catch (err) {
      console.error('Failed to load sales statistics:', err)
      setError(err.response?.data?.detail || err.message || '加载销售数据失败')
      // 使用默认值而不是mock数据
      setStats({
        monthlyTarget: 0,
        monthlyAchieved: 0,
        opportunityCount: 0,
        hotOpportunities: 0,
        pendingPayment: 0,
        overduePayment: 0,
        customerCount: 0,
        newCustomers: 0,
      })
    } finally {
      setLoading(false)
    }
  }, [])

  // Load data when component mounts
  useEffect(() => {
    loadStatistics()
  }, [loadStatistics])

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
              <SalesFunnel onStageClick={() => {
                // Handle stage click if needed
              }} />
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

