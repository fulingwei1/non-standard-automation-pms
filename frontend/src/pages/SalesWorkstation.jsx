/**
 * Sales Workstation - Main dashboard for sales engineers
 * Features: Performance metrics, Sales funnel, Todo list, Project tracking, Payment schedule
 */

import { useState, useMemo } from 'react'
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
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { SalesFunnel, CustomerCard, OpportunityCard, PaymentTimeline, PaymentStats } from '../components/sales'

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

const mockTodos = [
  { id: 1, type: 'follow', title: '跟进客户', target: '深圳XX科技', time: '10:00', priority: 'high', done: false },
  { id: 2, type: 'quote', title: '报价回复', target: 'BMS测试设备', time: '14:00', priority: 'high', done: false },
  { id: 3, type: 'payment', title: '催收提醒', target: 'EOL项目尾款', time: '15:00', priority: 'medium', done: false },
  { id: 4, type: 'visit', title: '拜访安排', target: '东莞XX电子', time: '明天', priority: 'medium', done: false },
  { id: 5, type: 'acceptance', title: '验收协调', target: 'ICT设备FAT', time: '01-08', priority: 'high', done: false },
]

const mockProjects = [
  {
    id: 'PJ250108001',
    name: 'BMS老化测试设备',
    customer: '深圳XX科技',
    stage: 'design',
    stageLabel: '设计',
    progress: 45,
    acceptanceDate: '2026-02-15',
    amount: 850000,
    health: 'good',
  },
  {
    id: 'PJ250106002',
    name: 'EOL功能测试设备',
    customer: '东莞XX电子',
    stage: 'assembly',
    stageLabel: '装配',
    progress: 78,
    acceptanceDate: '2026-01-20',
    amount: 620000,
    health: 'warning',
  },
  {
    id: 'PJ250103003',
    name: 'ICT在线测试设备',
    customer: '惠州XX电池',
    stage: 'solution',
    stageLabel: '方案',
    progress: 25,
    acceptanceDate: '2026-03-01',
    amount: 450000,
    health: 'good',
  },
]

const mockPayments = [
  { id: 1, type: 'progress', projectName: 'EOL项目进度款', amount: 150000, dueDate: '2026-01-08', status: 'pending' },
  { id: 2, type: 'deposit', projectName: 'BMS项目签约款', amount: 200000, dueDate: '2026-01-15', paidDate: '2026-01-05', status: 'paid' },
  { id: 3, type: 'acceptance', projectName: 'ICT项目验收款', amount: 180000, dueDate: '2026-01-20', status: 'pending' },
  { id: 4, type: 'warranty', projectName: '旧设备质保金', amount: 50000, dueDate: '2025-12-30', status: 'overdue' },
]

const mockCustomers = [
  {
    id: 1,
    name: '深圳XX科技有限公司',
    shortName: '深圳XX科技',
    grade: 'A',
    status: 'active',
    industry: '新能源电池',
    location: '深圳',
    lastContact: '2天前',
    opportunityCount: 3,
    totalAmount: 2500000,
  },
  {
    id: 2,
    name: '东莞XX电子有限公司',
    shortName: '东莞XX电子',
    grade: 'B',
    status: 'active',
    industry: '消费电子',
    location: '东莞',
    lastContact: '1周前',
    opportunityCount: 1,
    totalAmount: 1200000,
    isWarning: true,
  },
  {
    id: 3,
    name: '惠州XX电池科技',
    shortName: '惠州XX电池',
    grade: 'B',
    status: 'potential',
    industry: '储能系统',
    location: '惠州',
    lastContact: '3天前',
    opportunityCount: 2,
    totalAmount: 800000,
  },
]

const todoTypeConfig = {
  follow: { icon: Phone, color: 'text-blue-400', bg: 'bg-blue-500/20' },
  quote: { icon: FileText, color: 'text-amber-400', bg: 'bg-amber-500/20' },
  payment: { icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
  visit: { icon: Building2, color: 'text-purple-400', bg: 'bg-purple-500/20' },
  acceptance: { icon: CheckCircle2, color: 'text-pink-400', bg: 'bg-pink-500/20' },
}

const healthColors = {
  good: 'bg-emerald-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500',
}

export default function SalesWorkstation() {
  const [activeTab, setActiveTab] = useState('overview')
  const [todos, setTodos] = useState(mockTodos)

  const achievementRate = (mockStats.monthlyAchieved / mockStats.monthlyTarget * 100).toFixed(1)

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
        description={`业绩目标: ¥${(mockStats.monthlyTarget / 10000).toFixed(0)}万 | 已完成: ¥${(mockStats.monthlyAchieved / 10000).toFixed(0)}万 (${achievementRate}%)`}
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
                  ¥{(mockStats.monthlyAchieved / 10000).toFixed(0)}万
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
                <p className="text-2xl font-bold text-white mt-1">{mockStats.opportunityCount}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Flame className="w-3 h-3 text-amber-500" />
                  <span className="text-xs text-amber-400">{mockStats.hotOpportunities}个热门商机</span>
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
                  ¥{(mockStats.pendingPayment / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">
                    {(mockStats.overduePayment / 10000).toFixed(0)}万逾期
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
                <p className="text-2xl font-bold text-white mt-1">{mockStats.customerCount}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Plus className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">本月新增{mockStats.newCustomers}</span>
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
              <SalesFunnel onStageClick={(stage) => console.log('Stage clicked:', stage)} />
            </CardContent>
          </Card>

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
                        {todo.priority === 'high' && !todo.done && (
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
              {mockProjects.map((project) => (
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
              <PaymentTimeline payments={mockPayments} compact />
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
              {mockCustomers.map((customer) => (
                <CustomerCard
                  key={customer.id}
                  customer={customer}
                  compact
                  onClick={(c) => console.log('Customer clicked:', c)}
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
              <PaymentStats payments={mockPayments} />
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

