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
import { projectApi, bomApi, purchaseApi } from '../services/api'

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
          console.error(`Failed to load items for order ${order.id}:`, err)
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
          console.error(`Failed to load material status for project ${project.id}:`, err)
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
                console.error(`Failed to load BOM for machine ${machine.id}:`, err)
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
            console.error(`Fallback calculation also failed for project ${project.id}:`, fallbackErr)
          }
        }
      }

      setProjectMaterials(projectMaterialsData)
    } catch (err) {
      console.error('Failed to load project materials:', err)
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        // For demo accounts, use mock data on error
        setProjectMaterials(mockProjectMaterials)
        setError(null)
      } else {
        setError(err.response?.data?.detail || err.message || '加载物料分析数据失败')
        setProjectMaterials([])
      }
    } finally {
      setLoading(false)
    }
  }, [])

  // Load data when component mounts
  useEffect(() => {
    loadProjectMaterials()
  }, [loadProjectMaterials])

  // Filter projects
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

  // Calculate overall stats
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

  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
  
  // Mock data for demo accounts
  useEffect(() => {
    if (isDemoAccount && projectMaterials.length === 0 && !loading) {
      setProjectMaterials(mockProjectMaterials)
      setLoading(false)
    }
  }, [isDemoAccount, projectMaterials.length, loading])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="齐套分析"
        description="监控项目物料到货情况，确保按时开工"
      />

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
                <Button variant="outline" size="sm">
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
      {!loading && (
        <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredProjects.map((project) => (
            <ProjectMaterialCard key={project.id} project={project} />
          ))}
        </motion.div>
      )}

      {/* Material Shortage Alert Panel */}
      <motion.div variants={fadeIn}>
        <Card className="bg-slate-800/50 border-amber-500/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
              关键缺料汇总
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
                  {filteredProjects.flatMap((project) =>
                    project.criticalMaterials
                      .filter((m) => m.status === 'delayed' || m.status === 'not_ordered')
                      .map((material, index) => (
                        <tr
                          key={`${project.id}-${index}`}
                          className="border-b border-slate-700/50 hover:bg-slate-700/30"
                        >
                          <td className="p-3 font-mono text-xs text-slate-400">
                            {material.code}
                          </td>
                          <td className="p-3 text-white">{material.name}</td>
                          <td className="p-3">
                            <span className="text-accent">{project.id}</span>
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
                              {impactConfigs[material.impact].label}
                            </Badge>
                          </td>
                          <td className="p-3 text-center">
                            <Button variant="ghost" size="sm" className="h-7 text-xs">
                              <ExternalLink className="w-3 h-3 mr-1" />
                              跟进
                            </Button>
                          </td>
                        </tr>
                      ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
      </div>
    </div>
  )
}

