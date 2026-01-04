import { useState } from 'react'
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
        isAtRisk ? 'bg-red-500/5 border-red-500/30' : 'bg-surface-1 border-border'
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
                  : 'bg-surface-2/50'
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
            className="w-full p-3 flex items-center justify-between text-sm hover:bg-surface-2/30 transition-colors"
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
                  className="p-3 rounded-lg bg-surface-0/50 text-sm"
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

  // Calculate overall stats
  const overallStats = mockProjectMaterials.reduce(
    (acc, project) => {
      acc.total += project.materialStats.total
      acc.arrived += project.materialStats.arrived
      acc.delayed += project.materialStats.delayed
      return acc
    },
    { total: 0, arrived: 0, delayed: 0 }
  )

  const overallReadyRate = Math.round(
    (overallStats.arrived / overallStats.total) * 100
  )

  return (
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
            value: mockProjectMaterials.reduce(
              (sum, p) => sum + p.materialStats.inTransit,
              0
            ),
            icon: Truck,
            color: 'text-blue-400',
            desc: '运输中',
          },
          {
            label: '风险项目',
            value: mockProjectMaterials.filter((p) => p.readyRate < 80).length,
            icon: Box,
            color: 'text-amber-400',
            desc: '齐套率<80%',
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
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
                    <p className="text-xs text-slate-500 mt-1">{stat.desc}</p>
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
        <Card className="bg-surface-1/50">
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

      {/* Project Material Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {mockProjectMaterials.map((project) => (
          <ProjectMaterialCard key={project.id} project={project} />
        ))}
      </motion.div>

      {/* Material Shortage Alert Panel */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50 border-amber-500/30">
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
                  {mockProjectMaterials.flatMap((project) =>
                    project.criticalMaterials
                      .filter((m) => m.status === 'delayed' || m.status === 'not_ordered')
                      .map((material, index) => (
                        <tr
                          key={`${project.id}-${index}`}
                          className="border-b border-border/50 hover:bg-surface-2/30"
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
  )
}

