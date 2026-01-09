/**
 * 售前技术工程师工作台
 * 核心入口页面，展示技术支持任务、方案进度、投标项目等
 */
import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  LayoutDashboard,
  ListTodo,
  FileText,
  Target,
  BookOpen,
  Clock,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Users,
  Calendar,
  ChevronRight,
  Plus,
  Upload,
  Search,
  Building2,
  Briefcase,
  FileCheck,
  Timer,
  Zap,
  MessageSquare,
  ClipboardList,
  Flag,
  ArrowUpRight,
  DollarSign,
  Calculator,
  X,
  Lightbulb,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { fadeIn, staggerContainer } from '../lib/animations'
import { cn } from '../lib/utils'
import CostEstimateForm from '../components/presales/CostEstimateForm'
import FeasibilityAssessmentForm from '../components/presales/FeasibilityAssessmentForm'
import { presaleApi, opportunityApi } from '../services/api'

// Mock 数据 - 统计卡片
const statsData = [
  {
    id: 1,
    title: '本周任务',
    value: '12',
    subtitle: '待处理 5',
    icon: ListTodo,
    color: 'text-blue-400',
    bgColor: 'bg-blue-400/10',
    trend: '+3',
  },
  {
    id: 2,
    title: '进行中方案',
    value: '8',
    subtitle: '待评审 3',
    icon: FileText,
    color: 'text-violet-400',
    bgColor: 'bg-violet-400/10',
    trend: '+2',
  },
  {
    id: 3,
    title: '投标项目',
    value: '4',
    subtitle: '本月截止 2',
    icon: Target,
    color: 'text-amber-400',
    bgColor: 'bg-amber-400/10',
    trend: null,
  },
  {
    id: 4,
    title: '预计产出',
    value: '¥386万',
    subtitle: '按方案金额',
    icon: DollarSign,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
    trend: '+15%',
  },
]

// Mock 数据 - 待办任务
const todoTasks = [
  {
    id: 1,
    title: '深圳XX科技 - 电池Pack测试线方案',
    type: '方案设计',
    typeColor: 'bg-violet-500',
    source: '销售：张销售',
    deadline: '2026-01-08',
    priority: 'high',
    customer: '深圳XX科技',
  },
  {
    id: 6,
    title: '电池Pack自动化测试线成本核算',
    type: '成本核算',
    typeColor: 'bg-emerald-500',
    source: '方案评审后',
    deadline: '2026-01-09',
    priority: 'high',
    customer: '深圳XX科技',
    biddingId: null,
  },
  {
    id: 7,
    title: '广州汽车 - 零部件检测设备成本估算',
    type: '成本支持',
    typeColor: 'bg-amber-500',
    source: '投标项目：BID-2026-001',
    deadline: '2026-01-12',
    priority: 'high',
    customer: '广州汽车',
    biddingId: 1,
    requestedBy: '李销售',
    requestedAt: '2026-01-05',
  },
  {
    id: 8,
    title: '惠州储能 - ICT测试设备可行性评估',
    type: '可行性评估',
    typeColor: 'bg-cyan-500',
    source: '商机：OPP003',
    deadline: '2026-01-08',
    priority: 'high',
    customer: '惠州储能',
    opportunityId: 'OPP003',
    requestedBy: '张销售',
    requestedAt: '2026-01-02',
  },
  {
    id: 2,
    title: '东莞精密 - EOL测试设备技术交流',
    type: '技术交流',
    typeColor: 'bg-blue-500',
    source: '销售：李销售',
    deadline: '2026-01-06',
    priority: 'high',
    customer: '东莞精密',
  },
  {
    id: 3,
    title: '惠州储能 - ICT测试设备需求调研',
    type: '需求调研',
    typeColor: 'bg-emerald-500',
    source: '销售：张销售',
    deadline: '2026-01-10',
    priority: 'medium',
    customer: '惠州储能',
  },
  {
    id: 4,
    title: '广州汽车 - 烧录设备投标技术标书',
    type: '投标支持',
    typeColor: 'bg-amber-500',
    source: '投标项目',
    deadline: '2026-01-15',
    priority: 'medium',
    customer: '广州汽车',
  },
  {
    id: 5,
    title: 'BMS老化设备方案内部评审',
    type: '方案评审',
    typeColor: 'bg-pink-500',
    source: '内部流程',
    deadline: '2026-01-07',
    priority: 'low',
    customer: '深圳XX科技',
  },
]

// Mock 数据 - 进行中方案
const ongoingSolutions = [
  {
    id: 1,
    name: 'BMS老化测试设备技术方案',
    customer: '深圳XX科技',
    version: 'V1.2',
    status: '评审中',
    statusColor: 'bg-amber-500',
    progress: 85,
    deadline: '2026-01-10',
    amount: 85,
    deviceType: '老化设备',
  },
  {
    id: 2,
    name: '电池Pack自动化测试线方案',
    customer: '深圳XX科技',
    version: 'V0.9',
    status: '编写中',
    statusColor: 'bg-blue-500',
    progress: 60,
    deadline: '2026-01-15',
    amount: 220,
    deviceType: '测试线',
  },
  {
    id: 3,
    name: 'EOL功能测试设备方案',
    customer: '东莞精密',
    version: 'V1.0',
    status: '已发布',
    statusColor: 'bg-emerald-500',
    progress: 100,
    deadline: '2026-01-05',
    amount: 65,
    deviceType: 'EOL测试',
  },
]

// Mock 数据 - 近期投标
const upcomingBids = [
  {
    id: 1,
    name: '广州汽车零部件检测设备采购',
    customer: '广州汽车',
    deadline: '2026-01-15',
    daysLeft: 11,
    status: '准备中',
    statusColor: 'bg-blue-500',
    amount: 120,
    competitors: ['竞争对手A', '竞争对手B'],
  },
  {
    id: 2,
    name: '中山电子充电桩测试设备招标',
    customer: '中山电子',
    deadline: '2026-01-20',
    daysLeft: 16,
    status: '跟踪中',
    statusColor: 'bg-slate-500',
    amount: 80,
    competitors: ['竞争对手C'],
  },
  {
    id: 3,
    name: '佛山智能视觉检测系统采购',
    customer: '佛山智能',
    deadline: '2026-01-25',
    daysLeft: 21,
    status: '准备中',
    statusColor: 'bg-blue-500',
    amount: 95,
    competitors: [],
  },
]

// Mock 数据 - 关联商机
const linkedOpportunities = [
  {
    id: 1,
    name: 'BMS老化测试设备',
    customer: '深圳XX科技',
    salesPerson: '张销售',
    stage: '报价阶段',
    stageColor: 'bg-purple-500',
    amount: 85,
    winRate: 60,
  },
  {
    id: 2,
    name: '电池Pack测试线',
    customer: '深圳XX科技',
    salesPerson: '张销售',
    stage: '意向洽谈',
    stageColor: 'bg-blue-500',
    amount: 220,
    winRate: 35,
  },
  {
    id: 3,
    name: 'EOL功能测试设备',
    customer: '东莞精密',
    salesPerson: '李销售',
    stage: '合同谈判',
    stageColor: 'bg-amber-500',
    amount: 120,
    winRate: 80,
  },
]

// 快捷操作配置
const quickActions = [
  { name: '新建方案', icon: FileText, path: '/solutions', color: 'from-violet-500 to-purple-600' },
  { name: '新建调研', icon: ClipboardList, path: '/requirement-survey', color: 'from-emerald-500 to-teal-600' },
  { name: '上传文档', icon: Upload, path: '#', color: 'from-blue-500 to-cyan-600' },
  { name: '知识库', icon: BookOpen, path: '/knowledge-base', color: 'from-amber-500 to-orange-600' },
]

// 获取优先级样式
const getPriorityStyle = (priority) => {
  switch (priority) {
    case 'high':
      return 'text-red-400 bg-red-500/10'
    case 'medium':
      return 'text-amber-400 bg-amber-500/10'
    case 'low':
      return 'text-slate-400 bg-slate-500/10'
    default:
      return 'text-slate-400 bg-slate-500/10'
  }
}

// 获取优先级文本
const getPriorityText = (priority) => {
  switch (priority) {
    case 'high':
      return '紧急'
    case 'medium':
      return '中等'
    case 'low':
      return '普通'
    default:
      return '普通'
  }
}

// 获取任务类型颜色
const getTypeColor = (type) => {
  const colorMap = {
    '方案设计': 'bg-violet-500',
    '成本核算': 'bg-emerald-500',
    '成本支持': 'bg-emerald-500',
    '技术交流': 'bg-blue-500',
    '需求调研': 'bg-emerald-500',
    '投标支持': 'bg-amber-500',
    '方案评审': 'bg-pink-500',
    '可行性评估': 'bg-cyan-500',
  }
  return colorMap[type] || 'bg-slate-500'
}

export default function PresalesWorkstation() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(statsData)
  const [todoTasks, setTodoTasks] = useState([])
  const [ongoingSolutions, setOngoingSolutions] = useState([])
  const [recentTenders, setRecentTenders] = useState([])
  const [relatedOpportunities, setRelatedOpportunities] = useState([])
  const [selectedCostTask, setSelectedCostTask] = useState(null)
  const [showCostForm, setShowCostForm] = useState(false)
  const [selectedFeasibilityTask, setSelectedFeasibilityTask] = useState(null)
  const [showFeasibilityForm, setShowFeasibilityForm] = useState(false)

  // Map backend ticket type to frontend type
  const mapTicketType = (backendType) => {
    const typeMap = {
      'SOLUTION_DESIGN': '方案设计',
      'COST_ESTIMATE': '成本核算',
      'COST_SUPPORT': '成本支持',
      'TECHNICAL_EXCHANGE': '技术交流',
      'REQUIREMENT_RESEARCH': '需求调研',
      'TENDER_SUPPORT': '投标支持',
      'SOLUTION_REVIEW': '方案评审',
      'FEASIBILITY_ASSESSMENT': '可行性评估',
    }
    return typeMap[backendType] || backendType
  }

  // Map backend status to frontend status
  const mapSolutionStatus = (backendStatus) => {
    const statusMap = {
      'DRAFT': '设计中',
      'REVIEWING': '评审中',
      'APPROVED': '已通过',
      'REJECTED': '已驳回',
      'SUBMITTED': '已提交',
    }
    return statusMap[backendStatus] || backendStatus
  }

  // Load presales data
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Load tickets (my tasks)
      const ticketsResponse = await presaleApi.tickets.list({
        page: 1,
        page_size: 50,
        status: 'PENDING,ACCEPTED,IN_PROGRESS',
      })
      const tickets = ticketsResponse.data?.items || ticketsResponse.data || []

      // Transform tickets to todo tasks
      const transformedTasks = await Promise.all(tickets.map(async (ticket) => {
        // 查找关联的方案
        let solutionId = null
        try {
          const solutionsResponse = await presaleApi.solutions.list({
            ticket_id: ticket.id,
            page: 1,
            page_size: 1,
          })
          const solutions = solutionsResponse.data?.items || solutionsResponse.data || []
          if (solutions.length > 0) {
            solutionId = solutions[0].id
          }
        } catch (err) {
          // Ignore error
        }
        
        return {
          id: ticket.id,
          title: ticket.title,
          type: mapTicketType(ticket.ticket_type),
          typeColor: getTypeColor(mapTicketType(ticket.ticket_type)),
          source: ticket.applicant_name ? `销售：${ticket.applicant_name}` : '内部流程',
          deadline: ticket.deadline || ticket.expected_date || '',
          priority: ticket.urgency?.toLowerCase() || 'medium',
          customer: ticket.customer_name || '',
          ticketId: ticket.id,
          opportunityId: ticket.opportunity_id,
          biddingId: ticket.project_id, // Using project_id as bidding_id for now
          solutionId,
          requestedBy: ticket.applicant_name,
          requestedAt: ticket.apply_time,
        }
      }))

      setTodoTasks(transformedTasks)

      // Load solutions (ongoing)
      const solutionsResponse = await presaleApi.solutions.list({
        page: 1,
        page_size: 20,
        status: 'DRAFT,REVIEWING,SUBMITTED',
      })
      const solutions = solutionsResponse.data?.items || solutionsResponse.data || []

      // Transform solutions
      const transformedSolutions = solutions.map(solution => ({
        id: solution.id,
        name: solution.name,
        customer: solution.customer_id ? '客户' : '', // Need customer name from customer API
        version: solution.version || 'V1.0',
        status: mapSolutionStatus(solution.status),
        statusColor: solution.status === 'REVIEWING' ? 'bg-amber-500' : 
                     solution.status === 'APPROVED' ? 'bg-emerald-500' : 'bg-blue-500',
        progress: solution.status === 'APPROVED' ? 100 : 
                  solution.status === 'REVIEWING' ? 85 : 60,
        deadline: solution.estimated_duration ? '' : '', // Need deadline from ticket
        amount: solution.estimated_cost || solution.suggested_price || 0,
        deviceType: solution.test_type || solution.solution_type || '',
      }))

      setOngoingSolutions(transformedSolutions)

      // Load tenders
      const tendersResponse = await presaleApi.tenders.list({
        page: 1,
        page_size: 10,
      })
      const tenders = tendersResponse.data?.items || tendersResponse.data || []

      // Transform tenders
      const transformedTenders = tenders.map(tender => ({
        id: tender.id,
        name: tender.tender_name || tender.project_name || '',
        customer: tender.customer_name || '',
        deadline: tender.submission_deadline || '',
        status: tender.status || 'PREPARING',
        statusColor: tender.status === 'SUBMITTED' ? 'bg-emerald-500' : 'bg-amber-500',
        amount: tender.budget || 0,
        progress: tender.status === 'SUBMITTED' ? 100 : 60,
      }))

      setRecentTenders(transformedTenders)

      // Load opportunities
      const opportunitiesResponse = await opportunityApi.list({
        page: 1,
        page_size: 10,
        stage: 'QUALIFICATION,PROPOSAL',
      })
      const opportunities = opportunitiesResponse.data?.items || opportunitiesResponse.data || []

      // Transform opportunities
      const transformedOpportunities = opportunities.map(opp => ({
        id: opp.id,
        name: opp.name,
        customer: opp.customer_name || '',
        stage: opp.stage || '',
        amount: opp.estimated_value || 0,
        probability: opp.probability || 0,
        expectedDate: opp.expected_close_date || '',
      }))

      setRelatedOpportunities(transformedOpportunities)

      // Calculate stats
      const pendingTickets = tickets.filter(t => t.status === 'PENDING').length
      const inProgressTickets = tickets.filter(t => t.status === 'IN_PROGRESS').length
      const reviewingSolutions = solutions.filter(s => s.status === 'REVIEWING').length
      const totalEstimatedValue = transformedSolutions.reduce((sum, s) => sum + (s.amount || 0), 0)

      setStats([
        {
          id: 1,
          title: '本周任务',
          value: tickets.length.toString(),
          subtitle: `待处理 ${pendingTickets}`,
          icon: ListTodo,
          color: 'text-blue-400',
          bgColor: 'bg-blue-400/10',
          trend: null,
        },
        {
          id: 2,
          title: '进行中方案',
          value: solutions.length.toString(),
          subtitle: `待评审 ${reviewingSolutions}`,
          icon: FileText,
          color: 'text-violet-400',
          bgColor: 'bg-violet-400/10',
          trend: null,
        },
        {
          id: 3,
          title: '投标项目',
          value: tenders.length.toString(),
          subtitle: `本月截止 ${tenders.filter(t => {
            const deadline = new Date(t.submission_deadline)
            const now = new Date()
            return deadline >= now && deadline <= new Date(now.getFullYear(), now.getMonth() + 1, 0)
          }).length}`,
          icon: Target,
          color: 'text-amber-400',
          bgColor: 'bg-amber-400/10',
          trend: null,
        },
        {
          id: 4,
          title: '预计产出',
          value: `¥${(totalEstimatedValue / 10000).toFixed(0)}万`,
          subtitle: '按方案金额',
          icon: DollarSign,
          color: 'text-emerald-400',
          bgColor: 'bg-emerald-400/10',
          trend: null,
        },
      ])

    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载数据失败')
      // 不再使用mock数据，使用空数据
      setTodoTasks([])
      setOngoingSolutions([])
      setRecentTenders([])
      setRelatedOpportunities([])
      setStats(statsData.map(s => ({ ...s, value: '0', subtitle: '暂无数据' })))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleCostTaskClick = (task) => {
    if (task.type === '成本支持' || task.type === '成本核算') {
      setSelectedCostTask(task)
      setShowCostForm(true)
    } else if (task.type === '可行性评估') {
      setSelectedFeasibilityTask(task)
      setShowFeasibilityForm(true)
    }
  }

  const handleCostSave = async (costData) => {
    try {
      // 如果有关联的方案ID，更新方案的成本估算
      if (selectedCostTask?.solutionId) {
        // 更新现有方案的成本
        await presaleApi.solutions.update(selectedCostTask.solutionId, {
          estimated_cost: costData.totalAmount * 10000, // 转换为分
          suggested_price: costData.suggestedPrice * 10000, // 转换为分
        })
      } else if (selectedCostTask?.ticketId) {
        // 先查找关联的方案
        const solutionsResponse = await presaleApi.solutions.list({
          ticket_id: selectedCostTask.ticketId,
          page: 1,
          page_size: 1,
        })
        const solutions = solutionsResponse.data?.items || solutionsResponse.data || []
        
        if (solutions.length > 0) {
          // 更新现有方案的成本
          await presaleApi.solutions.update(solutions[0].id, {
            estimated_cost: costData.totalAmount * 10000, // 转换为分
            suggested_price: costData.suggestedPrice * 10000, // 转换为分
          })
        } else {
          // 如果没有方案，获取工单信息并创建新方案
          const ticketResponse = await presaleApi.tickets.get(selectedCostTask.ticketId)
          const ticket = ticketResponse.data
          
          if (ticket.opportunity_id) {
            await presaleApi.solutions.create({
              name: selectedCostTask.title,
              ticket_id: selectedCostTask.ticketId,
              opportunity_id: ticket.opportunity_id,
              customer_id: ticket.customer_id,
              estimated_cost: costData.totalAmount * 10000,
              suggested_price: costData.suggestedPrice * 10000,
            })
          }
        }
      }
      
      // 更新工单进度
      if (selectedCostTask?.ticketId && costData.status === 'submitted') {
        await presaleApi.tickets.updateProgress(selectedCostTask.ticketId, {
          progress: 100,
          notes: `成本估算已完成，总成本：¥${costData.totalAmount}万，建议报价：¥${costData.suggestedPrice}万`,
        })
      }
      
      // 重新加载数据
      await loadData()
      
      alert('成本估算已提交！')
      setShowCostForm(false)
      setSelectedCostTask(null)
    } catch (err) {
      alert('保存失败：' + (err.response?.data?.detail || err.message || '未知错误'))
    }
  }

  const handleFeasibilitySave = async (assessmentData) => {
    try {
      // 更新工单，添加可行性评估结果
      if (selectedFeasibilityTask?.ticketId) {
        await presaleApi.tickets.update(selectedFeasibilityTask.ticketId, {
          description: `${selectedFeasibilityTask.description || ''}\n\n可行性评估结果：\n综合评分：${assessmentData.overallScore.toFixed(1)}分\n可行性：${assessmentData.feasibility === 'feasible' ? '可行' : assessmentData.feasibility === 'conditional' ? '有条件可行' : '不可行'}\n评估建议：${assessmentData.recommendation}\n风险分析：${assessmentData.riskAnalysis}\n技术说明：${assessmentData.technicalNotes}`,
        })
        
        // 更新工单进度
        await presaleApi.tickets.updateProgress(selectedFeasibilityTask.ticketId, {
          progress: 100,
          notes: `可行性评估已完成，综合评分：${assessmentData.overallScore.toFixed(1)}分`,
        })
      }
      
      // 重新加载数据
      await loadData()
      
      alert('可行性评估已提交！')
      setShowFeasibilityForm(false)
      setSelectedFeasibilityTask(null)
    } catch (err) {
      alert('保存失败：' + (err.response?.data?.detail || err.message || '未知错误'))
    }
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="售前工作台"
        description="技术方案设计 · 客户需求对接 · 投标技术支持"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              搜索方案
            </Button>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建方案
            </Button>
          </motion.div>
        }
      />

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}
      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card
            key={stat.id}
            className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg hover:shadow-xl transition-shadow cursor-pointer"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm text-slate-400">{stat.title}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-500">{stat.subtitle}</span>
                    {stat.trend && (
                      <span className="text-xs text-emerald-400 flex items-center gap-0.5">
                        <TrendingUp className="w-3 h-3" />
                        {stat.trend}
                      </span>
                    )}
                  </div>
                </div>
                <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', stat.bgColor)}>
                  <stat.icon className={cn('w-5 h-5', stat.color)} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* 主内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧 - 待办任务 */}
        <motion.div variants={fadeIn} className="lg:col-span-2 space-y-6">
          {/* 待办任务卡片 */}
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <ListTodo className="w-5 h-5 text-primary" />
                待办任务
                <Badge variant="secondary" className="bg-primary/20 text-primary ml-2">
                  {todoTasks.length}
                </Badge>
              </CardTitle>
              <Link to="/presales-tasks">
                <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                  查看全部
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {todoTasks.map((task, index) => (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors group"
                  onClick={() => handleCostTaskClick(task)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge className={cn('text-xs', task.typeColor)}>
                          {task.type}
                        </Badge>
                        <Badge className={cn('text-xs', getPriorityStyle(task.priority))}>
                          {getPriorityText(task.priority)}
                        </Badge>
                      </div>
                      <h4 className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">
                        {task.title}
                      </h4>
                      <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {task.source}
                        </span>
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          {task.customer}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-400 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {task.deadline}
                      </p>
                      <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-primary transition-colors mt-2 ml-auto" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* 进行中方案 */}
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-violet-400" />
                进行中方案
              </CardTitle>
              <Link to="/solutions">
                <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                  方案中心
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {ongoingSolutions.map((solution, index) => (
                <motion.div
                  key={solution.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-4 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="text-sm font-medium text-white">{solution.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          {solution.version}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3 h-3" />
                          {solution.customer}
                        </span>
                        <span className="flex items-center gap-1">
                          <Briefcase className="w-3 h-3" />
                          {solution.deviceType}
                        </span>
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-3 h-3" />
                          ¥{solution.amount}万
                        </span>
                      </div>
                    </div>
                    <Badge className={cn('text-xs', solution.statusColor)}>
                      {solution.status}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">完成进度</span>
                      <span className="text-white">{solution.progress}%</span>
                    </div>
                    <Progress value={solution.progress} className="h-1.5" />
                  </div>
                  <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      截止: {solution.deadline}
                    </span>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* 右侧 */}
        <motion.div variants={fadeIn} className="space-y-6">
          {/* 快捷操作 */}
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                快捷操作
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              {quickActions.map((action) => (
                <Link key={action.name} to={action.path}>
                  <div className={cn(
                    'p-3 rounded-lg bg-gradient-to-br cursor-pointer',
                    'hover:scale-105 transition-transform',
                    action.color
                  )}>
                    <action.icon className="w-5 h-5 text-white mb-2" />
                    <p className="text-sm font-medium text-white">{action.name}</p>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* 近期投标 */}
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-amber-400" />
                近期投标
              </CardTitle>
              <Link to="/bidding">
                <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                  全部
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingBids.map((bid, index) => (
                <motion.div
                  key={bid.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-white truncate">{bid.name}</h4>
                      <p className="text-xs text-slate-500 mt-0.5">{bid.customer}</p>
                    </div>
                    <Badge className={cn('text-xs', bid.statusColor)}>
                      {bid.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Timer className="w-3 h-3" />
                      剩余 <span className={cn('font-medium', bid.daysLeft <= 7 ? 'text-red-400' : 'text-white')}>{bid.daysLeft}</span> 天
                    </span>
                    <span className="text-slate-400">¥{bid.amount}万</span>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>

          {/* 关联商机 */}
          <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-400" />
                商机支持
              </CardTitle>
              <Link to="/opportunities">
                <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                  全部
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {linkedOpportunities.map((opp, index) => (
                <motion.div
                  key={opp.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-white truncate">{opp.name}</h4>
                      <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                        <Building2 className="w-3 h-3" />
                        {opp.customer}
                        <span className="text-slate-600">|</span>
                        <Users className="w-3 h-3" />
                        {opp.salesPerson}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <Badge className={cn('text-xs', opp.stageColor)}>
                      {opp.stage}
                    </Badge>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">赢率 <span className="text-white">{opp.winRate}%</span></span>
                      <span className="text-emerald-400">¥{opp.amount}万</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 成本估算对话框 */}
      <AnimatePresence>
        {showCostForm && selectedCostTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowCostForm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-100 rounded-xl border border-white/10 shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* 对话框头部 */}
              <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div>
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Calculator className="w-5 h-5 text-primary" />
                    成本估算
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">{selectedCostTask.title}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowCostForm(false)}
                >
                  <X className="w-5 h-5 text-slate-400" />
                </Button>
              </div>

              {/* 对话框内容 */}
              <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                <CostEstimateForm
                  bidding={{
                    id: selectedCostTask.biddingId,
                    name: selectedCostTask.title,
                    amount: 120, // 可以从任务数据中获取
                  }}
                  onSave={handleCostSave}
                  onCancel={() => setShowCostForm(false)}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 可行性评估对话框 */}
      <AnimatePresence>
        {showFeasibilityForm && selectedFeasibilityTask && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setShowFeasibilityForm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-surface-100 rounded-xl border border-white/10 shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* 对话框头部 */}
              <div className="flex items-center justify-between p-4 border-b border-white/5">
                <div>
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-primary" />
                    可行性评估
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">{selectedFeasibilityTask.title}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowFeasibilityForm(false)}
                >
                  <X className="w-5 h-5 text-slate-400" />
                </Button>
              </div>

              {/* 对话框内容 */}
              <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                <FeasibilityAssessmentForm
                  opportunity={{
                    id: selectedFeasibilityTask.opportunityId,
                    name: selectedFeasibilityTask.title,
                    customerName: selectedFeasibilityTask.customer,
                    expectedAmount: 450000, // 可以从任务数据中获取
                  }}
                  onSave={handleFeasibilitySave}
                  onCancel={() => setShowFeasibilityForm(false)}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

