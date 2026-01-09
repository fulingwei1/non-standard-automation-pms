import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  Settings,
  Plus,
  Edit,
  Trash2,
  Power,
  PowerOff,
  AlertTriangle,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
  DialogDescription,
} from '../components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { Checkbox } from '../components/ui/checkbox'
import { fadeIn, staggerContainer } from '../lib/animations'
import { alertApi } from '../services/api'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'

// 规则类型选项
const ruleTypeOptions = [
  { value: 'SCHEDULE_DELAY', label: '进度延期' },
  { value: 'COST_OVERRUN', label: '成本超支' },
  { value: 'MILESTONE_DUE', label: '里程碑到期' },
  { value: 'DELIVERY_DUE', label: '交期预警' },
  { value: 'MATERIAL_SHORTAGE', label: '物料短缺' },
  { value: 'QUALITY_ISSUE', label: '质量问题' },
  { value: 'PAYMENT_DUE', label: '付款到期' },
  { value: 'SPECIFICATION_MISMATCH', label: '规格不匹配' },
  { value: 'CUSTOM', label: '自定义' },
]

// 监控对象类型选项
const targetTypeOptions = [
  { value: 'PROJECT', label: '项目' },
  { value: 'MACHINE', label: '设备' },
  { value: 'TASK', label: '任务' },
  { value: 'PURCHASE_ORDER', label: '采购订单' },
  { value: 'OUTSOURCING_ORDER', label: '外协订单' },
  { value: 'MATERIAL', label: '物料' },
  { value: 'MILESTONE', label: '里程碑' },
  { value: 'ACCEPTANCE', label: '验收' },
]

// 条件类型选项
const conditionTypeOptions = [
  { value: 'THRESHOLD', label: '阈值' },
  { value: 'DEVIATION', label: '偏差' },
  { value: 'OVERDUE', label: '逾期' },
  { value: 'CUSTOM', label: '自定义表达式' },
]

// 条件运算符选项
const operatorOptions = [
  { value: 'GT', label: '大于 (>)' },
  { value: 'GTE', label: '大于等于 (>=)' },
  { value: 'LT', label: '小于 (<)' },
  { value: 'LTE', label: '小于等于 (<=)' },
  { value: 'EQ', label: '等于 (=)' },
  { value: 'BETWEEN', label: '区间' },
]

// 预警级别选项
const alertLevelOptions = [
  { value: 'INFO', label: '提示', color: 'blue' },
  { value: 'WARNING', label: '注意', color: 'amber' },
  { value: 'CRITICAL', label: '严重', color: 'orange' },
  { value: 'URGENT', label: '紧急', color: 'red' },
]

// 检查频率选项
const frequencyOptions = [
  { value: 'REALTIME', label: '实时' },
  { value: 'HOURLY', label: '每小时' },
  { value: 'DAILY', label: '每天' },
  { value: 'WEEKLY', label: '每周' },
]

// 通知渠道选项
const channelOptions = [
  { value: 'SYSTEM', label: '站内消息' },
  { value: 'EMAIL', label: '邮件' },
  { value: 'WECHAT', label: '企业微信' },
  { value: 'SMS', label: '短信' },
]

export default function AlertRuleConfig() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState('ALL')
  const [selectedTarget, setSelectedTarget] = useState('ALL')
  const [showEnabled, setShowEnabled] = useState(null) // null=全部, true=启用, false=禁用
  const [showDialog, setShowDialog] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [templates, setTemplates] = useState([])
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  // 表单状态
  const [formData, setFormData] = useState({
    rule_code: '',
    rule_name: '',
    rule_type: '',
    target_type: '',
    target_field: '',
    condition_type: 'THRESHOLD',
    condition_operator: 'GT',
    threshold_value: '',
    threshold_min: '',
    threshold_max: '',
    condition_expr: '',
    alert_level: 'WARNING',
    advance_days: 0,
    notify_channels: ['SYSTEM'],
    notify_roles: [],
    notify_users: [],
    check_frequency: 'DAILY',
    is_enabled: true,
    description: '',
    solution_guide: '',
  })

  const loadRules = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page,
        page_size: pageSize,
      }
      if (searchQuery) {
        params.keyword = searchQuery
      }
      if (selectedType !== 'ALL') {
        params.rule_type = selectedType
      }
      if (selectedTarget !== 'ALL') {
        params.target_type = selectedTarget
      }
      if (showEnabled !== null) {
        params.is_enabled = showEnabled
      }
      const response = await alertApi.rules.list(params)
      const data = response.data?.data || response.data || response
      if (data && typeof data === 'object' && 'items' in data) {
        setRules(data.items || [])
        setTotal(data.total || 0)
      } else if (Array.isArray(data)) {
        setRules(data)
        setTotal(data.length)
      } else {
        setRules([])
        setTotal(0)
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载规则列表失败')
      setRules([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, searchQuery, selectedType, selectedTarget, showEnabled])

  const loadTemplates = useCallback(async () => {
    try {
      const response = await alertApi.templates()
      const data = response.data || response
      setTemplates(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('操作失败:', err)
    }
  }, [])

  useEffect(() => {
    loadRules()
  }, [loadRules])

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

  const handleCreate = () => {
    setEditingRule(null)
    setFormData({
      rule_code: '',
      rule_name: '',
      rule_type: '',
      target_type: '',
      target_field: '',
      condition_type: 'THRESHOLD',
      condition_operator: 'GT',
      threshold_value: '',
      threshold_min: '',
      threshold_max: '',
      condition_expr: '',
      alert_level: 'WARNING',
      advance_days: 0,
      notify_channels: ['SYSTEM'],
      notify_roles: [],
      notify_users: [],
      check_frequency: 'DAILY',
      is_enabled: true,
      description: '',
      solution_guide: '',
    })
    setSelectedTemplate(null)
    setShowDialog(true)
  }

  const handleEdit = (rule) => {
    setEditingRule(rule)
    setFormData({
      rule_code: rule.rule_code,
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      target_type: rule.target_type,
      target_field: rule.target_field || '',
      condition_type: rule.condition_type,
      condition_operator: rule.condition_operator || 'GT',
      threshold_value: rule.threshold_value || '',
      threshold_min: rule.threshold_min || '',
      threshold_max: rule.threshold_max || '',
      condition_expr: rule.condition_expr || '',
      alert_level: rule.alert_level,
      advance_days: rule.advance_days || 0,
      notify_channels: rule.notify_channels || ['SYSTEM'],
      notify_roles: rule.notify_roles || [],
      notify_users: rule.notify_users || [],
      check_frequency: rule.check_frequency || 'DAILY',
      is_enabled: rule.is_enabled !== false,
      description: rule.description || '',
      solution_guide: rule.solution_guide || '',
    })
    setShowDialog(true)
  }

  const handleDelete = async (rule) => {
    if (!confirm(`确定要删除规则 "${rule.rule_name}" 吗？`)) {
      return
    }
    try {
      await alertApi.rules.delete(rule.id)
      toast.success('规则已删除')
      loadRules()
    } catch (err) {
      toast.error(err.response?.data?.detail || '删除失败')
    }
  }

  const handleToggle = async (rule) => {
    try {
      await alertApi.rules.toggle(rule.id)
      toast.success(rule.is_enabled ? '规则已禁用' : '规则已启用')
      loadRules()
    } catch (err) {
      toast.error(err.response?.data?.detail || '操作失败')
    }
  }

  const handleSave = async () => {
    try {
      // 表单验证
      if (!formData.rule_code.trim()) {
        toast.error('请输入规则编码')
        return
      }
      if (!formData.rule_name.trim()) {
        toast.error('请输入规则名称')
        return
      }
      if (!formData.rule_type) {
        toast.error('请选择规则类型')
        return
      }
      if (!formData.target_type) {
        toast.error('请选择监控对象类型')
        return
      }
      if (formData.condition_type === 'THRESHOLD' && !formData.threshold_value && formData.condition_operator !== 'BETWEEN') {
        toast.error('请输入阈值')
        return
      }
      if (formData.condition_operator === 'BETWEEN' && (!formData.threshold_min || !formData.threshold_max)) {
        toast.error('请输入阈值范围')
        return
      }

      if (editingRule) {
        // 更新
        await alertApi.rules.update(editingRule.id, formData)
        toast.success('规则已更新')
      } else {
        // 创建
        await alertApi.rules.create(formData)
        toast.success('规则已创建')
      }
      setShowDialog(false)
      loadRules()
    } catch (err) {
      toast.error(err.response?.data?.detail || '保存失败')
    }
  }

  const handleTemplateSelect = (templateId) => {
    const template = templates.find(t => t.id === templateId)
    if (template && template.rule_config) {
      setSelectedTemplate(template)
      // 从模板填充表单
      const config = template.rule_config
      setFormData(prev => ({
        ...prev,
        rule_type: config.rule_type || prev.rule_type,
        target_type: config.target_type || prev.target_type,
        condition_type: config.condition_type || prev.condition_type,
        alert_level: config.alert_level || prev.alert_level,
        check_frequency: config.check_frequency || prev.check_frequency,
        notify_channels: config.notify_channels || prev.notify_channels,
        description: template.description || prev.description,
      }))
    }
  }

  const handleChannelToggle = (channel) => {
    setFormData(prev => {
      const channels = prev.notify_channels || []
      if (channels.includes(channel)) {
        return { ...prev, notify_channels: channels.filter(c => c !== channel) }
      } else {
        return { ...prev, notify_channels: [...channels, channel] }
      }
    })
  }

  const formatFrequency = (freq) => {
    const option = frequencyOptions.find(o => o.value === freq)
    return option?.label || freq
  }

  const formatLevel = (level) => {
    const option = alertLevelOptions.find(o => o.value === level)
    return option?.label || level
  }

  const getLevelColor = (level) => {
    const option = alertLevelOptions.find(o => o.value === level)
    return option?.color || 'slate'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="预警规则配置"
        description="管理预警规则，配置触发条件和通知方式"
        actions={
          <Button onClick={handleCreate} className="gap-2">
            <Plus className="w-4 h-4" />
            新建规则
          </Button>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 筛选栏 */}
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="搜索规则编码或名称..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-surface-2"
                />
              </div>
              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-[150px] bg-surface-2">
                  <SelectValue placeholder="规则类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">全部类型</SelectItem>
                  {ruleTypeOptions.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedTarget} onValueChange={setSelectedTarget}>
                <SelectTrigger className="w-[150px] bg-surface-2">
                  <SelectValue placeholder="监控对象" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">全部对象</SelectItem>
                  {targetTypeOptions.map(opt => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select 
                value={showEnabled === null ? 'ALL' : showEnabled ? 'ENABLED' : 'DISABLED'}
                onValueChange={(val) => {
                  if (val === 'ALL') setShowEnabled(null)
                  else setShowEnabled(val === 'ENABLED')
                }}
              >
                <SelectTrigger className="w-[120px] bg-surface-2">
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">全部状态</SelectItem>
                  <SelectItem value="ENABLED">已启用</SelectItem>
                  <SelectItem value="DISABLED">已禁用</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={loadRules}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                刷新
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 规则列表 */}
        {loading ? (
          <LoadingCard />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : rules.length === 0 ? (
          <EmptyState
            icon={Settings}
            title="暂无预警规则"
            description="点击「新建规则」按钮创建第一个预警规则"
          />
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-4"
          >
            {rules.map((rule) => (
              <motion.div key={rule.id} variants={fadeIn}>
                <Card className="bg-surface-1/50 hover:bg-surface-1 transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-white">
                            {rule.rule_name}
                          </h3>
                          {rule.is_system && (
                            <Badge variant="outline" className="text-xs">
                              系统预置
                            </Badge>
                          )}
                          <Badge
                            variant={rule.is_enabled ? 'default' : 'secondary'}
                            className={cn(
                              rule.is_enabled
                                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                            )}
                          >
                            {rule.is_enabled ? (
                              <>
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                已启用
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3 h-3 mr-1" />
                                已禁用
                              </>
                            )}
                          </Badge>
                          <Badge
                            className={`bg-${getLevelColor(rule.alert_level)}-500/20 text-${getLevelColor(rule.alert_level)}-400 border-${getLevelColor(rule.alert_level)}-500/30`}
                          >
                            {formatLevel(rule.alert_level)}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-400 mb-3">
                          <div>
                            <span className="text-slate-500">规则编码:</span>{' '}
                            <span className="text-white">{rule.rule_code}</span>
                          </div>
                          <div>
                            <span className="text-slate-500">规则类型:</span>{' '}
                            <span className="text-white">
                              {ruleTypeOptions.find(o => o.value === rule.rule_type)?.label || rule.rule_type}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">监控对象:</span>{' '}
                            <span className="text-white">
                              {targetTypeOptions.find(o => o.value === rule.target_type)?.label || rule.target_type}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500">检查频率:</span>{' '}
                            <span className="text-white">{formatFrequency(rule.check_frequency)}</span>
                          </div>
                        </div>
                        {rule.description && (
                          <p className="text-sm text-slate-400 mb-2">{rule.description}</p>
                        )}
                        {rule.threshold_value && (
                          <div className="text-sm text-slate-400">
                            <span className="text-slate-500">阈值:</span>{' '}
                            <span className="text-white">{rule.threshold_value}</span>
                            {rule.condition_operator && (
                              <>
                                {' '}
                                <span className="text-slate-500">运算符:</span>{' '}
                                <span className="text-white">
                                  {operatorOptions.find(o => o.value === rule.condition_operator)?.label || rule.condition_operator}
                                </span>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggle(rule)}
                          className="gap-2"
                          title={rule.is_enabled ? '禁用规则' : '启用规则'}
                        >
                          {rule.is_enabled ? (
                            <PowerOff className="w-4 h-4" />
                          ) : (
                            <Power className="w-4 h-4" />
                          )}
                        </Button>
                        {!rule.is_system && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(rule)}
                              className="gap-2"
                            >
                              <Edit className="w-4 h-4" />
                              编辑
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDelete(rule)}
                              className="gap-2 text-red-400 hover:text-red-300"
                            >
                              <Trash2 className="w-4 h-4" />
                              删除
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}

        {/* 分页 */}
        {total > pageSize && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              上一页
            </Button>
            <span className="text-sm text-slate-400">
              第 {page} 页，共 {Math.ceil(total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(Math.ceil(total / pageSize), p + 1))}
              disabled={page >= Math.ceil(total / pageSize)}
            >
              下一页
            </Button>
          </div>
        )}
      </div>

      {/* 创建/编辑对话框 */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingRule ? '编辑预警规则' : '新建预警规则'}
            </DialogTitle>
            <DialogDescription>
              {editingRule
                ? '修改预警规则的配置信息'
                : '创建新的预警规则，配置触发条件和通知方式'}
            </DialogDescription>
          </DialogHeader>
          <DialogBody className="space-y-6">
            {/* 从模板创建 */}
            {!editingRule && templates.length > 0 && (
              <div className="space-y-2">
                <Label>从模板创建（可选）</Label>
                <Select value={selectedTemplate?.id?.toString() || ''} onValueChange={(val) => handleTemplateSelect(parseInt(val))}>
                  <SelectTrigger className="bg-surface-2">
                    <SelectValue placeholder="选择模板..." />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map(template => (
                      <SelectItem key={template.id} value={template.id.toString()}>
                        {template.template_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* 基本信息 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">基本信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="rule_code">
                    规则编码 <span className="text-red-400">*</span>
                  </Label>
                  <Input
                    id="rule_code"
                    value={formData.rule_code}
                    onChange={(e) => setFormData(prev => ({ ...prev, rule_code: e.target.value.toUpperCase() }))}
                    placeholder="例如: PROJ_DELAY"
                    disabled={!!editingRule}
                    className="bg-surface-2"
                  />
                  <p className="text-xs text-slate-500">只能包含字母、数字和下划线</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule_name">
                    规则名称 <span className="text-red-400">*</span>
                  </Label>
                  <Input
                    id="rule_name"
                    value={formData.rule_name}
                    onChange={(e) => setFormData(prev => ({ ...prev, rule_name: e.target.value }))}
                    placeholder="例如: 项目进度延期预警"
                    className="bg-surface-2"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rule_type">
                    规则类型 <span className="text-red-400">*</span>
                  </Label>
                  <Select
                    value={formData.rule_type}
                    onValueChange={(val) => setFormData(prev => ({ ...prev, rule_type: val }))}
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue placeholder="选择规则类型" />
                    </SelectTrigger>
                    <SelectContent>
                      {ruleTypeOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="target_type">
                    监控对象类型 <span className="text-red-400">*</span>
                  </Label>
                  <Select
                    value={formData.target_type}
                    onValueChange={(val) => setFormData(prev => ({ ...prev, target_type: val }))}
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue placeholder="选择监控对象" />
                    </SelectTrigger>
                    <SelectContent>
                      {targetTypeOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 col-span-2">
                  <Label htmlFor="description">规则描述</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="描述规则的用途和触发条件"
                    className="bg-surface-2"
                    rows={2}
                  />
                </div>
              </div>
            </div>

            {/* 触发条件配置 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">触发条件配置</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="condition_type">条件类型</Label>
                  <Select
                    value={formData.condition_type}
                    onValueChange={(val) => setFormData(prev => ({ ...prev, condition_type: val }))}
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {conditionTypeOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {formData.condition_type === 'THRESHOLD' && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="condition_operator">条件运算符</Label>
                      <Select
                        value={formData.condition_operator}
                        onValueChange={(val) => setFormData(prev => ({ ...prev, condition_operator: val }))}
                      >
                        <SelectTrigger className="bg-surface-2">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {operatorOptions.map(opt => (
                            <SelectItem key={opt.value} value={opt.value}>
                              {opt.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    {formData.condition_operator === 'BETWEEN' ? (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="threshold_min">阈值下限</Label>
                          <Input
                            id="threshold_min"
                            type="number"
                            value={formData.threshold_min}
                            onChange={(e) => setFormData(prev => ({ ...prev, threshold_min: e.target.value }))}
                            placeholder="最小值"
                            className="bg-surface-2"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="threshold_max">阈值上限</Label>
                          <Input
                            id="threshold_max"
                            type="number"
                            value={formData.threshold_max}
                            onChange={(e) => setFormData(prev => ({ ...prev, threshold_max: e.target.value }))}
                            placeholder="最大值"
                            className="bg-surface-2"
                          />
                        </div>
                      </>
                    ) : (
                      <div className="space-y-2">
                        <Label htmlFor="threshold_value">阈值</Label>
                        <Input
                          id="threshold_value"
                          type="number"
                          value={formData.threshold_value}
                          onChange={(e) => setFormData(prev => ({ ...prev, threshold_value: e.target.value }))}
                          placeholder="例如: 3 (天) 或 0.1 (比例)"
                          className="bg-surface-2"
                        />
                      </div>
                    )}
                  </>
                )}
                {formData.condition_type === 'CUSTOM' && (
                  <div className="space-y-2 col-span-2">
                    <Label htmlFor="condition_expr">自定义表达式</Label>
                    <Textarea
                      id="condition_expr"
                      value={formData.condition_expr}
                      onChange={(e) => setFormData(prev => ({ ...prev, condition_expr: e.target.value }))}
                      placeholder="例如: progress < 80 AND days_left < 7"
                      className="bg-surface-2"
                      rows={3}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* 预警级别和检查频率 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">预警级别和检查频率</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="alert_level">预警级别</Label>
                  <Select
                    value={formData.alert_level}
                    onValueChange={(val) => setFormData(prev => ({ ...prev, alert_level: val }))}
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {alertLevelOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="check_frequency">检查频率</Label>
                  <Select
                    value={formData.check_frequency}
                    onValueChange={(val) => setFormData(prev => ({ ...prev, check_frequency: val }))}
                  >
                    <SelectTrigger className="bg-surface-2">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {frequencyOptions.map(opt => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="advance_days">提前预警天数</Label>
                  <Input
                    id="advance_days"
                    type="number"
                    min="0"
                    value={formData.advance_days}
                    onChange={(e) => setFormData(prev => ({ ...prev, advance_days: parseInt(e.target.value) || 0 }))}
                    placeholder="0"
                    className="bg-surface-2"
                  />
                </div>
              </div>
            </div>

            {/* 通知配置 */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-white">通知配置</h3>
              <div className="space-y-3">
                <div>
                  <Label>通知渠道</Label>
                  <div className="flex flex-wrap gap-3 mt-2">
                    {channelOptions.map(channel => (
                      <div key={channel.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`channel-${channel.value}`}
                          checked={formData.notify_channels?.includes(channel.value)}
                          onCheckedChange={() => handleChannelToggle(channel.value)}
                        />
                        <Label
                          htmlFor={`channel-${channel.value}`}
                          className="text-sm font-normal cursor-pointer"
                        >
                          {channel.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 处理指南 */}
            <div className="space-y-2">
              <Label htmlFor="solution_guide">处理指南</Label>
              <Textarea
                id="solution_guide"
                value={formData.solution_guide}
                onChange={(e) => setFormData(prev => ({ ...prev, solution_guide: e.target.value }))}
                placeholder="提供预警触发后的处理建议和步骤"
                className="bg-surface-2"
                rows={3}
              />
            </div>

            {/* 启用状态 */}
            {editingRule && (
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_enabled"
                  checked={formData.is_enabled}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_enabled: checked }))}
                />
                <Label htmlFor="is_enabled" className="cursor-pointer">
                  启用此规则
                </Label>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSave}>
              {editingRule ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
