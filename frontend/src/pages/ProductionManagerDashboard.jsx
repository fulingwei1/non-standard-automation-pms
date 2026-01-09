/**
 * Production Manager Dashboard - Main dashboard for production department manager
 * Features: Production overview, workshop management, production plans, work orders, team management
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
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
import { productionApi, shortageApi, projectApi, materialApi, alertApi } from '../services/api'

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

export default function ProductionManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // State for API data
  const [productionStats, setProductionStats] = useState({
    inProductionProjects: 0,
    todayOutput: 0,
    completionRate: 0,
    onTimeDeliveryRate: 0,
    totalWorkers: 0,
    activeWorkers: 0,
    totalWorkstations: 0,
    activeWorkstations: 0,
  })
  const [workshops, setWorkshops] = useState([])
  const [productionPlans, setProductionPlans] = useState([])
  const [workOrders, setWorkOrders] = useState([])
  const [productionDaily, setProductionDaily] = useState(null)
  const [shortageDaily, setShortageDaily] = useState(null)
  const [dailyError, setDailyError] = useState(null)
  const [workerRankings, setWorkerRankings] = useState([])
  const [rankingType, setRankingType] = useState('efficiency')
  const [rankingLoading, setRankingLoading] = useState(false)
  const [inProductionProjects, setInProductionProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)
  const [materialSearchResults, setMaterialSearchResults] = useState([])
  const [materialSearchKeyword, setMaterialSearchKeyword] = useState('')
  const [materialSearchLoading, setMaterialSearchLoading] = useState(false)
  const [alerts, setAlerts] = useState([])

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      'DRAFT': 'draft',
      'SUBMITTED': 'submitted',
      'APPROVED': 'approved',
      'PUBLISHED': 'published',
      'EXECUTING': 'executing',
      'PENDING': 'pending',
      'ASSIGNED': 'assigned',
      'STARTED': 'started',
      'COMPLETED': 'completed',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'pending'
  }

  const teamStats = useMemo(() => {
    const overall = productionDaily?.overall || {}
    const skill = overall.skill_distribution || {}
    const shouldAttend = overall.should_attend ?? productionStats.totalWorkers ?? 0
    const actualAttend = overall.actual_attend ?? productionStats.activeWorkers ?? 0
    const attendanceRate = shouldAttend > 0 ? Math.round((actualAttend / shouldAttend) * 100) : 0
    const efficiency = overall.efficiency ?? overall.completion_rate ?? productionStats.completionRate ?? 0

    return {
      totalWorkers: shouldAttend || productionStats.totalWorkers || 0,
      activeWorkers: actualAttend || productionStats.activeWorkers || 0,
      onLeave: Math.max((shouldAttend || 0) - (actualAttend || 0), 0),
      todayAttendance: attendanceRate,
      averageEfficiency: Math.round(efficiency),
      skillDistribution: {
        expert: skill.expert || 0,
        senior: skill.senior || 0,
        intermediate: skill.intermediate || 0,
        junior: skill.junior || 0,
      },
    }
  }, [productionDaily, productionStats])

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await productionApi.dashboard()
      const dashboardData = response.data || response
      if (dashboardData) {
        setProductionStats({
          inProductionProjects: dashboardData.in_production_projects || 0,
          todayOutput: dashboardData.today_output || 0,
          completionRate: dashboardData.completion_rate || 0,
          onTimeDeliveryRate: dashboardData.on_time_delivery_rate || 0,
          totalWorkers: dashboardData.total_workers || 0,
          activeWorkers: dashboardData.active_workers || 0,
          totalWorkstations: dashboardData.total_workstations || 0,
          activeWorkstations: dashboardData.active_workstations || 0,
        })
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载仪表板数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  const [selectedDate, setSelectedDate] = useState('')

  const loadDailySnapshots = useCallback(async (dateFilter) => {
    try {
      setDailyError(null)
      const [prodRes, shortageRes] = await Promise.all([
        dateFilter
          ? productionApi.reports.daily({ page: 1, page_size: 100, start_date: dateFilter, end_date: dateFilter })
          : productionApi.reports.latestDaily(),
        dateFilter
          ? shortageApi.statistics.dailyReportByDate(dateFilter)
          : shortageApi.statistics.latestDailyReport(),
      ])
      const prodPayload = dateFilter ? (prodRes?.data ?? prodRes) : (prodRes?.data?.data ?? prodRes?.data)
      let prodData = prodPayload
      if (dateFilter) {
        const items = prodPayload?.items || []
        if (items.length) {
          const normalized = items.map((item) => ({
            ...item,
            completion_rate: item.completion_rate ?? 0,
          }))
          prodData = {
            date: dateFilter,
            overall: normalized.find((report) => !report.workshop_id) || null,
            workshops: normalized.filter((report) => report.workshop_id),
          }
        } else {
          prodData = null
        }
      }
      if (prodData) {
        setProductionDaily(prodData)
        if (prodData.overall) {
          setProductionStats((prev) => ({
            ...prev,
            todayOutput: prodData.overall.completed_qty ?? prev.todayOutput,
            completionRate: prodData.overall.completion_rate ?? prev.completionRate,
            totalWorkers: prodData.overall.should_attend ?? prev.totalWorkers,
            activeWorkers: prodData.overall.actual_attend ?? prev.activeWorkers,
          }))
        }
      } else if (dateFilter) {
        setProductionDaily(null)
        setDailyError('该日期没有生产日报数据')
      }
      const shortageData = shortageRes?.data?.data ?? shortageRes?.data
      if (shortageData) {
        setShortageDaily(shortageData)
      } else if (dateFilter) {
        setShortageDaily(null)
        setDailyError('该日期没有缺料日报数据')
      }
    } catch (err) {
      setDailyError(err.response?.data?.detail || err.message || '日报数据加载失败')
    }
  }, [])

  // Load workshops
  const loadWorkshops = useCallback(async () => {
    try {
      const response = await productionApi.workshops.list({ page: 1, page_size: 100 })
      const workshopsData = response.data?.items || response.data || []
      const transformedWorkshops = workshopsData.map(ws => ({
        id: ws.id,
        name: ws.workshop_name || '',
        type: ws.workshop_type || 'MACHINING',
        capacity: ws.capacity || 0,
        currentLoad: ws.current_load || 0,
        activeWorkstations: ws.active_workstations || 0,
        totalWorkstations: ws.total_workstations || 0,
        workers: ws.workers || 0,
        activeWorkers: ws.active_workers || 0,
        todayOutput: ws.today_output || 0,
        status: ws.current_load > 90 ? 'warning' : 'normal',
      }))
      setWorkshops(transformedWorkshops)
    } catch (err) {
      setWorkshops([]) // 不再使用mock数据
    }
  }, [])

  // Load production plans
  const loadProductionPlans = useCallback(async () => {
    try {
      const params = { page: 1, page_size: 100 }
      if (filterStatus !== 'all') {
        const statusMap = {
          'executing': 'EXECUTING',
          'approved': 'APPROVED',
          'published': 'PUBLISHED',
          'draft': 'DRAFT',
        }
        params.status = statusMap[filterStatus] || filterStatus
      }
      const response = await productionApi.productionPlans.list(params)
      const plansData = response.data?.items || response.data || []
      const transformedPlans = plansData.map(plan => ({
        id: plan.id,
        planCode: plan.plan_no || '',
        projectName: plan.project_name || '',
        machineName: plan.machine_name || '',
        startDate: plan.start_date || '',
        endDate: plan.end_date || '',
        status: mapBackendStatus(plan.status),
        progress: plan.progress || 0,
        totalQuantity: plan.total_quantity || 0,
        completedQuantity: plan.completed_quantity || 0,
        priority: plan.priority?.toLowerCase() || 'normal',
      }))
      setProductionPlans(transformedPlans)
    } catch (err) {
      setProductionPlans([]) // 不再使用mock数据
    }
  }, [filterStatus])

  // Load work orders
  const loadWorkOrders = useCallback(async () => {
    try {
      const params = { page: 1, page_size: 100 }
      if (filterStatus !== 'all') {
        const statusMap = {
          'started': 'STARTED',
          'assigned': 'ASSIGNED',
          'completed': 'COMPLETED',
          'pending': 'PENDING',
        }
        params.status = statusMap[filterStatus] || filterStatus
      }
      const response = await productionApi.workOrders.list(params)
      const ordersData = response.data?.items || response.data || []
      const transformedOrders = ordersData.map(order => ({
        id: order.id,
        orderCode: order.work_order_no || '',
        projectName: order.project_name || '',
        machineName: order.machine_name || '',
        workshopName: order.workshop_name || '',
        workstationName: order.workstation_name || '',
        workerName: order.worker_name || '',
        startDate: order.start_date || '',
        endDate: order.end_date || '',
        status: mapBackendStatus(order.status),
        progress: order.progress || 0,
        quantity: order.quantity || 0,
        completedQuantity: order.completed_quantity || 0,
        priority: order.priority?.toLowerCase() || 'normal',
      }))
      setWorkOrders(transformedOrders)
    } catch (err) {
      setWorkOrders([]) // 不再使用mock数据
    }
  }, [filterStatus])

  // Load worker rankings
  const loadWorkerRankings = useCallback(async () => {
    try {
      setRankingLoading(true)
      const today = new Date()
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
      const params = {
        ranking_type: rankingType,
        period_start: monthStart.toISOString().split('T')[0],
        period_end: today.toISOString().split('T')[0],
        limit: 20,
      }
      const response = await productionApi.reports.workerRanking(params)
      const rankings = response.data || response
      setWorkerRankings(Array.isArray(rankings) ? rankings : [])
    } catch (err) {
      setWorkerRankings([])
    } finally {
      setRankingLoading(false)
    }
  }, [rankingType])

  // Load in-production projects
  const loadInProductionProjects = useCallback(async () => {
    try {
      setProjectsLoading(true)
      const response = await projectApi.getInProductionSummary({})
      const projects = response.data || response
      setInProductionProjects(Array.isArray(projects) ? projects : [])
    } catch (err) {
      setInProductionProjects([])
    } finally {
      setProjectsLoading(false)
    }
  }, [])

  // Load material search
  const loadMaterialSearch = useCallback(async (keyword) => {
    if (!keyword || keyword.trim().length < 2) {
      setMaterialSearchResults([])
      return
    }
    try {
      setMaterialSearchLoading(true)
      const response = await materialApi.search({
        keyword: keyword.trim(),
        page: 1,
        page_size: 20,
      })
      const data = response.data || response
      const items = data.items || data
      setMaterialSearchResults(Array.isArray(items) ? items : [])
    } catch (err) {
      setMaterialSearchResults([])
    } finally {
      setMaterialSearchLoading(false)
    }
  }, [])

  const loadAlerts = useCallback(async () => {
    try {
      const response = await alertApi.list({ page: 1, page_size: 6, status: 'PENDING' })
      const payload = response.data?.items || response.data?.data?.items || response.data?.data || response.data || []
      const list = Array.isArray(payload) ? payload : payload.items || []
      const normalized = list.map((alert) => {
        const levelMap = {
          URGENT: 'critical',
          CRITICAL: 'critical',
          WARNING: 'warning',
          INFO: 'info',
        }
        const statusMap = {
          PENDING: 'pending',
          HANDLING: 'processing',
          RESOLVED: 'resolved',
          CLOSED: 'closed',
        }
        const triggeredAt = alert.triggered_at ? new Date(alert.triggered_at) : null
        const timestamp = triggeredAt && !isNaN(triggeredAt.getTime())
          ? `${triggeredAt.getMonth() + 1}-${triggeredAt.getDate()} ${triggeredAt.getHours().toString().padStart(2, '0')}:${triggeredAt.getMinutes().toString().padStart(2, '0')}`
          : ''
        return {
          id: alert.id,
          level: levelMap[alert.alert_level?.toUpperCase?.()] || 'warning',
          title: alert.alert_title || alert.rule_name || '异常预警',
          content: alert.alert_content || alert.target_name || alert.target_type || '请查看详情',
          projectCode: alert.project_name || alert.project_code || alert.alert_no || '未关联项目',
          workshop: alert.target_name || alert.target_type || '—',
          createdAt: timestamp,
          status: statusMap[alert.status?.toUpperCase?.()] || 'pending',
        }
      })
      setAlerts(normalized)
    } catch (err) {
      setAlerts([])
    }
  }, [])

  // Load data when component mounts or tab changes
  useEffect(() => {
    if (selectedTab === 'overview') {
      loadDashboard()
      loadWorkshops()
      loadDailySnapshots(selectedDate || null)
      loadAlerts()
    } else if (selectedTab === 'workshops') {
      loadWorkshops()
    } else if (selectedTab === 'plans') {
      loadProductionPlans()
    } else if (selectedTab === 'orders') {
      loadWorkOrders()
    } else if (selectedTab === 'performance') {
      loadWorkerRankings()
    } else if (selectedTab === 'projects') {
      loadInProductionProjects()
    }
  }, [
    selectedTab,
    filterStatus,
    selectedDate,
    rankingType,
    loadDashboard,
    loadWorkshops,
    loadProductionPlans,
    loadWorkOrders,
    loadDailySnapshots,
    loadWorkerRankings,
    loadInProductionProjects,
    loadAlerts,
  ])

  // Material search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (materialSearchKeyword) {
        loadMaterialSearch(materialSearchKeyword)
      } else {
        setMaterialSearchResults([])
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [materialSearchKeyword, loadMaterialSearch])

  const filteredPlans = useMemo(() => {
    return productionPlans.filter(plan => {
      const matchesSearch = !searchQuery || 
        plan.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plan.planCode.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = filterStatus === 'all' || plan.status === filterStatus
      return matchesSearch && matchesStatus
    })
  }, [productionPlans, searchQuery, filterStatus])

  const filteredWorkOrders = useMemo(() => {
    return workOrders.filter(order => {
      const matchesSearch = !searchQuery || 
        order.projectName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        order.orderCode.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesStatus = filterStatus === 'all' || order.status === filterStatus
      return matchesSearch && matchesStatus
    })
  }, [workOrders, searchQuery, filterStatus])

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

  const getAlertStatusConfig = (status) => {
    const configs = {
      pending: { label: '待处理', className: 'bg-amber-500/20 text-amber-400' },
      processing: { label: '处理中', className: 'bg-blue-500/20 text-blue-400' },
      resolved: { label: '已处理', className: 'bg-emerald-500/20 text-emerald-400' },
      closed: { label: '已关闭', className: 'bg-slate-500/20 text-slate-400' },
    }
    return configs[status] || configs.pending
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <PageHeader
        title="生产管理"
        subtitle="生产部经理工作台"
        icon={Factory}
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
          <div>{selectedDate ? `当前日期：${selectedDate}` : '显示最新日报数据'}</div>
          <div className="flex items-center gap-2">
            <Input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-slate-900/50 border-slate-700 text-sm"
            />
            {selectedDate && (
              <Button variant="ghost" className="text-slate-300" onClick={() => setSelectedDate('')}>
                清空
              </Button>
            )}
          </div>
        </div>
        {dailyError && (
          <div className="rounded border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {dailyError}
          </div>
        )}
        {(productionDaily || shortageDaily) && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {productionDaily && (
              <Card className="bg-slate-900/60 border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Activity className="w-5 h-5 text-emerald-400" />
                    今日生产
                  </CardTitle>
                  <p className="text-sm text-slate-400">{productionDaily.date}</p>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-400">完成数量</p>
                    <p className="text-3xl font-semibold text-white">
                      {productionDaily.overall?.completed_qty ?? 0}
                    </p>
                    <p className="text-xs text-slate-500">
                      计划 {productionDaily.overall?.plan_qty ?? 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">完成率</p>
                    <p className="text-3xl font-semibold text-emerald-400">
                      {(productionDaily.overall?.completion_rate ?? 0).toFixed(1)}%
                    </p>
                    <Progress
                      value={productionDaily.overall?.completion_rate || 0}
                      className="h-2 mt-2"
                    />
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">实工 / 计划</p>
                    <p className="text-lg text-white">
                      {productionDaily.overall?.actual_hours ?? 0}h / {productionDaily.overall?.plan_hours ?? 0}h
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">到岗 / 应到</p>
                    <p className="text-lg text-white">
                      {productionDaily.overall?.actual_attend ?? 0} / {productionDaily.overall?.should_attend ?? 0}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
            {shortageDaily && (
              <Card className="bg-slate-900/60 border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    缺料动态
                  </CardTitle>
                  <p className="text-sm text-slate-400">{shortageDaily.date}</p>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-400">新增预警</p>
                    <p className="text-3xl font-semibold text-amber-400">
                      {shortageDaily.alerts?.new ?? 0}
                    </p>
                    <p className="text-xs text-slate-500">
                      未处理 {shortageDaily.alerts?.pending ?? 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">逾期预警</p>
                    <p className="text-3xl font-semibold text-red-400">
                      {shortageDaily.alerts?.overdue ?? 0}
                    </p>
                    <p className="text-xs text-slate-500">
                      已解决 {shortageDaily.alerts?.resolved ?? 0}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">齐套率</p>
                    <p className="text-lg text-white">
                      {shortageDaily.kit?.kit_rate ?? 0}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">准时到货</p>
                    <p className="text-lg text-white">
                      {shortageDaily.arrivals?.on_time_rate ?? 0}%
                    </p>
                    <p className="text-xs text-slate-500">
                      实到 {shortageDaily.arrivals?.actual ?? 0} / 计划 {shortageDaily.arrivals?.expected ?? 0}
                    </p>
                  </div>
                  <div className="text-xs text-slate-500 col-span-2">
                    响应 {shortageDaily.response?.avg_response_minutes ?? 0} 分钟 · 解决 {shortageDaily.response?.avg_resolve_hours ?? 0} 小时 ·
                    停工 {shortageDaily.stoppage?.count ?? 0} 次
                  </div>
                  <div className="col-span-2 grid grid-cols-4 gap-2 text-xs text-slate-400">
                    {['level1', 'level2', 'level3', 'level4'].map((levelKey, idx) => {
                      const labels = ['一级', '二级', '三级', '四级']
                      return (
                        <div key={levelKey} className="rounded bg-slate-800/60 px-2 py-1 text-center">
                          <p>{labels[idx]}</p>
                          <p className="text-base text-white">
                            {shortageDaily.alerts?.levels?.[levelKey] ?? 0}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
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
                      {productionStats.inProductionProjects}
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
                      {productionStats.todayOutput}
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
                      {productionStats.completionRate}%
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
                      {productionStats.onTimeDeliveryRate}%
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
            <TabsTrigger value="performance">人员绩效</TabsTrigger>
            <TabsTrigger value="projects">项目进展</TabsTrigger>
            <TabsTrigger value="alerts">异常预警</TabsTrigger>
          </TabsList>

          {/* 生产概览 */}
          <TabsContent value="overview" className="space-y-6">
            {loading && (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            )}
            {error && (
              <div className="text-center py-8 text-red-400">{error}</div>
            )}
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
                  {workshops.map((workshop, index) => (
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
                        {teamStats.todayAttendance}%
                      </p>
                    </div>
                    <Progress value={teamStats.todayAttendance} className="h-2" />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">平均效率</p>
                      <p className="text-lg font-bold text-white">
                        {teamStats.averageEfficiency}%
                      </p>
                    </div>
                    <Progress value={teamStats.averageEfficiency} className="h-2" />
                  </div>
                  <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm text-slate-400">在岗人员</p>
                      <p className="text-lg font-bold text-white">
                        {teamStats.activeWorkers}/{teamStats.totalWorkers}
                      </p>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">
                      请假: {teamStats.onLeave} 人
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
                  {filteredPlans.slice(0, 3).map((plan, index) => (
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
              {workshops.map((workshop, index) => (
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
                      <p className="text-3xl font-bold text-white">{teamStats.totalWorkers}</p>
                      <div className="mt-4 flex items-center gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">在岗</p>
                          <p className="text-white font-semibold">{teamStats.activeWorkers}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">请假</p>
                          <p className="text-white font-semibold">{teamStats.onLeave}</p>
                        </div>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">今日出勤率</p>
                      <p className="text-3xl font-bold text-white">{teamStats.todayAttendance}%</p>
                      <Progress value={teamStats.todayAttendance} className="h-2 mt-4" />
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">平均效率</p>
                      <p className="text-3xl font-bold text-white">{teamStats.averageEfficiency}%</p>
                      <Progress value={teamStats.averageEfficiency} className="h-2 mt-4" />
                    </div>
                    <div className="p-4 rounded-lg bg-surface-100 border border-white/5">
                      <p className="text-sm text-slate-400 mb-2">技能分布</p>
                      <div className="mt-2 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">专家</span>
                          <span className="text-white font-semibold">{teamStats.skillDistribution.expert}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">高级</span>
                          <span className="text-white font-semibold">{teamStats.skillDistribution.senior}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">中级</span>
                          <span className="text-white font-semibold">{teamStats.skillDistribution.intermediate}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">初级</span>
                          <span className="text-white font-semibold">{teamStats.skillDistribution.junior}</span>
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

          {/* 人员绩效 */}
          <TabsContent value="performance" className="space-y-6">
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    人员绩效排名
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <select
                      value={rankingType}
                      onChange={(e) => setRankingType(e.target.value)}
                      className="px-3 py-1.5 rounded-lg bg-surface-100 border border-white/10 text-white text-sm"
                    >
                      <option value="efficiency">效率排名</option>
                      <option value="output">产出排名</option>
                      <option value="quality">质量排名</option>
                    </select>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {rankingLoading ? (
                  <div className="text-center py-8 text-slate-400">加载中...</div>
                ) : workerRankings.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">暂无数据</div>
                ) : (
                  <div className="space-y-3">
                    {workerRankings.map((worker, index) => (
                      <motion.div
                        key={worker.worker_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className={cn(
                              'w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg',
                              worker.rank <= 3 ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'
                            )}>
                              {worker.rank}
                            </div>
                            <div>
                              <p className="font-semibold text-white">{worker.worker_name}</p>
                              <p className="text-xs text-slate-400">{worker.workshop_name || '未分配车间'}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-6 text-sm">
                            <div className="text-center">
                              <p className="text-slate-400">效率</p>
                              <p className="text-white font-semibold">{worker.efficiency.toFixed(1)}%</p>
                            </div>
                            <div className="text-center">
                              <p className="text-slate-400">产出</p>
                              <p className="text-white font-semibold">{worker.output}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-slate-400">质量率</p>
                              <p className="text-white font-semibold">{worker.quality_rate.toFixed(1)}%</p>
                            </div>
                            <div className="text-center">
                              <p className="text-slate-400">工时</p>
                              <p className="text-white font-semibold">{worker.total_hours.toFixed(1)}h</p>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 项目进展 */}
          <TabsContent value="projects" className="space-y-6">
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Factory className="w-5 h-5 text-primary" />
                  在产项目进度
                </CardTitle>
              </CardHeader>
              <CardContent>
                {projectsLoading ? (
                  <div className="text-center py-8 text-slate-400">加载中...</div>
                ) : inProductionProjects.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">暂无在产项目</div>
                ) : (
                  <div className="space-y-3">
                    {inProductionProjects.map((project, index) => (
                      <motion.div
                        key={project.project_id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Badge className={cn(
                                'text-xs',
                                project.health === 'H1' ? 'bg-emerald-500/20 text-emerald-400' :
                                project.health === 'H2' ? 'bg-amber-500/20 text-amber-400' :
                                project.health === 'H3' ? 'bg-red-500/20 text-red-400' :
                                'bg-slate-500/20 text-slate-400'
                              )}>
                                {project.health === 'H1' ? '正常' :
                                 project.health === 'H2' ? '有风险' :
                                 project.health === 'H3' ? '阻塞' : '已完结'}
                              </Badge>
                              <span className="text-sm font-semibold text-white">{project.project_name}</span>
                              <span className="text-xs text-slate-400">{project.project_code}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-slate-400 mb-2">
                              <span>阶段: {project.stage}</span>
                              <span>进度: {project.progress.toFixed(1)}%</span>
                              {project.next_milestone && (
                                <span>下个里程碑: {project.next_milestone}</span>
                              )}
                            </div>
                            {project.overdue_milestones_count > 0 && (
                              <div className="flex items-center gap-2 text-xs text-red-400">
                                <AlertTriangle className="w-4 h-4" />
                                <span>有 {project.overdue_milestones_count} 个里程碑已逾期</span>
                              </div>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-slate-400 mb-1">计划完成</p>
                            <p className="text-sm text-white">
                              {project.planned_end_date || '未设置'}
                            </p>
                          </div>
                        </div>
                        <Progress value={project.progress} className="h-2" />
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 异常预警 */}
          <TabsContent value="alerts" className="space-y-6">
            {/* 缺料预警统计 */}
            {shortageDaily && (
              <Card className="bg-surface-50 border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    缺料预警统计
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">新增预警</p>
                      <p className="text-2xl font-bold text-amber-400">
                        {shortageDaily.alerts?.new ?? 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">待处理</p>
                      <p className="text-2xl font-bold text-red-400">
                        {shortageDaily.alerts?.pending ?? 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">逾期预警</p>
                      <p className="text-2xl font-bold text-red-500">
                        {shortageDaily.alerts?.overdue ?? 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">齐套率</p>
                      <p className="text-2xl font-bold text-emerald-400">
                        {shortageDaily.kit?.kit_rate ?? 0}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 物料查找 */}
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5 text-primary" />
                  物料查找
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Input
                    placeholder="搜索物料编码/名称/规格..."
                    value={materialSearchKeyword}
                    onChange={(e) => setMaterialSearchKeyword(e.target.value)}
                    className="bg-surface-100 border-white/10"
                  />
                  {materialSearchLoading && (
                    <div className="text-center py-4 text-slate-400">搜索中...</div>
                  )}
                  {materialSearchResults.length > 0 && (
                    <div className="space-y-2">
                      {materialSearchResults.map((material) => (
                        <div
                          key={material.material_id}
                          className="p-3 rounded-lg bg-surface-100 border border-white/5"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-semibold text-white">{material.material_name}</p>
                              <p className="text-xs text-slate-400">{material.material_code}</p>
                              {material.specification && (
                                <p className="text-xs text-slate-500 mt-1">{material.specification}</p>
                              )}
                            </div>
                            <div className="text-right text-sm">
                              <div className="mb-1">
                                <span className="text-slate-400">库存: </span>
                                <span className={cn(
                                  'font-semibold',
                                  material.current_stock > 0 ? 'text-emerald-400' : 'text-red-400'
                                )}>
                                  {material.current_stock} {material.unit}
                                </span>
                              </div>
                              {material.in_transit_qty > 0 && (
                                <div className="mb-1">
                                  <span className="text-slate-400">在途: </span>
                                  <span className="text-amber-400 font-semibold">
                                    {material.in_transit_qty} {material.unit}
                                  </span>
                                </div>
                              )}
                              <div>
                                <span className="text-slate-400">可用: </span>
                                <span className="text-white font-semibold">
                                  {material.available_qty} {material.unit}
                                </span>
                              </div>
                              {material.supplier_name && (
                                <p className="text-xs text-slate-500 mt-1">供应商: {material.supplier_name}</p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {materialSearchKeyword && !materialSearchLoading && materialSearchResults.length === 0 && (
                    <div className="text-center py-8 text-slate-400">未找到匹配的物料</div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 异常预警列表 */}
            <Card className="bg-surface-50 border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-primary" />
                  异常预警
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {alerts.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 text-sm">
                      暂无新的预警
                    </div>
                  ) : (
                    alerts.map((alert, index) => {
                      const statusConfig = getAlertStatusConfig(alert.status)
                      return (
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
                              <Badge className={cn('text-xs', statusConfig.className)}>
                                {statusConfig.label}
                              </Badge>
                            </div>
                          </div>
                        </motion.div>
                      )
                    })
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
