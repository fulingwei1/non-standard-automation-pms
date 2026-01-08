/**
 * Performance Indicators - 绩效指标配置
 * Features: 指标模板管理、指标分类、权重配置、计算规则
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Target,
  Plus,
  Edit2,
  Trash2,
  Copy,
  Search,
  Filter,
  Download,
  Upload,
  Save,
  X,
  AlertCircle,
  TrendingUp,
  Percent,
  Settings,
  Loader2,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { performanceApi } from '../services/api'

// Mock data
const mockIndicators = [
  {
    id: 1,
    code: 'IND-001',
    name: '任务完成率',
    category: 'TASK',
    categoryName: '任务类',
    weight: 30,
    unit: '%',
    target: 95,
    description: '按时完成的任务数量占总任务数的百分比',
    calculationMethod: '(按时完成任务数 / 总任务数) × 100%',
    applicableRoles: ['工程师', '项目经理', '部门经理'],
    status: 'ACTIVE',
    createTime: '2025-12-01',
  },
  {
    id: 2,
    code: 'IND-002',
    name: '工作量完成度',
    category: 'WORKLOAD',
    categoryName: '工作量类',
    weight: 25,
    unit: '分',
    target: 100,
    description: '实际完成的工时分数',
    calculationMethod: '项目任务工时累计',
    applicableRoles: ['工程师', '装配工', '测试工程师'],
    status: 'ACTIVE',
    createTime: '2025-12-01',
  },
  {
    id: 3,
    code: 'IND-003',
    name: '质量合格率',
    category: 'QUALITY',
    categoryName: '质量类',
    weight: 25,
    unit: '%',
    target: 98,
    description: '工作成果一次性通过的比例',
    calculationMethod: '(一次通过数 / 总提交数) × 100%',
    applicableRoles: ['工程师', '项目经理'],
    status: 'ACTIVE',
    createTime: '2025-12-01',
  },
  {
    id: 4,
    code: 'IND-004',
    name: '协作评分',
    category: 'COLLABORATION',
    categoryName: '协作类',
    weight: 15,
    unit: '分',
    target: 90,
    description: '团队协作能力的综合评分',
    calculationMethod: '360度评价平均分',
    applicableRoles: ['全员'],
    status: 'ACTIVE',
    createTime: '2025-12-01',
  },
  {
    id: 5,
    code: 'IND-005',
    name: '成长性指标',
    category: 'GROWTH',
    categoryName: '成长类',
    weight: 5,
    unit: '分',
    target: 80,
    description: '技能提升、培训学习等成长性表现',
    calculationMethod: '培训参与度 + 技能认证 + 创新贡献',
    applicableRoles: ['全员'],
    status: 'ACTIVE',
    createTime: '2025-12-01',
  },
]

const categories = [
  { value: 'ALL', label: '全部', color: 'slate' },
  { value: 'WORKLOAD', label: '工作量类', color: 'blue' },
  { value: 'TASK', label: '任务类', color: 'purple' },
  { value: 'QUALITY', label: '质量类', color: 'emerald' },
  { value: 'COLLABORATION', label: '协作类', color: 'amber' },
  { value: 'GROWTH', label: '成长类', color: 'cyan' },
]

const statusOptions = [
  { value: 'ACTIVE', label: '启用', color: 'emerald' },
  { value: 'INACTIVE', label: '停用', color: 'slate' },
]

export default function PerformanceIndicators() {
  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [editingIndicator, setEditingIndicator] = useState(null)
  const [loading, setLoading] = useState(true)
  const [indicators, setIndicators] = useState(mockIndicators)

  // Fetch indicators from API
  useEffect(() => {
    const fetchIndicators = async () => {
      setLoading(true)
      try {
        // Try to fetch weight config which contains indicator settings
        const weightRes = await performanceApi.getWeightConfig()
        if (weightRes.data?.indicators?.length > 0) {
          setIndicators(weightRes.data.indicators)
        }
      } catch (err) {
        console.log('Weight config API unavailable, using mock data')
      }
      setLoading(false)
    }
    fetchIndicators()
  }, [])

  const filteredIndicators = indicators.filter((indicator) => {
    const matchesCategory = selectedCategory === 'ALL' || indicator.category === selectedCategory
    const matchesSearch =
      indicator.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      indicator.code.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const totalWeight = indicators
    .filter((ind) => ind.status === 'ACTIVE')
    .reduce((sum, ind) => sum + ind.weight, 0)

  const getCategoryColor = (category) => {
    const cat = categories.find((c) => c.value === category)
    return cat?.color || 'slate'
  }

  const getStatusColor = (status) => {
    const stat = statusOptions.find((s) => s.value === status)
    return stat?.color || 'slate'
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="绩效指标配置"
        description="配置和管理绩效考核指标体系"
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              导入模板
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出配置
            </Button>
            <Button className="flex items-center gap-2" onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4" />
              新建指标
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">指标总数</p>
                {loading ? (
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                ) : (
                  <p className="text-3xl font-bold text-white">{indicators.length}</p>
                )}
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">启用中</p>
                {loading ? (
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                ) : (
                  <p className="text-3xl font-bold text-emerald-400">
                    {indicators.filter((i) => i.status === 'ACTIVE').length}
                  </p>
                )}
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">权重总计</p>
                <p className="text-3xl font-bold text-cyan-400">{totalWeight}%</p>
              </div>
              <Percent className="h-8 w-8 text-cyan-400" />
            </div>
            {totalWeight !== 100 && (
              <div className="mt-2 flex items-center gap-1 text-xs text-amber-400">
                <AlertCircle className="w-3 h-3" />
                <span>权重总和应为100%</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">指标分类</p>
                <p className="text-3xl font-bold text-purple-400">{categories.length - 1}</p>
              </div>
              <Settings className="h-8 w-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="搜索指标名称或编号..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-slate-900/50 border-slate-700"
                  />
                </div>
              </div>

              {/* Category Filter */}
              <div className="flex gap-2 flex-wrap">
                {categories.map((cat) => (
                  <Button
                    key={cat.value}
                    variant={selectedCategory === cat.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory(cat.value)}
                    className={cn(
                      'transition-all',
                      selectedCategory === cat.value &&
                        `bg-${cat.color}-500/20 border-${cat.color}-500/50 text-${cat.color}-400`
                    )}
                  >
                    {cat.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Indicators Table */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-400" />
              指标列表
              <span className="text-sm font-normal text-slate-400 ml-2">
                (共 {filteredIndicators.length} 项)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredIndicators.map((indicator) => (
                <motion.div
                  key={indicator.id}
                  variants={fadeIn}
                  className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/80 transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-white">{indicator.name}</h3>
                        <Badge
                          className={cn(
                            'text-xs',
                            `bg-${getCategoryColor(indicator.category)}-500/20 text-${getCategoryColor(indicator.category)}-400 border-${getCategoryColor(indicator.category)}-500/50`
                          )}
                        >
                          {indicator.categoryName}
                        </Badge>
                        <Badge
                          className={cn(
                            'text-xs',
                            `bg-${getStatusColor(indicator.status)}-500/20 text-${getStatusColor(indicator.status)}-400 border-${getStatusColor(indicator.status)}-500/50`
                          )}
                        >
                          {statusOptions.find((s) => s.value === indicator.status)?.label}
                        </Badge>
                        <span className="text-xs text-slate-500">{indicator.code}</span>
                      </div>

                      <p className="text-sm text-slate-400">{indicator.description}</p>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-slate-500">权重：</span>
                          <span className="text-white font-semibold ml-1">
                            {indicator.weight}%
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500">目标值：</span>
                          <span className="text-white font-semibold ml-1">
                            {indicator.target}
                            {indicator.unit}
                          </span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-slate-500">适用角色：</span>
                          <span className="text-slate-300 ml-1">
                            {indicator.applicableRoles.join('、')}
                          </span>
                        </div>
                      </div>

                      <div className="text-xs">
                        <span className="text-slate-500">计算方式：</span>
                        <span className="text-cyan-400 ml-1 font-mono">
                          {indicator.calculationMethod}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => setEditingIndicator(indicator)}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}

              {filteredIndicators.length === 0 && (
                <div className="text-center py-12">
                  <Target className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-slate-400">暂无符合条件的指标</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}
