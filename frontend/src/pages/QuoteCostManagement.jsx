/**
 * Quote Cost Management Page - 报价成本管理页面
 * Features: Cost overview, cost breakdown, template application, cost check, approval workflow
 */

import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  DollarSign,
  Percent,
  Calculator,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Layers,
  TrendingUp,
  TrendingDown,
  Edit,
  Plus,
  Trash2,
  Save,
  RefreshCw,
  Search,
  Filter,
  Download,
  Send,
  History,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
  AlertDescription,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { quoteApi, salesTemplateApi } from '../services/api'

export default function QuoteCostManagement() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [quote, setQuote] = useState(null)
  const [version, setVersion] = useState(null)
  const [items, setItems] = useState([])
  const [costCheck, setCostCheck] = useState(null)
  const [approvalHistory, setApprovalHistory] = useState([])
  const [costTemplates, setCostTemplates] = useState([])
  
  // Dialog states
  const [showTemplateDialog, setShowTemplateDialog] = useState(false)
  const [showApprovalDialog, setShowApprovalDialog] = useState(false)
  const [showHistoryDialog, setShowHistoryDialog] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  
  // Form states
  const [approvalData, setApprovalData] = useState({
    approval_level: 1,
    comment: '',
  })
  
  // Group items by category
  const groupedItems = useMemo(() => {
    const groups = {}
    items.forEach(item => {
      const category = item.cost_category || '其他'
      if (!groups[category]) {
        groups[category] = []
      }
      groups[category].push(item)
    })
    return groups
  }, [items])
  
  // Calculate totals
  const totals = useMemo(() => {
    const totalPrice = items.reduce((sum, item) => sum + (parseFloat(item.unit_price || 0) * parseFloat(item.qty || 0)), 0)
    const totalCost = items.reduce((sum, item) => sum + (parseFloat(item.cost || 0) * parseFloat(item.qty || 0)), 0)
    const grossMargin = totalPrice > 0 ? ((totalPrice - totalCost) / totalPrice * 100) : 0
    return { totalPrice, totalCost, grossMargin }
  }, [items])
  
  // Margin status
  const marginStatus = useMemo(() => {
    if (totals.grossMargin >= 20) return { label: '正常', color: 'bg-green-500', textColor: 'text-green-400' }
    if (totals.grossMargin >= 15) return { label: '警告', color: 'bg-amber-500', textColor: 'text-amber-400' }
    return { label: '风险', color: 'bg-red-500', textColor: 'text-red-400' }
  }, [totals.grossMargin])
  
  useEffect(() => {
    loadData()
  }, [id])
  
  const loadData = async () => {
    setLoading(true)
    try {
      // Load quote
      const quoteRes = await quoteApi.get(id)
      setQuote(quoteRes.data?.data || quoteRes.data)
      
      // Load current version
      const quoteData = quoteRes.data?.data || quoteRes.data
      if (quoteData.current_version_id) {
        const versionsRes = await quoteApi.getVersions(id)
        const versions = versionsRes.data?.data || versionsRes.data || []
        const currentVersion = versions.find(v => v.id === quoteData.current_version_id) || versions[0]
        setVersion(currentVersion)
        
        // Load items from separate API
        try {
          const itemsRes = await quoteApi.getItems(id, currentVersion.id)
          const itemsList = itemsRes.data?.data || itemsRes.data || []
          setItems(itemsList)
        } catch (e) {
          // Fallback to version.items if API not available
          if (currentVersion.items) {
            setItems(currentVersion.items)
          }
        }
      }
      
      // Load cost check
      try {
        const checkRes = await quoteApi.checkCost(id)
        setCostCheck(checkRes.data?.data || checkRes.data)
      } catch (e) {
        console.log('Cost check not available:', e)
      }
      
      // Load approval history
      try {
        const historyRes = await quoteApi.getCostApprovalHistory(id)
        setApprovalHistory(historyRes.data?.data || historyRes.data || [])
      } catch (e) {
        console.log('Approval history not available:', e)
      }
      
      // Load cost templates
      try {
        const templatesRes = await salesTemplateApi.listCostTemplates({ page: 1, page_size: 100, is_active: true })
        const templates = templatesRes.data?.data?.items || templatesRes.data?.items || []
        setCostTemplates(templates)
      } catch (e) {
        console.log('Cost templates not available:', e)
      }
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleApplyTemplate = async () => {
    if (!selectedTemplate) return
    
    try {
      setLoading(true)
      await quoteApi.applyCostTemplate(id, selectedTemplate.id, version?.id, {})
      await loadData()
      setShowTemplateDialog(false)
      setSelectedTemplate(null)
    } catch (error) {
      console.error('应用模板失败:', error)
      alert('应用模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleCalculateCost = async () => {
    try {
      setLoading(true)
      await quoteApi.calculateCost(id, version?.id)
      await loadData()
    } catch (error) {
      console.error('计算成本失败:', error)
      alert('计算成本失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleCheckCost = async () => {
    try {
      setLoading(true)
      const res = await quoteApi.checkCost(id, version?.id)
      setCostCheck(res.data?.data || res.data)
    } catch (error) {
      console.error('成本检查失败:', error)
      alert('成本检查失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmitApproval = async () => {
    try {
      setLoading(true)
      await quoteApi.submitCostApproval(id, {
        quote_version_id: version?.id,
        ...approvalData,
      })
      await loadData()
      setShowApprovalDialog(false)
      setApprovalData({ approval_level: 1, comment: '' })
    } catch (error) {
      console.error('提交审批失败:', error)
      alert('提交审批失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleItemChange = (itemId, field, value) => {
    setItems(items.map(item => 
      item.id === itemId 
        ? { ...item, [field]: value }
        : item
    ))
  }
  
  const handleAutoMatchCost = async () => {
    if (!version) {
      alert('请先选择报价版本')
      return
    }
    
    try {
      setLoading(true)
      const res = await quoteApi.getCostMatchSuggestions(id, version.id)
      
      const suggestions = res.data?.data || res.data
      if (suggestions) {
        setCostSuggestions(suggestions)
        // 初始化编辑状态
        const edited = {}
        suggestions.suggestions?.forEach(s => {
          edited[s.item_id] = {
            cost: s.suggested_cost || s.current_cost,
            specification: s.suggested_specification,
            unit: s.suggested_unit,
            lead_time_days: s.suggested_lead_time_days,
            cost_category: s.suggested_cost_category,
          }
        })
        setEditedSuggestions(edited)
        setShowSuggestionsDialog(true)
      }
    } catch (error) {
      console.error('获取成本建议失败:', error)
      alert('获取成本建议失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleApplySuggestions = async () => {
    if (!costSuggestions || !version) {
      return
    }
    
    try {
      setLoading(true)
      
      // 准备应用数据
      const applyData = {
        suggestions: costSuggestions.suggestions.map(s => ({
          item_id: s.item_id,
          cost: editedSuggestions[s.item_id]?.cost || s.suggested_cost || s.current_cost,
          specification: editedSuggestions[s.item_id]?.specification || s.suggested_specification,
          unit: editedSuggestions[s.item_id]?.unit || s.suggested_unit,
          lead_time_days: editedSuggestions[s.item_id]?.lead_time_days || s.suggested_lead_time_days,
          cost_category: editedSuggestions[s.item_id]?.cost_category || s.suggested_cost_category,
        }))
      }
      
      await quoteApi.applyCostSuggestions(id, version.id, applyData)
      
      setShowSuggestionsDialog(false)
      setCostSuggestions(null)
      setEditedSuggestions({})
      
      // 重新加载数据
      await loadData()
      
      alert('成本建议已应用！')
    } catch (error) {
      console.error('应用成本建议失败:', error)
      alert('应用成本建议失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleSuggestionChange = (itemId, field, value) => {
    setEditedSuggestions({
      ...editedSuggestions,
      [itemId]: {
        ...editedSuggestions[itemId],
        [field]: value,
      }
    })
  }
  
  const handleSaveItems = async () => {
    if (!version) {
      alert('请先选择报价版本')
      return
    }
    
    try {
      setLoading(true)
      
      // 准备批量更新数据
      const batchData = {
        items: items.map(item => ({
          id: item.id,
          item_type: item.item_type,
          item_name: item.item_name,
          qty: item.qty ? parseFloat(item.qty) : null,
          unit_price: item.unit_price ? parseFloat(item.unit_price) : null,
          cost: item.cost ? parseFloat(item.cost) : null,
          lead_time_days: item.lead_time_days ? parseInt(item.lead_time_days) : null,
          remark: item.remark,
          cost_category: item.cost_category,
          cost_source: item.cost_source,
          specification: item.specification,
          unit: item.unit,
        }))
      }
      
      const res = await quoteApi.batchUpdateItems(id, batchData, version.id)
      
      // 更新版本的成本数据
      if (res.data?.data) {
        const costData = res.data.data
        if (version) {
          version.total_price = costData.total_price
          version.cost_total = costData.total_cost
          version.gross_margin = costData.gross_margin
        }
      }
      
      // 重新加载数据
      await loadData()
      
      alert('保存成功！')
    } catch (error) {
      console.error('保存成本明细失败:', error)
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  if (loading && !quote) {
    return <div className="flex items-center justify-center h-64">加载中...</div>
  }
  
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="报价成本管理"
        description={quote ? `报价编号: ${quote.quote_no || id}` : ''}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(`/sales/quotes`)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
            <Button variant="outline" onClick={handleCheckCost}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              成本检查
            </Button>
            <Button variant="outline" onClick={handleCalculateCost}>
              <Calculator className="h-4 w-4 mr-2" />
              重新计算
            </Button>
            <Button variant="outline" onClick={handleAutoMatchCost}>
              <Search className="h-4 w-4 mr-2" />
              自动匹配成本
            </Button>
            <Button onClick={() => setShowTemplateDialog(true)}>
              <Layers className="h-4 w-4 mr-2" />
              应用模板
            </Button>
          </div>
        }
      />
      
      {/* Cost Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">总价</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totals.totalPrice)}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">总成本</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totals.totalCost)}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">毛利率</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn("text-2xl font-bold", marginStatus.textColor)}>
              {totals.grossMargin.toFixed(2)}%
            </div>
            <Badge className={cn("mt-2", marginStatus.color)}>
              {marginStatus.label}
            </Badge>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-400">利润</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">
              {formatCurrency(totals.totalPrice - totals.totalCost)}
            </div>
          </CardContent>
        </Card>
      </div>
      
      <Tabs defaultValue="breakdown" className="space-y-4">
        <TabsList>
          <TabsTrigger value="breakdown">成本明细</TabsTrigger>
          <TabsTrigger value="check">成本检查</TabsTrigger>
          <TabsTrigger value="approval">审批流程</TabsTrigger>
        </TabsList>
        
        {/* Cost Breakdown Tab */}
        <TabsContent value="breakdown" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>成本明细</CardTitle>
                  <CardDescription>编辑成本项，系统将自动计算总成本和毛利率</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handleSaveItems}>
                    <Save className="h-4 w-4 mr-2" />
                    保存
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {Object.entries(groupedItems).map(([category, categoryItems]) => (
                <div key={category} className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 text-slate-300">{category}</h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>项目名称</TableHead>
                        <TableHead>规格型号</TableHead>
                        <TableHead>单位</TableHead>
                        <TableHead>数量</TableHead>
                        <TableHead>单价</TableHead>
                        <TableHead>成本</TableHead>
                        <TableHead>小计</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {categoryItems.map((item) => {
                        const subtotal = (parseFloat(item.unit_price || 0) * parseFloat(item.qty || 0))
                        const costSubtotal = (parseFloat(item.cost || 0) * parseFloat(item.qty || 0))
                        return (
                          <TableRow key={item.id}>
                            <TableCell>{item.item_name}</TableCell>
                            <TableCell>{item.specification || '-'}</TableCell>
                            <TableCell>{item.unit || '-'}</TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                value={item.qty || ''}
                                onChange={(e) => handleItemChange(item.id, 'qty', e.target.value)}
                                className="w-20"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                value={item.unit_price || ''}
                                onChange={(e) => handleItemChange(item.id, 'unit_price', e.target.value)}
                                className="w-24"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                value={item.cost || ''}
                                onChange={(e) => handleItemChange(item.id, 'cost', e.target.value)}
                                className="w-24"
                              />
                            </TableCell>
                            <TableCell>
                              <div className="space-y-1">
                                <div className="text-sm">{formatCurrency(subtotal)}</div>
                                <div className="text-xs text-slate-500">成本: {formatCurrency(costSubtotal)}</div>
                              </div>
                            </TableCell>
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                </div>
              ))}
              
              {items.length === 0 && (
                <div className="text-center py-8 text-slate-400">
                  暂无成本明细，请应用成本模板或手动添加
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Cost Check Tab */}
        <TabsContent value="check" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>成本完整性检查</CardTitle>
              <CardDescription>检查成本拆解的完整性和毛利率是否符合要求</CardDescription>
            </CardHeader>
            <CardContent>
              {costCheck ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2">
                    <Badge className={costCheck.is_complete ? 'bg-green-500' : 'bg-amber-500'}>
                      {costCheck.is_complete ? '检查通过' : '存在问题'}
                    </Badge>
                    <span className="text-sm text-slate-400">
                      总价: {formatCurrency(costCheck.total_price)} | 
                      总成本: {formatCurrency(costCheck.total_cost)} | 
                      毛利率: {costCheck.gross_margin?.toFixed(2)}%
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    {costCheck.checks?.map((check, index) => (
                      <Alert key={index} className={
                        check.status === 'PASS' ? 'border-green-500' :
                        check.status === 'WARNING' ? 'border-amber-500' :
                        'border-red-500'
                      }>
                        <div className="flex items-center gap-2">
                          {check.status === 'PASS' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                          {check.status === 'WARNING' && <AlertTriangle className="h-4 w-4 text-amber-500" />}
                          {check.status === 'FAIL' && <XCircle className="h-4 w-4 text-red-500" />}
                          <AlertDescription>
                            <strong>{check.check_item}:</strong> {check.message}
                          </AlertDescription>
                        </div>
                      </Alert>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  点击"成本检查"按钮进行检查
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Approval Tab */}
        <TabsContent value="approval" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>成本审批流程</CardTitle>
                  <CardDescription>提交成本审批，确保毛利率符合要求</CardDescription>
                </div>
                <Button onClick={() => setShowApprovalDialog(true)}>
                  <Send className="h-4 w-4 mr-2" />
                  提交审批
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {approvalHistory.length > 0 ? (
                <div className="space-y-4">
                  {approvalHistory.map((approval) => (
                    <div key={approval.id} className="border border-slate-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge className={
                            approval.approval_status === 'APPROVED' ? 'bg-green-500' :
                            approval.approval_status === 'REJECTED' ? 'bg-red-500' :
                            'bg-amber-500'
                          }>
                            {approval.approval_status === 'APPROVED' ? '已通过' :
                             approval.approval_status === 'REJECTED' ? '已驳回' :
                             '待审批'}
                          </Badge>
                          <span className="text-sm text-slate-400">
                            审批层级: {approval.approval_level === 1 ? '销售经理' :
                                      approval.approval_level === 2 ? '销售总监' :
                                      '财务'}
                          </span>
                        </div>
                        <span className="text-sm text-slate-400">
                          {formatDate(approval.created_at)}
                        </span>
                      </div>
                      <div className="text-sm text-slate-300 space-y-1">
                        <div>毛利率: {approval.gross_margin?.toFixed(2)}%</div>
                        {approval.approval_comment && (
                          <div>审批意见: {approval.approval_comment}</div>
                        )}
                        {approval.rejected_reason && (
                          <div className="text-red-400">驳回原因: {approval.rejected_reason}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-400">
                  暂无审批记录
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      
      {/* Apply Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>应用成本模板</DialogTitle>
            <DialogDescription>选择成本模板应用到当前报价</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>选择模板</Label>
              <Select value={selectedTemplate?.id?.toString()} onValueChange={(value) => {
                const template = costTemplates.find(t => t.id.toString() === value)
                setSelectedTemplate(template)
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="选择成本模板" />
                </SelectTrigger>
                <SelectContent>
                  {costTemplates.map((template) => (
                    <SelectItem key={template.id} value={template.id.toString()}>
                      {template.template_name} ({template.template_code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {selectedTemplate && (
              <div className="border border-slate-700 rounded-lg p-4">
                <div className="text-sm space-y-1">
                  <div><strong>模板名称:</strong> {selectedTemplate.template_name}</div>
                  <div><strong>模板类型:</strong> {selectedTemplate.template_type}</div>
                  <div><strong>适用设备:</strong> {selectedTemplate.equipment_type || '-'}</div>
                  <div><strong>总成本:</strong> {formatCurrency(selectedTemplate.total_cost || 0)}</div>
                  {selectedTemplate.description && (
                    <div><strong>说明:</strong> {selectedTemplate.description}</div>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTemplateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleApplyTemplate} disabled={!selectedTemplate}>
              应用模板
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Submit Approval Dialog */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>提交成本审批</DialogTitle>
            <DialogDescription>提交报价成本进行审批</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>审批层级</Label>
              <Select 
                value={approvalData.approval_level.toString()} 
                onValueChange={(value) => setApprovalData({ ...approvalData, approval_level: parseInt(value) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">一级审批（销售经理）- 毛利率≥20%</SelectItem>
                  <SelectItem value="2">二级审批（销售总监）- 毛利率≥15%</SelectItem>
                  <SelectItem value="3">三级审批（财务）- 最终决策</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Label>审批意见</Label>
              <Textarea
                value={approvalData.comment}
                onChange={(e) => setApprovalData({ ...approvalData, comment: e.target.value })}
                placeholder="请输入审批意见..."
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApprovalDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSubmitApproval}>
              提交审批
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Cost Suggestions Dialog */}
      <Dialog open={showSuggestionsDialog} onOpenChange={setShowSuggestionsDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>成本匹配建议</DialogTitle>
            <DialogDescription>
              AI已生成成本匹配建议，请确认并修改后应用。系统已检查异常情况。
            </DialogDescription>
          </DialogHeader>
          
          {costSuggestions && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="bg-slate-800 rounded-lg p-4 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">匹配统计</span>
                  <div className="flex gap-4 text-sm">
                    <span>总项数: <strong>{costSuggestions.total_items}</strong></span>
                    <span className="text-green-400">匹配成功: <strong>{costSuggestions.matched_count}</strong></span>
                    <span className="text-amber-400">未匹配: <strong>{costSuggestions.unmatched_count}</strong></span>
                  </div>
                </div>
                {costSuggestions.summary && (
                  <div className="grid grid-cols-3 gap-4 text-sm mt-2">
                    <div>
                      <span className="text-slate-400">当前总成本:</span>
                      <div className="font-medium">{formatCurrency(costSuggestions.summary.current_total_cost || 0)}</div>
                    </div>
                    <div>
                      <span className="text-slate-400">建议总成本:</span>
                      <div className="font-medium text-blue-400">{formatCurrency(costSuggestions.summary.suggested_total_cost || 0)}</div>
                    </div>
                    <div>
                      <span className="text-slate-400">建议毛利率:</span>
                      <div className="font-medium text-green-400">
                        {costSuggestions.summary.suggested_margin !== null 
                          ? `${costSuggestions.summary.suggested_margin.toFixed(2)}%`
                          : '-'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Warnings */}
              {costSuggestions.warnings && costSuggestions.warnings.length > 0 && (
                <div className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-medium text-amber-400 mb-1">整体异常警告</div>
                      <ul className="text-sm text-slate-300 space-y-1">
                        {costSuggestions.warnings.map((warning, idx) => (
                          <li key={idx}>• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Suggestions List */}
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {costSuggestions.suggestions?.map((suggestion) => {
                  const edited = editedSuggestions[suggestion.item_id] || {}
                  const item = items.find(i => i.id === suggestion.item_id)
                  
                  return (
                    <div key={suggestion.item_id} className="border border-slate-700 rounded-lg p-4 space-y-3">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-medium">{suggestion.item_name}</div>
                          {suggestion.reason && (
                            <div className="text-xs text-slate-400 mt-1">
                              匹配原因: {suggestion.reason}
                              {suggestion.match_score && ` (匹配度: ${suggestion.match_score}%)`}
                            </div>
                          )}
                        </div>
                        {suggestion.matched_cost_record && (
                          <Badge className="bg-blue-500">
                            来源: {suggestion.matched_cost_record.supplier_name || '历史采购'}
                          </Badge>
                        )}
                      </div>
                      
                      {/* Warnings */}
                      {suggestion.warnings && suggestion.warnings.length > 0 && (
                        <div className="bg-amber-900/20 border border-amber-500/50 rounded p-2 text-sm">
                          {suggestion.warnings.map((warning, idx) => (
                            <div key={idx} className="text-amber-400">⚠ {warning}</div>
                          ))}
                        </div>
                      )}
                      
                      {/* Editable Fields */}
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs">当前成本</Label>
                          <div className="text-sm text-slate-400">
                            {suggestion.current_cost ? formatCurrency(suggestion.current_cost) : '未填写'}
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs">建议成本 *</Label>
                          <Input
                            type="number"
                            value={edited.cost || suggestion.suggested_cost || suggestion.current_cost || ''}
                            onChange={(e) => handleSuggestionChange(suggestion.item_id, 'cost', e.target.value)}
                            placeholder="0.00"
                            className="h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">规格型号</Label>
                          <Input
                            value={edited.specification || suggestion.suggested_specification || item?.specification || ''}
                            onChange={(e) => handleSuggestionChange(suggestion.item_id, 'specification', e.target.value)}
                            placeholder="规格型号"
                            className="h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">单位</Label>
                          <Input
                            value={edited.unit || suggestion.suggested_unit || item?.unit || ''}
                            onChange={(e) => handleSuggestionChange(suggestion.item_id, 'unit', e.target.value)}
                            placeholder="单位"
                            className="h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">交期(天)</Label>
                          <Input
                            type="number"
                            value={edited.lead_time_days || suggestion.suggested_lead_time_days || item?.lead_time_days || ''}
                            onChange={(e) => handleSuggestionChange(suggestion.item_id, 'lead_time_days', e.target.value)}
                            placeholder="交期"
                            className="h-8"
                          />
                        </div>
                        <div>
                          <Label className="text-xs">成本分类</Label>
                          <Input
                            value={edited.cost_category || suggestion.suggested_cost_category || item?.cost_category || ''}
                            onChange={(e) => handleSuggestionChange(suggestion.item_id, 'cost_category', e.target.value)}
                            placeholder="成本分类"
                            className="h-8"
                          />
                        </div>
                      </div>
                      
                      {/* Matched Cost Record Info */}
                      {suggestion.matched_cost_record && (
                        <div className="text-xs text-slate-500 bg-slate-800/50 rounded p-2">
                          匹配记录: {suggestion.matched_cost_record.material_name}
                          {suggestion.matched_cost_record.specification && ` (${suggestion.matched_cost_record.specification})`}
                          {suggestion.matched_cost_record.purchase_date && ` | 采购日期: ${formatDate(suggestion.matched_cost_record.purchase_date)}`}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowSuggestionsDialog(false)
              setCostSuggestions(null)
              setEditedSuggestions({})
            }}>
              取消
            </Button>
            <Button onClick={handleApplySuggestions} disabled={!costSuggestions || costSuggestions.suggestions?.length === 0}>
              确认应用
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
