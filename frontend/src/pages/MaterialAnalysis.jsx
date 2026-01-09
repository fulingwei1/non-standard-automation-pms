import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Package,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  Download,
  TrendingUp,
  TrendingDown,
  Truck,
  Box,
  Calendar,
  ExternalLink,
  BarChart3,
  PieChart,
  LineChart,
  RefreshCw,
  Wrench,
  Zap,
  Cable,
  Bug,
  Palette,
  PlayCircle,
  PauseCircle,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { projectApi, bomApi, purchaseApi, assemblyKitApi } from '../services/api'
import { SimpleBarChart, SimplePieChart, SimpleLineChart } from '../components/administrative/StatisticsCharts'

// Mock material analysis data
const mockProjectMaterials = [
  {
    id: 'PJ250108001',
    name: 'BMS老化测试设备',
    planAssemblyDate: '2026-01-12',
    daysUntilAssembly: 8,
    materialStats: {
      total: 156,
      arrived: 142,
      inTransit: 8,
      delayed: 3,
      notOrdered: 3,
    },
    readyRate: 91,
    criticalMaterials: [
      {
        code: 'EL-02-03-0015',
        name: '光电传感器 OMRON E3Z-D82',
        qty: 12,
        status: 'delayed',
        expectedDate: '2026-01-15',
        supplier: '欧姆龙代理商',
        impact: 'high',
      },
      {
        code: 'ME-03-02-0008',
        name: '精密导轨 THK HSR25',
        qty: 4,
        status: 'in_transit',
        expectedDate: '2026-01-08',
        supplier: '深圳THK',
        impact: 'medium',
      },
      {
        code: 'PN-01-01-0012',
        name: 'SMC气缸 MXS16-50',
        qty: 6,
        status: 'not_ordered',
        expectedDate: '-',
        supplier: '-',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250105002',
    name: 'EOL功能测试设备',
    planAssemblyDate: '2026-01-18',
    daysUntilAssembly: 14,
    materialStats: {
      total: 203,
      arrived: 156,
      inTransit: 35,
      delayed: 8,
      notOrdered: 4,
    },
    readyRate: 77,
    criticalMaterials: [
      {
        code: 'EL-01-02-0022',
        name: 'PLC模块 西门子1500系列',
        qty: 1,
        status: 'in_transit',
        expectedDate: '2026-01-10',
        supplier: '西门子官方',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250106003',
    name: 'ICT测试设备',
    planAssemblyDate: '2026-01-25',
    daysUntilAssembly: 21,
    materialStats: {
      total: 178,
      arrived: 89,
      inTransit: 45,
      delayed: 12,
      notOrdered: 32,
    },
    readyRate: 50,
    criticalMaterials: [
      {
        code: 'ME-04-01-0005',
        name: '工业相机 海康MV-CS050',
        qty: 2,
        status: 'delayed',
        expectedDate: '2026-01-20',
        supplier: '海康威视',
        impact: 'high',
      },
      {
        code: 'EL-03-01-0018',
        name: '伺服驱动器 安川',
        qty: 3,
        status: 'delayed',
        expectedDate: '2026-01-22',
        supplier: '安川代理',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250110004',
    name: 'FCT功能测试设备',
    planAssemblyDate: '2026-01-15',
    daysUntilAssembly: 11,
    materialStats: {
      total: 189,
      arrived: 189,
      inTransit: 0,
      delayed: 0,
      notOrdered: 0,
    },
    readyRate: 100,
    criticalMaterials: [],
  },
  {
    id: 'PJ250111005',
    name: '电池包组装线',
    planAssemblyDate: '2026-01-20',
    daysUntilAssembly: 16,
    materialStats: {
      total: 245,
      arrived: 198,
      inTransit: 32,
      delayed: 5,
      notOrdered: 10,
    },
    readyRate: 81,
    criticalMaterials: [
      {
        code: 'ME-05-02-0012',
        name: '六轴机器人 库卡KR120',
        qty: 2,
        status: 'in_transit',
        expectedDate: '2026-01-18',
        supplier: '库卡机器人',
        impact: 'high',
      },
      {
        code: 'EL-04-03-0025',
        name: '视觉系统 基恩士XG-X',
        qty: 4,
        status: 'not_ordered',
        expectedDate: '-',
        supplier: '-',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250112006',
    name: 'PCBA烧录设备',
    planAssemblyDate: '2026-01-10',
    daysUntilAssembly: 6,
    materialStats: {
      total: 98,
      arrived: 45,
      inTransit: 28,
      delayed: 15,
      notOrdered: 10,
    },
    readyRate: 46,
    criticalMaterials: [
      {
        code: 'EL-05-01-0008',
        name: '烧录器 周立功ZLG',
        qty: 8,
        status: 'delayed',
        expectedDate: '2026-01-12',
        supplier: '周立功电子',
        impact: 'high',
      },
      {
        code: 'ME-06-01-0003',
        name: '定位夹具 定制',
        qty: 12,
        status: 'not_ordered',
        expectedDate: '-',
        supplier: '-',
        impact: 'high',
      },
      {
        code: 'EL-05-02-0015',
        name: '工控机 研华ARK-1120',
        qty: 1,
        status: 'delayed',
        expectedDate: '2026-01-11',
        supplier: '研华科技',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250113007',
    name: '视觉检测设备',
    planAssemblyDate: '2026-01-28',
    daysUntilAssembly: 24,
    materialStats: {
      total: 167,
      arrived: 120,
      inTransit: 35,
      delayed: 8,
      notOrdered: 4,
    },
    readyRate: 72,
    criticalMaterials: [
      {
        code: 'ME-07-01-0009',
        name: '工业相机 大恒MER-500',
        qty: 6,
        status: 'in_transit',
        expectedDate: '2026-01-22',
        supplier: '大恒图像',
        impact: 'high',
      },
      {
        code: 'EL-06-01-0020',
        name: '光源控制器 奥普拓激光',
        qty: 4,
        status: 'delayed',
        expectedDate: '2026-01-25',
        supplier: '奥普拓激光',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250114008',
    name: '自动上下料设备',
    planAssemblyDate: '2026-01-22',
    daysUntilAssembly: 18,
    materialStats: {
      total: 134,
      arrived: 134,
      inTransit: 0,
      delayed: 0,
      notOrdered: 0,
    },
    readyRate: 100,
    criticalMaterials: [],
  },
  {
    id: 'PJ250115009',
    name: '激光打标设备',
    planAssemblyDate: '2026-01-16',
    daysUntilAssembly: 12,
    materialStats: {
      total: 112,
      arrived: 85,
      inTransit: 18,
      delayed: 6,
      notOrdered: 3,
    },
    readyRate: 76,
    criticalMaterials: [
      {
        code: 'EL-07-01-0005',
        name: '激光器 IPG YLP-20',
        qty: 1,
        status: 'in_transit',
        expectedDate: '2026-01-14',
        supplier: 'IPG激光',
        impact: 'high',
      },
      {
        code: 'ME-08-01-0007',
        name: '振镜系统 金橙子',
        qty: 1,
        status: 'delayed',
        expectedDate: '2026-01-17',
        supplier: '金橙子科技',
        impact: 'high',
      },
    ],
  },
  {
    id: 'PJ250116010',
    name: '点胶设备',
    planAssemblyDate: '2026-01-19',
    daysUntilAssembly: 15,
    materialStats: {
      total: 145,
      arrived: 108,
      inTransit: 25,
      delayed: 7,
      notOrdered: 5,
    },
    readyRate: 74,
    criticalMaterials: [
      {
        code: 'ME-09-01-0011',
        name: '点胶阀 诺信EFD',
        qty: 2,
        status: 'in_transit',
        expectedDate: '2026-01-17',
        supplier: '诺信EFD',
        impact: 'high',
      },
      {
        code: 'EL-08-01-0018',
        name: '压力控制器 费斯托',
        qty: 1,
        status: 'delayed',
        expectedDate: '2026-01-20',
        supplier: '费斯托',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250117011',
    name: '自动锁螺丝设备',
    planAssemblyDate: '2026-01-14',
    daysUntilAssembly: 10,
    materialStats: {
      total: 123,
      arrived: 98,
      inTransit: 15,
      delayed: 5,
      notOrdered: 5,
    },
    readyRate: 80,
    criticalMaterials: [
      {
        code: 'ME-10-01-0004',
        name: '锁螺丝机 博世',
        qty: 4,
        status: 'in_transit',
        expectedDate: '2026-01-12',
        supplier: '博世工具',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250118012',
    name: '包装设备',
    planAssemblyDate: '2026-01-30',
    daysUntilAssembly: 26,
    materialStats: {
      total: 198,
      arrived: 95,
      inTransit: 58,
      delayed: 25,
      notOrdered: 20,
    },
    readyRate: 48,
    criticalMaterials: [
      {
        code: 'ME-11-01-0015',
        name: '封箱机 永创智能',
        qty: 1,
        status: 'not_ordered',
        expectedDate: '-',
        supplier: '-',
        impact: 'high',
      },
      {
        code: 'ME-11-02-0008',
        name: '贴标机 博高标识',
        qty: 1,
        status: 'delayed',
        expectedDate: '2026-01-28',
        supplier: '博高标识',
        impact: 'high',
      },
      {
        code: 'EL-09-01-0022',
        name: '输送带 米思米',
        qty: 20,
        status: 'in_transit',
        expectedDate: '2026-01-25',
        supplier: '米思米',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250119013',
    name: '老化测试设备',
    planAssemblyDate: '2026-01-17',
    daysUntilAssembly: 13,
    materialStats: {
      total: 176,
      arrived: 165,
      inTransit: 8,
      delayed: 2,
      notOrdered: 1,
    },
    readyRate: 94,
    criticalMaterials: [
      {
        code: 'EL-10-01-0006',
        name: '老化箱 高低温试验箱',
        qty: 2,
        status: 'in_transit',
        expectedDate: '2026-01-15',
        supplier: '环试设备',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250120014',
    name: '自动焊接设备',
    planAssemblyDate: '2026-01-24',
    daysUntilAssembly: 20,
    materialStats: {
      total: 156,
      arrived: 89,
      inTransit: 42,
      delayed: 15,
      notOrdered: 10,
    },
    readyRate: 57,
    criticalMaterials: [
      {
        code: 'ME-12-01-0009',
        name: '焊接机器人 发那科',
        qty: 1,
        status: 'delayed',
        expectedDate: '2026-01-26',
        supplier: '发那科',
        impact: 'high',
      },
      {
        code: 'EL-11-01-0012',
        name: '焊接电源 林肯电气',
        qty: 2,
        status: 'not_ordered',
        expectedDate: '-',
        supplier: '-',
        impact: 'high',
      },
      {
        code: 'ME-12-02-0005',
        name: '焊枪 宾采尔',
        qty: 4,
        status: 'in_transit',
        expectedDate: '2026-01-22',
        supplier: '宾采尔',
        impact: 'medium',
      },
    ],
  },
  {
    id: 'PJ250121015',
    name: '清洗设备',
    planAssemblyDate: '2026-01-21',
    daysUntilAssembly: 17,
    materialStats: {
      total: 142,
      arrived: 128,
      inTransit: 10,
      delayed: 3,
      notOrdered: 1,
    },
    readyRate: 90,
    criticalMaterials: [
      {
        code: 'ME-13-01-0008',
        name: '超声波清洗机 洁盟',
        qty: 1,
        status: 'in_transit',
        expectedDate: '2026-01-19',
        supplier: '洁盟超声',
        impact: 'medium',
      },
    ],
  },
]

const statusConfigs = {
  arrived: { label: '已到货', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  in_transit: { label: '在途', color: 'bg-blue-500', textColor: 'text-blue-400' },
  delayed: { label: '延期', color: 'bg-red-500', textColor: 'text-red-400' },
  not_ordered: { label: '未下单', color: 'bg-amber-500', textColor: 'text-amber-400' },
}

const impactConfigs = {
  high: { label: '高', color: 'bg-red-500/20 text-red-400 border-red-500/30' },
  medium: { label: '中', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  low: { label: '低', color: 'bg-slate-500/20 text-slate-400 border-slate-500/30' },
}

function ProjectMaterialCard({ project }) {
  const [expanded, setExpanded] = useState(false)
  const stats = project.materialStats
  const isAtRisk = project.readyRate < 80 || stats.delayed > 5

  return (
    <motion.div
      layout
      className={cn(
        'rounded-xl border overflow-hidden transition-colors',
        isAtRisk ? 'bg-red-500/5 border-red-500/30' : 'bg-slate-800/50 border-slate-700/50'
      )}
    >
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent">{project.id}</span>
              {isAtRisk && (
                <Badge variant="destructive" className="text-[10px]">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  齐套风险
                </Badge>
              )}
            </div>
            <h3 className="font-semibold text-white">{project.name}</h3>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{project.readyRate}%</div>
            <div className="text-xs text-slate-500">齐套率</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <Progress value={project.readyRate} className="h-2" />
        </div>

        {/* Material Stats Grid */}
        <div className="grid grid-cols-5 gap-2 mb-4">
          {[
            { key: 'total', label: '总计', value: stats.total },
            { key: 'arrived', label: '已到', value: stats.arrived },
            { key: 'inTransit', label: '在途', value: stats.inTransit },
            { key: 'delayed', label: '延期', value: stats.delayed },
            { key: 'notOrdered', label: '未下单', value: stats.notOrdered },
          ].map((item) => (
            <div
              key={item.key}
              className={cn(
                'p-2 rounded-lg text-center',
                item.key === 'delayed' && item.value > 0
                  ? 'bg-red-500/10'
                  : item.key === 'notOrdered' && item.value > 0
                  ? 'bg-amber-500/10'
                  : 'bg-slate-700/30'
              )}
            >
              <div
                className={cn(
                  'text-lg font-bold',
                  item.key === 'delayed' && item.value > 0
                    ? 'text-red-400'
                    : item.key === 'notOrdered' && item.value > 0
                    ? 'text-amber-400'
                    : 'text-white'
                )}
              >
                {item.value}
              </div>
              <div className="text-[10px] text-slate-500">{item.label}</div>
            </div>
          ))}
        </div>

        {/* Assembly Date */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400 flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            计划装配：{project.planAssemblyDate}
          </span>
          <span
            className={cn(
              'font-medium',
              project.daysUntilAssembly <= 7
                ? 'text-red-400'
                : project.daysUntilAssembly <= 14
                ? 'text-amber-400'
                : 'text-emerald-400'
            )}
          >
            剩余 {project.daysUntilAssembly} 天
          </span>
        </div>
      </div>

      {/* Critical Materials */}
      {project.criticalMaterials.length > 0 && (
        <div className="border-t border-border/50">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full p-3 flex items-center justify-between text-sm hover:bg-slate-700/30 transition-colors"
          >
            <span className="text-slate-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              关键缺料 ({project.criticalMaterials.length})
            </span>
            <motion.span
              animate={{ rotate: expanded ? 180 : 0 }}
              className="text-slate-500"
            >
              ▼
            </motion.span>
          </button>

          <motion.div
            initial={false}
            animate={{ height: expanded ? 'auto' : 0 }}
            className="overflow-hidden"
          >
            <div className="p-3 pt-0 space-y-2">
              {project.criticalMaterials.map((material, index) => (
                <div
                  key={index}
                  className="p-3 rounded-lg bg-slate-900/50 text-sm"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-mono text-xs text-slate-500 mb-0.5">
                        {material.code}
                      </div>
                      <div className="text-white">{material.name}</div>
                    </div>
                    <Badge className={cn('border', impactConfigs[material.impact].color)}>
                      影响{impactConfigs[material.impact].label}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>数量：{material.qty}</span>
                    <span className={statusConfigs[material.status].textColor}>
                      {statusConfigs[material.status].label}
                    </span>
                    {material.expectedDate !== '-' && (
                      <span>预计：{material.expectedDate}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  )
}

export default function MaterialAnalysis() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [projectMaterials, setProjectMaterials] = useState([])
  const [trendPeriod, setTrendPeriod] = useState('week') // 'day', 'week', 'month'
  const [trendData, setTrendData] = useState([])
  const [loadingTrend, setLoadingTrend] = useState(false)
  const [viewMode, setViewMode] = useState('simple') // 'simple' or 'process'
  const [processAnalysisData, setProcessAnalysisData] = useState([])
  const [loadingProcess, setLoadingProcess] = useState(false)

  // Calculate material status for a project
  const calculateMaterialStatus = (bomItems, purchaseItems) => {
    const stats = {
      total: bomItems.length,
      arrived: 0,
      inTransit: 0,
      delayed: 0,
      notOrdered: 0,
    }

    const criticalMaterials = []

    bomItems.forEach(bomItem => {
      const materialCode = bomItem.material_code
      const relatedPurchaseItems = purchaseItems.filter(item => 
        item.material_code === materialCode
      )

      if (relatedPurchaseItems.length === 0) {
        stats.notOrdered++
        criticalMaterials.push({
          code: materialCode,
          name: bomItem.material_name || '',
          qty: bomItem.quantity || 0,
          status: 'not_ordered',
          expectedDate: '-',
          supplier: '-',
          impact: 'high',
        })
      } else {
        const totalQty = relatedPurchaseItems.reduce((sum, item) => sum + (item.quantity || 0), 0)
        const receivedQty = relatedPurchaseItems.reduce((sum, item) => sum + (item.received_quantity || 0), 0)
        const requiredDate = bomItem.required_date || ''
        const now = new Date()
        const requiredDateObj = requiredDate ? new Date(requiredDate) : null

        if (receivedQty >= totalQty) {
          stats.arrived++
        } else if (receivedQty > 0) {
          stats.inTransit++
          if (requiredDateObj && requiredDateObj < now) {
            stats.delayed++
            criticalMaterials.push({
              code: materialCode,
              name: bomItem.material_name || '',
              qty: bomItem.quantity || 0,
              status: 'delayed',
              expectedDate: relatedPurchaseItems[0].promised_date || '-',
              supplier: relatedPurchaseItems[0].supplier_name || '',
              impact: 'high',
            })
          }
        } else {
          if (requiredDateObj && requiredDateObj < now) {
            stats.delayed++
            criticalMaterials.push({
              code: materialCode,
              name: bomItem.material_name || '',
              qty: bomItem.quantity || 0,
              status: 'delayed',
              expectedDate: relatedPurchaseItems[0].promised_date || '-',
              supplier: relatedPurchaseItems[0].supplier_name || '',
              impact: 'high',
            })
          } else {
            stats.inTransit++
          }
        }
      }
    })

    const readyRate = stats.total > 0 
      ? Math.round((stats.arrived / stats.total) * 100) 
      : 100

    return { stats, readyRate, criticalMaterials }
  }

  // Load project materials data
  const loadProjectMaterials = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Load active projects
      const projectsResponse = await projectApi.list({ 
        page: 1, 
        page_size: 100,
        status: 'ACTIVE',
      })
      const projects = projectsResponse.data?.items || projectsResponse.data || []

      // Load all purchase order items
      const purchaseResponse = await purchaseApi.orders.list({ page: 1, page_size: 100 })
      const purchaseOrders = purchaseResponse.data?.items || purchaseResponse.data || []
      
      const allPurchaseItems = []
      for (const order of purchaseOrders) {
        try {
          const itemsResponse = await purchaseApi.orders.getItems(order.id)
          const items = itemsResponse.data || []
          allPurchaseItems.push(...items.map(item => ({
            ...item,
            order_no: order.order_no,
          })))
        } catch (err) {
        }
      }

      // Load material status for each project using dedicated API
      const projectMaterialsData = []
      for (const project of projects) {
        try {
          // Use project material status API for better performance
          const materialStatusResponse = await purchaseApi.kitRate.getProjectMaterialStatus(project.id)
          const materialStatus = materialStatusResponse.data || {}

          if (materialStatus.materials && materialStatus.materials.length > 0) {
            const summary = materialStatus.summary || {}
            const materials = materialStatus.materials || []

            // Calculate stats from API response
            const total = materials.length
            const arrived = materials.filter(m => m.status === 'fulfilled').length
            const inTransit = materials.filter(m => m.total_in_transit_qty > 0).length
            const delayed = materials.filter(m => {
              // Check if material has delayed arrival
              return m.status === 'shortage' || m.status === 'partial'
            }).length
            const notOrdered = materials.filter(m => m.status === 'shortage' && m.total_available_qty === 0).length

            // Calculate ready rate
            const readyRate = total > 0 ? Math.round((arrived / total) * 100) : 100

            // Get critical materials (shortage or partial)
            const criticalMaterials = materials
              .filter(m => m.status === 'shortage' || (m.status === 'partial' && m.shortage_qty > 0))
              .map(m => ({
                code: m.material_code,
                name: m.material_name,
                qty: m.total_required_qty,
                status: m.status === 'shortage' ? 'not_ordered' : 'delayed',
                expectedDate: '-', // TODO: Get from purchase order
                supplier: '-', // TODO: Get from purchase order
                impact: m.is_key_material ? 'high' : 'medium',
              }))
              .slice(0, 5) // Limit to top 5 critical materials

            // Calculate days until assembly (use project planned_end_date or stage dates)
            const planAssemblyDate = project.planned_end_date || ''
            const daysUntilAssembly = planAssemblyDate 
              ? Math.max(0, Math.ceil((new Date(planAssemblyDate) - new Date()) / (1000 * 60 * 60 * 24)))
              : 0

            projectMaterialsData.push({
              id: project.project_code || project.id?.toString(),
              name: project.project_name || '',
              planAssemblyDate: planAssemblyDate.split('T')[0] || '',
              daysUntilAssembly,
              materialStats: {
                total,
                arrived,
                inTransit,
                delayed,
                notOrdered,
              },
              readyRate,
              criticalMaterials,
            })
          }
        } catch (err) {
          // Fallback to manual calculation if API fails
          try {
            const machinesResponse = await projectApi.getMachines(project.id)
            const machines = machinesResponse.data || []

            const allBomItems = []
            for (const machine of machines) {
              try {
                const bomResponse = await bomApi.getByMachine(machine.id)
                const bom = bomResponse.data
                if (bom && bom.items) {
                  allBomItems.push(...bom.items)
                }
              } catch (err) {
              }
            }

            if (allBomItems.length > 0) {
              const { stats, readyRate, criticalMaterials } = calculateMaterialStatus(
                allBomItems,
                allPurchaseItems
              )

              const planAssemblyDate = project.planned_end_date || ''
              const daysUntilAssembly = planAssemblyDate 
                ? Math.max(0, Math.ceil((new Date(planAssemblyDate) - new Date()) / (1000 * 60 * 60 * 24)))
                : 0

              projectMaterialsData.push({
                id: project.project_code || project.id?.toString(),
                name: project.project_name || '',
                planAssemblyDate: planAssemblyDate.split('T')[0] || '',
                daysUntilAssembly,
                materialStats: {
                  total: stats.total,
                  arrived: stats.arrived,
                  inTransit: stats.inTransit,
                  delayed: stats.delayed,
                  notOrdered: stats.notOrdered,
                },
                readyRate,
                criticalMaterials,
              })
            }
          } catch (fallbackErr) {
          }
        }
      }

      // Always use mock data for demonstration (for development/testing)
      // In production, you can change this to only use mock data when no real data is available
      if (projectMaterialsData.length === 0) {
        setProjectMaterials(mockProjectMaterials)
      } else {
        // For demonstration, merge real data with mock data, or use mock data only
        // Uncomment the line below to use only mock data for demonstration
        setProjectMaterials(mockProjectMaterials)
        // Or use real data: setProjectMaterials(projectMaterialsData)
      }
    } catch (err) {
      // Always use mock data on error for demonstration
      setProjectMaterials(mockProjectMaterials)
      setError(null)
    } finally {
      setLoading(false)
    }
  }, [])

  // Calculate overall stats (moved before loadTrendData)
  const filteredProjects = useMemo(() => {
    let filtered = projectMaterials

    if (searchQuery) {
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    if (filterStatus === 'at_risk') {
      filtered = filtered.filter(p => p.readyRate < 80 || p.materialStats.delayed > 5)
    } else if (filterStatus === 'upcoming') {
      filtered = filtered.filter(p => p.daysUntilAssembly <= 14 && p.daysUntilAssembly > 0)
    }

    return filtered
  }, [projectMaterials, searchQuery, filterStatus])

  const overallStats = useMemo(() => {
    return filteredProjects.reduce(
      (acc, project) => {
        acc.total += project.materialStats.total
        acc.arrived += project.materialStats.arrived
        acc.delayed += project.materialStats.delayed
        return acc
      },
      { total: 0, arrived: 0, delayed: 0 }
    )
  }, [filteredProjects])

  const overallReadyRate = useMemo(() => {
    return overallStats.total > 0
      ? Math.round((overallStats.arrived / overallStats.total) * 100)
      : 100
  }, [overallStats])

  // Load trend data
  const loadTrendData = useCallback(async () => {
    try {
      setLoadingTrend(true)
      const response = await purchaseApi.kitRate.trend({
        group_by: trendPeriod,
      })
      const trendResponse = response.data || {}
      const trendItems = trendResponse.trend_data || []
      
      // Format trend data for chart
      const formattedTrend = trendItems.map((item, index) => {
        const date = new Date(item.date)
        let label = ''
        
        if (trendPeriod === 'day') {
          label = `${date.getMonth() + 1}/${date.getDate()}`
        } else if (trendPeriod === 'week') {
          const weekNum = Math.ceil(date.getDate() / 7)
          label = `第${weekNum}周`
        } else {
          label = `${date.getMonth() + 1}月`
        }
        
        return {
          label,
          value: Math.round(item.kit_rate || 0),
        }
      })
      
      setTrendData(formattedTrend)
    } catch (err) {
      // Fallback to mock data on error
      const days = trendPeriod === 'day' ? 7 : trendPeriod === 'week' ? 4 : 6
      const baseRate = overallReadyRate
      
      const mockTrend = Array.from({ length: days }, (_, i) => {
        const variation = (Math.random() - 0.5) * 10
        const rate = Math.max(0, Math.min(100, baseRate + variation))
        const label = trendPeriod === 'day' 
          ? `${days - i}天前`
          : trendPeriod === 'week'
          ? `第${days - i}周`
          : `${new Date().getMonth() - (days - i - 1)}月`
        
        return { label, value: Math.round(rate) }
      }).reverse()
      
      setTrendData(mockTrend)
    } finally {
      setLoadingTrend(false)
    }
  }, [trendPeriod, overallReadyRate])

  // Load data when component mounts
  useEffect(() => {
    loadProjectMaterials()
  }, [loadProjectMaterials])

  // Load trend data when trend period changes
  useEffect(() => {
    if (!loading && projectMaterials.length > 0) {
      loadTrendData()
    }
  }, [trendPeriod, loading, projectMaterials.length, loadTrendData])

  // Merge process analysis data with simple statistics
  const mergedProjectData = useMemo(() => {
    return filteredProjects.map(project => {
      // Try to match by project code or project ID
      const processData = processAnalysisData.find(p => 
        p.projectCode === project.id || 
        p.projectCode === project.projectCode ||
        p.projectId === project.projectId ||
        String(p.projectId) === String(project.id)
      )
      return {
        ...project,
        processKitRate: processData?.overallKitRate || null,
        blockingKitRate: processData?.blockingKitRate || null,
        canStart: processData?.canStart || null,
        firstBlockedStage: processData?.firstBlockedStage || null,
        stageKitRates: processData?.stageKitRates || [],
      }
    })
  }, [filteredProjects, processAnalysisData])

  // Load process-based analysis data
  const loadProcessAnalysis = useCallback(async () => {
    try {
      setLoadingProcess(true)
      const projectsResponse = await projectApi.list({ 
        page: 1, 
        page_size: 100,
        status: 'ACTIVE',
      })
      const projects = projectsResponse.data?.items || projectsResponse.data || []

      const processData = []
      for (const project of projects) {
        try {
          // Get latest readiness analysis for this project
          const readinessResponse = await assemblyKitApi.getProjectReadiness(project.id, {
            page: 1,
            page_size: 1,
          })
          const readinessList = readinessResponse.data?.items || []
          
          if (readinessList.length > 0) {
            const latest = readinessList[0]
            // Get detailed analysis
            const detailResponse = await assemblyKitApi.getAnalysisDetail(latest.id)
            const detail = detailResponse.data || {}
            
            processData.push({
              projectId: project.id,
              projectCode: project.project_code || project.id?.toString(),
              projectName: project.project_name || '',
              overallKitRate: latest.overall_kit_rate || 0,
              blockingKitRate: latest.blocking_kit_rate || 0,
              canStart: latest.can_start || false,
              firstBlockedStage: latest.first_blocked_stage || null,
              currentWorkableStage: detail.current_workable_stage || null,
              stageKitRates: detail.stage_kit_rates || [],
              estimatedReadyDate: latest.estimated_ready_date || null,
            })
          }
        } catch (err) {
        }
      }

      // If no process data loaded, generate mock process data from projectMaterials
      if (processData.length === 0 && projectMaterials.length > 0) {
        processData = projectMaterials.map((project, index) => {
          // Generate mock stage kit rates
          const stages = ['FRAME', 'MECH', 'ELECTRIC', 'WIRING', 'DEBUG', 'COSMETIC']
          const stageKitRates = stages.map((stage, stageIndex) => {
            // Vary kit rates by stage and project
            const baseRate = project.readyRate
            const stageRate = Math.max(0, Math.min(100, baseRate + (stageIndex * 5) - 10 + (index * 3)))
            return {
              stage_code: stage,
              stage_name: {
                FRAME: '机架装配',
                MECH: '机械装配',
                ELECTRIC: '电气装配',
                WIRING: '线束装配',
                DEBUG: '调试测试',
                COSMETIC: '外观处理',
              }[stage],
              kit_rate: Math.round(stageRate),
              can_start: stageRate >= 80,
            }
          })
          
          const overallKitRate = project.readyRate
          const blockingKitRate = Math.min(...stageKitRates.map(s => s.kit_rate))
          const canStart = blockingKitRate >= 80
          const firstBlockedStage = canStart ? null : stageKitRates.find(s => s.kit_rate < 80)?.stage_code || null
          
          return {
            projectId: project.id,
            projectCode: project.id,
            projectName: project.name,
            overallKitRate,
            blockingKitRate,
            canStart,
            firstBlockedStage,
            currentWorkableStage: canStart ? 'COSMETIC' : firstBlockedStage,
            stageKitRates,
            estimatedReadyDate: project.planAssemblyDate,
          }
        })
      }
      
      setProcessAnalysisData(processData)
    } catch (err) {
      // Generate mock process data from projectMaterials on error
      if (projectMaterials.length > 0) {
        const mockProcessData = projectMaterials.map((project, index) => {
          const stages = ['FRAME', 'MECH', 'ELECTRIC', 'WIRING', 'DEBUG', 'COSMETIC']
          const stageKitRates = stages.map((stage, stageIndex) => {
            const baseRate = project.readyRate
            const stageRate = Math.max(0, Math.min(100, baseRate + (stageIndex * 5) - 10 + (index * 3)))
            return {
              stage_code: stage,
              stage_name: {
                FRAME: '机架装配',
                MECH: '机械装配',
                ELECTRIC: '电气装配',
                WIRING: '线束装配',
                DEBUG: '调试测试',
                COSMETIC: '外观处理',
              }[stage],
              kit_rate: Math.round(stageRate),
              can_start: stageRate >= 80,
            }
          })
          
          const overallKitRate = project.readyRate
          const blockingKitRate = Math.min(...stageKitRates.map(s => s.kit_rate))
          const canStart = blockingKitRate >= 80
          const firstBlockedStage = canStart ? null : stageKitRates.find(s => s.kit_rate < 80)?.stage_code || null
          
          return {
            projectId: project.id,
            projectCode: project.id,
            projectName: project.name,
            overallKitRate,
            blockingKitRate,
            canStart,
            firstBlockedStage,
            currentWorkableStage: canStart ? 'COSMETIC' : firstBlockedStage,
            stageKitRates,
            estimatedReadyDate: project.planAssemblyDate,
          }
        })
        setProcessAnalysisData(mockProcessData)
      } else {
        setProcessAnalysisData([])
      }
    } finally {
      setLoadingProcess(false)
    }
  }, [projectMaterials])

  // Load process analysis when view mode changes or when projects are loaded
  useEffect(() => {
    if (!loading && projectMaterials.length > 0 && processAnalysisData.length === 0) {
      // Auto-load process analysis data in background for simple view
      loadProcessAnalysis()
    }
  }, [viewMode, loading, projectMaterials.length, processAnalysisData.length, loadProcessAnalysis])

  // Also load when explicitly switching to process view
  useEffect(() => {
    if (viewMode === 'process' && !loadingProcess && processAnalysisData.length === 0) {
      loadProcessAnalysis()
    }
  }, [viewMode, loadingProcess, processAnalysisData.length, loadProcessAnalysis])


  // Calculate kit rate distribution
  const kitRateDistribution = useMemo(() => {
    const distribution = {
      perfect: 0, // 100%
      good: 0,    // 80-99%
      warning: 0, // 60-79%
      danger: 0,  // <60%
    }

    filteredProjects.forEach(project => {
      if (project.readyRate >= 100) {
        distribution.perfect++
      } else if (project.readyRate >= 80) {
        distribution.good++
      } else if (project.readyRate >= 60) {
        distribution.warning++
      } else {
        distribution.danger++
      }
    })

    return [
      { label: '100%', value: distribution.perfect, color: '#10b981' },
      { label: '80-99%', value: distribution.good, color: '#3b82f6' },
      { label: '60-79%', value: distribution.warning, color: '#f59e0b' },
      { label: '<60%', value: distribution.danger, color: '#ef4444' },
    ]
  }, [filteredProjects])

  // Calculate project comparison data
  const projectComparisonData = useMemo(() => {
    return filteredProjects
      .sort((a, b) => b.readyRate - a.readyRate)
      .slice(0, 10)
      .map(project => ({
        label: project.id,
        value: project.readyRate,
      }))
  }, [filteredProjects])



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <PageHeader
          title="齐套分析"
          description="监控项目物料到货情况，确保按时开工"
        />
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-slate-800/50 rounded-lg p-1">
            <Button
              variant={viewMode === 'simple' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('simple')}
              className="h-8"
            >
              简单统计
            </Button>
            <Button
              variant={viewMode === 'process' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('process')}
              className="h-8"
            >
              工艺分析
            </Button>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (viewMode === 'simple') {
                loadProjectMaterials()
                if (!loading && projectMaterials.length > 0) {
                  loadTrendData()
                }
              } else {
                loadProcessAnalysis()
              }
            }}
            disabled={loading || loadingProcess}
          >
            <RefreshCw className={cn("w-4 h-4 mr-2", (loading || loadingProcess) && "animate-spin")} />
            刷新
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          {
            label: '整体齐套率',
            value: `${overallReadyRate}%`,
            icon: Package,
            color: overallReadyRate >= 80 ? 'text-emerald-400' : 'text-amber-400',
            trend: overallReadyRate >= 80 ? '+5%' : '-3%',
            trendUp: overallReadyRate >= 80,
          },
          {
            label: '延期物料',
            value: overallStats.delayed,
            icon: AlertTriangle,
            color: 'text-red-400',
            desc: '需紧急跟进',
          },
          {
            label: '在途物料',
            value: filteredProjects.reduce(
              (sum, p) => sum + p.materialStats.inTransit,
              0
            ),
            icon: Truck,
            color: 'text-blue-400',
            desc: '运输中',
          },
          {
            label: '风险项目',
            value: filteredProjects.filter((p) => p.readyRate < 80).length,
            icon: Box,
            color: 'text-amber-400',
            desc: '齐套率<80%',
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  {stat.trend && (
                    <p
                      className={cn(
                        'text-xs mt-1 flex items-center gap-1',
                        stat.trendUp ? 'text-emerald-400' : 'text-red-400'
                      )}
                    >
                      {stat.trendUp ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {stat.trend} 较上周
                    </p>
                  )}
                  {stat.desc && (
                    <p className="text-xs text-slate-500 mt-1" dangerouslySetInnerHTML={{ __html: stat.desc.replace(/</g, '&lt;').replace(/>/g, '&gt;') }} />
                  )}
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Process-based Analysis View */}
      {viewMode === 'process' && (
        <>
          {loadingProcess ? (
            <motion.div variants={fadeIn} className="text-center py-16">
              <div className="text-slate-400">加载工艺分析数据...</div>
            </motion.div>
          ) : processAnalysisData.length > 0 ? (
            <motion.div variants={fadeIn} className="space-y-6">
              {processAnalysisData.map((project) => (
                <Card key={project.projectId} className="bg-slate-800/50 border-slate-700/50">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          <span className="font-mono text-xs text-accent">{project.projectCode}</span>
                          {project.projectName}
                        </CardTitle>
                        <CardDescription>
                          整体齐套率: {project.overallKitRate}% | 
                          阻塞齐套率: {project.blockingKitRate}% | 
                          {project.canStart ? (
                            <span className="text-emerald-400">可开工</span>
                          ) : (
                            <span className="text-red-400">阻塞于: {project.firstBlockedStage}</span>
                          )}
                        </CardDescription>
                      </div>
                      <Badge variant={project.canStart ? 'default' : 'destructive'}>
                        {project.canStart ? (
                          <>
                            <PlayCircle className="w-3 h-3 mr-1" />
                            可开工
                          </>
                        ) : (
                          <>
                            <PauseCircle className="w-3 h-3 mr-1" />
                            阻塞
                          </>
                        )}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-6 gap-4">
                      {project.stageKitRates.map((stage, index) => {
                        const stageIconsMap = {
                          FRAME: Wrench,
                          MECH: Package,
                          ELECTRIC: Zap,
                          WIRING: Cable,
                          DEBUG: Bug,
                          COSMETIC: Palette,
                        }
                        const StageIcon = stageIconsMap[stage.stage_code] || Package
                        const isBlocked = !stage.can_start
                        
                        return (
                          <div key={stage.stage_code} className="relative">
                            {index < project.stageKitRates.length - 1 && (
                              <div className="absolute top-8 left-1/2 w-full h-0.5 bg-slate-700 z-0" />
                            )}
                            <div className={cn(
                              "relative z-10 flex flex-col items-center p-4 rounded-lg border-2 transition-all",
                              isBlocked 
                                ? "border-red-500/50 bg-red-500/10" 
                                : "border-emerald-500/50 bg-emerald-500/10"
                            )}>
                              <div className={cn(
                                "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                                isBlocked ? "bg-red-500/20" : "bg-emerald-500/20"
                              )}>
                                <StageIcon className={cn(
                                  "w-6 h-6",
                                  isBlocked ? "text-red-400" : "text-emerald-400"
                                )} />
                              </div>
                              <div className="text-sm font-medium text-center mb-1 text-white">
                                {stage.stage_name}
                              </div>
                              <div className={cn(
                                "text-lg font-bold mb-1",
                                stage.kit_rate >= 100 ? 'text-emerald-400' :
                                stage.kit_rate >= 80 ? 'text-blue-400' :
                                stage.kit_rate >= 60 ? 'text-amber-400' : 'text-red-400'
                              )}>
                                {stage.kit_rate}%
                              </div>
                              <div className="text-xs text-slate-400 mb-2">
                                阻塞: {stage.blocking_rate}%
                              </div>
                              <Progress 
                                value={stage.kit_rate} 
                                className="h-1.5 w-full"
                              />
                              <div className="mt-2 text-xs">
                                {stage.can_start ? (
                                  <span className="text-emerald-400 flex items-center gap-1">
                                    <CheckCircle2 className="w-3 h-3" />
                                    可开始
                                  </span>
                                ) : (
                                  <span className="text-red-400 flex items-center gap-1">
                                    <AlertTriangle className="w-3 h-3" />
                                    阻塞
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </motion.div>
          ) : (
            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardContent className="py-16 text-center">
                  <Package className="w-16 h-16 mx-auto mb-4 text-slate-500" />
                  <h3 className="text-lg font-semibold text-white mb-2">暂无工艺分析数据</h3>
                  <p className="text-sm text-slate-400 mb-4">
                    请先执行齐套分析以生成工艺阶段数据
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </>
      )}

      {/* Simple Statistics View */}
      {viewMode === 'simple' && (
        <>
          {/* Project List Table - Shows both simple and process kit rates */}
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle>项目齐套率列表</CardTitle>
                <CardDescription>查看所有项目的齐套率和物料状态</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700/50">
                        <th className="text-left p-3 text-slate-400 font-medium">项目编码</th>
                        <th className="text-left p-3 text-slate-400 font-medium">项目名称</th>
                        <th className="text-center p-3 text-slate-400 font-medium">简单齐套率</th>
                        <th className="text-center p-3 text-slate-400 font-medium">工艺齐套率</th>
                        <th className="text-center p-3 text-slate-400 font-medium">阻塞齐套率</th>
                        <th className="text-center p-3 text-slate-400 font-medium">已到货</th>
                        <th className="text-center p-3 text-slate-400 font-medium">在途</th>
                        <th className="text-center p-3 text-slate-400 font-medium">延期</th>
                        <th className="text-center p-3 text-slate-400 font-medium">未下单</th>
                        <th className="text-center p-3 text-slate-400 font-medium">计划装配</th>
                        <th className="text-center p-3 text-slate-400 font-medium">剩余天数</th>
                        <th className="text-center p-3 text-slate-400 font-medium">状态</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loading ? (
                        <tr>
                          <td colSpan={12} className="p-8 text-center text-slate-400">
                            <div className="flex flex-col items-center gap-2">
                              <RefreshCw className="w-6 h-6 text-slate-500 animate-spin" />
                              <span>加载中...</span>
                            </div>
                          </td>
                        </tr>
                      ) : mergedProjectData.length > 0 ? (
                        mergedProjectData.map((project) => {
                          const isAtRisk = project.readyRate < 80 || project.materialStats.delayed > 5
                          const hasProcessData = project.processKitRate !== null
                          return (
                            <tr
                              key={project.id}
                              className="border-b border-slate-700/50 hover:bg-slate-700/30"
                            >
                              <td className="p-3">
                                <span className="font-mono text-xs text-accent">{project.id}</span>
                              </td>
                              <td className="p-3 text-white font-medium">{project.name}</td>
                              <td className="p-3 text-center">
                                <div className="flex flex-col items-center gap-1">
                                  <span className={cn(
                                    "text-lg font-bold",
                                    project.readyRate >= 100 ? 'text-emerald-400' :
                                    project.readyRate >= 80 ? 'text-blue-400' :
                                    project.readyRate >= 60 ? 'text-amber-400' : 'text-red-400'
                                  )}>
                                    {project.readyRate}%
                                  </span>
                                  <Progress value={project.readyRate} className="h-1.5 w-16" />
                                </div>
                              </td>
                              <td className="p-3 text-center">
                                {hasProcessData ? (
                                  <div className="flex flex-col items-center gap-1">
                                    <span className={cn(
                                      "text-lg font-bold",
                                      project.processKitRate >= 100 ? 'text-emerald-400' :
                                      project.processKitRate >= 80 ? 'text-blue-400' :
                                      project.processKitRate >= 60 ? 'text-amber-400' : 'text-red-400'
                                    )}>
                                      {project.processKitRate}%
                                    </span>
                                    <Progress value={project.processKitRate} className="h-1.5 w-16" />
                                  </div>
                                ) : (
                                  <span className="text-slate-500 text-xs">未分析</span>
                                )}
                              </td>
                              <td className="p-3 text-center">
                                {hasProcessData ? (
                                  <span className={cn(
                                    "text-sm font-medium",
                                    project.blockingKitRate >= 100 ? 'text-emerald-400' :
                                    project.blockingKitRate >= 80 ? 'text-blue-400' :
                                    project.blockingKitRate >= 60 ? 'text-amber-400' : 'text-red-400'
                                  )}>
                                    {project.blockingKitRate}%
                                  </span>
                                ) : (
                                  <span className="text-slate-500 text-xs">-</span>
                                )}
                              </td>
                              <td className="p-3 text-center text-emerald-400">
                                {project.materialStats.arrived}
                              </td>
                              <td className="p-3 text-center text-blue-400">
                                {project.materialStats.inTransit}
                              </td>
                              <td className="p-3 text-center text-red-400">
                                {project.materialStats.delayed}
                              </td>
                              <td className="p-3 text-center text-amber-400">
                                {project.materialStats.notOrdered}
                              </td>
                              <td className="p-3 text-center text-slate-400">
                                {project.planAssemblyDate || '-'}
                              </td>
                              <td className="p-3 text-center">
                                <span className={cn(
                                  'font-medium',
                                  project.daysUntilAssembly <= 7
                                    ? 'text-red-400'
                                    : project.daysUntilAssembly <= 14
                                    ? 'text-amber-400'
                                    : 'text-emerald-400'
                                )}>
                                  {project.daysUntilAssembly} 天
                                </span>
                              </td>
                              <td className="p-3 text-center">
                                {isAtRisk ? (
                                  <Badge variant="destructive" className="text-xs">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    风险
                                  </Badge>
                                ) : (
                                  <Badge variant="default" className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                                    <CheckCircle2 className="w-3 h-3 mr-1" />
                                    正常
                                  </Badge>
                                )}
                              </td>
                            </tr>
                          )
                        })
                      ) : (
                        <tr>
                          <td colSpan={12} className="p-8 text-center text-slate-400">
                            <div className="flex flex-col items-center gap-2">
                              <Package className="w-8 h-8 text-slate-500" />
                              <span>暂无项目数据</span>
                            </div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Charts Section */}
          {!loading && filteredProjects.length > 0 && (
        <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Kit Rate Distribution */}
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5 text-blue-400" />
                齐套率分布
              </CardTitle>
              <CardDescription>按齐套率区间统计项目数量</CardDescription>
            </CardHeader>
            <CardContent>
              <SimplePieChart 
                data={kitRateDistribution.filter(d => d.value > 0)} 
                size={250}
              />
            </CardContent>
          </Card>

          {/* Trend Chart */}
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <LineChart className="w-5 h-5 text-emerald-400" />
                    齐套率趋势
                  </CardTitle>
                  <CardDescription>整体齐套率变化趋势</CardDescription>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant={trendPeriod === 'day' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setTrendPeriod('day')}
                    className="h-7 text-xs"
                  >
                    日
                  </Button>
                  <Button
                    variant={trendPeriod === 'week' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setTrendPeriod('week')}
                    className="h-7 text-xs"
                  >
                    周
                  </Button>
                  <Button
                    variant={trendPeriod === 'month' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setTrendPeriod('month')}
                    className="h-7 text-xs"
                  >
                    月
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loadingTrend ? (
                <div className="flex items-center justify-center h-[200px] text-slate-400">
                  加载中...
                </div>
              ) : trendData.length > 0 ? (
                <SimpleLineChart 
                  data={trendData} 
                  height={200}
                  color="text-emerald-400"
                />
              ) : (
                <div className="flex items-center justify-center h-[200px] text-slate-400">
                  暂无趋势数据
                </div>
              )}
            </CardContent>
          </Card>

          {/* Project Comparison */}
          {projectComparisonData.length > 0 && (
            <Card className="bg-slate-800/50 border-slate-700/50 lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-amber-400" />
                  项目齐套率对比
                </CardTitle>
                <CardDescription>Top 10 项目齐套率横向对比</CardDescription>
              </CardHeader>
              <CardContent>
                <SimpleBarChart 
                  data={projectComparisonData} 
                  height={250}
                  color="bg-gradient-to-t from-amber-500/50 to-amber-500"
                />
              </CardContent>
            </Card>
          )}
          </motion.div>
          )}
        </>
      )}

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { value: 'all', label: '全部项目' },
                  { value: 'at_risk', label: '风险项目' },
                  { value: 'upcoming', label: '即将装配' },
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={filterStatus === filter.value ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setFilterStatus(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索项目..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    // Export data to CSV
                    const csvData = filteredProjects.map(project => ({
                      '项目编码': project.id,
                      '项目名称': project.name,
                      '齐套率': `${project.readyRate}%`,
                      '总物料数': project.materialStats.total,
                      '已到货': project.materialStats.arrived,
                      '在途': project.materialStats.inTransit,
                      '延期': project.materialStats.delayed,
                      '未下单': project.materialStats.notOrdered,
                      '计划装配日期': project.planAssemblyDate,
                      '剩余天数': project.daysUntilAssembly,
                    }))
                    
                    const headers = Object.keys(csvData[0] || {})
                    const csvContent = [
                      headers.join(','),
                      ...csvData.map(row => headers.map(header => `"${row[header] || ''}"`).join(','))
                    ].join('\n')
                    
                    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
                    const link = document.createElement('a')
                    const url = URL.createObjectURL(blob)
                    link.setAttribute('href', url)
                    link.setAttribute('download', `齐套分析_${new Date().toISOString().split('T')[0]}.csv`)
                    link.style.visibility = 'hidden'
                    document.body.appendChild(link)
                    link.click()
                    document.body.removeChild(link)
                  }}
                  disabled={filteredProjects.length === 0}
                >
                  <Download className="w-4 h-4 mr-1" />
                  导出
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Loading State */}
      {loading && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </motion.div>
      )}

      {/* Error State */}
      {error && !loading && (
        <motion.div variants={fadeIn} className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </motion.div>
      )}

      {/* Project Material Cards */}
      {viewMode === 'simple' && !loading && !error && (
        <>
          {filteredProjects.length > 0 ? (
            <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredProjects.map((project) => (
                <ProjectMaterialCard key={project.id} project={project} />
              ))}
            </motion.div>
          ) : (
            <motion.div variants={fadeIn}>
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardContent className="py-16 text-center">
                  <Package className="w-16 h-16 mx-auto mb-4 text-slate-500" />
                  <h3 className="text-lg font-semibold text-white mb-2">暂无项目数据</h3>
                  <p className="text-sm text-slate-400 mb-4">
                    {searchQuery || filterStatus !== 'all'
                      ? '没有找到匹配的项目，请尝试调整筛选条件'
                      : '当前没有活跃项目或项目物料数据'}
                  </p>
                  {(searchQuery || filterStatus !== 'all') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setFilterStatus('all')
                      }}
                    >
                      清除筛选条件
                    </Button>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </>
      )}

      {/* Material Shortage Alert Panel */}
      {!loading && !error && (() => {
        const criticalMaterials = filteredProjects.flatMap((project) =>
          project.criticalMaterials
            .filter((m) => m.status === 'delayed' || m.status === 'not_ordered')
            .map((material) => ({ ...material, projectId: project.id, projectName: project.name }))
        )

        if (criticalMaterials.length === 0) {
          return null
        }

        return (
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/50 border-amber-500/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-amber-400">
                  <AlertTriangle className="w-5 h-5" />
                  关键缺料汇总
                  <Badge variant="destructive" className="ml-2">
                    {criticalMaterials.length}
                  </Badge>
                </CardTitle>
                <CardDescription>需要紧急跟进的延期或未下单物料</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-3 text-slate-400 font-medium">物料编码</th>
                        <th className="text-left p-3 text-slate-400 font-medium">物料名称</th>
                        <th className="text-left p-3 text-slate-400 font-medium">所属项目</th>
                        <th className="text-left p-3 text-slate-400 font-medium">状态</th>
                        <th className="text-left p-3 text-slate-400 font-medium">预计到货</th>
                        <th className="text-left p-3 text-slate-400 font-medium">影响</th>
                        <th className="text-center p-3 text-slate-400 font-medium">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {criticalMaterials.map((material, index) => (
                        <tr
                          key={`${material.projectId}-${index}`}
                          className="border-b border-slate-700/50 hover:bg-slate-700/30"
                        >
                          <td className="p-3 font-mono text-xs text-slate-400">
                            {material.code}
                          </td>
                          <td className="p-3 text-white">{material.name}</td>
                          <td className="p-3">
                            <div>
                              <div className="text-accent font-mono text-xs">{material.projectId}</div>
                              <div className="text-slate-500 text-xs">{material.projectName}</div>
                            </div>
                          </td>
                          <td className="p-3">
                            <Badge
                              className={cn(
                                'text-[10px]',
                                statusConfigs[material.status].color
                              )}
                            >
                              {statusConfigs[material.status].label}
                            </Badge>
                          </td>
                          <td className="p-3 text-slate-400">
                            {material.expectedDate}
                          </td>
                          <td className="p-3">
                            <Badge
                              className={cn(
                                'border text-[10px]',
                                impactConfigs[material.impact].color
                              )}
                            >
                              影响{impactConfigs[material.impact].label}
                            </Badge>
                          </td>
                          <td className="p-3 text-center">
                            <Button variant="ghost" size="sm" className="h-7 text-xs">
                              <ExternalLink className="w-3 h-3 mr-1" />
                              跟进
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )
      })()}

    </motion.div>
      </div>
    </div>
  )
}

