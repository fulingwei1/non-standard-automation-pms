/**
 * CPQ Configurator - 配置化报价页面
 * Features: Product configuration, Real-time price preview, Price adjustment tracking, Approval prompts
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Calculator,
  Settings,
  AlertTriangle,
  CheckCircle2,
  Save,
  FileText,
  TrendingUp,
  TrendingDown,
  History,
  Info,
  Plus,
  Minus,
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
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertDescription,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesTemplateApi, quoteApi } from '../services/api'
import { toast } from 'sonner'

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

export default function CpqConfigurator() {
  const [ruleSets, setRuleSets] = useState([])
  const [templates, setTemplates] = useState([])
  const [selectedRuleSet, setSelectedRuleSet] = useState(null)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [configSchema, setConfigSchema] = useState({})
  const [selections, setSelections] = useState({})
  const [pricePreview, setPricePreview] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [manualDiscount, setManualDiscount] = useState('')
  const [manualMarkup, setManualMarkup] = useState('')
  const [quoteDraft, setQuoteDraft] = useState(null)

  // Load rule sets and templates
  useEffect(() => {
    loadRuleSetsAndTemplates()
  }, [])

  const loadRuleSetsAndTemplates = async () => {
    setLoading(true)
    try {
      const [ruleRes, templateRes] = await Promise.all([
        salesTemplateApi.listRuleSets({ page: 1, page_size: 100, status: 'ACTIVE' }),
        salesTemplateApi.listQuoteTemplates({ page: 1, page_size: 100, status: 'PUBLISHED' }),
      ])
      setRuleSets(ruleRes.data?.items || ruleRes.items || [])
      setTemplates(templateRes.data?.items || templateRes.items || [])
    } catch (err) {
      console.error('Failed to load rule sets and templates:', err)
      toast.error('加载配置数据失败')
    } finally {
      setLoading(false)
    }
  }

  // Load config schema when rule set or template is selected
  useEffect(() => {
    if (selectedRuleSet) {
      const ruleSet = ruleSets.find(r => r.id === selectedRuleSet)
      if (ruleSet?.config_schema) {
        setConfigSchema(ruleSet.config_schema)
      }
    } else if (selectedTemplate) {
      const template = templates.find(t => t.id === selectedTemplate)
      if (template?.current_version?.config_schema) {
        setConfigSchema(template.current_version.config_schema)
      }
    } else {
      setConfigSchema({})
      setSelections({})
    }
  }, [selectedRuleSet, selectedTemplate, ruleSets, templates])

  // Preview price when selections change
  useEffect(() => {
    if (selectedRuleSet || selectedTemplate) {
      const timer = setTimeout(() => {
        previewPrice()
      }, 500) // Debounce 500ms
      return () => clearTimeout(timer)
    }
  }, [selections, manualDiscount, manualMarkup, selectedRuleSet, selectedTemplate])

  const previewPrice = async () => {
    if (!selectedRuleSet && !selectedTemplate) return

    setPreviewLoading(true)
    try {
      const requestData = {
        rule_set_id: selectedRuleSet || null,
        template_version_id: selectedTemplate ? templates.find(t => t.id === selectedTemplate)?.current_version_id : null,
        selections: selections,
        manual_discount_pct: manualDiscount ? parseFloat(manualDiscount) : null,
        manual_markup_pct: manualMarkup ? parseFloat(manualMarkup) : null,
      }

      const res = await salesTemplateApi.previewPrice(requestData)
      const preview = res.data || res

      setPricePreview(preview)

      // Add to price history
      setPriceHistory(prev => [{
        timestamp: new Date().toISOString(),
        selections: { ...selections },
        base_price: preview.base_price,
        final_price: preview.final_price,
        adjustments: preview.adjustments || [],
      }, ...prev.slice(0, 9)]) // Keep last 10 entries
    } catch (err) {
      console.error('Failed to preview price:', err)
      toast.error('价格预览失败')
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleSelectionChange = (key, value) => {
    setSelections(prev => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleSaveDraft = async () => {
    if (!pricePreview) {
      toast.error('请先配置并预览价格')
      return
    }

    try {
      // Create a quote draft
      const quoteData = {
        opportunity_id: null, // Can be linked later
        quote_code: `DRAFT-${Date.now()}`,
        customer_id: null,
        total_price: pricePreview.final_price,
        currency: pricePreview.currency || 'CNY',
        status: 'DRAFT',
        cpq_config: {
          rule_set_id: selectedRuleSet,
          template_version_id: selectedTemplate ? templates.find(t => t.id === selectedTemplate)?.current_version_id : null,
          selections: selections,
          manual_discount_pct: manualDiscount ? parseFloat(manualDiscount) : null,
          manual_markup_pct: manualMarkup ? parseFloat(manualMarkup) : null,
        },
      }

      const res = await quoteApi.create(quoteData)
      setQuoteDraft(res.data || res)
      toast.success('已保存为报价草稿')
    } catch (err) {
      console.error('Failed to save draft:', err)
      toast.error(err.response?.data?.message || '保存草稿失败')
    }
  }

  const renderConfigField = (key, fieldConfig) => {
    const fieldType = fieldConfig.type || 'text'
    const fieldValue = selections[key] || fieldConfig.default || ''

    switch (fieldType) {
      case 'select':
        return (
          <Select
            value={fieldValue}
            onValueChange={(value) => handleSelectionChange(key, value)}
          >
            <SelectTrigger>
              <SelectValue placeholder={fieldConfig.placeholder || `选择${fieldConfig.label}`} />
            </SelectTrigger>
            <SelectContent>
              {fieldConfig.options?.map(opt => (
                <SelectItem key={typeof opt === 'string' ? opt : opt.value} value={typeof opt === 'string' ? opt : opt.value}>
                  {typeof opt === 'string' ? opt : opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )
      case 'number':
        return (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSelectionChange(key, Math.max(0, (parseFloat(fieldValue) || 0) - 1))}
            >
              <Minus className="w-4 h-4" />
            </Button>
            <Input
              type="number"
              value={fieldValue}
              onChange={(e) => handleSelectionChange(key, parseFloat(e.target.value) || 0)}
              className="flex-1"
              min={0}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSelectionChange(key, (parseFloat(fieldValue) || 0) + 1)}
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        )
      case 'boolean':
        return (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={fieldValue === true || fieldValue === 'true'}
              onChange={(e) => handleSelectionChange(key, e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-800"
            />
            <span className="text-sm text-slate-400">{fieldConfig.label}</span>
          </div>
        )
      default:
        return (
          <Input
            value={fieldValue}
            onChange={(e) => handleSelectionChange(key, e.target.value)}
            placeholder={fieldConfig.placeholder || `输入${fieldConfig.label}`}
          />
        )
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
        title="CPQ 配置化报价"
        description="通过产品配置快速生成报价，实时预览价格和审批要求"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
              disabled={!pricePreview}
              className="flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              保存草稿
            </Button>
          </motion.div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Configuration Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Rule Set / Template Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-400" />
                选择配置规则
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>CPQ 规则集</Label>
                  <Select
                    value={selectedRuleSet?.toString() || ''}
                    onValueChange={(value) => {
                      setSelectedRuleSet(value ? parseInt(value) : null)
                      setSelectedTemplate(null)
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择规则集" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">不使用规则集</SelectItem>
                      {ruleSets.map(ruleSet => (
                        <SelectItem key={ruleSet.id} value={ruleSet.id.toString()}>
                          {ruleSet.rule_name} ({ruleSet.rule_code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>报价模板</Label>
                  <Select
                    value={selectedTemplate?.toString() || ''}
                    onValueChange={(value) => {
                      setSelectedTemplate(value ? parseInt(value) : null)
                      setSelectedRuleSet(null)
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择模板" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">不使用模板</SelectItem>
                      {templates.map(template => (
                        <SelectItem key={template.id} value={template.id.toString()}>
                          {template.template_name} ({template.template_code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Configuration Fields */}
          {Object.keys(configSchema).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-blue-400" />
                  产品配置
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(configSchema).map(([key, fieldConfig]) => {
                  const config = typeof fieldConfig === 'object' ? fieldConfig : { label: key, type: 'text' }
                  return (
                    <div key={key}>
                      <Label className="mb-2 block">
                        {config.label || key}
                        {config.required && <span className="text-red-400 ml-1">*</span>}
                      </Label>
                      {renderConfigField(key, config)}
                      {config.description && (
                        <p className="text-xs text-slate-400 mt-1">{config.description}</p>
                      )}
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )}

          {/* Manual Adjustments */}
          {pricePreview && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-blue-400" />
                  手动调整
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>手动折扣 (%)</Label>
                  <Input
                    type="number"
                    value={manualDiscount}
                    onChange={(e) => setManualDiscount(e.target.value)}
                    placeholder="输入折扣百分比"
                    min={0}
                    max={100}
                  />
                </div>
                <div>
                  <Label>附加费用 (%)</Label>
                  <Input
                    type="number"
                    value={manualMarkup}
                    onChange={(e) => setManualMarkup(e.target.value)}
                    placeholder="输入附加费用百分比"
                    min={0}
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Price Preview Panel */}
        <div className="space-y-6">
          {/* Price Preview */}
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5 text-emerald-400" />
                价格预览
                {previewLoading && (
                  <Badge variant="outline" className="ml-auto">计算中...</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!pricePreview ? (
                <div className="text-center py-8 text-slate-400">
                  <Info className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>请选择规则集或模板并配置产品</p>
                </div>
              ) : (
                <>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">基础价格</span>
                      <span className="text-white font-medium">
                        {formatCurrency(pricePreview.base_price || 0)}
                      </span>
                    </div>
                    {pricePreview.adjustments && pricePreview.adjustments.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-slate-700">
                        <div className="text-sm text-slate-400 mb-2">价格调整明细</div>
                        {pricePreview.adjustments.map((adj, idx) => (
                          <div key={idx} className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{adj.label || adj.reason}</span>
                            <span className={cn(
                              'font-medium',
                              (adj.value || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                            )}>
                              {(adj.value || 0) >= 0 ? '+' : ''}{formatCurrency(adj.value || 0)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-700">
                      <span className="text-lg font-semibold text-white">最终价格</span>
                      <span className="text-2xl font-bold text-emerald-400">
                        {formatCurrency(pricePreview.final_price || 0)}
                      </span>
                    </div>
                  </div>

                  {/* Approval Alert */}
                  {pricePreview.requires_approval && (
                    <Alert className="bg-amber-500/10 border-amber-500/20">
                      <AlertTriangle className="h-4 w-4 text-amber-400" />
                      <AlertDescription className="text-amber-400">
                        <div className="font-medium mb-1">需要审批</div>
                        <div className="text-sm">{pricePreview.approval_reason || '此报价需要上级审批'}</div>
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Confidence Level */}
                  {pricePreview.confidence_level && (
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-slate-400">配置完整度:</span>
                      <Badge
                        variant="outline"
                        className={cn(
                          pricePreview.confidence_level === 'HIGH' && 'bg-emerald-500/20 text-emerald-400',
                          pricePreview.confidence_level === 'MEDIUM' && 'bg-amber-500/20 text-amber-400',
                          pricePreview.confidence_level === 'LOW' && 'bg-red-500/20 text-red-400',
                        )}
                      >
                        {pricePreview.confidence_level === 'HIGH' && '高'}
                        {pricePreview.confidence_level === 'MEDIUM' && '中'}
                        {pricePreview.confidence_level === 'LOW' && '低'}
                      </Badge>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* Price History */}
          {priceHistory.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-400" />
                  价格调整轨迹
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {priceHistory.map((entry, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-slate-400">
                          {new Date(entry.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-sm font-medium text-white">
                          {formatCurrency(entry.final_price)}
                        </span>
                      </div>
                      {entry.adjustments && entry.adjustments.length > 0 && (
                        <div className="text-xs text-slate-500 space-y-1">
                          {entry.adjustments.slice(0, 3).map((adj, adjIdx) => (
                            <div key={adjIdx} className="flex items-center justify-between">
                              <span>{adj.label || adj.reason}</span>
                              <span className={cn(
                                (adj.value || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'
                              )}>
                                {(adj.value || 0) >= 0 ? '+' : ''}{formatCurrency(adj.value || 0)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </motion.div>
  )
}
