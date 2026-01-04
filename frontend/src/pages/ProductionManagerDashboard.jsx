/**
 * Production Manager Dashboard - Main dashboard for production department manager
 * Features: Production overview, workshop management, production plans, work orders, team management
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Factory,
  Calendar,
  Users,
  Wrench,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  Clock,
  Package,
  BarChart3,
  FileText,
  Settings,
  Filter,
  Search,
  Plus,
  Eye,
  Edit,
  ChevronRight,
  Activity,
  Target,
  Zap,
  Truck,
  ClipboardList,
  UserCheck,
  AlertCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn } from '../lib/utils'

// Mock data
const mockProductionStats = {
  inProductionProjects: 12,
  todayOutput: 8,
  completionRate: 85.5,
  onTimeDeliveryRate: 92.3,
  totalWorkers: 45,
  activeWorkers: 42,
  totalWorkstations: 28,
  activeWorkstations: 25,
}

const mockWorkshops = [
  {
    id: 1,
    name: '机加车间',
    type: 'MACHINING',
    capacity: 100,
    currentLoad: 75,
    activeWorkstations: 8,
    totalWorkstations: 10,
    workers: 15,
    activeWorkers: 14,
    todayOutput: 3,
    status: 'normal',
  },
  {
    id: 2,
    name: '装配车间',
    type: 'ASSEMBLY',
    capacity: 80,
    currentLoad: 90,
    activeWorkstations: 12,
    totalWorkstations: 12,
    workers: 20,
    activeWorkers: 18,
    todayOutput: 5,
    status: 'warning',
  },
  {
    id: 3,
    name: '调试车间',
    type: 'DEBUGGING',
    capacity: 60,
    currentLoad: 50,
    activeWorkstations: 5,
    totalWorkstations: 6,
    workers: 10,
    activeWorkers: 10,
    todayOutput: 0,
    status: 'normal',
  },
]

const mockProductionPlans = [
  {
    id: 1,
    planCode: 'MPS-2025-001',
    projectCode: 'PJ250708001',
    projectName: 'BMS老化测试设备',
    workshop: '装配车间',
    startDate: '2025-01-15',
    endDate: '2025-02-28',
    status: 'executing',
    progress: 65,
    priority: 'high',
    workOrders: 15,
    completedOrders: 10,
  },
  {
    id: 2,
    planCode: 'MPS-2025-002',
    projectCode: 'PJ250708002',
    projectName: 'ICT测试设备',
    workshop: '机加车间',
    startDate: '2025-01-20',
    endDate: '2025-03-10',
    status: 'executing',
    progress: 45,
    priority: 'normal',
    workOrders: 20,
    completedOrders: 9,
  },
  {
    id: 3,
    planCode: 'MPS-2025-003',
    projectCode: 'PJ250708003',
    projectName: '视觉检测设备',
    workshop: '装配车间',
    startDate: '2025-02-01',
    endDate: '2025-03-15',
    status: 'approved',
    progress: 0,
    priority: 'high',
    workOrders: 12,
    completedOrders: 0,
  },
]

const mockWorkOrders = [
  {
    id: 1,
    orderCode: 'WO-2025-001',
    projectCode: 'PJ250708001',
    projectName: 'BMS老化测试设备',
    workshop: '装配车间',
    workstation: '工位A-01',
    type: 'ASSEMBLY',
    priority: 'high',
    status: 'started',
    assignedWorker: '张师傅',
    plannedStart: '2025-01-15',
    plannedEnd: '2025-01-20',
    actualStart: '2025-01-15',
    progress: 75,
    quantity: 1,
    completedQuantity: 0.75,
  },
  {
    id: 2,
    orderCode: 'WO-2025-002',
    projectCode: 'PJ250708001',
    projectName: 'BMS老化测试设备',
    workshop: '装配车间',
    workstation: '工位A-02',
    type: 'ASSEMBLY',
    priority: 'high',
    status: 'started',
    assignedWorker: '李师傅',
    plannedStart: '2025-01-16',
    plannedEnd: '2025-01-22',
    actualStart: '2025-01-16',
    progress: 60,
    quantity: 1,
    completedQuantity: 0.6,
  },
  {
    id: 3,
    orderCode: 'WO-2025-003',
    projectCode: 'PJ250708002',
    projectName: 'ICT测试设备',
    workshop: '机加车间',
    workstation: '工位B-01',
    type: 'MACHINING',
    priority: 'normal',
    status: 'assigned',
    assignedWorker: '王师傅',
    plannedStart: '2025-01-20',
    plannedEnd: '2025-01-25',
    actualStart: null,
    progress: 0,
    quantity: 5,
    completedQuantity: 0,
  },
]

const mockAlerts = [
  {
    id: 1,
    type: 'material_shortage',
    level: 'warning',
    title: '缺料预警',
    content: 'BMS老化测试设备 - 缺料：导轨 20mm x 500mm x 2根',
    projectCode: 'PJ250708001',
    workshop: '装配车间',
    createdAt: '2025-01-15 10:30',
    status: 'pending',
  },
  {
    id: 2,
    type: 'delay',
    level: 'critical',
    title: '进度延误',
    content: 'ICT测试设备 - 机加进度延误 3 天',
    projectCode: 'PJ250708002',
    workshop: '机加车间',
    createdAt: '2025-01-15 09:15',
    status: 'pending',
  },
  {
    id: 3,
    type: 'quality',
    level: 'warning',
    title: '质量问题',
    content: '视觉检测设备 - 装配质量异常，需返工',
    projectCode: 'PJ250708003',
    workshop: '装配车间',
    createdAt: '2025-01-14 16:45',
    status: 'processing',
  },
]

const mockTeamStats = {
  totalWorkers: 45,
  activeWorkers: 42,
  onLeave: 3,
  averageEfficiency: 88.5,
  todayAttendance: 95.6,
  skillDistribution: {
    expert: 5,
    senior: 15,
    intermediate: 20,
    junior: 5,
  },
}

export default function ProductionManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filteredPlans = useMemo(() => {
    return mockProductionPlans.filter(plan => {
      const matchesSearch = !searchQuery || 
        plan.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plan.planCode.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = filterStatus === 'all' || plan.status === filterStatus
      return matchesSearch && matchesStatus
    })
  }, [searchQuery, filterStatus])

  const filteredWorkOrders = useMemo(() => {
    return mockWorkOrders.filter(order => {
      const matchesSearch = !searchQuery || 
        order.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        order.orderCode.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = filterStatus === 'all' || order.status === filterStatus
      return matchesSearch && matchesStatus
    })
  }, [searchQuery, filterStatus])

  const getStatusColor = (status) => {
    const colors = {
      executing: 'bg-blue-500',
      approved: 'bg-emerald-500',
      published: 'bg-purple-500',
      draft: 'bg-slate-500',
      started: 'bg-blue-500',
      assigned: 'bg-amber-500',
      completed: 'bg-emerald-500',
      pending: 'bg-slate-500',
    }
    return colors[status] || 'bg-slate-500'
  }

  const getStatusLabel = (status) => {
    const labels = {
      executing: '执行中',
      approved: '已审批',
      published: '已发布',
      draft: '草稿',
      started: '已开工',
      assigned: '已派工',
      completed: '已完工',
      pending: '待处理',
    }
    return labels[status] || status
  }

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-500',
      normal: 'bg-amber-500',
      low: 'bg-slate-500',
    }
    return colors[priority] || 'bg-slate-500'
  }

  const getAlertLevelColor = (level) => {
    const colors = {
      critical: 'bg-red-500',
      warning: 'bg-amber-500',
      info: 'bg-blue-500',
    }
    return colors[level] || 'bg-slate-500'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <PageHeader
        title="生产管理"
        subtitle="生产部经理工作台"
        icon={Factory}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">在产项目</p>
                    <p className="text-3xl font-bold text-white">
                      {mockProductionStats.inProductionProjects}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Factory className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">+2 本周</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">今日产出</p>
                    <p className="text-3xl font-bold text-white">
                      {mockProductionStats.todayOutput}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">+1 较昨日</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">完成率</p>
                    <p className="text-3xl font-bold text-white">
                      {mockProductionStats.completionRate}%
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Target className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400">+2.5% 较上周</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">准时交付率</p>
                    <p className="text-3xl font-bold text-white">
                      {mockProductionStats.onTimeDeliveryRate}%
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
                <div className="mt-4 flex items-center gap-2 text-sm">
                  <TrendingDown className="w-4 h-4 text-red-400" />
                  <span className="text-red-400">-1.2% 较上周</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* 主要内容区域 */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="bg-surface-50 border-white/10">
            <TabsTrigger value="overview">生产概览</TabsTrigger>
            <TabsTrigger value="workshops">车间管理</TabsTrigger>
            <TabsTrigger value="plans">生产计划</TabsTrigger>
            <TabsTrigger value="orders">工单管理</TabsTrigger>
            <TabsTrigger value="team">团队管理</TabsTrigger>
            <TabsTrigger value="alerts">异常预警</TabsTrigger>
          </TabsList>

          {/* 生产概览 */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* 车间负荷 */}
              <Card className="lg:col-span-2 bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    车间负荷情况
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {mockWorkshops.map((workshop, index) => (
                    <motion.div
                      key={workshop.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-lg bg-surface-100 border border-white/5"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            'w-3 h-3 rounded-full',
                            workshop.status === 'normal' ? 'bg-emerald-500' : 'bg-amber-500'
                          )} />
                          <h4 className="font-semibold text-white">{workshop.name}</h4>
                          <Badge className={cn(
                            'text-xs',
                            workshop.status === 'normal' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                          )}>
                            {workshop.status === 'normal' ? '正常' : '负荷高'}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-400">负荷率</p>
                          <p className="text-lg font-bold text-white">{workshop.currentLoad}%</p>
                        </div>
                      </div>
                      <Progress value={workshop.currentLoad} className="h-2 mb-3" />
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">工位</p>
                          <p className="text-white font-semibold">
                            {workshop.activeWorkstations}/{workshop.totalWorkstations}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">人员</p>
                          <p className="text-white font-semibold">
                            {workshop.activeWorkers}/{workshop.workers}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">今日产出</p>
                          <p className="text-white font-semibold">{workshop.todayOutput}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </CardContent>
              </Card>

              {/* 关键指标 */}
              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    关键指标
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">人员出勤率</p>
                      <p className="text-lg font-bold text-white">
                        {mockTeamStats.todayAttendance}%
                      </p>
                    </div>
                    <Progress value={mockTeamStats.todayAttendance} className="h-2" />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">平均效率</p>
                      <p className="text-lg font-bold text-white">
                        {mockTeamStats.averageEfficiency}%
                      </p>
                    </div>
                    <Progress value={mockTeamStats.averageEfficiency} className="h-2" />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">在岗人员</p>
                      <p className="text-lg font-bold text-white">
                        {mockTeamStats.activeWorkers}/{mockTeamStats.totalWorkers}
                      </p>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">
                      请假: {mockTeamStats.onLeave} 人
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* 近期生产计划 */}
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-primary" />
                    近期生产计划
                  </CardTitle>
                  <Button variant="outline" size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    新建计划
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockProductionPlans.slice(0, 3).map((plan, index) => (
                    <motion.div
                      key={plan.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge className={cn('text-xs', getStatusColor(plan.status))}>
                            {getStatusLabel(plan.status)}
                          </Badge>
                          <span className="text-sm text-slate-400">{plan.planCode}</span>
                          <span className="text-sm font-semibold text-white">{plan.projectName}</span>
                        </div>
                        <Badge className={cn('text-xs', getPriorityColor(plan.priority))}>
                          {plan.priority === 'high' ? '高优先级' : '普通'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-400">
                        <span>{plan.workshop}</span>
                        <span>{plan.startDate} ~ {plan.endDate}</span>
                        <span>工单: {plan.completedOrders}/{plan.workOrders}</span>
                      </div>
                      <Progress value={plan.progress} className="h-2 mt-3" />
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 车间管理 */}
          <TabsContent value="workshops" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mockWorkshops.map((workshop, index) => (
                <motion.div
                  key={workshop.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="bg-surface-50 border-white/10 h-full">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                          <Factory className="w-5 h-5 text-primary" />
                          {workshop.name}
                        </CardTitle>
                        <Badge className={cn(
                          'text-xs',
                          workshop.status === 'normal' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                        )}>
                          {workshop.status === 'normal' ? '正常' : '负荷高'}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm text-slate-400">负荷率</p>
                          <p className="text-lg font-bold text-white">{workshop.currentLoad}%</p>
                        </div>
                        <Progress value={workshop.currentLoad} className="h-2" />
                      </div>
                      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                        <div>
                          <p className="text-xs text-slate-400 mb-1">工位</p>
                          <p className="text-lg font-semibold text-white">
                            {workshop.activeWorkstations}/{workshop.totalWorkstations}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400 mb-1">人员</p>
                          <p className="text-lg font-semibold text-white">
                            {workshop.activeWorkers}/{workshop.workers}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400 mb-1">今日产出</p>
                          <p className="text-lg font-semibold text-white">{workshop.todayOutput}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-400 mb-1">产能</p>
                          <p className="text-lg font-semibold text-white">{workshop.capacity}%</p>
                        </div>
                      </div>
                      <Button variant="outline" className="w-full mt-4" size="sm">
                        <Eye className="w-4 h-4 mr-2" />
                        查看详情
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* 生产计划 */}
          <TabsContent value="plans" className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索计划或项目..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-64 bg-surface-100 border-white/10"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-surface-100 border border-white/10 text-white text-sm"
                >
                  <option value="all">全部状态</option>
                  <option value="executing">执行中</option>
                  <option value="approved">已审批</option>
                  <option value="published">已发布</option>
                  <option value="draft">草稿</option>
                </select>
              </div>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                新建生产计划
              </Button>
            </div>

            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-surface-100 border-b border-white/10">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">计划编号</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">项目</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">车间</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">计划时间</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">进度</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">优先级</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">状态</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {filteredPlans.map((plan, index) => (
                        <motion.tr
                          key={plan.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-white/[0.02]"
                        >
                          <td className="px-6 py-4 text-sm text-white">{plan.planCode}</td>
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-semibold text-white">{plan.projectName}</p>
                              <p className="text-xs text-slate-400">{plan.projectCode}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">{plan.workshop}</td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {plan.startDate} ~ {plan.endDate}
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Progress value={plan.progress} className="h-2 w-24" />
                              <span className="text-sm text-slate-400">{plan.progress}%</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <Badge className={cn('text-xs', getPriorityColor(plan.priority))}>
                              {plan.priority === 'high' ? '高' : '普通'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <Badge className={cn('text-xs', getStatusColor(plan.status))}>
                              {getStatusLabel(plan.status)}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Button variant="ghost" size="sm">
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm">
                                <Edit className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* 工单管理 */}
          <TabsContent value="orders" className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索工单或项目..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-64 bg-surface-100 border-white/10"
                  />
                </div>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-surface-100 border border-white/10 text-white text-sm"
                >
                  <option value="all">全部状态</option>
                  <option value="started">已开工</option>
                  <option value="assigned">已派工</option>
                  <option value="completed">已完工</option>
                  <option value="pending">待派工</option>
                </select>
              </div>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                批量派工
              </Button>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {filteredWorkOrders.map((order, index) => (
                <motion.div
                  key={order.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="bg-surface-50 border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-3">
                            <Badge className={cn('text-xs', getStatusColor(order.status))}>
                              {getStatusLabel(order.status)}
                            </Badge>
                            <span className="text-sm font-semibold text-white">{order.orderCode}</span>
                            <span className="text-sm text-slate-400">{order.projectName}</span>
                            <Badge className={cn('text-xs', getPriorityColor(order.priority))}>
                              {order.priority === 'high' ? '高优先级' : '普通'}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-4 gap-4 text-sm mb-4">
                            <div>
                              <p className="text-slate-400 mb-1">车间/工位</p>
                              <p className="text-white">{order.workshop} / {order.workstation}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 mb-1">负责人</p>
                              <p className="text-white">{order.assignedWorker}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 mb-1">计划时间</p>
                              <p className="text-white">{order.plannedStart} ~ {order.plannedEnd}</p>
                            </div>
                            <div>
                              <p className="text-slate-400 mb-1">完成数量</p>
                              <p className="text-white">{order.completedQuantity}/{order.quantity}</p>
                            </div>
                          </div>
                          <Progress value={order.progress} className="h-2" />
                        </div>
                        <div className="ml-6 flex items-center gap-2">
                          <Button variant="ghost" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </TabsContent>

          {/* 团队管理 */}
          <TabsContent value="team" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="lg:col-span-2 bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-primary" />
                    人员统计
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">总人数</p>
                      <p className="text-3xl font-bold text-white">{mockTeamStats.totalWorkers}</p>
                      <div className="mt-4 flex items-center gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">在岗</p>
                          <p className="text-white font-semibold">{mockTeamStats.activeWorkers}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">请假</p>
                          <p className="text-white font-semibold">{mockTeamStats.onLeave}</p>
                        </div>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">今日出勤率</p>
                      <p className="text-3xl font-bold text-white">{mockTeamStats.todayAttendance}%</p>
                      <Progress value={mockTeamStats.todayAttendance} className="h-2 mt-4" />
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">平均效率</p>
                      <p className="text-3xl font-bold text-white">{mockTeamStats.averageEfficiency}%</p>
                      <Progress value={mockTeamStats.averageEfficiency} className="h-2 mt-4" />
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">技能分布</p>
                      <div className="mt-2 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">专家</span>
                          <span className="text-white font-semibold">{mockTeamStats.skillDistribution.expert}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">高级</span>
                          <span className="text-white font-semibold">{mockTeamStats.skillDistribution.senior}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">中级</span>
                          <span className="text-white font-semibold">{mockTeamStats.skillDistribution.intermediate}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">初级</span>
                          <span className="text-white font-semibold">{mockTeamStats.skillDistribution.junior}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <UserCheck className="w-5 h-5 text-primary" />
                    快捷操作
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Button variant="outline" className="w-full justify-start">
                    <Users className="w-4 h-4 mr-2" />
                    人员花名册
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Target className="w-4 h-4 mr-2" />
                    技能矩阵
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <Calendar className="w-4 h-4 mr-2" />
                    出勤管理
                  </Button>
                  <Button variant="outline" className="w-full justify-start">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    绩效统计
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* 异常预警 */}
          <TabsContent value="alerts" className="space-y-6">
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-primary" />
                  异常预警
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockAlerts.map((alert, index) => (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Badge className={cn('text-xs', getAlertLevelColor(alert.level))}>
                              {alert.level === 'critical' ? '严重' : alert.level === 'warning' ? '警告' : '提示'}
                            </Badge>
                            <span className="text-sm font-semibold text-white">{alert.title}</span>
                            <span className="text-xs text-slate-400">{alert.createdAt}</span>
                          </div>
                          <p className="text-sm text-slate-300 mb-2">{alert.content}</p>
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <span>{alert.projectCode}</span>
                            <span>{alert.workshop}</span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <Badge className={cn(
                            'text-xs',
                            alert.status === 'pending' ? 'bg-amber-500/20 text-amber-400' : 'bg-blue-500/20 text-blue-400'
                          )}>
                            {alert.status === 'pending' ? '待处理' : '处理中'}
                          </Badge>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

