/**
 * Cost Accounting Page - Project cost accounting and analysis
 * Features: Cost recording, Cost query, Cost statistics, Cost analysis
 */

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calculator,
  Search,
  Filter,
  Plus,
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Briefcase,
  Calendar,
  BarChart3,
  PieChart,
  FileText,
  Edit,
  Trash2,
  Eye,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Package,
  Users,
  Wrench,
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn, formatCurrency } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock cost data
const mockCosts = [
  {
    id: 1,
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineId: null,
    machineName: null,
    costType: 'MATERIAL',
    costTypeLabel: '材料成本',
    costCategory: 'STANDARD_PARTS',
    costCategoryLabel: '标准件',
    amount: 125000,
    taxAmount: 16250,
    costDate: '2025-01-05',
    sourceModule: 'PURCHASE',
    sourceType: 'PURCHASE_ORDER',
    sourceId: 18,
    sourceNo: 'PO-2025-0018',
    description: '铝合金型材、导轨等标准件',
    createdBy: '陈采购',
    createdAt: '2025-01-05 10:30',
  },
  {
    id: 2,
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineId: 1,
    machineName: 'BMS-001',
    costType: 'LABOR',
    costTypeLabel: '人工成本',
    costCategory: 'DESIGN',
    costCategoryLabel: '设计',
    amount: 45000,
    taxAmount: 0,
    costDate: '2025-01-04',
    sourceModule: 'TIMESHEET',
    sourceType: 'TIMESHEET',
    sourceId: 156,
    sourceNo: 'TS-2025-00156',
    description: '机械设计工时 120小时 × 375元/小时',
    createdBy: '系统',
    createdAt: '2025-01-04 18:00',
  },
  {
    id: 3,
    projectId: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    machineId: null,
    machineName: null,
    costType: 'OUTSOURCING',
    costTypeLabel: '外协费用',
    costCategory: 'MACHINING',
    costCategoryLabel: '机加工',
    amount: 240000,
    taxAmount: 31200,
    costDate: '2025-01-03',
    sourceModule: 'OUTSOURCING',
    sourceType: 'OUTSOURCING_ORDER',
    sourceId: 12,
    sourceNo: 'OS-2025-0012',
    description: '钣金件机加工外协',
    createdBy: '生产部',
    createdAt: '2025-01-03 14:20',
  },
  {
    id: 4,
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineId: null,
    machineName: null,
    costType: 'EXPENSE',
    costTypeLabel: '费用',
    costCategory: 'TRAVEL',
    costCategoryLabel: '差旅费',
    amount: 8500,
    taxAmount: 0,
    costDate: '2025-01-02',
    sourceModule: 'EXPENSE',
    sourceType: 'EXPENSE_REPORT',
    sourceId: 45,
    sourceNo: 'EXP-2025-0045',
    description: '现场调试差旅费',
    createdBy: '李项目经理',
    createdAt: '2025-01-02 16:45',
  },
  {
    id: 5,
    projectId: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    machineId: null,
    machineName: null,
    costType: 'MATERIAL',
    costTypeLabel: '材料成本',
    costCategory: 'ELECTRICAL',
    costCategoryLabel: '电气件',
    amount: 68000,
    taxAmount: 8840,
    costDate: '2025-01-01',
    sourceModule: 'PURCHASE',
    sourceType: 'PURCHASE_ORDER',
    sourceId: 15,
    sourceNo: 'PO-2025-0015',
    description: 'PLC、传感器等电气件',
    createdBy: '褚工',
    createdAt: '2025-01-01 11:20',
  },
]

// Cost type configuration
const costTypeConfig = {
  MATERIAL: { label: '材料成本', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: Package },
  LABOR: { label: '人工成本', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30', icon: Users },
  OUTSOURCING: { label: '外协费用', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: Wrench },
  EXPENSE: { label: '费用', color: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30', icon: FileText },
}

// Cost category configuration
const costCategoryConfig = {
  STANDARD_PARTS: '标准件',
  ELECTRICAL: '电气件',
  MECHANICAL: '机械件',
  DESIGN: '设计',
  ASSEMBLY: '装配',
  DEBUGGING: '调试',
  MACHINING: '机加工',
  TRAVEL: '差旅费',
  OTHER: '其他',
}

export default function CostAccounting() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedProject, setSelectedProject] = useState('all')
  const [selectedCostType, setSelectedCostType] = useState('all')
  const [selectedDateRange, setSelectedDateRange] = useState('month')
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [selectedCost, setSelectedCost] = useState(null)

  // 从 URL 查询参数读取筛选条件
  useEffect(() => {
    const projectId = searchParams.get('project_id')
    const costType = searchParams.get('cost_type')
    
    if (projectId) {
      setSelectedProject(projectId)
    }
    
    if (costType) {
      setSelectedCostType(costType)
    }
  }, [searchParams])

  // Filter costs
  const filteredCosts = useMemo(() => {
    return mockCosts.filter(cost => {
      const matchesSearch = !searchTerm ||
        cost.projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cost.sourceNo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        cost.description.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesProject = selectedProject === 'all' || cost.projectId === selectedProject
      const matchesType = selectedCostType === 'all' || cost.costType === selectedCostType

      return matchesSearch && matchesProject && matchesType
    })
  }, [searchTerm, selectedProject, selectedCostType])

  // Statistics
  const stats = useMemo(() => {
    const total = filteredCosts.reduce((sum, c) => sum + c.amount, 0)
    const byType = filteredCosts.reduce((acc, c) => {
      acc[c.costType] = (acc[c.costType] || 0) + c.amount
      return acc
    }, {})
    
    return {
      total,
      count: filteredCosts.length,
      byType,
      average: filteredCosts.length > 0 ? total / filteredCosts.length : 0,
    }
  }, [filteredCosts])

  // Projects list
  const projects = useMemo(() => {
    const projectSet = new Set()
    mockCosts.forEach(cost => {
      projectSet.add(JSON.stringify({ id: cost.projectId, name: cost.projectName }))
    })
    return Array.from(projectSet).map(p => JSON.parse(p))
  }, [])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="成本核算"
        description="项目成本记录、查询、统计和分析"
        icon={Calculator}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
            <Button className="flex items-center gap-2" onClick={() => setShowAddDialog(true)}>
              <Plus className="w-4 h-4" />
              录入成本
            </Button>
          </motion.div>
        }
      />

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4"
      >
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">总成本</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(stats.total)}
                </p>
                <p className="text-xs text-slate-500 mt-1">{stats.count}条记录</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">材料成本</p>
                <p className="text-2xl font-bold text-blue-400">
                  {formatCurrency(stats.byType.MATERIAL || 0)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.total > 0 ? ((stats.byType.MATERIAL || 0) / stats.total * 100).toFixed(1) : 0}%
                </p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <BarChart3 className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">人工成本</p>
                <p className="text-2xl font-bold text-purple-400">
                  {formatCurrency(stats.byType.LABOR || 0)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {stats.total > 0 ? ((stats.byType.LABOR || 0) / stats.total * 100).toFixed(1) : 0}%
                </p>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Users className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">平均成本</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {formatCurrency(stats.average)}
                </p>
                <p className="text-xs text-slate-500 mt-1">单条记录</p>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索项目、单号、描述..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">全部项目</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <select
                value={selectedCostType}
                onChange={(e) => setSelectedCostType(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">全部类型</option>
                {Object.entries(costTypeConfig).map(([key, val]) => (
                  <option key={key} value={key}>{val.label}</option>
                ))}
              </select>
              <select
                value={selectedDateRange}
                onChange={(e) => setSelectedDateRange(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="month">本月</option>
                <option value="quarter">本季度</option>
                <option value="year">本年</option>
                <option value="all">全部</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost List */}
        <div className="lg:col-span-2 space-y-6">
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="h-5 w-5 text-blue-400" />
                    成本记录
                  </CardTitle>
                  <Badge variant="outline" className="bg-slate-700/40">
                    {filteredCosts.length}条
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {filteredCosts.map((cost) => {
                    const typeConf = costTypeConfig[cost.costType]
                    const TypeIcon = typeConf?.icon || FileText
                    return (
                      <div
                        key={cost.id}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                        onClick={() => setSelectedCost(cost)}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className={cn('text-xs', typeConf?.color)}>
                                <TypeIcon className="w-3 h-3 mr-1" />
                                {cost.costTypeLabel}
                              </Badge>
                              <span className="text-sm text-slate-400">{cost.costCategoryLabel}</span>
                            </div>
                            <div className="font-medium text-white text-sm mb-1">
                              {cost.projectName}
                            </div>
                            <div className="text-xs text-slate-400">
                              {cost.description}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {cost.sourceNo} · {cost.createdBy} · {cost.costDate}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-amber-400">
                              {formatCurrency(cost.amount)}
                            </div>
                            {cost.taxAmount > 0 && (
                              <div className="text-xs text-slate-400">
                                含税: {formatCurrency(cost.amount + cost.taxAmount)}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                  {filteredCosts.length === 0 && (
                    <div className="text-center py-12 text-slate-500">
                      暂无成本记录
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Cost Analysis */}
        <div className="space-y-6">
          {/* Cost by Type */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <PieChart className="h-5 w-5 text-purple-400" />
                  成本类型分布
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {Object.entries(costTypeConfig).map(([key, config]) => {
                  const amount = stats.byType[key] || 0
                  const percentage = stats.total > 0 ? (amount / stats.total * 100) : 0
                  const Icon = config.icon
                  return (
                    <div key={key} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4 text-slate-400" />
                          <span className="text-slate-400">{config.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">
                            {formatCurrency(amount)}
                          </span>
                          <span className="text-slate-500 text-xs w-12 text-right">
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <Progress value={percentage} className="h-2 bg-slate-700/50" />
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </motion.div>

          {/* Cost by Project */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Briefcase className="h-5 w-5 text-blue-400" />
                  项目成本排行
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {projects.slice(0, 5).map((project) => {
                  const projectCosts = filteredCosts.filter(c => c.projectId === project.id)
                  const projectTotal = projectCosts.reduce((sum, c) => sum + c.amount, 0)
                  const percentage = stats.total > 0 ? (projectTotal / stats.total * 100) : 0
                  return (
                    <div key={project.id} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400 truncate flex-1">{project.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">
                            {formatCurrency(projectTotal)}
                          </span>
                          <span className="text-slate-500 text-xs w-12 text-right">
                            {percentage.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <Progress value={percentage} className="h-2 bg-slate-700/50" />
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Add Cost Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>录入成本</DialogTitle>
            <DialogDescription>
              录入项目成本记录
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-slate-400">项目 *</label>
                <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                  <option value="">请选择项目</option>
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm text-slate-400">成本类型 *</label>
                <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                  <option value="">请选择类型</option>
                  {Object.entries(costTypeConfig).map(([key, val]) => (
                    <option key={key} value={key}>{val.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm text-slate-400">金额 *</label>
                <Input type="number" placeholder="请输入金额" />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-slate-400">发生日期 *</label>
                <Input type="date" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">描述</label>
              <textarea
                placeholder="请输入成本描述..."
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowAddDialog(false)}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cost Detail Dialog */}
      <Dialog open={!!selectedCost} onOpenChange={() => setSelectedCost(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>成本详情</DialogTitle>
          </DialogHeader>
          {selectedCost && (
            <div className="py-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-slate-400">项目</label>
                  <p className="text-white font-medium">{selectedCost.projectName}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">成本类型</label>
                  <p className="text-white font-medium">{selectedCost.costTypeLabel}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">金额</label>
                  <p className="text-amber-400 font-bold text-lg">
                    {formatCurrency(selectedCost.amount)}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">发生日期</label>
                  <p className="text-white">{selectedCost.costDate}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">来源单号</label>
                  <p className="text-white">{selectedCost.sourceNo}</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400">创建人</label>
                  <p className="text-white">{selectedCost.createdBy}</p>
                </div>
              </div>
              <div>
                <label className="text-sm text-slate-400">描述</label>
                <p className="text-white">{selectedCost.description}</p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedCost(null)}>
              关闭
            </Button>
            <Button>编辑</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

