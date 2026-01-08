/**
 * Lead Assessment Page - Sales lead evaluation and qualification
 * Features: Lead list, assessment form, scoring, qualification status
 */

import { useState, useMemo, useEffect } from 'react'
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
import { leadApi } from '../services/api'

// 线索状态配置（映射后端状态到前端显示）
const statusConfig = {
  new: { label: '新线索', color: 'bg-blue-500', textColor: 'text-blue-400', backend: 'NEW' },
  assessing: { label: '评估中', color: 'bg-amber-500', textColor: 'text-amber-400', backend: 'QUALIFYING' },
  qualified: { label: '已合格', color: 'bg-emerald-500', textColor: 'text-emerald-400', backend: 'QUALIFYING' },
  unqualified: { label: '不合格', color: 'bg-red-500', textColor: 'text-red-400', backend: 'INVALID' },
  converted: { label: '已转化', color: 'bg-purple-500', textColor: 'text-purple-400', backend: 'CONVERTED' },
  lost: { label: '已流失', color: 'bg-slate-600', textColor: 'text-slate-500', backend: 'INVALID' },
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
  const [leads, setLeads] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [gradeFilter, setGradeFilter] = useState('all')
  const [viewMode, setViewMode] = useState('grid')
  const [selectedLead, setSelectedLead] = useState(null)
  const [showAssessmentForm, setShowAssessmentForm] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [assessmentScores, setAssessmentScores] = useState({})
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20
  const [newLead, setNewLead] = useState({
    lead_name: '',
    company_name: '',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    source: 'direct',
    estimated_amount: '',
    demand_summary: '',
  })

  // 加载线索列表
  const loadLeads = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusConfig[statusFilter]?.backend : undefined,
      }
      const response = await leadApi.list(params)
      if (response.data && response.data.items) {
        // 转换数据格式以适配评估页面
        const transformedLeads = response.data.items.map((lead) => {
          // 从需求摘要中解析评估信息（如果有）
          let assessmentInfo = null
          if (lead.demand_summary) {
            try {
              const parsed = JSON.parse(lead.demand_summary)
              if (parsed.assessment) {
                assessmentInfo = parsed.assessment
              }
            } catch (e) {
              // 不是JSON格式，忽略
            }
          }

          // 根据状态映射到评估页面的状态
          const statusMap = {
            NEW: 'new',
            QUALIFYING: 'assessing',
            CONVERTED: 'converted',
            INVALID: 'unqualified',
          }

          // 反向映射：从后端状态到前端状态
          const getFrontendStatus = (backendStatus) => {
            for (const [frontendStatus, config] of Object.entries(statusConfig)) {
              if (config.backend === backendStatus) {
                return frontendStatus
              }
            }
            return 'new'
          }

          // 根据评估分数确定等级
          const getGrade = (score) => {
            if (!score) return null
            if (score >= 75) return 'hot'
            if (score >= 60) return 'warm'
            return 'cold'
          }

          return {
            id: lead.id,
            lead_code: lead.lead_code,
            name: lead.demand_summary || lead.customer_name || '未命名线索',
            companyName: lead.customer_name || '',
            companyShort: lead.customer_name || '',
            contactPerson: lead.contact_name || '',
            phone: lead.contact_phone || '',
            email: '',
            location: '',
            industry: lead.industry || '',
            source: lead.source || '',
            status: getFrontendStatus(lead.status) || 'new',
            grade: assessmentInfo?.grade || getGrade(assessmentInfo?.score),
            expectedAmount: assessmentInfo?.expectedAmount || 0,
            expectedCloseDate: assessmentInfo?.expectedCloseDate || null,
            score: assessmentInfo?.score || null,
            assessmentDate: assessmentInfo?.assessmentDate || null,
            assessedBy: assessmentInfo?.assessedBy || null,
            notes: lead.demand_summary || '',
            tags: [],
            createdAt: lead.created_at || '',
            lastContact: '',
            raw: lead, // 保存原始数据
          }
        })
        setLeads(transformedLeads)
        setTotal(response.data.total || 0)
      }
    } catch (error) {
      console.error('加载线索列表失败:', error)
      // 如果API失败，使用mock数据作为fallback
      setLeads(mockLeads)
      setTotal(mockLeads.length)
    } finally {
      setLoading(false)
    }
  }

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        loadLeads()
      } else {
        setPage(1) // 重置到第一页
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [searchTerm])

  useEffect(() => {
    loadLeads()
  }, [page, statusFilter])

  // 筛选线索（前端筛选，用于等级筛选）
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const matchesGrade = gradeFilter === 'all' || lead.grade === gradeFilter
      return matchesGrade
    })
  }, [leads, gradeFilter])

  // 统计数据（基于所有数据，不仅仅是当前页）
  const stats = useMemo(() => {
    return {
      total: total, // 使用总数而不是当前页数量
      new: leads.filter((l) => l.status === 'new').length,
      assessing: leads.filter((l) => l.status === 'assessing' || l.status === 'qualified').length,
      qualified: leads.filter((l) => l.status === 'qualified').length,
      converted: leads.filter((l) => l.status === 'converted').length,
      totalAmount: leads.reduce((sum, l) => sum + (l.expectedAmount || 0), 0),
    }
  }, [leads, total])

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

  // 创建新线索
  const handleCreateLead = async () => {
    if (!newLead.lead_name || !newLead.company_name) {
      alert('请填写线索名称和公司名称')
      return
    }

    try {
      // 构建需求摘要JSON，包含线索名称和其他信息
      const demandData = {
        lead_name: newLead.lead_name,
        description: newLead.demand_summary || '',
        estimated_amount: newLead.estimated_amount ? parseFloat(newLead.estimated_amount) : null,
        contact_email: newLead.contact_email || null,
      }

      await leadApi.create({
        // lead_code 由后端自动生成
        customer_name: newLead.company_name,
        contact_name: newLead.contact_name || undefined,
        contact_phone: newLead.contact_phone || undefined,
        source: newLead.source || 'direct',
        demand_summary: JSON.stringify(demandData),
        status: 'NEW',
      })

      // 重置表单
      setNewLead({
        lead_name: '',
        company_name: '',
        contact_name: '',
        contact_phone: '',
        contact_email: '',
        source: 'direct',
        estimated_amount: '',
        demand_summary: '',
      })
      setShowCreateDialog(false)

      // 刷新列表
      loadLeads()
    } catch (err) {
      console.error('Failed to create lead:', err)
      alert('创建线索失败，请重试')
    }
  }

  // 提交评估
  const handleSubmitAssessment = async () => {
    if (!selectedLead || !selectedLead.raw) return

    // 计算总分
    let totalScore = 0
    assessmentDimensions.forEach((dim) => {
      totalScore += (assessmentScores[dim.id] || 0) * dim.weight * 20 // 转换为100分制
    })
    totalScore = Math.round(totalScore)

    // 根据分数确定等级和状态
    const grade = totalScore >= 75 ? 'hot' : totalScore >= 60 ? 'warm' : 'cold'
    const newStatus = totalScore >= 70 ? 'QUALIFYING' : totalScore >= 50 ? 'QUALIFYING' : 'INVALID'

    try {
      // 将评估信息保存到需求摘要的JSON中
      const assessmentInfo = {
        score: totalScore,
        grade: grade,
        assessmentDate: new Date().toISOString().split('T')[0],
        assessedBy: '当前用户', // TODO: 从当前用户获取
        dimensions: assessmentScores,
      }

      // 解析现有的需求摘要
      let demandData = {}
      if (selectedLead.raw.demand_summary) {
        try {
          demandData = JSON.parse(selectedLead.raw.demand_summary)
        } catch (e) {
          // 如果不是JSON，保存为文本
          demandData = { original: selectedLead.raw.demand_summary }
        }
      }

      // 更新评估信息
      demandData.assessment = assessmentInfo

      // 更新线索
      await leadApi.update(selectedLead.raw.id, {
        status: newStatus,
        demand_summary: JSON.stringify(demandData),
      })

      // 添加一条跟进记录
      await leadApi.createFollowUp(selectedLead.raw.id, {
        follow_up_type: 'OTHER',
        content: `线索评估完成，得分：${totalScore}分，等级：${gradeConfig[grade]?.label}`,
        next_action: totalScore >= 70 ? '继续跟进，准备转商机' : totalScore >= 50 ? '继续评估' : '暂不跟进',
      })

      // 重新加载数据
      loadLeads()
      setShowAssessmentForm(false)
      setSelectedLead(null)
      setAssessmentScores({})
    } catch (error) {
      console.error('保存评估失败:', error)
      alert('保存评估失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 查看详情
  const handleViewDetail = async (lead) => {
    if (lead.raw) {
      try {
        const response = await leadApi.get(lead.raw.id)
        if (response.data) {
          setSelectedLead({
            ...lead,
            raw: response.data,
          })
          setShowDetailDialog(true)
        }
      } catch (error) {
        console.error('加载线索详情失败:', error)
        setSelectedLead(lead)
        setShowDetailDialog(true)
      }
    } else {
      setSelectedLead(lead)
      setShowDetailDialog(true)
    }
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
            <Button className="flex items-center gap-2" onClick={() => setShowCreateDialog(true)}>
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
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="flex-1"
                      onClick={() => handleViewDetail(lead)}
                    >
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

      {/* No results */}
      {filteredLeads.length === 0 && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <Search className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无线索</h3>
          <p className="text-sm text-slate-500 mt-1">没有找到匹配的线索</p>
        </motion.div>
      )}

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

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-primary" />
              线索详情
            </DialogTitle>
            <DialogDescription>
              {selectedLead ? `查看线索 "${selectedLead.name || selectedLead.lead_code}" 的详细信息` : ''}
            </DialogDescription>
          </DialogHeader>

          {selectedLead && (
            <div className="space-y-6 py-4">
              {/* 基本信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">线索编码</span>
                      <p className="text-white font-medium">{selectedLead.lead_code || selectedLead.id}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">状态</span>
                      <p>
                        <Badge className={cn('text-xs', statusConfig[selectedLead.status]?.color, statusConfig[selectedLead.status]?.textColor)}>
                          {statusConfig[selectedLead.status]?.label}
                        </Badge>
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">客户名称</span>
                      <p className="text-white">{selectedLead.companyName || selectedLead.raw?.customer_name || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">行业</span>
                      <p className="text-white">{selectedLead.industry || selectedLead.raw?.industry || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">联系人</span>
                      <p className="text-white">{selectedLead.contactPerson || selectedLead.raw?.contact_name || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">联系电话</span>
                      <p className="text-white">{selectedLead.phone || selectedLead.raw?.contact_phone || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">来源</span>
                      <p className="text-white">{selectedLead.source || selectedLead.raw?.source || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">负责人</span>
                      <p className="text-white">{selectedLead.raw?.owner_name || '-'}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 需求摘要 */}
              {(selectedLead.notes || selectedLead.raw?.demand_summary) && (
                <Card className="bg-surface-50/50 border border-white/5">
                  <CardHeader>
                    <CardTitle className="text-sm text-white">需求摘要</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">
                      {selectedLead.notes || selectedLead.raw?.demand_summary || '-'}
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* 评估信息 */}
              {selectedLead.score !== null && (
                <Card className="bg-surface-50/50 border border-white/5">
                  <CardHeader>
                    <CardTitle className="text-sm text-white">评估信息</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">评估分数</span>
                      <Badge
                        className={cn(
                          'text-lg font-semibold',
                          selectedLead.score >= 70
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : selectedLead.score >= 50
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-red-500/20 text-red-400'
                        )}
                      >
                        {selectedLead.score}分
                      </Badge>
                    </div>
                    {selectedLead.grade && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">线索等级</span>
                        <Badge
                          variant="outline"
                          className={cn('text-sm', gradeConfig[selectedLead.grade]?.textColor, 'border-current')}
                        >
                          {gradeConfig[selectedLead.grade]?.icon} {gradeConfig[selectedLead.grade]?.label}
                        </Badge>
                      </div>
                    )}
                    {selectedLead.assessmentDate && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">评估日期</span>
                        <span className="text-white">{selectedLead.assessmentDate}</span>
                      </div>
                    )}
                    {selectedLead.assessedBy && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">评估人</span>
                        <span className="text-white">{selectedLead.assessedBy}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* 时间信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">时间信息</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">创建时间</span>
                      <p className="text-white">{selectedLead.createdAt || selectedLead.raw?.created_at || '-'}</p>
                    </div>
                    {selectedLead.raw?.next_action_at && (
                      <div>
                        <span className="text-slate-400">下次行动时间</span>
                        <p className="text-white">{selectedLead.raw.next_action_at}</p>
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
            {selectedLead && (
              <Button onClick={() => {
                setShowDetailDialog(false)
                handleOpenAssessment(selectedLead)
              }}>
                <Star className="w-4 h-4 mr-2" />
                {selectedLead.score !== null ? '重新评估' : '开始评估'}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Lead Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-primary" />
              新建线索
            </DialogTitle>
            <DialogDescription>
              创建新的销售线索，填写基本信息后可进行评估
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="lead_name">线索名称 *</Label>
                <Input
                  id="lead_name"
                  placeholder="如：新能源电池测试设备需求"
                  value={newLead.lead_name}
                  onChange={(e) => setNewLead({ ...newLead, lead_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company_name">公司名称 *</Label>
                <Input
                  id="company_name"
                  placeholder="如：深圳新能源科技"
                  value={newLead.company_name}
                  onChange={(e) => setNewLead({ ...newLead, company_name: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="contact_name">联系人</Label>
                <Input
                  id="contact_name"
                  placeholder="如：张总"
                  value={newLead.contact_name}
                  onChange={(e) => setNewLead({ ...newLead, contact_name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact_phone">联系电话</Label>
                <Input
                  id="contact_phone"
                  placeholder="如：138****1234"
                  value={newLead.contact_phone}
                  onChange={(e) => setNewLead({ ...newLead, contact_phone: e.target.value })}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="contact_email">邮箱</Label>
                <Input
                  id="contact_email"
                  type="email"
                  placeholder="如：zhang@company.com"
                  value={newLead.contact_email}
                  onChange={(e) => setNewLead({ ...newLead, contact_email: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="estimated_amount">预期金额（万元）</Label>
                <Input
                  id="estimated_amount"
                  type="number"
                  placeholder="如：120"
                  value={newLead.estimated_amount}
                  onChange={(e) => setNewLead({ ...newLead, estimated_amount: e.target.value })}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="demand_summary">需求描述</Label>
              <Textarea
                id="demand_summary"
                placeholder="简要描述客户需求..."
                value={newLead.demand_summary}
                onChange={(e) => setNewLead({ ...newLead, demand_summary: e.target.value })}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateLead}>
              <Plus className="w-4 h-4 mr-2" />
              创建线索
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Empty State */}
      {!loading && filteredLeads.length === 0 && (
        <motion.div
          variants={fadeIn}
          className="flex flex-col items-center justify-center py-12 text-center"
        >
          <Target className="w-16 h-16 text-slate-600 mb-4" />
          <p className="text-slate-400 text-lg mb-2">暂无线索</p>
          <p className="text-slate-500 text-sm">请调整筛选条件或创建新线索</p>
        </motion.div>
      )}

      {/* Pagination */}
      {!loading && total > pageSize && (
        <motion.div variants={fadeIn} className="flex items-center justify-between pt-4">
          <div className="text-sm text-slate-400">
            共 {total} 条线索，第 {page} / {Math.ceil(total / pageSize)} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= Math.ceil(total / pageSize)}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}

