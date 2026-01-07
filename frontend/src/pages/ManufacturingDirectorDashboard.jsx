/**
 * Manufacturing Director Dashboard - Executive dashboard for manufacturing director
 * Features: Manufacturing center management, Production planning approval, Resource coordination
 * Departments: Production, Customer Service, Warehouse, Shipping
 * Core Functions: Production plan approval, Resource coordination, Multi-department management
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Factory,
  Users,
  Package,
  Truck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Calendar,
  ClipboardCheck,
  Activity,
  Target,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Eye,
  ChevronRight,
  Wrench,
  Headphones,
  Warehouse,
  Ship,
  FileText,
  UserCheck,
  Box,
  PackageCheck,
  PackageX,
  MapPin,
  Timer,
  Award,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Input,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { productionApi, shortageApi } from '../services/api'

// Mock data - Overall manufacturing center stats
const mockManufacturingStats = {
  // Production Department
  production: {
    inProductionProjects: 12,
    todayOutput: 8,
    completionRate: 85.5,
    onTimeDeliveryRate: 92.3,
    totalWorkers: 45,
    activeWorkers: 42,
    totalWorkstations: 28,
    activeWorkstations: 25,
    workshopLoad: 78.5,
  },
  // Customer Service Department
  customerService: {
    activeCases: 18,
    resolvedToday: 5,
    pendingCases: 8,
    avgResponseTime: 2.5, // hours
    customerSatisfaction: 94.5,
    onSiteServices: 3,
    totalEngineers: 12,
    activeEngineers: 10,
  },
  // Warehouse Department
  warehouse: {
    totalItems: 1250,
    inStockItems: 1180,
    lowStockItems: 15,
    outOfStockItems: 5,
    inventoryTurnover: 8.5,
    warehouseUtilization: 82.3,
    pendingInbound: 8,
    pendingOutbound: 12,
  },
  // Shipping Department
  shipping: {
    pendingShipments: 6,
    shippedToday: 4,
    inTransit: 8,
    deliveredThisWeek: 28,
    onTimeShippingRate: 96.5,
    avgShippingTime: 3.2, // days
    totalOrders: 42,
  },
}

// Mock workshops data
const mockWorkshops = [
  {
    id: 1,
    name: '机加车间',
    currentLoad: 75,
    activeWorkstations: 8,
    totalWorkstations: 10,
    activeWorkers: 14,
    workers: 15,
    todayOutput: 3,
    status: 'normal',
  },
  {
    id: 2,
    name: '装配车间',
    currentLoad: 90,
    activeWorkstations: 12,
    totalWorkstations: 12,
    activeWorkers: 18,
    workers: 20,
    todayOutput: 5,
    status: 'warning',
  },
  {
    id: 3,
    name: '调试车间',
    currentLoad: 50,
    activeWorkstations: 5,
    totalWorkstations: 6,
    activeWorkers: 10,
    workers: 10,
    todayOutput: 0,
    status: 'normal',
  },
]

// Mock production plans pending approval
const mockPendingApprovals = [
  {
    id: 1,
    type: 'production_plan',
    planCode: 'MPS-2025-003',
    projectName: '视觉检测设备',
    workshop: '装配车间',
    startDate: '2025-02-01',
    endDate: '2025-03-15',
    priority: 'high',
    submitter: '生产部经理',
    submitTime: '2025-01-06 09:30',
    status: 'pending',
  },
  {
    id: 2,
    type: 'resource_allocation',
    title: '人员调配申请',
    department: '生产部',
    request: '从装配车间调配3人到调试车间',
    submitter: '生产部经理',
    submitTime: '2025-01-06 11:20',
    priority: 'medium',
    status: 'pending',
  },
  {
    id: 3,
    type: 'warehouse_expansion',
    title: '仓储扩容申请',
    department: '仓储部',
    request: '新增500平米仓储面积',
    amount: 500000,
    submitter: '仓储部经理',
    submitTime: '2025-01-05 16:45',
    priority: 'low',
    status: 'pending',
  },
]

// Mock customer service cases
const mockServiceCases = [
  {
    id: 1,
    projectCode: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    customer: '深圳XX科技',
    type: '故障维修',
    priority: 'high',
    status: 'in_progress',
    assignedEngineer: '钱工',
    reportedAt: '2025-01-06 08:30',
    responseTime: 1.5,
  },
  {
    id: 2,
    projectCode: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    customer: '东莞XX电子',
    type: '现场调试',
    priority: 'medium',
    status: 'pending',
    assignedEngineer: null,
    reportedAt: '2025-01-06 10:15',
    responseTime: null,
  },
  {
    id: 3,
    projectCode: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    customer: '惠州XX电池',
    type: '技术咨询',
    priority: 'low',
    status: 'resolved',
    assignedEngineer: '孙工',
    reportedAt: '2025-01-05 14:20',
    resolvedAt: '2025-01-05 16:30',
    responseTime: 2.1,
  },
]

// Mock warehouse alerts
const mockWarehouseAlerts = [
  {
    id: 1,
    type: 'low_stock',
    item: '导轨 20mm x 500mm',
    currentStock: 5,
    minStock: 10,
    status: 'warning',
  },
  {
    id: 2,
    type: 'out_of_stock',
    item: '气缸 SMC CDM2B25-50',
    currentStock: 0,
    minStock: 5,
    status: 'critical',
  },
  {
    id: 3,
    type: 'pending_inbound',
    item: '钣金件组件 x50套',
    expectedDate: '2025-01-08',
    status: 'pending',
  },
]

// Mock shipping orders
const mockShippingOrders = [
  {
    id: 1,
    orderNo: 'SO-2025-0018',
    projectCode: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    customer: '深圳XX科技',
    destination: '深圳',
    status: 'pending',
    plannedShipDate: '2025-01-08',
    priority: 'high',
  },
  {
    id: 2,
    orderNo: 'SO-2025-0019',
    projectCode: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    customer: '东莞XX电子',
    destination: '东莞',
    status: 'in_transit',
    shippedDate: '2025-01-05',
    estimatedArrival: '2025-01-08',
  },
  {
    id: 3,
    orderNo: 'SO-2025-0020',
    projectCode: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    customer: '惠州XX电池',
    destination: '惠州',
    status: 'delivered',
    deliveredDate: '2025-01-04',
  },
]

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              )}
              <span className="text-xs text-slate-500 ml-1">vs 上月</span>
            </div>
          )}
        </div>
        <div className={cn('rounded-lg p-3 bg-opacity-20', bg)}>
          <Icon className={cn('h-6 w-6', color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  )
}

export default function ManufacturingDirectorDashboard() {
  const [productionStats, setProductionStats] = useState(mockManufacturingStats.production)
  const [workshopCards, setWorkshopCards] = useState(mockWorkshops)
  const [productionDaily, setProductionDaily] = useState(null)
  const [shortageDaily, setShortageDaily] = useState(null)
  const [loadingDaily, setLoadingDaily] = useState(false)
  const [dailyError, setDailyError] = useState(null)
  const [selectedDate, setSelectedDate] = useState('')
  const formattedDate = selectedDate || ''

  const fetchProductionDaily = useCallback(async (dateFilter) => {
    if (!dateFilter) {
      const res = await productionApi.reports.latestDaily()
      return res?.data?.data ?? res?.data
    }
    const res = await productionApi.reports.daily({
      page: 1,
      page_size: 100,
      start_date: dateFilter,
      end_date: dateFilter,
    })
    const payload = res?.data ?? res
    const items = payload?.items || []
    if (!items.length) {
      return null
    }
    const normalized = items.map((item) => ({
      id: item.id,
      report_date: item.report_date,
      workshop_id: item.workshop_id,
      workshop_name: item.workshop_name,
      plan_qty: item.plan_qty,
      completed_qty: item.completed_qty,
      completion_rate: item.completion_rate ?? 0,
      plan_hours: item.plan_hours ?? 0,
      actual_hours: item.actual_hours ?? 0,
      overtime_hours: item.overtime_hours ?? 0,
      efficiency: item.efficiency ?? 0,
      should_attend: item.should_attend ?? 0,
      actual_attend: item.actual_attend ?? 0,
      summary: item.summary,
    }))
    const overall = normalized.find((report) => !report.workshop_id) || null
    const workshops = normalized.filter((report) => report.workshop_id)
    return {
      date: dateFilter,
      overall,
      workshops,
    }
  }, [])

  const fetchShortageDaily = useCallback(async (dateFilter) => {
    if (!dateFilter) {
      const res = await shortageApi.statistics.latestDailyReport()
      return res?.data?.data ?? res?.data
    }
    const res = await shortageApi.statistics.dailyReportByDate(dateFilter)
    return res?.data?.data ?? res?.data
  }, [])

  const loadDailySnapshots = useCallback(async (dateFilter) => {
    try {
      setLoadingDaily(true)
      setDailyError(null)
      const [prodData, shortageData] = await Promise.all([
        fetchProductionDaily(dateFilter),
        fetchShortageDaily(dateFilter),
      ])
      if (prodData) {
        setProductionDaily(prodData)
        if (prodData.overall) {
          setProductionStats((prev) => ({
            ...prev,
            todayOutput: prodData.overall.completed_qty ?? prev.todayOutput,
            completionRate: prodData.overall.completion_rate ?? prev.completionRate,
            totalWorkers: prodData.overall.should_attend ?? prev.totalWorkers,
            activeWorkers: prodData.overall.actual_attend ?? prev.activeWorkers,
            workshopLoad: prodData.overall.efficiency ?? prev.workshopLoad,
          }))
        }
        if (Array.isArray(prodData.workshops) && prodData.workshops.length > 0) {
          const transformed = prodData.workshops.map((ws) => ({
            id: ws.workshop_id || ws.id || ws.workshop_name || 'workshop',
            name: ws.workshop_name || '车间',
            currentLoad: Math.round(ws.efficiency || ws.completion_rate || 0),
            activeWorkstations: ws.active_workstations || 0,
            totalWorkstations: ws.total_workstations || 0,
            activeWorkers: ws.actual_attend || 0,
            workers: ws.should_attend || 0,
            todayOutput: ws.completed_qty || 0,
            status: (ws.completion_rate || 0) < 75 ? 'warning' : 'normal',
          }))
          setWorkshopCards(transformed)
        }
      } else {
        setProductionDaily(null)
        if (dateFilter) {
          setDailyError('该日期没有生产日报数据')
        }
      }
      if (shortageData) {
        setShortageDaily(shortageData)
      } else {
        setShortageDaily(null)
        if (dateFilter) {
          setDailyError((prev) => prev ?? '该日期没有缺料日报数据')
        }
      }
    } catch (err) {
      console.error('Failed to load daily snapshots:', err)
      setDailyError(err.response?.data?.detail || err.message || '日报数据加载失败')
    } finally {
      setLoadingDaily(false)
    }
  }, [fetchProductionDaily, fetchShortageDaily])

  useEffect(() => {
    loadDailySnapshots(formattedDate || null)
  }, [formattedDate, loadDailySnapshots])
  const [selectedTab, setSelectedTab] = useState('overview')

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="制造总监工作台"
        description="制造中心全面管理 | 生产计划审批 | 资源协调"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              运营报表
            </Button>
            <Button className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
          </motion.div>
        }
      />

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
        <div>
          {selectedDate
            ? `当前日期：${selectedDate}`
            : '显示最新生成的日报数据'}
        </div>
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-slate-900/50 border-slate-700 text-sm"
          />
          {selectedDate && (
            <Button
              variant="ghost"
              className="text-slate-300"
              onClick={() => setSelectedDate('')}
            >
              清空
            </Button>
          )}
        </div>
      </div>

      {(dailyError || productionDaily || shortageDaily || loadingDaily) && (
        <div className="space-y-3">
          {dailyError && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
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
                      今日生产日报
                    </CardTitle>
                    <p className="text-sm text-slate-400">{productionDaily.date}</p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
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
                          {(productionDaily.overall?.completion_rate ?? 0).toFixed(1)}
                          %
                        </p>
                        <Progress
                          value={productionDaily.overall?.completion_rate || 0}
                          className="h-2 mt-2"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400">实工 / 计划工时</p>
                        <p className="text-lg text-white">
                          {productionDaily.overall?.actual_hours ?? 0}h /
                          {' '}
                          {productionDaily.overall?.plan_hours ?? 0}h
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400">到岗 / 应到</p>
                        <p className="text-lg text-white">
                          {productionDaily.overall?.actual_attend ?? 0} /
                          {' '}
                          {productionDaily.overall?.should_attend ?? 0}
                        </p>
                      </div>
                    </div>
                    {productionDaily.overall?.summary && (
                      <p className="text-sm text-slate-300">{productionDaily.overall.summary}</p>
                    )}
                  </CardContent>
                </Card>
              )}
              {shortageDaily && (
                <Card className="bg-slate-900/60 border-slate-800">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                      缺料日报
                    </CardTitle>
                    <p className="text-sm text-slate-400">{shortageDaily.date}</p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400">新增预警</p>
                        <p className="text-3xl font-semibold text-amber-400">
                          {shortageDaily.alerts?.new ?? 0}
                        </p>
                        <p className="text-xs text-slate-500">
                          待处理 {shortageDaily.alerts?.pending ?? 0}
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
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm text-slate-300">
                      <div>
                        <p>齐套率</p>
                        <p className="text-lg text-white">
                          {shortageDaily.kit?.kit_rate ?? 0}%
                        </p>
                        <p className="text-xs text-slate-500">
                          {shortageDaily.kit?.complete_count ?? 0}/{shortageDaily.kit?.total_work_orders ?? 0} 工单完成齐套
                        </p>
                      </div>
                      <div>
                        <p>准时到货率</p>
                        <p className="text-lg text-white">
                          {shortageDaily.arrivals?.on_time_rate ?? 0}%
                        </p>
                        <p className="text-xs text-slate-500">
                          实到 {shortageDaily.arrivals?.actual ?? 0} / 计划 {shortageDaily.arrivals?.expected ?? 0}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500">
                      平均响应 {shortageDaily.response?.avg_response_minutes ?? 0} 分钟，
                      平均解决 {shortageDaily.response?.avg_resolve_hours ?? 0} 小时
                    </div>
                    <div className="grid grid-cols-4 gap-2 text-xs text-slate-400">
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
                    <div className="text-xs text-slate-500">
                      停工 {shortageDaily.stoppage?.count ?? 0} 次 · {shortageDaily.stoppage?.hours ?? 0} 小时
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
          {loadingDaily && (
            <div className="text-sm text-slate-400">正在同步最新日报数据...</div>
          )}
        </div>
      )}


      {/* Key Statistics - 8 column grid for 4 departments */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-8"
      >
        {/* Production Department Stats */}
        <StatCard
          title="生产项目"
          value={productionStats.inProductionProjects}
          subtitle={`今日产出 ${productionStats.todayOutput}`}
          trend={5.2}
          icon={Factory}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="完成率"
          value={`${productionStats.completionRate}%`}
          subtitle="生产完成率"
          icon={Target}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />

        {/* Customer Service Department Stats */}
        <StatCard
          title="服务案例"
          value={mockManufacturingStats.customerService.activeCases}
          subtitle={`今日解决 ${mockManufacturingStats.customerService.resolvedToday}`}
          trend={8.5}
          icon={Headphones}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="满意度"
          value={`${mockManufacturingStats.customerService.customerSatisfaction}%`}
          subtitle="客户满意度"
          icon={Award}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />

        {/* Warehouse Department Stats */}
        <StatCard
          title="库存SKU"
          value={mockManufacturingStats.warehouse.totalItems}
          subtitle={`在库 ${mockManufacturingStats.warehouse.inStockItems}`}
          trend={-2.3}
          icon={Warehouse}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
        <StatCard
          title="周转率"
          value={`${mockManufacturingStats.warehouse.inventoryTurnover}x`}
          subtitle="库存周转"
          icon={Activity}
          color="text-indigo-400"
          bg="bg-indigo-500/10"
        />

        {/* Shipping Department Stats */}
        <StatCard
          title="待发货"
          value={mockManufacturingStats.shipping.pendingShipments}
          subtitle={`今日已发 ${mockManufacturingStats.shipping.shippedToday}`}
          trend={12.5}
          icon={Ship}
          color="text-orange-400"
          bg="bg-orange-500/10"
        />
        <StatCard
          title="准时率"
          value={`${mockManufacturingStats.shipping.onTimeShippingRate}%`}
          subtitle="发货准时率"
          icon={CheckCircle2}
          color="text-green-400"
          bg="bg-green-500/10"
        />
      </motion.div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="bg-surface-50 border-white/10">
          <TabsTrigger value="overview">综合概览</TabsTrigger>
          <TabsTrigger value="production">生产部</TabsTrigger>
          <TabsTrigger value="service">客服部</TabsTrigger>
          <TabsTrigger value="warehouse">仓储部</TabsTrigger>
          <TabsTrigger value="shipping">发货部</TabsTrigger>
          <TabsTrigger value="approvals">审批事项</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Production Overview */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Factory className="w-5 h-5 text-blue-400" />
                  生产部概览
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">车间负荷</span>
                    <span className="text-white font-semibold">
                      {productionStats.workshopLoad}%
                    </span>
                  </div>
                  <Progress value={productionStats.workshopLoad} className="h-2" />
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">在岗人员</p>
                    <p className="text-lg font-semibold text-white">
                      {productionStats.activeWorkers}/{productionStats.totalWorkers}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">在用工位</p>
                    <p className="text-lg font-semibold text-white">
                      {productionStats.activeWorkstations}/{productionStats.totalWorkstations}
                    </p>
                  </div>
                </div>
                <Button variant="outline" className="w-full mt-4" size="sm">
                  <Eye className="w-4 h-4 mr-2" />
                  查看详情
                </Button>
              </CardContent>
            </Card>

            {/* Customer Service Overview */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Headphones className="w-5 h-5 text-purple-400" />
                  客服部概览
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">平均响应时间</span>
                    <span className="text-white font-semibold">
                      {mockManufacturingStats.customerService.avgResponseTime} 小时
                    </span>
                  </div>
                  <Progress value={95} className="h-2" />
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">待处理</p>
                    <p className="text-lg font-semibold text-white">
                      {mockManufacturingStats.customerService.pendingCases}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">在岗工程师</p>
                    <p className="text-lg font-semibold text-white">
                      {mockManufacturingStats.customerService.activeEngineers}/{mockManufacturingStats.customerService.totalEngineers}
                    </p>
                  </div>
                </div>
                <Button variant="outline" className="w-full mt-4" size="sm">
                  <Eye className="w-4 h-4 mr-2" />
                  查看详情
                </Button>
              </CardContent>
            </Card>

            {/* Warehouse & Shipping Overview */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Package className="w-5 h-5 text-cyan-400" />
                  仓储&发货概览
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">仓储利用率</span>
                    <span className="text-white font-semibold">
                      {mockManufacturingStats.warehouse.warehouseUtilization}%
                    </span>
                  </div>
                  <Progress value={mockManufacturingStats.warehouse.warehouseUtilization} className="h-2" />
                  <div className="flex items-center justify-between text-sm pt-2 border-t border-white/10">
                    <span className="text-slate-400">在途订单</span>
                    <span className="text-white font-semibold">
                      {mockManufacturingStats.shipping.inTransit}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">待入库</p>
                    <p className="text-lg font-semibold text-white">
                      {mockManufacturingStats.warehouse.pendingInbound}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">待出库</p>
                    <p className="text-lg font-semibold text-white">
                      {mockManufacturingStats.warehouse.pendingOutbound}
                    </p>
                  </div>
                </div>
                <Button variant="outline" className="w-full mt-4" size="sm">
                  <Eye className="w-4 h-4 mr-2" />
                  查看详情
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Pending Approvals Quick View */}
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardCheck className="w-5 h-5 text-amber-400" />
                  待审批事项
                </CardTitle>
                <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                  {mockPendingApprovals.length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockPendingApprovals.slice(0, 3).map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              item.type === 'production_plan' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              item.type === 'resource_allocation' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                              item.type === 'warehouse_expansion' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                            )}
                          >
                            {item.type === 'production_plan' ? '生产计划' : 
                             item.type === 'resource_allocation' ? '资源调配' : '仓储扩容'}
                          </Badge>
                          {item.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm">
                          {item.projectName || item.title}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {item.submitter} · {item.submitTime.split(' ')[1]}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
                <Button variant="outline" className="w-full mt-3">
                  查看全部审批
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Production Department Tab */}
        <TabsContent value="production" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Workshop Load */}
            <Card className="lg:col-span-2 bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="w-5 h-5 text-primary" />
                  车间负荷情况
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {workshopCards.map((workshop, index) => (
                  <motion.div
                    key={workshop.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50"
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

            {/* Production Stats */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-primary" />
                  生产指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">完成率</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.completionRate}%
                    </p>
                  </div>
                  <Progress value={productionStats.completionRate} className="h-2" />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">准时交付率</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.onTimeDeliveryRate}%
                    </p>
                  </div>
                  <Progress value={productionStats.onTimeDeliveryRate} className="h-2" />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在岗人员</p>
                    <p className="text-lg font-bold text-white">
                      {productionStats.activeWorkers}/{productionStats.totalWorkers}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Customer Service Department Tab */}
        <TabsContent value="service" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Cases */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Headphones className="w-5 h-5 text-purple-400" />
                  服务案例
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockServiceCases.map((caseItem) => (
                  <div
                    key={caseItem.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              caseItem.priority === 'high' && 'bg-red-500/20 text-red-400 border-red-500/30',
                              caseItem.priority === 'medium' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                              caseItem.priority === 'low' && 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                            )}
                          >
                            {caseItem.type}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              caseItem.status === 'resolved' && 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                              caseItem.status === 'in_progress' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              caseItem.status === 'pending' && 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                            )}
                          >
                            {caseItem.status === 'resolved' ? '已解决' : 
                             caseItem.status === 'in_progress' ? '处理中' : '待处理'}
                          </Badge>
                        </div>
                        <p className="font-medium text-white text-sm">{caseItem.projectName}</p>
                        <p className="text-xs text-slate-400 mt-1">{caseItem.customer}</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-400">
                        {caseItem.assignedEngineer ? `工程师: ${caseItem.assignedEngineer}` : '待分配'}
                      </span>
                      {caseItem.responseTime && (
                        <span className="text-slate-400">
                          响应: {caseItem.responseTime} 小时
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Service Stats */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-purple-400" />
                  服务指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">客户满意度</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.customerService.customerSatisfaction}%
                    </p>
                  </div>
                  <Progress value={mockManufacturingStats.customerService.customerSatisfaction} className="h-2" />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">平均响应时间</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.customerService.avgResponseTime} 小时
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在岗工程师</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.customerService.activeEngineers}/{mockManufacturingStats.customerService.totalEngineers}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Warehouse Department Tab */}
        <TabsContent value="warehouse" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Warehouse Alerts */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  库存预警
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockWarehouseAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              alert.status === 'critical' && 'bg-red-500/20 text-red-400 border-red-500/30',
                              alert.status === 'warning' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                              alert.status === 'pending' && 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                            )}
                          >
                            {alert.type === 'low_stock' ? '低库存' : 
                             alert.type === 'out_of_stock' ? '缺货' : '待入库'}
                          </Badge>
                        </div>
                        <p className="font-medium text-white text-sm">{alert.item}</p>
                        {alert.currentStock !== undefined && (
                          <p className="text-xs text-slate-400 mt-1">
                            当前库存: {alert.currentStock} | 最低库存: {alert.minStock}
                          </p>
                        )}
                        {alert.expectedDate && (
                          <p className="text-xs text-slate-400 mt-1">
                            预计到货: {alert.expectedDate}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Warehouse Stats */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-cyan-400" />
                  仓储指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">仓储利用率</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.warehouse.warehouseUtilization}%
                    </p>
                  </div>
                  <Progress value={mockManufacturingStats.warehouse.warehouseUtilization} className="h-2" />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">库存周转率</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.warehouse.inventoryTurnover}x
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在库SKU</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.warehouse.inStockItems}/{mockManufacturingStats.warehouse.totalItems}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Shipping Department Tab */}
        <TabsContent value="shipping" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Shipping Orders */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Ship className="w-5 h-5 text-orange-400" />
                  发货订单
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockShippingOrders.map((order) => (
                  <div
                    key={order.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              order.status === 'delivered' && 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                              order.status === 'in_transit' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              order.status === 'pending' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                            )}
                          >
                            {order.status === 'delivered' ? '已送达' : 
                             order.status === 'in_transit' ? '运输中' : '待发货'}
                          </Badge>
                          {order.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm">{order.projectName}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {order.orderNo} · {order.customer} · {order.destination}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-400">
                        {order.status === 'pending' && `计划发货: ${order.plannedShipDate}`}
                        {order.status === 'in_transit' && `预计到达: ${order.estimatedArrival}`}
                        {order.status === 'delivered' && `送达时间: ${order.deliveredDate}`}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Shipping Stats */}
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="w-5 h-5 text-orange-400" />
                  发货指标
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">准时发货率</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.shipping.onTimeShippingRate}%
                    </p>
                  </div>
                  <Progress value={mockManufacturingStats.shipping.onTimeShippingRate} className="h-2" />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">平均发货时间</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.shipping.avgShippingTime} 天
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在途订单</p>
                    <p className="text-lg font-bold text-white">
                      {mockManufacturingStats.shipping.inTransit}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Approvals Tab */}
        <TabsContent value="approvals" className="space-y-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardCheck className="w-5 h-5 text-amber-400" />
                  待审批事项
                </CardTitle>
                <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                  {mockPendingApprovals.length}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {mockPendingApprovals.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            item.type === 'production_plan' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                            item.type === 'resource_allocation' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                            item.type === 'warehouse_expansion' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                          )}
                        >
                          {item.type === 'production_plan' ? '生产计划' : 
                           item.type === 'resource_allocation' ? '资源调配' : '仓储扩容'}
                        </Badge>
                        {item.priority === 'high' && (
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                            紧急
                          </Badge>
                        )}
                      </div>
                      <p className="font-medium text-white text-sm mb-1">
                        {item.projectName || item.title}
                      </p>
                      {item.planCode && (
                        <p className="text-xs text-slate-400 mb-1">
                          {item.planCode} · {item.workshop} · {item.startDate} ~ {item.endDate}
                        </p>
                      )}
                      {item.request && (
                        <p className="text-xs text-slate-400 mb-1">{item.request}</p>
                      )}
                      {item.amount && (
                        <p className="text-xs text-slate-400 mb-1">金额: {formatCurrency(item.amount)}</p>
                      )}
                      <p className="text-xs text-slate-400 mt-2">
                        {item.submitter} · {item.submitTime}
                      </p>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600">
                        审批
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
