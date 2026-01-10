/**
 * Opportunity Board Page - Sales pipeline kanban view
 * Features: Stage columns, drag-and-drop, opportunity cards, funnel visualization
 */

import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Target,
  Search,
  Filter,
  Plus,
  LayoutGrid,
  List,
  ChevronRight,
  Calendar,
  DollarSign,
  User,
  Building2,
  Clock,
  AlertTriangle,
  Flame,
  TrendingUp,
  TrendingDown,
  BarChart3,
  ChevronDown,
  Edit,
  Trash2,
  FileText,
  Phone,
  MessageSquare,
  X,
  CheckCircle2,
  XCircle,
  Lightbulb,
  CheckCircle,
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
import { OpportunityCard, SalesFunnel } from '../components/sales'
import { opportunityApi, salesStatisticsApi } from '../services/api'

// Stage configuration - 映射后端阶段到看板列
const stages = [
  { key: 'DISCOVERY', label: '需求发现', color: 'bg-violet-500', textColor: 'text-violet-400', probability: 10, frontendKey: 'lead' },
  { key: 'QUALIFIED', label: '已合格', color: 'bg-blue-500', textColor: 'text-blue-400', probability: 30, frontendKey: 'contact' },
  { key: 'PROPOSAL', label: '方案报价', color: 'bg-amber-500', textColor: 'text-amber-400', probability: 50, frontendKey: 'quote' },
  { key: 'NEGOTIATION', label: '合同谈判', color: 'bg-pink-500', textColor: 'text-pink-400', probability: 75, frontendKey: 'negotiate' },
  { key: 'WON', label: '签约赢单', color: 'bg-emerald-500', textColor: 'text-emerald-400', probability: 100, frontendKey: 'won' },
  { key: 'LOST', label: '输单', color: 'bg-red-500', textColor: 'text-red-400', probability: 0, frontendKey: 'lost' },
  { key: 'ON_HOLD', label: '客户搁置', color: 'bg-slate-500', textColor: 'text-slate-400', probability: 0, frontendKey: 'hold' },
]

// 阶段映射函数
const mapStageToFrontend = (backendStage) => {
  const stage = stages.find(s => s.key === backendStage)
  return stage?.frontendKey || 'lead'
}

// Mock opportunity data
// Mock data - 已移除，使用真实API
const priorityConfig = {
  high: { label: '高', color: 'text-red-400 bg-red-500/20' },
  medium: { label: '中', color: 'text-amber-400 bg-amber-500/20' },
  low: { label: '低', color: 'text-slate-400 bg-slate-500/20' },
}

export default function OpportunityBoard() {
  const [viewMode, setViewMode] = useState('board') // 'board', 'list', 'funnel'
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPriority, setSelectedPriority] = useState('all')
  const [selectedOwner, setSelectedOwner] = useState('all')
  const [showHotOnly, setShowHotOnly] = useState(false)
  const [selectedOpportunity, setSelectedOpportunity] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [hideLost, setHideLost] = useState(true)
  const [opportunities, setOpportunities] = useState([])
  const [loading, setLoading] = useState(false)
  const [owners, setOwners] = useState([])

  // Load opportunities from API
  const loadOpportunities = async () => {
    setLoading(true)
    try {
      const response = await opportunityApi.list({ page: 1, page_size: 1000 })
      const data = response.data?.items || response.data || []
      
      // 转换数据格式
      const transformedOpps = data.map((opp) => {
        // 计算在当前阶段的停留天数
        const stageChangedAt = opp.gate_passed_at || opp.updated_at || opp.created_at
        const daysInStage = stageChangedAt 
          ? Math.floor((new Date() - new Date(stageChangedAt)) / (1000 * 60 * 60 * 24))
          : 0

        // 根据评分和阶段判断是否为热门商机
        const isHot = (opp.score || 0) >= 70 || opp.stage === 'PROPOSAL' || opp.stage === 'NEGOTIATION'
        
        // 根据风险等级确定优先级
        const priorityMap = {
          HIGH: 'high',
          MEDIUM: 'medium',
          LOW: 'low',
        }
        const priority = priorityMap[opp.risk_level] || 'medium'

        // 计算成交概率（基于阶段）
        const stageConf = stages.find(s => s.key === opp.stage)
        const probability = stageConf?.probability || 0

        return {
          id: opp.id,
          opp_code: opp.opp_code,
          name: opp.opp_name || '',
          customerName: opp.customer_name || '',
          customerShort: opp.customer_name || '',
          customerId: opp.customer_id,
          stage: mapStageToFrontend(opp.stage),
          backendStage: opp.stage,
          expectedAmount: parseFloat(opp.est_amount || 0),
          probability: probability,
          owner: opp.owner_name || opp.owner_id?.toString() || '',
          ownerId: opp.owner_id,
          isHot: isHot,
          priority: priority,
          daysInStage: daysInStage,
          score: opp.score || 0,
          riskLevel: opp.risk_level || 'MEDIUM',
          budgetRange: opp.budget_range || '',
          deliveryWindow: opp.delivery_window || '',
          createdAt: opp.created_at || '',
          updatedAt: opp.updated_at || '',
          raw: opp, // 保存原始数据
        }
      })

      setOpportunities(transformedOpps)
      
      // 提取负责人列表
      const ownerSet = new Set()
      transformedOpps.forEach(opp => {
        if (opp.owner) {
          ownerSet.add(opp.owner)
        }
      })
      setOwners(Array.from(ownerSet).sort())
    } catch (error) {
      console.error('加载商机列表失败:', error)
      // 如果API失败，使用mock数据作为fallback
      setOpportunities(mockOpportunities)
      const ownerSet = new Set()
      mockOpportunities.forEach(opp => {
        if (opp.owner) {
          ownerSet.add(opp.owner)
        }
      })
      setOwners(Array.from(ownerSet).sort())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOpportunities()
  }, [])
  
  // Issue 5.4: 处理商机阶段变更（拖拽）
  const handleStageChange = async (opportunityId, newStageKey) => {
    const opportunity = opportunities.find(opp => opp.id === opportunityId)
    if (!opportunity) return
    
    const newStage = stages.find(s => s.frontendKey === newStageKey)
    if (!newStage) return
    
    try {
      // Update opportunity stage via API
      await opportunityApi.update(opportunityId, {
        stage: newStage.key
      })
      
      // Reload opportunities
      await loadOpportunities()
    } catch (err) {
      console.error('Failed to update opportunity stage:', err)
      // Show error toast
      alert('更新商机阶段失败：' + (err.response?.data?.detail || err.message))
    }
  }

  // Filter opportunities
  const filteredOpportunities = useMemo(() => {
    return opportunities.filter(opp => {
      const matchesSearch = !searchTerm || 
        opp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        opp.customerShort.toLowerCase().includes(searchTerm.toLowerCase()) ||
        opp.opp_code?.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesPriority = selectedPriority === 'all' || opp.priority === selectedPriority
      const matchesOwner = selectedOwner === 'all' || opp.owner === selectedOwner
      const matchesHot = !showHotOnly || opp.isHot
      const matchesLost = !hideLost || opp.stage !== 'lost'

      return matchesSearch && matchesPriority && matchesOwner && matchesHot && matchesLost
    })
  }, [opportunities, searchTerm, selectedPriority, selectedOwner, showHotOnly, hideLost])

  // Group by stage for board view
  const groupedOpportunities = useMemo(() => {
    const groups = {}
    stages.forEach(stage => {
      if (hideLost && stage.frontendKey === 'lost') return
      groups[stage.frontendKey] = filteredOpportunities.filter(opp => opp.stage === stage.frontendKey)
    })
    return groups
  }, [filteredOpportunities, hideLost])

  // Stats
  const stats = useMemo(() => {
    const activeOpps = opportunities.filter(o => o.stage !== 'lost' && o.stage !== 'won')
    const totalValue = activeOpps.reduce((sum, o) => sum + (o.expectedAmount || 0), 0)
    const weightedValue = activeOpps.reduce((sum, o) => sum + ((o.expectedAmount || 0) * (o.probability || 0) / 100), 0)
    const hotCount = activeOpps.filter(o => o.isHot).length
    const overdueCount = activeOpps.filter(o => (o.daysInStage || 0) > 14).length
    
    // 计算本月赢单和输单
    const now = new Date()
    const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1)
    const wonThisMonth = opportunities.filter(o => {
      if (o.stage !== 'won') return false
      const wonDate = o.raw?.gate_passed_at || o.updatedAt
      return wonDate && new Date(wonDate) >= thisMonthStart
    }).length
    
    const lostThisMonth = opportunities.filter(o => {
      if (o.stage !== 'lost') return false
      const lostDate = o.updatedAt
      return lostDate && new Date(lostDate) >= thisMonthStart
    }).length
    
    return {
      total: activeOpps.length,
      totalValue,
      weightedValue,
      hotCount,
      overdueCount,
      wonThisMonth,
      lostThisMonth,
    }
  }, [opportunities])

  const handleOpportunityClick = async (opportunity) => {
    if (opportunity.raw && opportunity.raw.id) {
      try {
        const response = await opportunityApi.get(opportunity.raw.id)
        if (response.data) {
          setSelectedOpportunity({
            ...opportunity,
            raw: response.data,
          })
        } else {
          setSelectedOpportunity(opportunity)
        }
      } catch (error) {
        console.error('加载商机详情失败:', error)
        setSelectedOpportunity(opportunity)
      }
    } else {
      setSelectedOpportunity(opportunity)
    }
    setShowDetailDialog(true)
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="商机跟踪"
        description="管理销售漏斗，跟踪商机进展"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button className="flex items-center gap-2" onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4" />
              新建商机
            </Button>
          </motion.div>
        }
      />

      {/* Stats Row */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 sm:grid-cols-5 gap-4">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
                <p className="text-xs text-slate-400">进行中商机</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  ¥{(stats.totalValue / 10000).toFixed(0)}万
                </p>
                <p className="text-xs text-slate-400">商机总额</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  ¥{(stats.weightedValue / 10000).toFixed(0)}万
                </p>
                <p className="text-xs text-slate-400">加权金额</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/20 rounded-lg">
                <Flame className="w-5 h-5 text-orange-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.hotCount}</p>
                <p className="text-xs text-slate-400">热门商机</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">{stats.wonThisMonth}</p>
                <p className="text-xs text-slate-400">本月赢单</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn} className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索商机、客户..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-56"
            />
          </div>
          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">全部优先级</option>
            <option value="high">高优先级</option>
            <option value="medium">中优先级</option>
            <option value="low">低优先级</option>
          </select>
          <Button
            variant={showHotOnly ? 'default' : 'outline'}
            size="sm"
            onClick={() => setShowHotOnly(!showHotOnly)}
            className="flex items-center gap-1"
          >
            <Flame className={cn('w-4 h-4', showHotOnly && 'text-amber-400')} />
            热门
          </Button>
          <Button
            variant={!hideLost ? 'default' : 'outline'}
            size="sm"
            onClick={() => setHideLost(!hideLost)}
          >
            {hideLost ? '显示输单' : '隐藏输单'}
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex border border-white/10 rounded-lg overflow-hidden">
            <Button
              variant={viewMode === 'board' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('board')}
            >
              <LayoutGrid className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'funnel' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('funnel')}
            >
              <BarChart3 className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('list')}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Content */}
      <motion.div variants={fadeIn}>
        {viewMode === 'board' && (
          <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
            {loading ? (
              <div className="flex-1 text-center py-12 text-slate-400">加载中...</div>
            ) : (
              stages.filter(s => !hideLost || s.frontendKey !== 'lost').map((stage) => {
                const stageOpps = groupedOpportunities[stage.frontendKey] || []
                const stageTotal = stageOpps.reduce((sum, o) => sum + (o.expectedAmount || 0), 0)
              
              return (
                <div key={stage.key} className="flex-shrink-0 w-80">
                  {/* Column Header */}
                  <div className="flex items-center justify-between mb-3 p-3 bg-surface-100 rounded-lg">
                    <div className="flex items-center gap-2">
                      <div className={cn('w-3 h-3 rounded-full', stage.color)} />
                      <span className="font-medium text-white">{stage.label}</span>
                      <Badge variant="secondary" className="text-xs">
                        {stageOpps.length}
                      </Badge>
                    </div>
                    <span className="text-xs text-slate-400">
                      ¥{(stageTotal / 10000).toFixed(0)}万
                    </span>
                  </div>

                  {/* Column Content - Issue 5.4: 支持拖拽改变商机阶段 */}
                  <div className="space-y-3 min-h-[200px]">
                    {stageOpps.map((opportunity) => (
                      <OpportunityCard
                        key={opportunity.id}
                        opportunity={opportunity}
                        onClick={handleOpportunityClick}
                        draggable
                        onDragEnd={(newStage) => {
                          // Handle drag end to change stage
                          handleStageChange(opportunity.id, newStage)
                        }}
                      />
                    ))}
                    {stageOpps.length === 0 && (
                      <div className="text-center py-8 text-slate-500 text-sm">
                        暂无商机
                      </div>
                    )}
                  </div>
                </div>
              )
            }))}
          </div>
        )}

        {viewMode === 'funnel' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>销售漏斗</CardTitle>
              </CardHeader>
              <CardContent>
                <SalesFunnel
                  data={{
                    lead: groupedOpportunities.lead?.length || 0,
                    contact: groupedOpportunities.contact?.length || 0,
                    quote: groupedOpportunities.quote?.length || 0,
                    negotiate: groupedOpportunities.negotiate?.length || 0,
                    won: groupedOpportunities.won?.length || 0,
                  }}
                  onStageClick={(stage) => {
                    // Handle stage click if needed
                  }}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>转化分析</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {stages.slice(0, -1).map((stage, index) => {
                  const currentCount = groupedOpportunities[stage.key]?.length || 0
                  const nextStage = stages[index + 1]
                  const nextCount = nextStage ? (groupedOpportunities[nextStage.key]?.length || 0) : 0
                  const conversionRate = currentCount > 0 ? ((nextCount / currentCount) * 100).toFixed(0) : 0

                  return (
                    <div key={stage.key} className="flex items-center gap-4">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-white">{stage.label} → {nextStage?.label}</span>
                          <span className={cn(
                            'text-sm font-medium',
                            parseInt(conversionRate) > 50 ? 'text-emerald-400' : 
                            parseInt(conversionRate) > 25 ? 'text-amber-400' : 'text-red-400'
                          )}>
                            {conversionRate}%
                          </span>
                        </div>
                        <Progress value={parseInt(conversionRate)} className="h-2" />
                      </div>
                    </div>
                  )
                })}
                
                <div className="pt-4 border-t border-white/5 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">整体转化率</span>
                    <span className="text-emerald-400 font-medium">
                      {((groupedOpportunities.won?.length || 0) / 
                        Math.max((groupedOpportunities.lead?.length || 1), 1) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">平均成交周期</span>
                    <span className="text-white font-medium">32天</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">赢单率</span>
                    <span className="text-white font-medium">
                      {(stats.wonThisMonth / Math.max(stats.wonThisMonth + stats.lostThisMonth, 1) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {viewMode === 'list' && (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">商机名称</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">客户</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">阶段</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">优先级</th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">预期金额</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">预计成交</th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400">成功率</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">负责人</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOpportunities.map((opp) => {
                    const stageConf = stages.find(s => s.key === opp.stage)
                    const priorityConf = priorityConfig[opp.priority]
                    
                    return (
                      <tr
                        key={opp.id}
                        onClick={() => handleOpportunityClick(opp)}
                        className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            {opp.isHot && <Flame className="w-4 h-4 text-amber-500" />}
                            <span className="font-medium text-white">{opp.name}</span>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-400">{opp.customerShort}</td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <div className={cn('w-2 h-2 rounded-full', stageConf?.color)} />
                            <span className={stageConf?.textColor}>{stageConf?.label}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge className={priorityConf.color}>{priorityConf.label}</Badge>
                        </td>
                        <td className="p-4 text-right">
                          <span className="text-amber-400 font-medium">
                            ¥{(opp.expectedAmount / 10000).toFixed(0)}万
                          </span>
                        </td>
                        <td className="p-4 text-sm text-slate-400">{opp.expectedCloseDate}</td>
                        <td className="p-4 text-center">
                          <span className={cn(
                            'text-sm font-medium',
                            opp.probability >= 70 ? 'text-emerald-400' :
                            opp.probability >= 40 ? 'text-amber-400' : 'text-red-400'
                          )}>
                            {opp.probability}%
                          </span>
                        </td>
                        <td className="p-4 text-sm text-slate-400">{opp.owner}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </motion.div>

      {/* Opportunity Detail Panel */}
      <AnimatePresence>
        {selectedOpportunity && (
          <OpportunityDetailPanel
            opportunity={selectedOpportunity}
            onClose={() => setSelectedOpportunity(null)}
          />
        )}
      </AnimatePresence>

      {/* Opportunity Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              商机详情
            </DialogTitle>
            <DialogDescription>
              {selectedOpportunity ? `查看商机 "${selectedOpportunity.name}" 的详细信息` : ''}
            </DialogDescription>
          </DialogHeader>

          {selectedOpportunity && (
            <div className="space-y-6 py-4">
              {/* 基本信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">商机编码</span>
                      <p className="text-white font-medium">{selectedOpportunity.opp_code || selectedOpportunity.id}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">阶段</span>
                      <p>
                        {(() => {
                          const stageConf = stages.find(s => s.frontendKey === selectedOpportunity.stage || s.key === selectedOpportunity.backendStage)
                          return stageConf ? (
                            <Badge className={cn('text-xs', stageConf.color, stageConf.textColor)}>
                              {stageConf.label}
                            </Badge>
                          ) : (
                            <span className="text-white">{selectedOpportunity.backendStage || selectedOpportunity.stage}</span>
                          )
                        })()}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">客户名称</span>
                      <p className="text-white">{selectedOpportunity.customerName || selectedOpportunity.raw?.customer_name || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">负责人</span>
                      <p className="text-white">{selectedOpportunity.owner || selectedOpportunity.raw?.owner_name || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">预估金额</span>
                      <p className="text-white font-semibold">¥{((selectedOpportunity.expectedAmount || 0) / 10000).toFixed(2)}万</p>
                    </div>
                    <div>
                      <span className="text-slate-400">成交概率</span>
                      <p className="text-white">{selectedOpportunity.probability || 0}%</p>
                    </div>
                    <div>
                      <span className="text-slate-400">评分</span>
                      <p className="text-white">
                        <Badge className={cn(
                          'text-sm',
                          (selectedOpportunity.score || 0) >= 80 ? 'bg-emerald-500/20 text-emerald-400' :
                          (selectedOpportunity.score || 0) >= 60 ? 'bg-amber-500/20 text-amber-400' :
                          'bg-red-500/20 text-red-400'
                        )}>
                          {selectedOpportunity.score || 0}分
                        </Badge>
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">风险等级</span>
                      <p>
                        <Badge className={cn(
                          'text-xs',
                          selectedOpportunity.riskLevel === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                          selectedOpportunity.riskLevel === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-slate-500/20 text-slate-400'
                        )}>
                          {selectedOpportunity.riskLevel === 'HIGH' ? '高' : selectedOpportunity.riskLevel === 'MEDIUM' ? '中' : '低'}
                        </Badge>
                      </p>
                    </div>
                    {selectedOpportunity.budgetRange && (
                      <div>
                        <span className="text-slate-400">预算范围</span>
                        <p className="text-white">{selectedOpportunity.budgetRange}</p>
                      </div>
                    )}
                    {selectedOpportunity.deliveryWindow && (
                      <div>
                        <span className="text-slate-400">交付窗口</span>
                        <p className="text-white">{selectedOpportunity.deliveryWindow}</p>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-400">在当前阶段</span>
                      <p className="text-white">{selectedOpportunity.daysInStage || 0}天</p>
                    </div>
                    {selectedOpportunity.isHot && (
                      <div>
                        <span className="text-slate-400">状态</span>
                        <p>
                          <Badge className="text-xs bg-orange-500/20 text-orange-400">
                            <Flame className="w-3 h-3 mr-1" />
                            热门商机
                          </Badge>
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 时间信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">时间信息</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">创建时间</span>
                      <p className="text-white">{selectedOpportunity.createdAt || selectedOpportunity.raw?.created_at || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">更新时间</span>
                      <p className="text-white">{selectedOpportunity.updatedAt || selectedOpportunity.raw?.updated_at || '-'}</p>
                    </div>
                    {selectedOpportunity.raw?.gate_passed_at && (
                      <div>
                        <span className="text-slate-400">阶段门通过时间</span>
                        <p className="text-white">{selectedOpportunity.raw.gate_passed_at}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedOpportunity && (
              <Button onClick={() => {
                // 导航到商机管理页面进行编辑
                window.location.href = `/sales/opportunities?edit=${selectedOpportunity.id}`
              }}>
                <Edit className="w-4 h-4 mr-2" />
                编辑商机
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建商机</DialogTitle>
            <DialogDescription>
              创建新的销售商机
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">商机名称 *</label>
              <Input placeholder="请输入商机名称" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">关联客户 *</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择客户</option>
                <option value="1">深圳新能源</option>
                <option value="2">东莞精密</option>
                <option value="3">惠州储能</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">预期金额</label>
              <Input type="number" placeholder="请输入预期金额" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">预计成交日期</label>
              <Input type="date" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">优先级</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="low">低</option>
              </select>
            </div>
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">商机描述</label>
              <textarea
                placeholder="请输入商机描述"
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowCreateDialog(false)}>
              创建商机
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

// Opportunity Detail Panel
function OpportunityDetailPanel({ opportunity, onClose }) {
  const stageConf = stages.find(s => s.key === opportunity.stage)
  const priorityConf = priorityConfig[opportunity.priority]

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              {opportunity.isHot && <Flame className="w-5 h-5 text-amber-500" />}
              <h2 className="text-lg font-semibold text-white">{opportunity.name}</h2>
            </div>
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-400">{opportunity.customerShort}</span>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Stage & Priority */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={cn('w-3 h-3 rounded-full', stageConf?.color)} />
            <Badge variant="secondary">{stageConf?.label}</Badge>
          </div>
          <Badge className={priorityConf.color}>{priorityConf.label}优先级</Badge>
          {opportunity.isHot && (
            <Badge className="bg-amber-500/20 text-amber-400">热门</Badge>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-surface-50 rounded-lg">
            <div className="text-xs text-slate-400">预期金额</div>
            <div className="text-lg font-semibold text-amber-400">
              ¥{(opportunity.expectedAmount / 10000).toFixed(0)}万
            </div>
          </div>
          <div className="p-3 bg-surface-50 rounded-lg">
            <div className="text-xs text-slate-400">成功率</div>
            <div className={cn(
              'text-lg font-semibold',
              opportunity.probability >= 70 ? 'text-emerald-400' :
              opportunity.probability >= 40 ? 'text-amber-400' : 'text-red-400'
            )}>
              {opportunity.probability}%
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">商机信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">预计成交:</span>
              <span className="text-white">{opportunity.expectedCloseDate}</span>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">负责人:</span>
              <span className="text-white">{opportunity.owner}</span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">当前阶段停留:</span>
              <span className={cn(
                opportunity.daysInStage > 14 ? 'text-red-400' :
                opportunity.daysInStage > 7 ? 'text-amber-400' : 'text-white'
              )}>
                {opportunity.daysInStage}天
              </span>
            </div>
            <div className="flex items-center gap-3">
              <MessageSquare className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">最近活动:</span>
              <span className="text-white">{opportunity.lastActivity}</span>
            </div>
          </div>
        </div>

        {/* Description */}
        {opportunity.description && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">商机描述</h3>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {opportunity.description}
            </p>
          </div>
        )}

        {/* Tags */}
        {opportunity.tags?.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">标签</h3>
            <div className="flex flex-wrap gap-2">
              {opportunity.tags.map((tag, index) => (
                <Badge key={index} variant="secondary">{tag}</Badge>
              ))}
            </div>
          </div>
        )}

        {/* Stage Progress */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">阶段进展</h3>
          <div className="space-y-2">
            {stages.slice(0, -1).map((stage, index) => {
              const isCompleted = stages.findIndex(s => s.key === opportunity.stage) > index
              const isCurrent = stage.key === opportunity.stage
              
              return (
                <div key={stage.key} className="flex items-center gap-3">
                  <div className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs',
                    isCompleted ? stage.color + ' text-white' :
                    isCurrent ? 'border-2 ' + stage.color.replace('bg-', 'border-') + ' ' + stage.textColor :
                    'border border-slate-600 text-slate-600'
                  )}>
                    {isCompleted ? '✓' : index + 1}
                  </div>
                  <span className={cn(
                    'text-sm',
                    isCompleted || isCurrent ? 'text-white' : 'text-slate-500'
                  )}>
                    {stage.label}
                  </span>
                  {isCurrent && (
                    <Badge variant="secondary" className="text-xs">当前</Badge>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* 可行性评估 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-slate-400 flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-primary" />
              可行性评估
            </h3>
            {(!opportunity.feasibilityAssessment || opportunity.feasibilityAssessment.status === 'none') && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  // 申请可行性评估
                  const updatedOpp = {
                    ...opportunity,
                    feasibilityAssessment: {
                      status: 'requested',
                      requestedAt: new Date().toISOString().split('T')[0],
                      requestedBy: '当前用户',
                      overallScore: null,
                      feasibility: null,
                      submittedAt: null,
                      submittedBy: null,
                    },
                  }
                  // 这里应该调用API更新
                  alert('可行性评估申请已提交，售前技术工程师将尽快处理')
                }}
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                申请评估
              </Button>
            )}
          </div>

          {(!opportunity.feasibilityAssessment || opportunity.feasibilityAssessment.status === 'none') && (
            <div className="p-3 bg-slate-500/10 border border-slate-500/20 rounded-lg">
              <p className="text-xs text-slate-400">尚未申请可行性评估</p>
            </div>
          )}

          {opportunity.feasibilityAssessment?.status === 'requested' && (
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-white">可行性评估申请已提交</span>
              </div>
              <p className="text-xs text-slate-400">
                申请时间：{opportunity.feasibilityAssessment.requestedAt} | 申请人员：{opportunity.feasibilityAssessment.requestedBy}
              </p>
              <p className="text-xs text-slate-500 mt-1">售前技术工程师正在处理中...</p>
            </div>
          )}

          {opportunity.feasibilityAssessment?.status === 'in_progress' && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-white">可行性评估进行中</span>
              </div>
              <p className="text-xs text-slate-400">售前技术工程师正在评估中...</p>
            </div>
          )}

          {opportunity.feasibilityAssessment?.status === 'submitted' && (
            <div className="space-y-3">
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-white">可行性评估已完成</span>
                  </div>
                  <Badge className={cn(
                    'text-xs',
                    opportunity.feasibilityAssessment.feasibility === 'feasible' ? 'bg-emerald-500/20 text-emerald-400' :
                    opportunity.feasibilityAssessment.feasibility === 'conditional' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-red-500/20 text-red-400'
                  )}>
                    {opportunity.feasibilityAssessment.feasibility === 'feasible' ? '可行' :
                     opportunity.feasibilityAssessment.feasibility === 'conditional' ? '有条件可行' : '不可行'}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">综合评分</p>
                    <p className="text-lg font-bold text-white">
                      {opportunity.feasibilityAssessment.overallScore?.toFixed(1)}分
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">评估时间</p>
                    <p className="text-sm text-white">{opportunity.feasibilityAssessment.submittedAt}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <p className="text-xs text-slate-400 mb-1">评估人</p>
                  <p className="text-sm text-white">{opportunity.feasibilityAssessment.submittedBy}</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => {
                  // 基于评估结果创建方案
                  alert('将跳转到方案创建页面，基于可行性评估结果创建技术方案')
                }}
              >
                <FileText className="w-4 h-4 mr-2" />
                基于评估结果创建方案
              </Button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">快捷操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Phone className="w-4 h-4 mr-2 text-blue-400" />
              联系客户
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <MessageSquare className="w-4 h-4 mr-2 text-green-400" />
              添加跟进
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <FileText className="w-4 h-4 mr-2 text-amber-400" />
              创建报价
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <ChevronRight className="w-4 h-4 mr-2 text-purple-400" />
              推进阶段
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button variant="destructive" size="sm">
          <XCircle className="w-4 h-4 mr-1" />
          输单
        </Button>
        <Button className="flex-1">
          <CheckCircle2 className="w-4 h-4 mr-2" />
          赢单
        </Button>
      </div>
    </motion.div>
  )
}

