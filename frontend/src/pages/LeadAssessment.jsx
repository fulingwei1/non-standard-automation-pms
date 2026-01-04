/**
 * Lead Assessment Page - Sales lead evaluation and qualification
 * Features: Lead list, assessment form, scoring, qualification status
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  LayoutGrid,
  List,
  Calendar,
  Building2,
  User,
  Phone,
  Mail,
  MapPin,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Star,
  TrendingUp,
  TrendingDown,
  Eye,
  Edit,
  FileText,
  Target,
  DollarSign,
  Percent,
  BarChart3,
  X,
  ChevronRight,
  MessageSquare,
  Briefcase,
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
  Label,
  Textarea,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// 线索状态配置
const statusConfig = {
  new: { label: '新线索', color: 'bg-blue-500', textColor: 'text-blue-400' },
  assessing: { label: '评估中', color: 'bg-amber-500', textColor: 'text-amber-400' },
  qualified: { label: '已合格', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  unqualified: { label: '不合格', color: 'bg-red-500', textColor: 'text-red-400' },
  converted: { label: '已转化', color: 'bg-purple-500', textColor: 'text-purple-400' },
  lost: { label: '已流失', color: 'bg-slate-600', textColor: 'text-slate-500' },
}

// 线索等级配置
const gradeConfig = {
  hot: { label: '热门', color: 'bg-red-500', textColor: 'text-red-400', icon: '🔥' },
  warm: { label: '温线索', color: 'bg-orange-500', textColor: 'text-orange-400', icon: '🟠' },
  cold: { label: '冷线索', color: 'bg-blue-500', textColor: 'text-blue-400', icon: '🔵' },
}

// Mock 线索数据
const mockLeads = [
  {
    id: 'LD2026010001',
    name: '新能源汽车电池测试设备需求',
    companyName: '深圳市新能源科技有限公司',
    companyShort: '深圳新能源',
    contactPerson: '张总',
    phone: '138****1234',
    email: 'zhang@example.com',
    location: '深圳市南山区',
    industry: '新能源电池',
    source: '展会',
    status: 'assessing',
    grade: 'hot',
    expectedAmount: 1200000,
    expectedCloseDate: '2026-03-15',
    score: 75,
    assessmentDate: '2026-01-05',
    assessedBy: '张销售',
    notes: '客户有明确需求，预算充足，决策周期短',
    tags: ['新能源', '测试设备', '高价值'],
    createdAt: '2026-01-03',
    lastContact: '2天前',
  },
  {
    id: 'LD2026010002',
    name: 'ICT在线测试设备采购',
    companyName: '惠州储能电池科技有限公司',
    companyShort: '惠州储能',
    contactPerson: '王工',
    phone: '137****9012',
    email: 'wang@example.com',
    location: '惠州市仲恺区',
    industry: '储能系统',
    source: '转介绍',
    status: 'qualified',
    grade: 'warm',
    expectedAmount: 450000,
    expectedCloseDate: '2026-02-28',
    score: 82,
    assessmentDate: '2026-01-04',
    assessedBy: '张销售',
    notes: '技术需求明确，有合作意向，需要进一步跟进',
    tags: ['储能', 'ICT测试'],
    createdAt: '2026-01-02',
    lastContact: '1天前',
  },
  {
    id: 'LD2026010003',
    name: '视觉检测系统升级',
    companyName: '佛山市智能装备科技有限公司',
    companyShort: '佛山智能',
    contactPerson: '周经理',
    phone: '135****7890',
    email: 'zhou@example.com',
    location: '佛山市顺德区',
    industry: '智能制造',
    source: '网络推广',
    status: 'new',
    grade: 'cold',
    expectedAmount: 380000,
    expectedCloseDate: '2026-04-01',
    score: null,
    assessmentDate: null,
    assessedBy: null,
    notes: '初步接触，需求不明确',
    tags: ['智能制造', '视觉检测'],
    createdAt: '2026-01-06',
    lastContact: '5天前',
  },
  {
    id: 'LD2026010004',
    name: 'EOL功能测试线',
    companyName: '东莞市精密电子有限公司',
    companyShort: '东莞精密',
    contactPerson: '李经理',
    phone: '139****5678',
    email: 'li@example.com',
    location: '东莞市长安镇',
    industry: '消费电子',
    source: '老客户',
    status: 'converted',
    grade: 'hot',
    expectedAmount: 1200000,
    expectedCloseDate: '2026-01-20',
    score: 88,
    assessmentDate: '2025-12-20',
    assessedBy: '张销售',
    notes: '已转化为商机，进入合同谈判阶段',
    tags: ['消费电子', 'EOL测试', '老客户'],
    createdAt: '2025-12-15',
    lastContact: '今天',
  },
  {
    id: 'LD2026010005',
    name: '烧录设备升级改造',
    companyName: '广州市汽车零部件有限公司',
    companyShort: '广州汽车',
    contactPerson: '陈总',
    phone: '136****3456',
    email: 'chen@example.com',
    location: '广州市番禺区',
    industry: '汽车零部件',
    source: '电话营销',
    status: 'unqualified',
    grade: 'cold',
    expectedAmount: 280000,
    expectedCloseDate: null,
    score: 45,
    assessmentDate: '2026-01-01',
    assessedBy: '张销售',
    notes: '预算不足，需求不匹配，暂时不跟进',
    tags: ['汽车', '烧录设备'],
    createdAt: '2025-12-28',
    lastContact: '1周前',
  },
]

// 评估维度配置
const assessmentDimensions = [
  { id: 'demand', label: '需求明确度', weight: 0.25 },
  { id: 'budget', label: '预算充足度', weight: 0.25 },
  { id: 'authority', label: '决策权限', weight: 0.20 },
  { id: 'timeline', label: '时间紧迫度', weight: 0.15 },
  { id: 'fit', label: '方案匹配度', weight: 0.15 },
]

export default function LeadAssessment() {
  const [leads, setLeads] = useState(mockLeads)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [gradeFilter, setGradeFilter] = useState('all')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedLead, setSelectedLead] = useState(null)
  const [showAssessmentForm, setShowAssessmentForm] = useState(false)
  const [assessmentScores, setAssessmentScores] = useState({})

  // 筛选线索
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const matchesSearch =
        lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.companyName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.contactPerson.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = statusFilter === 'all' || lead.status === statusFilter
      const matchesGrade = gradeFilter === 'all' || lead.grade === gradeFilter
      return matchesSearch && matchesStatus && matchesGrade
    })
  }, [leads, searchTerm, statusFilter, gradeFilter])

  // 统计数据
  const stats = useMemo(() => {
    return {
      total: leads.length,
      new: leads.filter((l) => l.status === 'new').length,
      assessing: leads.filter((l) => l.status === 'assessing').length,
      qualified: leads.filter((l) => l.status === 'qualified').length,
      converted: leads.filter((l) => l.status === 'converted').length,
      totalAmount: leads.reduce((sum, l) => sum + (l.expectedAmount || 0), 0),
    }
  }, [leads])

  // 打开评估表单
  const handleOpenAssessment = (lead) => {
    setSelectedLead(lead)
    // 如果有已评估的分数，加载它
    if (lead.score !== null) {
      const scores = {}
      assessmentDimensions.forEach((dim) => {
        scores[dim.id] = Math.floor((lead.score || 0) / assessmentDimensions.length)
      })
      setAssessmentScores(scores)
    } else {
      // 初始化分数
      const scores = {}
      assessmentDimensions.forEach((dim) => {
        scores[dim.id] = 3 // 默认3分（5分制）
      })
      setAssessmentScores(scores)
    }
    setShowAssessmentForm(true)
  }

  // 提交评估
  const handleSubmitAssessment = () => {
    if (!selectedLead) return

    // 计算总分
    let totalScore = 0
    assessmentDimensions.forEach((dim) => {
      totalScore += (assessmentScores[dim.id] || 0) * dim.weight * 20 // 转换为100分制
    })
    totalScore = Math.round(totalScore)

    // 更新线索
    const updatedLeads = leads.map((lead) => {
      if (lead.id === selectedLead.id) {
        const newStatus = totalScore >= 70 ? 'qualified' : totalScore >= 50 ? 'assessing' : 'unqualified'
        return {
          ...lead,
          score: totalScore,
          status: newStatus,
          assessmentDate: new Date().toISOString().split('T')[0],
          assessedBy: '张销售', // Mock user
        }
      }
      return lead
    })
    setLeads(updatedLeads)
    setShowAssessmentForm(false)
    setSelectedLead(null)
    setAssessmentScores({})
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
        title="线索评估"
        description="评估销售线索质量，筛选高价值商机"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </Button>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              新建线索
            </Button>
          </motion.div>
        }
      />

      {/* Stats Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">线索总数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Target className="w-8 h-8 text-primary opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">新线索</p>
                <p className="text-2xl font-bold text-blue-400">{stats.new}</p>
              </div>
              <Star className="w-8 h-8 text-blue-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">评估中</p>
                <p className="text-2xl font-bold text-amber-400">{stats.assessing}</p>
              </div>
              <Clock className="w-8 h-8 text-amber-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已合格</p>
                <p className="text-2xl font-bold text-emerald-400">{stats.qualified}</p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已转化</p>
                <p className="text-2xl font-bold text-purple-400">{stats.converted}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">预期金额</p>
                <p className="text-2xl font-bold text-white">
                  ¥{(stats.totalAmount / 10000).toFixed(0)}万
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-primary opacity-50" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn} className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索线索名称、公司、联系人..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-surface-100/50 border-white/5"
          />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-full sm:w-auto">
              <Filter className="w-4 h-4 mr-2" />
              {statusFilter === 'all' ? '全部状态' : statusConfig[statusFilter]?.label}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setStatusFilter('all')}>全部状态</DropdownMenuItem>
            {Object.entries(statusConfig).map(([key, config]) => (
              <DropdownMenuItem key={key} onClick={() => setStatusFilter(key)}>
                {config.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-full sm:w-auto">
              <Star className="w-4 h-4 mr-2" />
              {gradeFilter === 'all' ? '全部等级' : gradeConfig[gradeFilter]?.label}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setGradeFilter('all')}>全部等级</DropdownMenuItem>
            {Object.entries(gradeConfig).map(([key, config]) => (
              <DropdownMenuItem key={key} onClick={() => setGradeFilter(key)}>
                {config.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setViewMode('grid')}
          >
            <LayoutGrid className="w-4 h-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'outline'}
            size="icon"
            onClick={() => setViewMode('list')}
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </motion.div>

      {/* Leads List */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {filteredLeads.map((lead, index) => (
            <motion.div
              key={lead.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:border-primary/30 transition-all cursor-pointer h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base text-white mb-1">{lead.name}</CardTitle>
                      <div className="flex items-center gap-2 text-sm text-slate-400">
                        <Building2 className="w-3 h-3" />
                        <span>{lead.companyShort}</span>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <Badge
                        className={cn(
                          'text-xs',
                          statusConfig[lead.status]?.color,
                          statusConfig[lead.status]?.textColor
                        )}
                      >
                        {statusConfig[lead.status]?.label}
                      </Badge>
                      {lead.grade && (
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            gradeConfig[lead.grade]?.textColor,
                            'border-current'
                          )}
                        >
                          {gradeConfig[lead.grade]?.icon} {gradeConfig[lead.grade]?.label}
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {/* 联系人信息 */}
                  <div className="space-y-1.5 text-sm">
                    <div className="flex items-center gap-2 text-slate-400">
                      <User className="w-3 h-3" />
                      <span>{lead.contactPerson}</span>
                      <span className="text-slate-600">·</span>
                      <Phone className="w-3 h-3" />
                      <span>{lead.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <MapPin className="w-3 h-3" />
                      <span>{lead.location}</span>
                      <span className="text-slate-600">·</span>
                      <span>{lead.industry}</span>
                    </div>
                  </div>

                  {/* 评估分数 */}
                  {lead.score !== null ? (
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">评估分数</span>
                        <Badge
                          className={cn(
                            'text-sm font-semibold',
                            lead.score >= 70
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : lead.score >= 50
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-red-500/20 text-red-400'
                          )}
                        >
                          {lead.score}分
                        </Badge>
                      </div>
                      <Progress
                        value={lead.score}
                        className="h-2"
                        style={{
                          '--progress-background': lead.score >= 70 ? '#10b981' : lead.score >= 50 ? '#f59e0b' : '#ef4444',
                        }}
                      />
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500">尚未评估</div>
                  )}

                  {/* 预期信息 */}
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-slate-400">预期金额</span>
                      <p className="text-white font-medium">
                        ¥{(lead.expectedAmount / 10000).toFixed(0)}万
                      </p>
                    </div>
                    {lead.expectedCloseDate && (
                      <div>
                        <span className="text-slate-400">预计成交</span>
                        <p className="text-white font-medium">{lead.expectedCloseDate}</p>
                      </div>
                    )}
                  </div>

                  {/* 标签 */}
                  {lead.tags && lead.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {lead.tags.map((tag, idx) => (
                        <Badge
                          key={idx}
                          variant="outline"
                          className="text-xs text-slate-400 border-white/10"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex gap-2 pt-2 border-t border-white/5">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleOpenAssessment(lead)}
                    >
                      {lead.score !== null ? (
                        <>
                          <Edit className="w-3 h-3 mr-1" />
                          重新评估
                        </>
                      ) : (
                        <>
                          <FileText className="w-3 h-3 mr-1" />
                          开始评估
                        </>
                      )}
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      <Eye className="w-3 h-3 mr-1" />
                      查看详情
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {/* Assessment Form Dialog */}
      <Dialog open={showAssessmentForm} onOpenChange={setShowAssessmentForm}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              线索评估
            </DialogTitle>
            <DialogDescription>
              {selectedLead
                ? `评估线索 "${selectedLead.name}" - ${selectedLead.companyShort}`
                : '请对线索的各项维度进行评分'}
            </DialogDescription>
          </DialogHeader>

          {selectedLead && (
            <div className="space-y-6 py-4">
              {/* 线索基本信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">线索信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-400">公司名称</span>
                      <p className="text-white">{selectedLead.companyName}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">联系人</span>
                      <p className="text-white">{selectedLead.contactPerson}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">预期金额</span>
                      <p className="text-white">
                        ¥{(selectedLead.expectedAmount / 10000).toFixed(0)}万
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">来源</span>
                      <p className="text-white">{selectedLead.source}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 评估维度 */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-white">评估维度（5分制）</h4>
                {assessmentDimensions.map((dim) => (
                  <div key={dim.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm text-slate-400">
                        {dim.label}
                        <span className="text-slate-600 ml-1">(权重: {dim.weight * 100}%)</span>
                      </Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="range"
                          min="1"
                          max="5"
                          step="1"
                          value={assessmentScores[dim.id] || 3}
                          onChange={(e) =>
                            setAssessmentScores({
                              ...assessmentScores,
                              [dim.id]: Number(e.target.value),
                            })
                          }
                          className="w-32"
                        />
                        <span className="text-sm text-white w-8 text-right">
                          {assessmentScores[dim.id] || 3}
                        </span>
                      </div>
                    </div>
                    <Progress
                      value={((assessmentScores[dim.id] || 3) / 5) * 100}
                      className="h-1.5"
                    />
                  </div>
                ))}
              </div>

              {/* 评估结果预览 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">综合评分</span>
                    <Badge
                      className={cn(
                        'text-lg font-bold',
                        (() => {
                          let totalScore = 0
                          assessmentDimensions.forEach((dim) => {
                            totalScore += (assessmentScores[dim.id] || 0) * dim.weight * 20
                          })
                          totalScore = Math.round(totalScore)
                          return totalScore >= 70
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : totalScore >= 50
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-red-500/20 text-red-400'
                        })()
                      )}
                    >
                      {(() => {
                        let totalScore = 0
                        assessmentDimensions.forEach((dim) => {
                          totalScore += (assessmentScores[dim.id] || 0) * dim.weight * 20
                        })
                        return Math.round(totalScore)
                      })()}
                      分
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* 备注 */}
              <div className="space-y-2">
                <Label htmlFor="notes" className="text-sm text-slate-400">
                  评估备注
                </Label>
                <Textarea
                  id="notes"
                  placeholder="请输入评估说明、跟进建议等"
                  className="bg-surface-100 border-white/10 min-h-[80px]"
                  defaultValue={selectedLead.notes}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssessmentForm(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitAssessment}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              提交评估
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

