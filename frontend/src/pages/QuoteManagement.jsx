/**
 * Quote Management Page - Sales quotation management
 * Features: Quote list, creation, version management, approval
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Search,
  Filter,
  Plus,
  FileText,
  DollarSign,
  Calendar,
  User,
  Building2,
  CheckCircle2,
  XCircle,
  Clock,
  Edit,
  Eye,
  History,
  Send,
  Copy,
  Percent,
  X,
  Layers,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { quoteApi, opportunityApi, customerApi, salesTemplateApi } from '../services/api'

// 报价状态配置
const statusConfig = {
  DRAFT: { label: '草稿', color: 'bg-slate-500', textColor: 'text-slate-400' },
  IN_REVIEW: { label: '审批中', color: 'bg-amber-500', textColor: 'text-amber-400' },
  APPROVED: { label: '已批准', color: 'bg-blue-500', textColor: 'text-blue-400' },
  SENT: { label: '已发送', color: 'bg-purple-500', textColor: 'text-purple-400' },
  EXPIRED: { label: '过期', color: 'bg-red-500', textColor: 'text-red-400' },
  REJECTED: { label: '被拒', color: 'bg-red-600', textColor: 'text-red-500' },
}

export default function QuoteManagement() {
  const [quotes, setQuotes] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [customers, setCustomers] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedQuote, setSelectedQuote] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showVersionDialog, setShowVersionDialog] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showVersionsDialog, setShowVersionsDialog] = useState(false)
  const [showCompareDialog, setShowCompareDialog] = useState(false)
  const [versions, setVersions] = useState([])
  const [selectedVersions, setSelectedVersions] = useState([null, null])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20

  const [formData, setFormData] = useState({
    opportunity_id: '',
    customer_id: '',
    status: 'DRAFT',
    valid_until: '',
    version: {
      version_no: 'V1',
      total_price: '',
      cost_total: '',
      gross_margin: '',
      lead_time_days: '',
      delivery_date: '',
      risk_terms: '',
      items: [],
    },
  })

  const [approveData, setApproveData] = useState({
    approved: true,
    remark: '',
  })

  const [newItem, setNewItem] = useState({
    item_type: 'MODULE',
    item_name: '',
    qty: '',
    unit_price: '',
    cost: '',
    lead_time_days: '',
    remark: '',
  })
  const [quoteTemplates, setQuoteTemplates] = useState([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [selectedTemplateVersionId, setSelectedTemplateVersionId] = useState('')
  const [templatePreview, setTemplatePreview] = useState(null)
  const [templateLoading, setTemplateLoading] = useState(false)

  const loadQuotes = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      }
      const response = await quoteApi.list(params)
      if (response.data && response.data.items) {
        setQuotes(response.data.items)
        setTotal(response.data.total || 0)
      }
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadOpportunities = async () => {
    try {
      const response = await opportunityApi.list({ page: 1, page_size: 100 })
      if (response.data && response.data.items) {
        setOpportunities(response.data.items)
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 })
      if (response.data && response.data.items) {
        setCustomers(response.data.items)
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const loadQuoteTemplates = async () => {
    try {
      const response = await salesTemplateApi.listQuoteTemplates({ page: 1, page_size: 100 })
      if (response.data && response.data.items) {
        setQuoteTemplates(response.data.items)
      } else if (response.items) {
        setQuoteTemplates(response.items)
      }
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const handleApplyTemplate = async (templateId, versionId) => {
    if (!templateId) return
    setTemplateLoading(true)
    try {
      const payload = {
        template_version_id: versionId || undefined,
        selections: {},
      }
      const response = await salesTemplateApi.applyQuoteTemplate(templateId, payload)
      const preview = response.data || response
      setTemplatePreview(preview)
      setFormData(prev => ({
        ...prev,
        version: {
          ...prev.version,
          version_no: preview?.version?.version_no || prev.version.version_no,
          risk_terms: preview?.version?.sections
            ? JSON.stringify(preview.version.sections, null, 2)
            : prev.version.risk_terms,
          total_price: preview?.cpq_preview?.final_price ?? prev.version.total_price,
        },
      }))
    } catch (error) {
      alert('应用模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setTemplateLoading(false)
    }
  }

  const handleTemplateSelection = (value) => {
    setSelectedTemplateId(value)
    const template = quoteTemplates.find(t => String(t.id) === value)
    const defaultVersion = template?.versions?.[0]
    const versionId = defaultVersion ? String(defaultVersion.id) : ''
    setSelectedTemplateVersionId(versionId)
    if (template) {
      handleApplyTemplate(template.id, defaultVersion?.id)
    } else {
      setTemplatePreview(null)
    }
  }

  const handleTemplateVersionSelection = (value) => {
    setSelectedTemplateVersionId(value)
    const template = quoteTemplates.find(t => String(t.id) === selectedTemplateId)
    const version = template?.versions?.find(v => String(v.id) === value)
    if (template && version) {
      handleApplyTemplate(template.id, version.id)
    }
  }

  const renderDiffSummary = (diff) => {
    if (!diff) {
      return <div className="text-slate-500">无差异</div>
    }
    const sections = [
      { key: 'sections', label: '结构' },
      { key: 'pricing_rules', label: '定价' },
    ]
    const hasChanges = sections.some(({ key }) => {
      const block = diff[key]
      return block && ((block.added?.length || 0) + (block.removed?.length || 0) + (block.changed?.length || 0) > 0)
    })
    if (!hasChanges) {
      return <div className="text-slate-500">与上一版本一致</div>
    }
    return (
      <div className="space-y-1">
        {sections.map(({ key, label }) => {
          const block = diff[key]
          if (!block) return null
          const changes = (block.added || []).length + (block.removed || []).length + (block.changed || []).length
          if (!changes) return null
          return (
            <div key={key} className="bg-slate-800 rounded px-2 py-1">
              <div className="text-slate-300">{label}</div>
              <div className="text-slate-400">
                +{block.added?.length || 0} / -{block.removed?.length || 0} / Δ{block.changed?.length || 0}
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  useEffect(() => {
    loadQuotes()
  }, [page, searchTerm, statusFilter])

  useEffect(() => {
    loadOpportunities()
    loadCustomers()
    loadQuoteTemplates()
  }, [])

  useEffect(() => {
    if (!showCreateDialog) {
      setTemplatePreview(null)
      setSelectedTemplateId('')
      setSelectedTemplateVersionId('')
    }
  }, [showCreateDialog])

  const handleCreate = async () => {
    try {
      await quoteApi.create(formData)
      setShowCreateDialog(false)
      resetForm()
      loadQuotes()
    } catch (error) {
      alert('创建报价失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateVersion = async () => {
    if (!selectedQuote) return
    try {
      await quoteApi.createVersion(selectedQuote.id, formData.version)
      setShowVersionDialog(false)
      setSelectedQuote(null)
      loadQuotes()
    } catch (error) {
      alert('创建报价版本失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleApprove = async () => {
    if (!selectedQuote) return
    try {
      await quoteApi.approve(selectedQuote.id, approveData)
      setShowApproveDialog(false)
      setSelectedQuote(null)
      loadQuotes()
    } catch (error) {
      alert('审批报价失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleViewVersions = async (quote) => {
    setSelectedQuote(quote)
    try {
      const response = await quoteApi.getVersions(quote.id)
      if (response.data) {
        setVersions(response.data)
      }
      setShowVersionsDialog(true)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  // 查看详情
  const handleViewDetail = async (quote) => {
    try {
      const response = await quoteApi.get(quote.id)
      if (response.data) {
        setSelectedQuote(response.data)
        setShowDetailDialog(true)
        // 加载版本信息
        try {
          const versionsResponse = await quoteApi.getVersions(quote.id)
          if (versionsResponse.data) {
            setVersions(versionsResponse.data)
          }
        } catch (error) {
      console.error('操作失败:', error)
    }
      }
    } catch (error) {
      setSelectedQuote(quote)
      setShowDetailDialog(true)
    }
  }

  // 编辑报价
  const handleEditClick = async (quote) => {
    try {
      const response = await quoteApi.get(quote.id)
      if (response.data) {
        const quoteData = response.data
        setSelectedQuote(quoteData)
        setFormData({
          opportunity_id: quoteData.opportunity_id || '',
          customer_id: quoteData.customer_id || '',
          status: quoteData.status || 'DRAFT',
          valid_until: quoteData.valid_until || '',
          version: quoteData.current_version
            ? {
                version_no: quoteData.current_version.version_no || 'V1',
                total_price: quoteData.current_version.total_price || '',
                cost_total: quoteData.current_version.cost_total || '',
                gross_margin: quoteData.current_version.gross_margin || '',
                lead_time_days: quoteData.current_version.lead_time_days || '',
                delivery_date: quoteData.current_version.delivery_date || '',
                risk_terms: quoteData.current_version.risk_terms || '',
                items: quoteData.current_version.items || [],
              }
            : {
                version_no: 'V1',
                total_price: '',
                cost_total: '',
                gross_margin: '',
                lead_time_days: '',
                delivery_date: '',
                risk_terms: '',
                items: [],
              },
        })
        setShowEditDialog(true)
      }
    } catch (error) {
      alert('加载报价详情失败')
    }
  }

  // 更新报价
  const handleUpdate = async () => {
    if (!selectedQuote) return
    try {
      await quoteApi.update(selectedQuote.id, formData)
      setShowEditDialog(false)
      setSelectedQuote(null)
      loadQuotes()
    } catch (error) {
      alert('更新报价失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 版本对比
  const handleCompareVersions = () => {
    if (selectedVersions[0] && selectedVersions[1]) {
      setShowCompareDialog(true)
    } else {
      alert('请选择两个版本进行对比')
    }
  }

  const addItem = () => {
    if (!newItem.item_name || !newItem.qty || !newItem.unit_price) {
      alert('请填写完整的明细信息')
      return
    }
    setFormData({
      ...formData,
      version: {
        ...formData.version,
        items: [...formData.version.items, { ...newItem }],
      },
    })
    setNewItem({
      item_type: 'MODULE',
      item_name: '',
      qty: '',
      unit_price: '',
      cost: '',
      lead_time_days: '',
      remark: '',
    })
  }

  const removeItem = (index) => {
    const newItems = formData.version.items.filter((_, i) => i !== index)
    setFormData({
      ...formData,
      version: {
        ...formData.version,
        items: newItems,
      },
    })
  }

  const resetForm = () => {
    setFormData({
      opportunity_id: '',
      customer_id: '',
      status: 'DRAFT',
      valid_until: '',
      version: {
        version_no: 'V1',
        total_price: '',
        cost_total: '',
        gross_margin: '',
        lead_time_days: '',
        delivery_date: '',
        risk_terms: '',
        items: [],
      },
    })
  }

  const stats = useMemo(() => {
    return {
      total: total,
      draft: quotes.filter((q) => q.status === 'DRAFT').length,
      inReview: quotes.filter((q) => q.status === 'IN_REVIEW').length,
      approved: quotes.filter((q) => q.status === 'APPROVED').length,
      totalAmount: quotes.reduce((sum, q) => {
        const version = q.current_version
        return sum + (parseFloat(version?.total_price) || 0)
      }, 0),
    }
  }, [quotes, total])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="报价管理"
        description="管理销售报价，支持多版本管理和审批流程"
        action={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            新建报价
          </Button>
        }
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总报价数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">草稿</p>
                <p className="text-2xl font-bold text-white">{stats.draft}</p>
              </div>
              <Clock className="h-8 w-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">审批中</p>
                <p className="text-2xl font-bold text-white">{stats.inReview}</p>
              </div>
              <Clock className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总金额</p>
                <p className="text-2xl font-bold text-white">
                  {(stats.totalAmount / 10000).toFixed(1)}万
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索报价编码..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  状态: {statusFilter === 'all' ? '全部' : statusConfig[statusFilter]?.label}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStatusFilter('all')}>全部</DropdownMenuItem>
                {Object.entries(statusConfig).map(([key, config]) => (
                  <DropdownMenuItem key={key} onClick={() => setStatusFilter(key)}>
                    {config.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardContent>
      </Card>

      {/* 报价列表 */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">加载中...</div>
      ) : quotes.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无报价数据</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quotes.map((quote) => (
            <motion.div key={quote.id} variants={fadeIn} whileHover={{ y: -4 }}>
              <Card className="h-full hover:border-blue-500 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{quote.quote_code}</CardTitle>
                      <p className="text-sm text-slate-400 mt-1">{quote.opportunity_code}</p>
                    </div>
                    <Badge className={cn(statusConfig[quote.status]?.color)}>
                      {statusConfig[quote.status]?.label}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-300">
                      <Building2 className="h-4 w-4 text-slate-400" />
                      {quote.customer_name}
                    </div>
                    {quote.current_version && (
                      <>
                        <div className="flex items-center gap-2 text-slate-300">
                          <DollarSign className="h-4 w-4 text-slate-400" />
                          {parseFloat(quote.current_version.total_price || 0).toLocaleString()} 元
                        </div>
                        {quote.current_version.gross_margin && (
                          <div className="flex items-center gap-2 text-slate-300">
                            <Percent className="h-4 w-4 text-slate-400" />
                            毛利率: {quote.current_version.gross_margin}%
                          </div>
                        )}
                      </>
                    )}
                    {quote.valid_until && (
                      <div className="flex items-center gap-2 text-slate-300">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        有效期至: {quote.valid_until}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewDetail(quote)}
                      className="flex-1"
                    >
                      <Eye className="mr-2 h-4 w-4" />
                      详情
                    </Button>
                    {quote.status === 'DRAFT' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditClick(quote)}
                        className="flex-1"
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        编辑
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewVersions(quote)}
                      className="flex-1"
                    >
                      <History className="mr-2 h-4 w-4" />
                      版本
                    </Button>
                    {quote.status === 'DRAFT' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedQuote(quote)
                          setShowVersionDialog(true)
                        }}
                        className="flex-1"
                      >
                        <Copy className="mr-2 h-4 w-4" />
                        新版本
                      </Button>
                    )}
                    {quote.status === 'IN_REVIEW' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedQuote(quote)
                          setShowApproveDialog(true)
                        }}
                        className="flex-1"
                      >
                        <CheckCircle2 className="mr-2 h-4 w-4" />
                        审批
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)}>
            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage(page + 1)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 创建报价对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>新建报价</DialogTitle>
            <DialogDescription>创建新的销售报价</DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="basic" className="w-full">
            <TabsList>
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="version">报价版本</TabsTrigger>
              <TabsTrigger value="items">报价明细</TabsTrigger>
            </TabsList>
            <TabsContent value="basic" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>商机 *</Label>
                  <select
                    value={formData.opportunity_id}
                    onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    <option value="">请选择商机</option>
                    {opportunities.map((opp) => (
                      <option key={opp.id} value={opp.id}>
                        {opp.opp_code} - {opp.opp_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>客户 *</Label>
                  <select
                    value={formData.customer_id}
                    onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    <option value="">请选择客户</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.customer_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>状态</Label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    {Object.entries(statusConfig).map(([key, config]) => (
                      <option key={key} value={key}>
                        {config.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>有效期至</Label>
                  <Input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                  />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="version" className="space-y-4">
              <div className="border border-slate-700 rounded-md p-4 bg-slate-900 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-semibold">模板驱动</Label>
                    <p className="text-xs text-slate-400">选择模板以复制条款、同步 CPQ 预测并查看版本差异</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => window.open('/sales/templates', '_blank')}>
                    <Layers className="w-4 h-4 mr-1" />
                    模板中心
                  </Button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <Label>报价模板</Label>
                    <select
                      value={selectedTemplateId}
                      onChange={(e) => handleTemplateSelection(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                    >
                      <option value="">不使用模板</option>
                      {quoteTemplates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.template_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {selectedTemplateId && (
                    <div>
                      <Label>模板版本</Label>
                      <select
                        value={selectedTemplateVersionId}
                        onChange={(e) => handleTemplateVersionSelection(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
                      >
                        {(quoteTemplates.find(t => String(t.id) === selectedTemplateId)?.versions || []).map(
                          (version) => (
                            <option key={version.id} value={version.id}>
                              {version.version_no} · {version.status}
                            </option>
                          )
                        )}
                      </select>
                    </div>
                  )}
                </div>
                {templateLoading && (
                  <p className="text-xs text-slate-400">模板应用中...</p>
                )}
                {templatePreview?.cpq_preview && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                    <div>
                      <div className="text-slate-400">基础价格</div>
                      <div className="text-lg font-semibold text-white">
                        {templatePreview.cpq_preview.base_price}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-400">调价合计</div>
                      <div className="text-lg font-semibold text-blue-300">
                        {templatePreview.cpq_preview.adjustment_total}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-400">预测报价</div>
                      <div className="text-lg font-semibold text-emerald-300">
                        {templatePreview.cpq_preview.final_price}
                      </div>
                    </div>
                  </div>
                )}
                {templatePreview?.version_diff && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="text-slate-400 mb-1">版本差异</div>
                      {renderDiffSummary(templatePreview.version_diff)}
                    </div>
                    <div>
                      <div className="text-slate-400 mb-1">审批 / 发布记录</div>
                      <div className="space-y-1">
                        {(templatePreview.approval_history || []).slice(0, 4).map((record) => (
                          <div
                            key={record.version_id}
                            className="flex items-center justify-between bg-slate-800 rounded px-2 py-1"
                          >
                            <span>{record.version_no}</span>
                            <span className="text-slate-400">
                              {record.status}{' '}
                              {record.published_at ? formatDate(record.published_at) : ''}
                            </span>
                          </div>
                        ))}
                        {(templatePreview.approval_history || []).length === 0 && (
                          <div className="text-slate-500">暂无记录</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>版本号 *</Label>
                  <Input
                    value={formData.version.version_no}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, version_no: e.target.value },
                      })
                    }
                    placeholder="V1"
                  />
                </div>
                <div>
                  <Label>总价</Label>
                  <Input
                    type="number"
                    value={formData.version.total_price}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, total_price: e.target.value },
                      })
                    }
                    placeholder="请输入总价"
                  />
                </div>
                <div>
                  <Label>成本总计</Label>
                  <Input
                    type="number"
                    value={formData.version.cost_total}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, cost_total: e.target.value },
                      })
                    }
                    placeholder="请输入成本总计"
                  />
                </div>
                <div>
                  <Label>毛利率 (%)</Label>
                  <Input
                    type="number"
                    value={formData.version.gross_margin}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, gross_margin: e.target.value },
                      })
                    }
                    placeholder="请输入毛利率"
                  />
                </div>
                <div>
                  <Label>交期 (天)</Label>
                  <Input
                    type="number"
                    value={formData.version.lead_time_days}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, lead_time_days: e.target.value },
                      })
                    }
                    placeholder="请输入交期"
                  />
                </div>
                <div>
                  <Label>交付日期</Label>
                  <Input
                    type="date"
                    value={formData.version.delivery_date}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, delivery_date: e.target.value },
                      })
                    }
                  />
                </div>
              </div>
              <div>
                <Label>风险条款</Label>
                <Textarea
                  value={formData.version.risk_terms}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      version: { ...formData.version, risk_terms: e.target.value },
                    })
                  }
                  placeholder="请输入风险条款"
                  rows={3}
                />
              </div>
            </TabsContent>
            <TabsContent value="items" className="space-y-4">
              <div className="space-y-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Label>明细类型</Label>
                    <select
                      value={newItem.item_type}
                      onChange={(e) => setNewItem({ ...newItem, item_type: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                    >
                      <option value="MODULE">模块</option>
                      <option value="LABOR">工时</option>
                      <option value="SOFTWARE">软件</option>
                      <option value="OUTSOURCE">外协</option>
                      <option value="OTHER">其他</option>
                    </select>
                  </div>
                  <div className="flex-1">
                    <Label>明细名称 *</Label>
                    <Input
                      value={newItem.item_name}
                      onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })}
                      placeholder="请输入明细名称"
                    />
                  </div>
                  <div className="w-24">
                    <Label>数量 *</Label>
                    <Input
                      type="number"
                      value={newItem.qty}
                      onChange={(e) => setNewItem({ ...newItem, qty: e.target.value })}
                      placeholder="1"
                    />
                  </div>
                  <div className="w-32">
                    <Label>单价 *</Label>
                    <Input
                      type="number"
                      value={newItem.unit_price}
                      onChange={(e) => setNewItem({ ...newItem, unit_price: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                  <div className="w-32">
                    <Label>成本</Label>
                    <Input
                      type="number"
                      value={newItem.cost}
                      onChange={(e) => setNewItem({ ...newItem, cost: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={addItem}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {formData.version.items.length > 0 && (
                  <div className="border border-slate-700 rounded-md p-4">
                    <div className="space-y-2">
                      {formData.version.items.map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center gap-2 p-2 bg-slate-800 rounded"
                        >
                          <span className="flex-1 text-sm">{item.item_name}</span>
                          <span className="text-sm text-slate-400">数量: {item.qty}</span>
                          <span className="text-sm text-slate-400">
                            单价: {parseFloat(item.unit_price || 0).toLocaleString()}
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeItem(index)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 审批对话框 */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>审批报价</DialogTitle>
            <DialogDescription>审批报价申请</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>审批结果 *</Label>
              <select
                value={approveData.approved ? 'true' : 'false'}
                onChange={(e) =>
                  setApproveData({ ...approveData, approved: e.target.value === 'true' })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
              >
                <option value="true">批准</option>
                <option value="false">驳回</option>
              </select>
            </div>
            <div>
              <Label>备注</Label>
              <Textarea
                value={approveData.remark}
                onChange={(e) => setApproveData({ ...approveData, remark: e.target.value })}
                placeholder="请输入审批备注"
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
              取消
            </Button>
            <Button onClick={handleApprove}>提交</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 版本列表对话框 */}
      <Dialog open={showVersionsDialog} onOpenChange={setShowVersionsDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>报价版本列表</DialogTitle>
            <DialogDescription>查看报价的所有版本</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            {versions.length === 0 ? (
              <p className="text-center text-slate-400 py-8">暂无版本数据</p>
            ) : (
              versions.map((version) => (
                <Card key={version.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{version.version_no}</CardTitle>
                      {version.approved_at && (
                        <Badge className="bg-emerald-500">已审批</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-400">总价: </span>
                        <span className="text-white">
                          {parseFloat(version.total_price || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">成本: </span>
                        <span className="text-white">
                          {parseFloat(version.cost_total || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">毛利率: </span>
                        <span className="text-white">{version.gross_margin || 0}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400">交期: </span>
                        <span className="text-white">{version.lead_time_days || 0} 天</span>
                      </div>
                      {version.items && version.items.length > 0 && (
                        <div className="col-span-2">
                          <p className="text-slate-400 mb-2">明细:</p>
                          <div className="space-y-1">
                            {version.items.map((item, idx) => (
                              <div key={idx} className="text-sm text-slate-300">
                                {item.item_name} × {item.qty} ={' '}
                                {parseFloat(item.unit_price || 0) * parseFloat(item.qty || 0)}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersionsDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑报价对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑报价</DialogTitle>
            <DialogDescription>更新报价信息</DialogDescription>
          </DialogHeader>
          <Tabs defaultValue="basic" className="w-full">
            <TabsList>
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="version">报价版本</TabsTrigger>
              <TabsTrigger value="items">报价明细</TabsTrigger>
            </TabsList>
            <TabsContent value="basic" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>商机 *</Label>
                  <select
                    value={formData.opportunity_id}
                    onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    <option value="">请选择商机</option>
                    {opportunities.map((opp) => (
                      <option key={opp.id} value={opp.id}>
                        {opp.opp_code} - {opp.opp_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>客户 *</Label>
                  <select
                    value={formData.customer_id}
                    onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    <option value="">请选择客户</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.customer_name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>状态</Label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                  >
                    {Object.entries(statusConfig).map(([key, config]) => (
                      <option key={key} value={key}>
                        {config.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>有效期至</Label>
                  <Input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                  />
                </div>
              </div>
            </TabsContent>
            <TabsContent value="version" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>版本号 *</Label>
                  <Input
                    value={formData.version.version_no}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, version_no: e.target.value },
                      })
                    }
                    placeholder="V1"
                  />
                </div>
                <div>
                  <Label>总价</Label>
                  <Input
                    type="number"
                    value={formData.version.total_price}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, total_price: e.target.value },
                      })
                    }
                    placeholder="请输入总价"
                  />
                </div>
                <div>
                  <Label>成本总计</Label>
                  <Input
                    type="number"
                    value={formData.version.cost_total}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, cost_total: e.target.value },
                      })
                    }
                    placeholder="请输入成本总计"
                  />
                </div>
                <div>
                  <Label>毛利率 (%)</Label>
                  <Input
                    type="number"
                    value={formData.version.gross_margin}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, gross_margin: e.target.value },
                      })
                    }
                    placeholder="请输入毛利率"
                  />
                </div>
                <div>
                  <Label>交期 (天)</Label>
                  <Input
                    type="number"
                    value={formData.version.lead_time_days}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, lead_time_days: e.target.value },
                      })
                    }
                    placeholder="请输入交期"
                  />
                </div>
                <div>
                  <Label>交付日期</Label>
                  <Input
                    type="date"
                    value={formData.version.delivery_date}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        version: { ...formData.version, delivery_date: e.target.value },
                      })
                    }
                  />
                </div>
              </div>
              <div>
                <Label>风险条款</Label>
                <Textarea
                  value={formData.version.risk_terms}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      version: { ...formData.version, risk_terms: e.target.value },
                    })
                  }
                  placeholder="请输入风险条款"
                  rows={3}
                />
              </div>
            </TabsContent>
            <TabsContent value="items" className="space-y-4">
              <div className="space-y-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <Label>明细类型</Label>
                    <select
                      value={newItem.item_type}
                      onChange={(e) => setNewItem({ ...newItem, item_type: e.target.value })}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-md text-white"
                    >
                      <option value="MODULE">模块</option>
                      <option value="LABOR">工时</option>
                      <option value="SOFTWARE">软件</option>
                      <option value="OUTSOURCE">外协</option>
                      <option value="OTHER">其他</option>
                    </select>
                  </div>
                  <div className="flex-1">
                    <Label>明细名称 *</Label>
                    <Input
                      value={newItem.item_name}
                      onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })}
                      placeholder="请输入明细名称"
                    />
                  </div>
                  <div className="w-24">
                    <Label>数量 *</Label>
                    <Input
                      type="number"
                      value={newItem.qty}
                      onChange={(e) => setNewItem({ ...newItem, qty: e.target.value })}
                      placeholder="1"
                    />
                  </div>
                  <div className="w-32">
                    <Label>单价 *</Label>
                    <Input
                      type="number"
                      value={newItem.unit_price}
                      onChange={(e) => setNewItem({ ...newItem, unit_price: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                  <div className="w-32">
                    <Label>成本</Label>
                    <Input
                      type="number"
                      value={newItem.cost}
                      onChange={(e) => setNewItem({ ...newItem, cost: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                  <div className="flex items-end">
                    <Button onClick={addItem}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {formData.version.items.length > 0 && (
                  <div className="border border-slate-700 rounded-md p-4">
                    <div className="space-y-2">
                      {formData.version.items.map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center gap-2 p-2 bg-slate-800 rounded"
                        >
                          <span className="flex-1 text-sm">{item.item_name}</span>
                          <span className="text-sm text-slate-400">数量: {item.qty}</span>
                          <span className="text-sm text-slate-400">
                            单价: {parseFloat(item.unit_price || 0).toLocaleString()}
                          </span>
                          <Button variant="ghost" size="sm" onClick={() => removeItem(index)}>
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>报价详情</DialogTitle>
            <DialogDescription>查看报价详细信息和版本</DialogDescription>
          </DialogHeader>
          {selectedQuote && (
            <div className="space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold mb-4">基本信息</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">报价编码</Label>
                    <p className="text-white">{selectedQuote.quote_code}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">状态</Label>
                    <Badge className={cn(statusConfig[selectedQuote.status]?.color, 'mt-1')}>
                      {statusConfig[selectedQuote.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-slate-400">客户</Label>
                    <p className="text-white">{selectedQuote.customer_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">商机</Label>
                    <p className="text-white">{selectedQuote.opportunity_code}</p>
                  </div>
                  {selectedQuote.valid_until && (
                    <div>
                      <Label className="text-slate-400">有效期至</Label>
                      <p className="text-white">{selectedQuote.valid_until}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* 当前版本信息 */}
              {selectedQuote.current_version && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">当前版本信息</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-slate-400">版本号</Label>
                      <p className="text-white">{selectedQuote.current_version.version_no}</p>
                    </div>
                    <div>
                      <Label className="text-slate-400">总价</Label>
                      <p className="text-white">
                        {parseFloat(selectedQuote.current_version.total_price || 0).toLocaleString()}{' '}
                        元
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">成本总计</Label>
                      <p className="text-white">
                        {parseFloat(selectedQuote.current_version.cost_total || 0).toLocaleString()}{' '}
                        元
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">毛利率</Label>
                      <p className="text-white">
                        {selectedQuote.current_version.gross_margin || 0}%
                      </p>
                    </div>
                    <div>
                      <Label className="text-slate-400">交期</Label>
                      <p className="text-white">
                        {selectedQuote.current_version.lead_time_days || 0} 天
                      </p>
                    </div>
                    {selectedQuote.current_version.delivery_date && (
                      <div>
                        <Label className="text-slate-400">交付日期</Label>
                        <p className="text-white">{selectedQuote.current_version.delivery_date}</p>
                      </div>
                    )}
                    {selectedQuote.current_version.risk_terms && (
                      <div className="col-span-2">
                        <Label className="text-slate-400">风险条款</Label>
                        <p className="text-white mt-1">{selectedQuote.current_version.risk_terms}</p>
                      </div>
                    )}
                  </div>

                  {/* 报价明细 */}
                  {selectedQuote.current_version.items &&
                    selectedQuote.current_version.items.length > 0 && (
                      <div className="mt-4">
                        <Label className="text-slate-400 mb-2 block">报价明细</Label>
                        <div className="space-y-2">
                          {selectedQuote.current_version.items.map((item, index) => (
                            <Card key={index}>
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="text-white font-medium">{item.item_name}</p>
                                    <p className="text-sm text-slate-400">
                                      {item.item_type} × {item.qty}
                                    </p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-white">
                                      {parseFloat(item.unit_price || 0).toLocaleString()} 元/单位
                                    </p>
                                    <p className="text-sm text-slate-400">
                                      小计:{' '}
                                      {(
                                        parseFloat(item.unit_price || 0) * parseFloat(item.qty || 0)
                                      ).toLocaleString()}{' '}
                                      元
                                    </p>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                </div>
              )}

              {/* 版本列表 */}
              {versions.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">版本历史</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (versions.length >= 2) {
                          setSelectedVersions([versions[0], versions[1]])
                          setShowCompareDialog(true)
                        } else {
                          alert('至少需要两个版本才能对比')
                        }
                      }}
                    >
                      版本对比
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {versions.map((version) => (
                      <Card key={version.id}>
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-white font-medium">{version.version_no}</p>
                              <p className="text-sm text-slate-400">
                                总价: {parseFloat(version.total_price || 0).toLocaleString()} 元 |{' '}
                                毛利率: {version.gross_margin || 0}%
                              </p>
                            </div>
                            {version.approved_at && (
                              <Badge className="bg-emerald-500">已审批</Badge>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 版本对比对话框 */}
      <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>版本对比</DialogTitle>
            <DialogDescription>对比两个报价版本的差异</DialogDescription>
          </DialogHeader>
          {selectedVersions[0] && selectedVersions[1] && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-400 mb-2 block">版本 1: {selectedVersions[0].version_no}</Label>
                  <Card>
                    <CardContent className="p-4 space-y-2">
                      <div>
                        <span className="text-slate-400">总价: </span>
                        <span className="text-white">
                          {parseFloat(selectedVersions[0].total_price || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">成本: </span>
                        <span className="text-white">
                          {parseFloat(selectedVersions[0].cost_total || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">毛利率: </span>
                        <span className="text-white">{selectedVersions[0].gross_margin || 0}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400">交期: </span>
                        <span className="text-white">{selectedVersions[0].lead_time_days || 0} 天</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                <div>
                  <Label className="text-slate-400 mb-2 block">版本 2: {selectedVersions[1].version_no}</Label>
                  <Card>
                    <CardContent className="p-4 space-y-2">
                      <div>
                        <span className="text-slate-400">总价: </span>
                        <span className="text-white">
                          {parseFloat(selectedVersions[1].total_price || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">成本: </span>
                        <span className="text-white">
                          {parseFloat(selectedVersions[1].cost_total || 0).toLocaleString()} 元
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400">毛利率: </span>
                        <span className="text-white">{selectedVersions[1].gross_margin || 0}%</span>
                      </div>
                      <div>
                        <span className="text-slate-400">交期: </span>
                        <span className="text-white">{selectedVersions[1].lead_time_days || 0} 天</span>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompareDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
