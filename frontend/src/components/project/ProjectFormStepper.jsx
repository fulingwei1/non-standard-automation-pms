/**
 * 项目创建/编辑表单 - 分步骤表单组件
 * 
 * Issue 3.1: 使用 shadcn/ui 组件重构，分步骤表单
 * Issue 3.2: 智能提示和自动填充功能
 */

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Card,
  CardContent,
  Button,
  Input,
  FormField,
  FormTextarea,
  FormSelect,
  Badge,
} from '../ui'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../ui'
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Info,
  Sparkles,
  Building2,
  DollarSign,
  Calendar,
  User,
  FileText,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { projectApi, customerApi, orgApi } from '../../services/api'
import { toast } from '../ui/toast'

// 步骤配置
const STEPS = [
  {
    id: 'basic',
    name: '基本信息',
    icon: FileText,
    description: '项目编码、名称、类型等',
  },
  {
    id: 'customer',
    name: '客户信息',
    icon: Building2,
    description: '客户、联系人、联系方式',
  },
  {
    id: 'finance',
    name: '财务信息',
    icon: DollarSign,
    description: '合同金额、预算、收款计划',
  },
  {
    id: 'schedule',
    name: '时间节点',
    icon: Calendar,
    description: '计划开始、结束日期',
  },
]

// 项目类型选项
const PROJECT_TYPES = [
  { value: 'FIXED_PRICE', label: '固定价格' },
  { value: 'TIME_MATERIAL', label: '工时材料' },
  { value: 'COST_PLUS', label: '成本加成' },
]

export default function ProjectFormStepper({
  open,
  onOpenChange,
  onSubmit,
  initialData = {},
  recommendedTemplates = [],
}) {
  const [currentStep, setCurrentStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [savingDraft, setSavingDraft] = useState(false)
  const [validatingCode, setValidatingCode] = useState(false)
  const [codeError, setCodeError] = useState('')
  
  // 表单数据
  const [formData, setFormData] = useState({
    project_code: '',
    project_name: '',
    short_name: '',
    project_type: 'FIXED_PRICE',
    product_category: '',
    industry: '',
    customer_id: '',
    customer_name: '',
    customer_contact: '',
    customer_phone: '',
    contract_no: '',
    contract_date: '',
    contract_amount: 0,
    budget_amount: 0,
    pm_id: '',
    pm_name: '',
    planned_start_date: '',
    planned_end_date: '',
    description: '',
    requirements: '',
    template_id: null,
    ...initialData,
  })
  
  // 选项数据
  const [customers, setCustomers] = useState([])
  const [employees, setEmployees] = useState([])
  const [filteredCustomers, setFilteredCustomers] = useState([])
  const [customerSearch, setCustomerSearch] = useState('')
  const [selectedCustomer, setSelectedCustomer] = useState(null)
  const [pmStats, setPmStats] = useState({}) // Sprint 3.2: 项目经理统计信息
  
  // 加载选项数据
  useEffect(() => {
    if (open) {
      const loadOptions = async () => {
        try {
          const [custRes, empRes, statsRes] = await Promise.all([
            customerApi.list(),
            orgApi.employees(),
            projectApi.getStats?.() || Promise.resolve({ data: { by_pm: [] } }), // Sprint 3.2: 加载项目经理统计
          ])
          setCustomers(custRes.data || [])
          setEmployees(empRes.data || [])
          setFilteredCustomers(custRes.data || [])
          
          // Sprint 3.2: 构建项目经理统计映射
          if (statsRes.data?.by_pm) {
            const statsMap = {}
            statsRes.data.by_pm.forEach((pm) => {
              statsMap[pm.pm_id] = pm.count
            })
            setPmStats(statsMap)
          }
        } catch (err) {
          toast.error('无法加载客户和员工数据')
        }
      }
      loadOptions()
    }
  }, [open, toast])
  
  // 客户搜索
  useEffect(() => {
    if (customerSearch) {
      const filtered = customers.filter(
        (c) =>
          c.customer_name?.toLowerCase().includes(customerSearch.toLowerCase()) ||
          c.customer_code?.toLowerCase().includes(customerSearch.toLowerCase())
      )
      setFilteredCustomers(filtered)
    } else {
      setFilteredCustomers(customers)
    }
  }, [customerSearch, customers])
  
  // 选择客户时自动填充信息
  const handleCustomerSelect = (customerId) => {
    const customer = customers.find((c) => c.id === customerId)
    if (customer) {
      setSelectedCustomer(customer)
      setFormData((prev) => ({
        ...prev,
        customer_id: customer.id,
        customer_name: customer.customer_name,
        customer_contact: customer.contact_person || '',
        customer_phone: customer.contact_phone || '',
      }))
      setCustomerSearch('')
    }
  }
  
  // 项目编码唯一性检查
  const handleCodeBlur = async () => {
    if (!formData.project_code || initialData.id) return
    
    setValidatingCode(true)
    setCodeError('')
    
    try {
      // 检查编码是否已存在
      const response = await projectApi.list({ project_code: formData.project_code })
      if (response.data?.items?.length > 0) {
        setCodeError('项目编码已存在，请使用其他编码')
      }
    } catch (err) {
      // 忽略错误，可能是网络问题
    } finally {
      setValidatingCode(false)
    }
  }
  
  // 应用模板推荐
  const handleApplyTemplate = (template) => {
    if (template.template_config) {
      try {
        const config = JSON.parse(template.template_config)
        setFormData((prev) => ({
          ...prev,
          template_id: template.template_id,
          project_type: config.project_type || prev.project_type,
          product_category: config.product_category || prev.product_category,
          industry: config.industry || prev.industry,
          stage: config.default_stage || 'S1',
          status: config.default_status || 'ST01',
          health: config.default_health || 'H1',
        }))
        toast.success(`已应用模板：${template.template_name}`)
      } catch (err) {
      }
    }
  }
  
  // 保存草稿
  const handleSaveDraft = async () => {
    setSavingDraft(true)
    try {
      // 保存到 localStorage
      const draftKey = `project_draft_${initialData.id || 'new'}`
      localStorage.setItem(draftKey, JSON.stringify(formData))
      toast.success('表单数据已保存为草稿')
    } catch (err) {
    } finally {
      setSavingDraft(false)
    }
  }
  
  // 加载草稿
  useEffect(() => {
    if (open && !initialData.id) {
      const draftKey = 'project_draft_new'
      const draft = localStorage.getItem(draftKey)
      if (draft) {
        try {
          const draftData = JSON.parse(draft)
          setFormData((prev) => ({ ...prev, ...draftData }))
        } catch (err) {
        }
      }
    }
  }, [open, initialData.id])
  
  // 表单验证
  const validateStep = (stepIndex) => {
    const step = STEPS[stepIndex]
    switch (step.id) {
      case 'basic':
        if (!formData.project_code) return '请输入项目编码'
        if (!formData.project_name) return '请输入项目名称'
        if (codeError) return codeError
        return null
      case 'customer':
        if (!formData.customer_id) return '请选择客户'
        return null
      case 'finance':
        // 财务信息可选
        return null
      case 'schedule':
        // 时间节点可选
        return null
      default:
        return null
    }
  }
  
  // 下一步
  const handleNext = () => {
    const error = validateStep(currentStep)
    if (error) {
      toast.error(error)
      return
    }
    
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }
  
  // 上一步
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }
  
  // 提交表单
  const handleSubmit = async () => {
    const error = validateStep(currentStep)
    if (error) {
      toast.error(error)
      return
    }
    
    // 验证所有步骤
    for (let i = 0; i < STEPS.length; i++) {
      const stepError = validateStep(i)
      if (stepError) {
        setCurrentStep(i)
        toast.error(`${STEPS[i].name}：${stepError}`)
        return
      }
    }
    
    setLoading(true)
    try {
      await onSubmit(formData)
      // 清除草稿
      if (!initialData.id) {
        localStorage.removeItem('project_draft_new')
      }
      onOpenChange(false)
    } catch (err) {
      toast.error(err.response?.data?.detail || '无法创建项目，请稍后重试')
    } finally {
      setLoading(false)
    }
  }
  
  // 渲染步骤内容
  const renderStepContent = () => {
    const step = STEPS[currentStep]
    
    switch (step.id) {
      case 'basic':
        return (
          <div className="space-y-4">
            {/* 模板推荐 */}
            {recommendedTemplates.length > 0 && currentStep === 0 && (
              <Card className="bg-gradient-to-r from-violet-500/10 to-indigo-500/10 border-violet-500/20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="h-4 w-4 text-violet-400" />
                    <span className="text-sm font-medium text-violet-300">推荐模板</span>
                  </div>
                  <div className="space-y-2">
                    {recommendedTemplates.slice(0, 3).map((template) => (
                      <div
                        key={template.template_id}
                        className="flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                        onClick={() => handleApplyTemplate(template)}
                      >
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white">
                            {template.template_name}
                          </div>
                          <div className="text-xs text-slate-400 mt-1">
                            {template.reasons.join('、')}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleApplyTemplate(template)
                          }}
                        >
                          应用
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                项目编码 <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Input
                  value={formData.project_code}
                  onChange={(e) => {
                    setFormData({ ...formData, project_code: e.target.value })
                    setCodeError('')
                  }}
                  onBlur={handleCodeBlur}
                  placeholder="例如: PJ260104001"
                  disabled={!!initialData.id}
                  error={codeError}
                />
                {validatingCode && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-slate-400" />
                )}
              </div>
              {codeError && (
                <p className="text-xs text-red-400">{codeError}</p>
              )}
              {!initialData.id && !codeError && (
                <p className="text-xs text-slate-500">
                  格式：PJ + 年月日(YYMMDD) + 序号(3位)
                </p>
              )}
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                项目名称 <span className="text-red-400">*</span>
              </label>
              <Input
                value={formData.project_name}
                onChange={(e) =>
                  setFormData({ ...formData, project_name: e.target.value })
                }
                placeholder="请输入项目全称"
                required
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">项目简称</label>
                <Input
                  value={formData.short_name}
                  onChange={(e) =>
                    setFormData({ ...formData, short_name: e.target.value })
                  }
                  placeholder="项目简称（可选）"
                />
              </div>
              
              <FormSelect
                label="项目类型"
                name="project_type"
                value={formData.project_type}
                onChange={(e) =>
                  setFormData({ ...formData, project_type: e.target.value })
                }
                required
              >
                <option value="">选择项目类型</option>
                {PROJECT_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </FormSelect>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">产品类别</label>
                <Input
                  value={formData.product_category}
                  onChange={(e) =>
                    setFormData({ ...formData, product_category: e.target.value })
                  }
                  placeholder="例如: ICT测试设备"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">行业</label>
                <Input
                  value={formData.industry}
                  onChange={(e) =>
                    setFormData({ ...formData, industry: e.target.value })
                  }
                  placeholder="例如: 消费电子"
                />
              </div>
            </div>
            
            <FormTextarea
              label="项目描述"
              name="description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="请输入项目描述（可选）"
              rows={3}
            />
          </div>
        )
        
      case 'customer':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                客户 <span className="text-red-400">*</span>
              </label>
              <div className="space-y-2">
                <Input
                  value={customerSearch}
                  onChange={(e) => setCustomerSearch(e.target.value)}
                  placeholder="搜索客户名称或编码"
                  icon={Building2}
                />
                {customerSearch && (
                  <div className="max-h-48 overflow-y-auto border border-white/10 rounded-lg bg-slate-900/50">
                    {filteredCustomers.length > 0 ? (
                      filteredCustomers.map((customer) => (
                        <div
                          key={customer.id}
                          className="p-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-0"
                          onClick={() => handleCustomerSelect(customer.id)}
                        >
                          <div className="font-medium text-white">
                            {customer.customer_name}
                          </div>
                          <div className="text-xs text-slate-400 mt-1">
                            {customer.customer_code}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-3 text-sm text-slate-400 text-center">
                        未找到匹配的客户
                      </div>
                    )}
                  </div>
                )}
                {selectedCustomer && (
                  <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-white">
                          {selectedCustomer.customer_name}
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          {selectedCustomer.customer_code}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setSelectedCustomer(null)
                          setFormData((prev) => ({
                            ...prev,
                            customer_id: '',
                            customer_name: '',
                            customer_contact: '',
                            customer_phone: '',
                          }))
                        }}
                      >
                        清除
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">联系人</label>
                <Input
                  value={formData.customer_contact}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_contact: e.target.value })
                  }
                  placeholder="客户联系人"
                  disabled={!selectedCustomer}
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">联系电话</label>
                <Input
                  value={formData.customer_phone}
                  onChange={(e) =>
                    setFormData({ ...formData, customer_phone: e.target.value })
                  }
                  placeholder="客户联系电话"
                  disabled={!selectedCustomer}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">合同编号</label>
              <Input
                value={formData.contract_no}
                onChange={(e) =>
                  setFormData({ ...formData, contract_no: e.target.value })
                }
                placeholder="合同编号（可选）"
              />
            </div>
          </div>
        )
        
      case 'finance':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">合同金额 (CNY)</label>
                <Input
                  type="number"
                  value={formData.contract_amount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      contract_amount: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">预算金额 (CNY)</label>
                <Input
                  type="number"
                  value={formData.budget_amount}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      budget_amount: parseFloat(e.target.value) || 0,
                    })
                  }
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">合同日期</label>
              <Input
                type="date"
                value={formData.contract_date}
                onChange={(e) =>
                  setFormData({ ...formData, contract_date: e.target.value })
                }
              />
            </div>
            
            <FormSelect
              label="项目经理 (PM)"
              name="pm_id"
              value={formData.pm_id}
              onChange={(e) => {
                const pmId = e.target.value
                const pm = employees.find((e) => e.id === parseInt(pmId))
                setFormData({
                  ...formData,
                  pm_id: pmId,
                  pm_name: pm ? pm.name || pm.real_name : '',
                })
              }}
            >
              <option value="">选择项目经理（可选）</option>
              {employees.map((emp) => {
                const projectCount = pmStats[emp.id] || 0
                return (
                  <option key={emp.id} value={emp.id}>
                    {emp.name || emp.real_name} ({emp.employee_code})
                    {projectCount > 0 && ` - ${projectCount}个项目`}
                  </option>
                )
              })}
            </FormSelect>
            
            {formData.pm_id && (
              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm text-blue-300">
                    <Info className="h-4 w-4" />
                    <span>项目经理信息将自动填充</span>
                  </div>
                  {pmStats[formData.pm_id] !== undefined && (
                    <div className="text-xs text-blue-200/80 ml-6">
                      当前负责项目数: {pmStats[formData.pm_id]} 个
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )
        
      case 'schedule':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">计划开始日期</label>
                <Input
                  type="date"
                  value={formData.planned_start_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      planned_start_date: e.target.value,
                    })
                  }
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">计划结束日期</label>
                <Input
                  type="date"
                  value={formData.planned_end_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      planned_end_date: e.target.value,
                    })
                  }
                  min={formData.planned_start_date}
                />
              </div>
            </div>
            
            {formData.planned_start_date && formData.planned_end_date && (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-2 text-sm text-amber-300">
                  <Calendar className="h-4 w-4" />
                  <span>
                    项目周期：
                    {Math.ceil(
                      (new Date(formData.planned_end_date) -
                        new Date(formData.planned_start_date)) /
                        (1000 * 60 * 60 * 24)
                    )}{' '}
                    天
                  </span>
                </div>
              </div>
            )}
            
            <FormTextarea
              label="项目需求摘要"
              name="requirements"
              value={formData.requirements}
              onChange={(e) =>
                setFormData({ ...formData, requirements: e.target.value })
              }
              placeholder="请输入项目需求摘要（可选）"
              rows={4}
            />
          </div>
        )
        
      default:
        return null
    }
  }
  
  if (!open) return null
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {initialData.id ? '编辑项目' : '新建项目'}
          </DialogTitle>
        </DialogHeader>
        
        {/* 步骤指示器 */}
        <div className="flex items-center justify-between mb-6 px-2">
          {STEPS.map((step, index) => {
            const Icon = step.icon
            const isActive = index === currentStep
            const isCompleted = index < currentStep
            
            return (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={cn(
                      'w-10 h-10 rounded-full flex items-center justify-center transition-all',
                      isActive
                        ? 'bg-primary text-white'
                        : isCompleted
                        ? 'bg-emerald-500 text-white'
                        : 'bg-white/10 text-slate-400'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <div className="mt-2 text-center">
                    <div
                      className={cn(
                        'text-xs font-medium',
                        isActive ? 'text-white' : 'text-slate-400'
                      )}
                    >
                      {step.name}
                    </div>
                  </div>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={cn(
                      'h-0.5 flex-1 mx-2 transition-colors',
                      isCompleted ? 'bg-emerald-500' : 'bg-white/10'
                    )}
                  />
                )}
              </div>
            )
          })}
        </div>
        
        {/* 步骤内容 */}
        <DialogBody>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {renderStepContent()}
            </motion.div>
          </AnimatePresence>
        </DialogBody>
        
        {/* 底部操作 */}
        <DialogFooter className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              onClick={handleSaveDraft}
              disabled={savingDraft}
            >
              {savingDraft ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  保存中...
                </>
              ) : (
                '保存草稿'
              )}
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <Button
                type="button"
                variant="secondary"
                onClick={handlePrev}
                disabled={loading}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                上一步
              </Button>
            )}
            
            {currentStep < STEPS.length - 1 ? (
              <Button
                type="button"
                onClick={handleNext}
                disabled={loading}
              >
                下一步
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            ) : (
              <Button
                type="button"
                onClick={handleSubmit}
                loading={loading}
              >
                {initialData.id ? '保存项目' : '创建项目'}
              </Button>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
