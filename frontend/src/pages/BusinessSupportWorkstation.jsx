/**
 * Business Support Workstation - Professional demonstration page
 * Features: Contract management, Document processing, Payment tracking, Tender management
 * Core Functions: Customer filing, Bidding, Contract review, Order processing, Invoice management,
 * Payment collection, Acceptance management, Report statistics, Document archiving
 * 
 * Design: Following the Business Support Module UI/UX Design Guide
 * Version: v1.0
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  DollarSign,
  Briefcase,
  User,
  Building2,
  TrendingUp,
  Send,
  Plus,
  ChevronRight,
  Search,
  Filter,
  Download,
  Phone,
  Mail,
  Calendar,
  Target,
  Package,
  Receipt,
  BarChart3,
  Zap,
  Layers,
  Shield,
  Eye,
  Edit,
  MoreVertical,
  Flag,
  Inbox,
  Archive,
  FileCheck,
  Calculator,
  CreditCard,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { businessSupportApi } from '../services/api'

// Statistics configuration - will be populated from API
const getStatConfig = (dashboardData) => ({
  activeContracts: {
    label: '进行中合同',
    value: dashboardData.active_contracts_count || 0,
    unit: '个',
    icon: Briefcase,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  pendingAmount: {
    label: '待回款金额',
    value: dashboardData.pending_amount || 0,
    unit: '元',
    icon: DollarSign,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    format: 'currency',
  },
  overdueAmount: {
    label: '逾期款项',
    value: dashboardData.overdue_amount || 0,
    unit: '元',
    icon: AlertTriangle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    format: 'currency',
  },
  invoiceRate: {
    label: '本月开票率',
    value: Math.round(dashboardData.invoice_rate || 0),
    unit: '%',
    icon: Receipt,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  bidCount: {
    label: '进行中投标',
    value: dashboardData.active_bidding_count || 0,
    unit: '个',
    icon: Target,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
  },
  acceptanceRate: {
    label: '验收按期率',
    value: Math.round(dashboardData.acceptance_rate || 0),
    unit: '%',
    icon: CheckCircle2,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
  },
})

// Task priority colors
const priorityColors = {
  high: { bg: 'bg-red-500/20', text: 'text-red-400', label: '紧急' },
  medium: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '中等' },
  low: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: '普通' },
}

// Task type configuration
const taskTypeConfig = {
  contract: { icon: FileText, label: '合同', color: 'text-blue-400' },
  bidding: { icon: Target, label: '投标', color: 'text-purple-400' },
  invoice: { icon: Receipt, label: '开票', color: 'text-amber-400' },
  payment: { icon: DollarSign, label: '催款', color: 'text-red-400' },
  acceptance: { icon: CheckCircle2, label: '验收', color: 'text-emerald-400' },
  shipping: { icon: Package, label: '出货', color: 'text-cyan-400' },
  document: { icon: Archive, label: '归档', color: 'text-slate-400' },
  customer: { icon: Building2, label: '客户', color: 'text-indigo-400' },
}

// Mock data for todos
const mockTodos = [
  {
    id: 1,
    type: 'contract',
    title: '合同审核待签',
    target: '深圳XX科技 - BMS测试设备',
    deadline: '2025-01-05',
    daysLeft: 0,
    priority: 'high',
    status: 'pending',
  },
  {
    id: 2,
    type: 'invoice',
    title: '开票申请待提交',
    target: '东莞精密 - EOL设备进度款',
    deadline: '2025-01-06',
    daysLeft: 1,
    priority: 'high',
    status: 'pending',
  },
  {
    id: 3,
    type: 'payment',
    title: '催款跟进',
    target: 'ICT设备预付款 - 惠州XX电池',
    deadline: '2025-01-07',
    daysLeft: 2,
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 4,
    type: 'acceptance',
    title: '验收单跟踪',
    target: 'FAT报告签章待补',
    deadline: '2025-01-08',
    daysLeft: 3,
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 5,
    type: 'bidding',
    title: '标书编制上传',
    target: '某客户线体改造项目',
    deadline: '2025-01-08',
    daysLeft: 3,
    priority: 'high',
    status: 'pending',
  },
  {
    id: 6,
    type: 'shipping',
    title: '出货审批',
    target: 'BMS测试设备 - 发货单核对',
    deadline: '2025-01-10',
    daysLeft: 5,
    priority: 'low',
    status: 'pending',
  },
  {
    id: 7,
    type: 'customer',
    title: '客户入驻资料补充',
    target: '新客户供应商平台入驻',
    deadline: '2025-01-12',
    daysLeft: 7,
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 8,
    type: 'document',
    title: '文件归档整理',
    target: '2024年验收报告汇总',
    deadline: '2025-01-15',
    daysLeft: 10,
    priority: 'low',
    status: 'pending',
  },
]

// Mock data for active contracts
const mockContracts = [
  {
    id: 'HT2026-001',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    customerName: '深圳XX科技',
    contractAmount: 850000,
    signedDate: '2025-11-20',
    dueDate: '2026-02-15',
    paidAmount: 255000,
    paymentProgress: 30,
    paymentStages: [
      { type: '签约款', amount: 255000, status: 'paid', date: '2025-11-25' },
      { type: '进度款', amount: 340000, status: 'pending', dueDate: '2026-01-20' },
      { type: '验收款', amount: 170000, status: 'pending', dueDate: '2026-02-15' },
      { type: '质保金', amount: 85000, status: 'pending', dueDate: '2026-02-20' },
    ],
    invoiceStatus: 'partial', // partial | complete
    invoiceCount: 1,
    acceptanceStatus: 'in_progress', // pending | in_progress | completed
    health: 'good',
  },
  {
    id: 'HT2025-012',
    projectId: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    customerName: '东莞精密电子',
    contractAmount: 620000,
    signedDate: '2025-10-15',
    dueDate: '2026-01-20',
    paidAmount: 186000,
    paymentProgress: 30,
    paymentStages: [
      { type: '签约款', amount: 186000, status: 'paid', date: '2025-10-20' },
      { type: '进度款', amount: 248000, status: 'pending', dueDate: '2026-01-10' },
      { type: '验收款', amount: 124000, status: 'pending', dueDate: '2026-01-20' },
      { type: '质保金', amount: 62000, status: 'pending', dueDate: '2026-01-25' },
    ],
    invoiceStatus: 'partial',
    invoiceCount: 1,
    acceptanceStatus: 'in_progress',
    health: 'warning',
  },
  {
    id: 'HT2025-008',
    projectId: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    customerName: '惠州XX电池',
    contractAmount: 450000,
    signedDate: '2025-09-10',
    dueDate: '2026-03-01',
    paidAmount: 135000,
    paymentProgress: 30,
    paymentStages: [
      { type: '签约款', amount: 135000, status: 'paid', date: '2025-09-15' },
      { type: '进度款', amount: 180000, status: 'pending', dueDate: '2026-01-15' },
      { type: '验收款', amount: 90000, status: 'pending', dueDate: '2026-03-01' },
      { type: '质保金', amount: 45000, status: 'pending', dueDate: '2026-03-05' },
    ],
    invoiceStatus: 'complete',
    invoiceCount: 2,
    acceptanceStatus: 'pending',
    health: 'good',
  },
]

// Mock data for bidding projects
const mockBidding = [
  {
    id: 'BID-2025-0001',
    projectName: '某大型汽车电池测试线体',
    customerName: '某汽车供应商',
    bidAmount: 2500000,
    bidDeadline: '2025-01-10',
    daysLeft: 5,
    status: 'bidding_phase', // inquiry | bidding_phase | technical_evaluation | commercial_evaluation | won | lost
    documentStatus: 'draft', // draft | review | submitted
    progress: 60,
  },
  {
    id: 'BID-2025-0002',
    projectName: 'ICT自动化升级项目',
    customerName: '某电子制造商',
    bidAmount: 1800000,
    bidDeadline: '2025-01-15',
    daysLeft: 10,
    status: 'technical_evaluation',
    documentStatus: 'submitted',
    progress: 75,
  },
  {
    id: 'BID-2025-0003',
    projectName: 'AOI视觉检测系统',
    customerName: '某LED生产商',
    bidAmount: 950000,
    bidDeadline: '2025-01-20',
    daysLeft: 15,
    status: 'bidding_phase',
    documentStatus: 'review',
    progress: 45,
  },
]

// Helper functions
const formatCurrency = (value) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const getDaysColor = (daysLeft) => {
  if (daysLeft === 0) return 'text-red-400'
  if (daysLeft <= 2) return 'text-orange-400'
  if (daysLeft <= 7) return 'text-amber-400'
  return 'text-cyan-400'
}

const StatCard = ({ config, value }) => {
  const Icon = config.icon
  const isValueCurrency = config.format === 'currency'
  
  // Format currency with simplified display for large amounts
  let displayValue = value
  if (isValueCurrency) {
    if (value >= 10000) {
      displayValue = `¥${(value / 10000).toFixed(0)}万`
    } else {
      displayValue = formatCurrency(value)
    }
  }

  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
      style={{ height: '140px' }}
    >
      <div className="flex items-start justify-between h-full">
        <div className="flex-1 flex flex-col justify-between">
          <p className="text-sm font-normal text-slate-400 mb-2">{config.label}</p>
          <div>
            <p className={cn('text-2xl font-bold mb-1', config.color)}>{displayValue}</p>
            {!isValueCurrency && (
              <p className="text-xs font-normal text-slate-500">{config.unit}</p>
            )}
          </div>
        </div>
        <div className={cn('rounded-lg p-3 bg-opacity-20', config.bg)}>
          <Icon className={cn('h-6 w-6', config.color)} />
        </div>
      </div>
      {/* Background glow effect */}
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  )
}

const TodoItem = ({ todo, onComplete }) => {
  const typeConfig = taskTypeConfig[todo.type]
  const priorityConfig = priorityColors[todo.priority]
  const Icon = typeConfig.icon

  return (
    <motion.div
      variants={fadeIn}
      className="group flex items-start gap-3 rounded-lg border border-slate-700/50 bg-slate-800/40 p-4 transition-all hover:border-slate-600/80 hover:bg-slate-800/60"
    >
      <div className="relative mt-1 flex-shrink-0">
        <div className={cn('rounded-lg p-2', priorityConfig.bg)}>
          <Icon className={cn('h-5 w-5', typeConfig.color)} />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <p className="font-medium text-slate-200">{todo.title}</p>
            <p className="mt-1 text-sm text-slate-400">{todo.target}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="bg-slate-700/40 text-xs">
                {typeConfig.label}
              </Badge>
              <Badge className={cn('text-xs', priorityConfig.bg, priorityConfig.text)}>
                {priorityConfig.label}
              </Badge>
              {todo.daysLeft === 0 ? (
                <span className="text-xs font-medium text-red-400">今天截止</span>
              ) : (
                <span className={cn('text-xs font-medium', getDaysColor(todo.daysLeft))}>
                  {todo.daysLeft}天截止
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          size="sm"
          variant="ghost"
          className="h-8 w-8 p-0"
          onClick={() => onComplete(todo.id)}
        >
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        </Button>
      </div>
    </motion.div>
  )
}

const ContractCard = ({ contract }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="group overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600 hover:shadow-lg cursor-pointer"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-start gap-2">
            <div className="mt-1 rounded-lg bg-blue-500/20 p-2">
              <Briefcase className="h-4 w-4 text-blue-400" />
            </div>
            <div className="flex-1">
              <p className="font-semibold text-slate-100">{contract.projectName}</p>
              <p className="text-sm text-slate-400">{contract.customerName}</p>
              <p className="mt-1 text-xs text-slate-500">{contract.id}</p>
            </div>
          </div>
        </div>
        <div className="flex-shrink-0 text-right">
          <p className="text-lg font-bold text-amber-400">
            {formatCurrency(contract.contractAmount)}
          </p>
          <p className="text-xs text-slate-400">合同金额</p>
        </div>
      </div>

      {/* Payment progress */}
      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">回款进度:</span>
          <span className="text-sm font-medium text-slate-300">
            {contract.paidAmount >= 10000 
              ? `¥${(contract.paidAmount / 10000).toFixed(1)}万` 
              : formatCurrency(contract.paidAmount)} / {contract.contractAmount >= 10000
              ? `¥${(contract.contractAmount / 10000).toFixed(1)}万`
              : formatCurrency(contract.contractAmount)}
          </span>
        </div>
        <Progress
          value={contract.paymentProgress}
          className="h-2 bg-slate-700/50"
        />
      </div>

      {/* Payment stages */}
      <div className="mt-3 space-y-1.5">
        <p className="text-xs text-slate-400 mb-2">支付阶段:</p>
        {contract.paymentStages.map((stage, idx) => (
          <div key={idx} className="flex items-center justify-between text-xs">
            <span className="text-slate-400">└─ {stage.type}</span>
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-300">
                {stage.amount >= 10000 
                  ? `¥${(stage.amount / 10000).toFixed(1)}万`
                  : formatCurrency(stage.amount)}
              </span>
              <Badge
                variant="outline"
                className={cn(
                  'text-xs',
                  stage.status === 'paid'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : 'bg-slate-700/40 text-slate-400 border-slate-600/30'
                )}
              >
                {stage.status === 'paid' ? '已到账' : '待回款'}
              </Badge>
            </div>
          </div>
        ))}
      </div>

      {/* Status indicators */}
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge
          variant="outline"
          className={cn(
            'text-xs',
            contract.invoiceStatus === 'complete'
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
          )}
        >
          <Receipt className="mr-1 h-3 w-3" />
          发票: {contract.invoiceCount}张
        </Badge>
        <Badge
          variant="outline"
          className={cn(
            'text-xs',
            contract.acceptanceStatus === 'completed'
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : contract.acceptanceStatus === 'in_progress'
              ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
              : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
          )}
        >
          <CheckCircle2 className="mr-1 h-3 w-3" />
          验收: {contract.acceptanceStatus === 'completed' ? '已完成' : contract.acceptanceStatus === 'in_progress' ? '进行中' : '待开始'}
        </Badge>
      </div>
    </motion.div>
  )
}

const BiddingCard = ({ bid }) => {
  const statusMap = {
    inquiry: '询价阶段',
    bidding_phase: '投标中',
    technical_evaluation: '技术评标',
    commercial_evaluation: '商务评标',
    won: '中标',
    lost: '未中标',
  }

  const documentStatusMap = {
    draft: '编制中',
    review: '审核中',
    submitted: '已提交',
  }

  return (
    <motion.div
      variants={fadeIn}
      className="group overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-4 backdrop-blur transition-all hover:border-slate-600 hover:shadow-lg cursor-pointer"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="font-semibold text-slate-100">{bid.projectName}</p>
          <p className="mt-1 text-sm text-slate-400">{bid.customerName}</p>
          <p className="mt-2 text-lg font-bold text-purple-400">
            {bid.bidAmount >= 10000 
              ? `¥${(bid.bidAmount / 10000).toFixed(0)}万`
              : formatCurrency(bid.bidAmount)}
          </p>
        </div>
        <div className="flex-shrink-0 text-right">
          <Badge
            variant="outline"
            className={cn(
              'text-xs mb-2 block',
              bid.status === 'won'
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : bid.status === 'technical_evaluation' || bid.status === 'commercial_evaluation'
                ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
            )}
          >
            {statusMap[bid.status]}
          </Badge>
          <Badge 
            variant="outline" 
            className="block text-xs bg-slate-700/40 text-slate-400 border-slate-600/30"
          >
            {documentStatusMap[bid.documentStatus]}
          </Badge>
        </div>
      </div>

      {/* Progress */}
      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">标书进度</span>
          <span className="text-xs font-medium text-slate-300">{bid.progress}%</span>
        </div>
        <Progress value={bid.progress} className="h-2 bg-slate-700/50" />
      </div>

      {/* Deadline */}
      <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
        <Calendar className="h-3 w-3" />
        <span>
          📅 截止日期:{' '}
          <span className={cn('font-medium', getDaysColor(bid.daysLeft))}>
            {bid.daysLeft}天后
          </span>
        </span>
      </div>
    </motion.div>
  )
}

export default function BusinessSupportWorkstation() {
  const [completedTodos, setCompletedTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Dashboard data state
  const [dashboardData, setDashboardData] = useState({
    active_contracts_count: 0,
    pending_amount: 0,
    overdue_amount: 0,
    invoice_rate: 0,
    active_bidding_count: 0,
    acceptance_rate: 0,
    urgent_tasks: [],
    today_todos: [],
  })

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await businessSupportApi.dashboard()
      const data = response.data?.data || response.data || {}
      
      setDashboardData({
        active_contracts_count: data.active_contracts_count || 0,
        pending_amount: parseFloat(data.pending_amount || 0),
        overdue_amount: parseFloat(data.overdue_amount || 0),
        invoice_rate: parseFloat(data.invoice_rate || 0),
        active_bidding_count: data.active_bidding_count || 0,
        acceptance_rate: parseFloat(data.acceptance_rate || 0),
        urgent_tasks: data.urgent_tasks || [],
        today_todos: data.today_todos || [],
      })
    } catch (err) {
      console.error('Failed to load dashboard:', err)
      setError(err.response?.data?.detail || err.message || '加载工作台数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // Load dashboard when component mounts
  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  const handleCompleteTodo = (todoId) => {
    setCompletedTodos([...completedTodos, todoId])
  }

  // Use API data instead of mock data
  const urgentTodos = (dashboardData.urgent_tasks || []).filter(
    (todo) => {
      const daysLeft = todo.daysLeft !== null && todo.daysLeft !== undefined ? todo.daysLeft : 999
      return daysLeft <= 3 && !completedTodos.includes(todo.id)
    }
  )
  const allTodos = (dashboardData.today_todos || []).filter((todo) => !completedTodos.includes(todo.id))

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="商务支持工作台"
        description="合同管理、单据处理、回款跟踪、投标支持"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建合同
            </Button>
          </motion.div>
        }
      />

      {/* Key statistics - 6 column grid */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="bg-surface-1/50 animate-pulse">
              <CardContent className="p-4">
                <div className="h-20 bg-slate-700/50 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="bg-red-500/10 border-red-500/30">
          <CardContent className="p-4">
            <p className="text-red-400 text-sm">{error}</p>
          </CardContent>
        </Card>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
        >
          {Object.entries(getStatConfig(dashboardData)).map(([key, config]) => (
            <StatCard
              key={key}
              config={config}
              value={config.value}
            />
          ))}
        </motion.div>
      )}

      {/* Main content - two column layout (2/3 + 1/3) */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left column - Todos and Tasks (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Urgent tasks panel */}
          {urgentTodos.length > 0 && (
            <motion.div variants={fadeIn}>
              <Card className="border-red-500/30 bg-gradient-to-br from-red-500/10 via-red-500/5 to-slate-900/50">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Zap className="h-5 w-5 text-red-400" />
                      紧急任务提醒
                    </CardTitle>
                    <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                      {urgentTodos.length} 项
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="space-y-3"
                  >
                    {urgentTodos.slice(0, 3).map((todo) => (
                      <TodoItem
                        key={todo.id}
                        todo={todo}
                        onComplete={handleCompleteTodo}
                      />
                    ))}
                  </motion.div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* All todos - Today's work list */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Inbox className="h-5 w-5 text-slate-400" />
                    今日工作清单
                  </CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    {allTodos.length} / {mockTodos.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <motion.div
                  variants={staggerContainer}
                  initial="hidden"
                  animate="visible"
                  className="space-y-3"
                >
                  {allTodos.length > 0 ? (
                    allTodos.map((todo) => (
                      <TodoItem
                        key={todo.id}
                        todo={todo}
                        onComplete={handleCompleteTodo}
                      />
                    ))
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500/50" />
                      <p className="text-sm">所有任务已完成！</p>
                    </div>
                  )}
                </motion.div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right column - Quick actions & Stats (1/3 width) */}
        <div className="space-y-6">
          {/* Quick actions menu */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-base">快捷操作菜单</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                {[
                  { icon: Plus, label: '新建合同', color: 'text-blue-400', bg: 'bg-blue-500/10' },
                  { icon: FileCheck, label: '合同审核', color: 'text-slate-400', bg: 'bg-slate-500/10' },
                  { icon: Receipt, label: '申请开票', color: 'text-amber-400', bg: 'bg-amber-500/10' },
                  { icon: Package, label: '出货审批', color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
                  { icon: Target, label: '投标管理', color: 'text-purple-400', bg: 'bg-purple-500/10' },
                  { icon: DollarSign, label: '催款跟进', color: 'text-red-400', bg: 'bg-red-500/10' },
                  { icon: Building2, label: '客户管理', color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
                  { icon: Archive, label: '文件归档', color: 'text-slate-500', bg: 'bg-slate-500/10' },
                ].map((item, idx) => (
                  <Button
                    key={idx}
                    variant="ghost"
                    className="w-full justify-start gap-3 text-slate-400 hover:bg-slate-800/60 hover:text-slate-100 transition-colors"
                  >
                    <div className={cn('p-1.5 rounded', item.bg)}>
                      <item.icon className={cn('h-4 w-4', item.color)} />
                    </div>
                    <span>{item.label}</span>
                  </Button>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Performance metrics */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-base">本月绩效指标</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {[
                  { label: '新签合同', value: 3, unit: '份', color: 'text-blue-400', progress: 75 },
                  { label: '回款完成率', value: 78, unit: '%', color: 'text-emerald-400', progress: 78 },
                  { label: '开票及时率', value: 92, unit: '%', color: 'text-purple-400', progress: 92 },
                  { label: '文件流转', value: 28, unit: '份', color: 'text-amber-400', progress: 70 },
                ].map((metric, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{metric.label}</span>
                      <span className={cn('font-semibold', metric.color)}>
                        {metric.value}{metric.unit}
                      </span>
                    </div>
                    <Progress
                      value={metric.progress}
                      className="h-1.5 bg-slate-700/50"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Support team */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-base">技术支持</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-slate-400 hover:bg-slate-800/60 hover:text-slate-100 transition-colors"
                >
                  <Phone className="h-4 w-4 text-cyan-400" />
                  <span className="flex-1 text-left">联系IT支持</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-slate-400 hover:bg-slate-800/60 hover:text-slate-100 transition-colors"
                >
                  <FileText className="h-4 w-4 text-blue-400" />
                  <span className="flex-1 text-left">查看文档库</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3 text-slate-400 hover:bg-slate-800/60 hover:text-slate-100 transition-colors"
                >
                  <BarChart3 className="h-4 w-4 text-purple-400" />
                  <span className="flex-1 text-left">系统报表</span>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Active contracts section */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-5 w-5 text-blue-400" />
              进行中的合同
            </CardTitle>
          </CardHeader>
          <CardContent>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              {mockContracts.map((contract) => (
                <ContractCard key={contract.id} contract={contract} />
              ))}
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Bidding projects section */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Target className="h-5 w-5 text-purple-400" />
                进行中的投标
              </CardTitle>
              <Badge variant="outline" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                {mockBidding.length} 个项目
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              {mockBidding.map((bid) => (
                <BiddingCard key={bid.id} bid={bid} />
              ))}
            </motion.div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
