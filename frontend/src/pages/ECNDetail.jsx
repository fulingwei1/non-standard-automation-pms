/**
 * ECN Detail Page - ECN详情页面
 * Features: ECN完整信息展示、评估管理、审批流程可视化、执行任务看板、影响分析、变更日志
 */
import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  FileText,
  Users,
  Calendar,
  TrendingUp,
  DollarSign,
  GitBranch,
  History,
  Play,
  RefreshCw,
  Layers,
  Eye,
  Edit2,
  Download,
  ArrowRight,
  Search,
  Lightbulb,
  X,
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
import { Badge } from '../components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { Input } from '../components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { formatDate } from '../lib/utils'
import { ecnApi } from '../services/api'
import { Skeleton } from '../components/ui/skeleton'

const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500' },
  SUBMITTED: { label: '已提交', color: 'bg-blue-500' },
  EVALUATING: { label: '评估中', color: 'bg-amber-500' },
  EVALUATED: { label: '评估完成', color: 'bg-amber-600' },
  PENDING_APPROVAL: { label: '待审批', color: 'bg-purple-500' },
  APPROVED: { label: '已批准', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
  EXECUTING: { label: '执行中', color: 'bg-violet-500' },
  PENDING_VERIFY: { label: '待验证', color: 'bg-indigo-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
  CLOSED: { label: '已关闭', color: 'bg-gray-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}

const typeConfigs = {
  // 客户相关（3种）
  CUSTOMER_REQUIREMENT: { label: '客户需求变更', color: 'bg-blue-500' },
  CUSTOMER_SPEC: { label: '客户规格调整', color: 'bg-blue-400' },
  CUSTOMER_FEEDBACK: { label: '客户现场反馈', color: 'bg-blue-600' },
  
  // 设计变更（5种）
  MECHANICAL_STRUCTURE: { label: '机械结构变更', color: 'bg-cyan-500' },
  ELECTRICAL_SCHEME: { label: '电气方案变更', color: 'bg-cyan-400' },
  SOFTWARE_FUNCTION: { label: '软件功能变更', color: 'bg-cyan-600' },
  TECH_OPTIMIZATION: { label: '技术方案优化', color: 'bg-teal-500' },
  DESIGN_FIX: { label: '设计缺陷修复', color: 'bg-teal-600' },
  
  // 测试相关（4种）
  TEST_STANDARD: { label: '测试标准变更', color: 'bg-purple-500' },
  TEST_FIXTURE: { label: '测试工装变更', color: 'bg-purple-400' },
  CALIBRATION_SCHEME: { label: '校准方案变更', color: 'bg-purple-600' },
  TEST_PROGRAM: { label: '测试程序变更', color: 'bg-violet-500' },
  
  // 生产制造（4种）
  PROCESS_IMPROVEMENT: { label: '工艺改进', color: 'bg-orange-500' },
  MATERIAL_SUBSTITUTE: { label: '物料替代', color: 'bg-orange-400' },
  SUPPLIER_CHANGE: { label: '供应商变更', color: 'bg-orange-600' },
  COST_OPTIMIZATION: { label: '成本优化', color: 'bg-amber-500' },
  
  // 质量安全（3种）
  QUALITY_ISSUE: { label: '质量问题整改', color: 'bg-red-500' },
  SAFETY_COMPLIANCE: { label: '安全合规变更', color: 'bg-red-600' },
  RELIABILITY_IMPROVEMENT: { label: '可靠性改进', color: 'bg-rose-500' },
  
  // 项目管理（3种）
  SCHEDULE_ADJUSTMENT: { label: '进度调整', color: 'bg-green-500' },
  DOCUMENT_UPDATE: { label: '文档更新', color: 'bg-green-400' },
  DRAWING_CHANGE: { label: '图纸变更', color: 'bg-emerald-500' },
  
  // 兼容旧版本
  DESIGN: { label: '设计变更', color: 'bg-blue-500' },
  MATERIAL: { label: '物料变更', color: 'bg-amber-500' },
  PROCESS: { label: '工艺变更', color: 'bg-purple-500' },
  SPECIFICATION: { label: '规格变更', color: 'bg-green-500' },
  SCHEDULE: { label: '计划变更', color: 'bg-orange-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}

const priorityConfigs = {
  URGENT: { label: '紧急', color: 'bg-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500' },
  LOW: { label: '低', color: 'bg-blue-500' },
}

const evalResultConfigs = {
  APPROVED: { label: '通过', color: 'bg-green-500' },
  CONDITIONAL: { label: '有条件通过', color: 'bg-yellow-500' },
  REJECTED: { label: '不通过', color: 'bg-red-500' },
}

const taskStatusConfigs = {
  PENDING: { label: '待开始', color: 'bg-slate-500' },
  IN_PROGRESS: { label: '进行中', color: 'bg-blue-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
}

export default function ECNDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [ecn, setEcn] = useState(null)
  const [evaluations, setEvaluations] = useState([])
  const [approvals, setApprovals] = useState([])
  const [tasks, setTasks] = useState([])
  const [affectedMaterials, setAffectedMaterials] = useState([])
  const [affectedOrders, setAffectedOrders] = useState([])
  const [logs, setLogs] = useState([])
  const [evaluationSummary, setEvaluationSummary] = useState(null)
  const [activeTab, setActiveTab] = useState('info')
  
  // Log filters
  const [logSearchKeyword, setLogSearchKeyword] = useState('')
  const [logFilterType, setLogFilterType] = useState('all')
  
  // BOM Analysis
  const [bomImpactSummary, setBomImpactSummary] = useState(null)
  const [obsoleteAlerts, setObsoleteAlerts] = useState([])
  const [analyzingBom, setAnalyzingBom] = useState(false)
  
  // Responsibility Allocation
  const [responsibilitySummary, setResponsibilitySummary] = useState(null)
  const [showResponsibilityDialog, setShowResponsibilityDialog] = useState(false)
  const [responsibilityForm, setResponsibilityForm] = useState([{
    dept: '',
    responsibility_ratio: 0,
    responsibility_type: 'PRIMARY',
    impact_description: '',
    responsibility_scope: '',
  }])
  
  // RCA Analysis
  const [rcaAnalysis, setRcaAnalysis] = useState(null)
  const [showRcaDialog, setShowRcaDialog] = useState(false)
  const [rcaForm, setRcaForm] = useState({
    root_cause: '',
    root_cause_analysis: '',
    root_cause_category: '',
  })
  
  // Knowledge Base
  const [similarEcns, setSimilarEcns] = useState([])
  const [solutionRecommendations, setSolutionRecommendations] = useState([])
  const [extractedSolution, setExtractedSolution] = useState(null)
  const [loadingKnowledge, setLoadingKnowledge] = useState(false)
  const [showSolutionTemplateDialog, setShowSolutionTemplateDialog] = useState(false)
  const [solutionTemplateForm, setSolutionTemplateForm] = useState({
    template_name: '',
    template_category: '',
    keywords: [],
  })
  
  // Dialogs
  const [showEvaluationDialog, setShowEvaluationDialog] = useState(false)
  const [showTaskDialog, setShowTaskDialog] = useState(false)
  const [showVerifyDialog, setShowVerifyDialog] = useState(false)
  const [showCloseDialog, setShowCloseDialog] = useState(false)
  const [showMaterialDialog, setShowMaterialDialog] = useState(false)
  const [showOrderDialog, setShowOrderDialog] = useState(false)
  const [editingMaterial, setEditingMaterial] = useState(null)
  const [editingOrder, setEditingOrder] = useState(null)
  
  // Forms
  const [evaluationForm, setEvaluationForm] = useState({
    eval_dept: '',
    impact_analysis: '',
    cost_estimate: 0,
    schedule_estimate: 0,
    resource_requirement: '',
    risk_assessment: '',
    eval_result: 'APPROVED',
    eval_opinion: '',
    conditions: '',
  })
  
  const [taskForm, setTaskForm] = useState({
    task_name: '',
    task_type: '',
    task_dept: '',
    task_description: '',
    assignee_id: null,
    planned_start: '',
    planned_end: '',
  })
  
  const [verifyForm, setVerifyForm] = useState({
    verify_result: 'PASS',
    verify_note: '',
  })
  
  const [closeForm, setCloseForm] = useState({
    close_note: '',
  })
  
  const [materialForm, setMaterialForm] = useState({
    material_id: null,
    bom_item_id: null,
    material_code: '',
    material_name: '',
    specification: '',
    change_type: 'UPDATE',
    old_quantity: '',
    old_specification: '',
    old_supplier_id: null,
    new_quantity: '',
    new_specification: '',
    new_supplier_id: null,
    cost_impact: 0,
    remark: '',
  })
  
  const [orderForm, setOrderForm] = useState({
    order_type: 'PURCHASE',
    order_id: null,
    order_no: '',
    impact_description: '',
    action_type: '',
    action_description: '',
  })

  useEffect(() => {
    fetchECNDetail()
  }, [id])

  const fetchECNDetail = async () => {
    try {
      setLoading(true)
      const [ecnRes, evalsRes, approvalsRes, tasksRes, materialsRes, ordersRes, logsRes, summaryRes, bomImpactRes, obsoleteRes, responsibilityRes, rcaRes] = await Promise.all([
        ecnApi.get(id).catch(() => ({ data: null })),
        ecnApi.getEvaluations(id).catch(() => ({ data: [] })),
        ecnApi.getApprovals(id).catch(() => ({ data: [] })),
        ecnApi.getTasks(id).catch(() => ({ data: [] })),
        ecnApi.getAffectedMaterials(id).catch(() => ({ data: [] })),
        ecnApi.getAffectedOrders(id).catch(() => ({ data: [] })),
        ecnApi.getLogs(id).catch(() => ({ data: [] })),
        ecnApi.getEvaluationSummary(id).catch(() => ({ data: null })),
      ])
      
      setEcn(ecnRes.data || ecnRes)
      setEvaluations(evalsRes.data || [])
      setApprovals(approvalsRes.data || [])
      setTasks(tasksRes.data || [])
      setAffectedMaterials(materialsRes.data || [])
      setAffectedOrders(ordersRes.data || [])
      setLogs(logsRes.data || [])
      setEvaluationSummary(summaryRes.data)
    } catch (error) {
      console.error('Failed to fetch ECN detail:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    try {
      await ecnApi.submit(id, { remark: '提交ECN申请' })
      await fetchECNDetail()
      alert('ECN已提交')
    } catch (error) {
      alert('提交失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleApprove = async (approvalId, comment = '') => {
    try {
      await ecnApi.approve(approvalId, comment)
      await fetchECNDetail()
      alert('审批通过')
    } catch (error) {
      alert('审批失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleReject = async (approvalId, reason) => {
    try {
      await ecnApi.reject(approvalId, reason)
      await fetchECNDetail()
      alert('已驳回')
    } catch (error) {
      alert('驳回失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleStartExecution = async () => {
    try {
      await ecnApi.startExecution(id, { remark: '开始执行ECN' })
      await fetchECNDetail()
      alert('ECN执行已开始')
    } catch (error) {
      alert('开始执行失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleVerify = async () => {
    try {
      await ecnApi.verify(id, verifyForm)
      await fetchECNDetail()
      setShowVerifyDialog(false)
      alert('验证完成')
    } catch (error) {
      alert('验证失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleClose = async () => {
    try {
      await ecnApi.close(id, closeForm)
      await fetchECNDetail()
      setShowCloseDialog(false)
      alert('ECN已关闭')
    } catch (error) {
      alert('关闭失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleUpdateTaskProgress = async (taskId, progress) => {
    try {
      await ecnApi.updateTaskProgress(taskId, progress)
      await fetchECNDetail()
    } catch (error) {
      alert('更新进度失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCompleteTask = async (taskId) => {
    try {
      await ecnApi.completeTask(taskId)
      await fetchECNDetail()
      alert('任务已完成')
    } catch (error) {
      alert('完成任务失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleAddMaterial = () => {
    setEditingMaterial(null)
    setMaterialForm({
      material_id: null,
      bom_item_id: null,
      material_code: '',
      material_name: '',
      specification: '',
      change_type: 'UPDATE',
      old_quantity: '',
      old_specification: '',
      old_supplier_id: null,
      new_quantity: '',
      new_specification: '',
      new_supplier_id: null,
      cost_impact: 0,
      remark: '',
    })
    setShowMaterialDialog(true)
  }

  const handleEditMaterial = (material) => {
    setEditingMaterial(material)
    setMaterialForm({
      material_id: material.material_id,
      bom_item_id: material.bom_item_id,
      material_code: material.material_code || '',
      material_name: material.material_name || '',
      specification: material.specification || '',
      change_type: material.change_type || 'UPDATE',
      old_quantity: material.old_quantity || '',
      old_specification: material.old_specification || '',
      old_supplier_id: material.old_supplier_id,
      new_quantity: material.new_quantity || '',
      new_specification: material.new_specification || '',
      new_supplier_id: material.new_supplier_id,
      cost_impact: material.cost_impact || 0,
      remark: material.remark || '',
    })
    setShowMaterialDialog(true)
  }

  const handleSaveMaterial = async () => {
    try {
      if (editingMaterial) {
        await ecnApi.updateAffectedMaterial(id, editingMaterial.id, materialForm)
      } else {
        await ecnApi.createAffectedMaterial(id, materialForm)
      }
      await fetchECNDetail()
      setShowMaterialDialog(false)
      alert(editingMaterial ? '物料已更新' : '物料已添加')
    } catch (error) {
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteMaterial = async (materialId) => {
    if (!confirm('确定要删除这个受影响物料吗？')) return
    try {
      await ecnApi.deleteAffectedMaterial(id, materialId)
      await fetchECNDetail()
      alert('物料已删除')
    } catch (error) {
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleAddOrder = () => {
    setEditingOrder(null)
    setOrderForm({
      order_type: 'PURCHASE',
      order_id: null,
      order_no: '',
      impact_description: '',
      action_type: '',
      action_description: '',
    })
    setShowOrderDialog(true)
  }

  const handleEditOrder = (order) => {
    setEditingOrder(order)
    setOrderForm({
      order_type: order.order_type || 'PURCHASE',
      order_id: order.order_id,
      order_no: order.order_no || '',
      impact_description: order.impact_description || '',
      action_type: order.action_type || '',
      action_description: order.action_description || '',
    })
    setShowOrderDialog(true)
  }

  const handleSaveOrder = async () => {
    try {
      if (editingOrder) {
        await ecnApi.updateAffectedOrder(id, editingOrder.id, orderForm)
      } else {
        await ecnApi.createAffectedOrder(id, orderForm)
      }
      await fetchECNDetail()
      setShowOrderDialog(false)
      alert(editingOrder ? '订单已更新' : '订单已添加')
    } catch (error) {
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDeleteOrder = async (orderId) => {
    if (!confirm('确定要删除这个受影响订单吗？')) return
    try {
      await ecnApi.deleteAffectedOrder(id, orderId)
      await fetchECNDetail()
      alert('订单已删除')
    } catch (error) {
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateEvaluation = async () => {
    if (!evaluationForm.eval_dept) {
      alert('请选择评估部门')
      return
    }
    try {
      await ecnApi.createEvaluation(id, evaluationForm)
      setShowEvaluationDialog(false)
      setEvaluationForm({
        eval_dept: '',
        impact_analysis: '',
        cost_estimate: 0,
        schedule_estimate: 0,
        resource_requirement: '',
        risk_assessment: '',
        eval_result: 'APPROVED',
        eval_opinion: '',
        conditions: '',
      })
      await fetchECNDetail()
      alert('评估已创建')
    } catch (error) {
      alert('创建评估失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateTask = async () => {
    if (!taskForm.task_name) {
      alert('请填写任务名称')
      return
    }
    try {
      await ecnApi.createTask(id, taskForm)
      setShowTaskDialog(false)
      setTaskForm({
        task_name: '',
        task_type: '',
        task_dept: '',
        task_description: '',
        assignee_id: null,
        planned_start: '',
        planned_end: '',
      })
      await fetchECNDetail()
      alert('任务已创建')
    } catch (error) {
      alert('创建任务失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // Filter logs
  const filteredLogs = useMemo(() => {
    let filtered = [...logs]
    
    // Filter by type
    if (logFilterType !== 'all') {
      filtered = filtered.filter(log => log.log_type === logFilterType)
    }
    
    // Filter by keyword
    if (logSearchKeyword) {
      const keyword = logSearchKeyword.toLowerCase()
      filtered = filtered.filter(log => 
        log.log_action?.toLowerCase().includes(keyword) ||
        log.log_content?.toLowerCase().includes(keyword) ||
        log.old_status?.toLowerCase().includes(keyword) ||
        log.new_status?.toLowerCase().includes(keyword) ||
        log.created_by_name?.toLowerCase().includes(keyword)
      )
    }
    
    return filtered
  }, [logs, logFilterType, logSearchKeyword])

  // BOM Analysis handlers
  const handleAnalyzeBomImpact = async () => {
    try {
      setAnalyzingBom(true)
      const result = await ecnApi.analyzeBomImpact(id, { include_cascade: true })
      if (result.data?.has_impact) {
        alert(`BOM影响分析完成：影响${result.data.total_affected_items}项物料，成本影响¥${result.data.total_cost_impact?.toLocaleString()}`)
      } else {
        alert('BOM影响分析完成：未发现影响')
      }
      await fetchECNDetail()
    } catch (error) {
      alert('BOM分析失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setAnalyzingBom(false)
    }
  }

  const handleCheckObsoleteRisk = async () => {
    try {
      setAnalyzingBom(true)
      const result = await ecnApi.checkObsoleteRisk(id)
      if (result.data?.has_obsolete_risk) {
        alert(`呆滞料风险检查完成：发现${result.data.obsolete_risks?.length || 0}个风险，总成本¥${result.data.total_obsolete_cost?.toLocaleString()}`)
      } else {
        alert('呆滞料风险检查完成：未发现呆滞料风险')
      }
      await fetchECNDetail()
    } catch (error) {
      alert('呆滞料检查失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setAnalyzingBom(false)
    }
  }

  // Responsibility handlers
  const handleCreateResponsibility = async () => {
    const totalRatio = responsibilityForm.reduce((sum, r) => sum + parseFloat(r.responsibility_ratio || 0), 0)
    if (Math.abs(totalRatio - 100) > 0.01) {
      alert(`责任比例总和必须为100%，当前为${totalRatio.toFixed(2)}%`)
      return
    }
    
    try {
      await ecnApi.createResponsibilityAnalysis(id, responsibilityForm)
      setShowResponsibilityDialog(false)
      await fetchECNDetail()
      alert('责任分摊创建成功')
    } catch (error) {
      alert('创建失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // RCA handlers
  const handleSaveRcaAnalysis = async () => {
    try {
      await ecnApi.updateRcaAnalysis(id, rcaForm)
      setShowRcaDialog(false)
      await fetchECNDetail()
      alert('RCA分析保存成功')
    } catch (error) {
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // Knowledge Base handlers
  const handleExtractSolution = async () => {
    try {
      setLoadingKnowledge(true)
      const result = await ecnApi.extractSolution(id, true)
      setExtractedSolution(result.data)
      await fetchECNDetail()
      alert('解决方案提取成功')
    } catch (error) {
      alert('提取失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingKnowledge(false)
    }
  }

  const handleFindSimilarEcns = async () => {
    try {
      setLoadingKnowledge(true)
      const result = await ecnApi.getSimilarEcns(id, { top_n: 5, min_similarity: 0.3 })
      setSimilarEcns(result.data?.similar_ecns || [])
    } catch (error) {
      alert('查找失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingKnowledge(false)
    }
  }

  const handleRecommendSolutions = async () => {
    try {
      setLoadingKnowledge(true)
      const result = await ecnApi.recommendSolutions(id, { top_n: 5 })
      setSolutionRecommendations(result.data?.recommendations || [])
    } catch (error) {
      alert('推荐失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoadingKnowledge(false)
    }
  }

  const handleApplySolutionTemplate = async (templateId) => {
    try {
      await ecnApi.applySolutionTemplate(id, templateId)
      await fetchECNDetail()
      alert('解决方案模板应用成功')
    } catch (error) {
      alert('应用失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreateSolutionTemplate = async () => {
    try {
      await ecnApi.createSolutionTemplate(id, {
        template_name: solutionTemplateForm.template_name || `${ecn.ecn_title} - 解决方案模板`,
        template_category: solutionTemplateForm.template_category || ecn.ecn_type,
        keywords: solutionTemplateForm.keywords,
      })
      setShowSolutionTemplateDialog(false)
      alert('解决方案模板创建成功')
    } catch (error) {
      alert('创建失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  if (!ecn) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold mb-2">未找到ECN</h2>
        <p className="text-slate-400 mb-6">该ECN可能已被删除或不存在</p>
        <Button onClick={() => navigate('/ecns')}>返回ECN列表</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title={
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/ecns')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold">{ecn.ecn_title}</span>
                <Badge className={statusConfigs[ecn.status]?.color}>
                  {statusConfigs[ecn.status]?.label}
                </Badge>
              </div>
              <div className="text-sm text-slate-400 mt-1">
                {ecn.ecn_no} · {ecn.project_name || '未关联项目'}
              </div>
            </div>
          </div>
        }
        description="ECN变更管理详情"
        actions={
          <div className="flex gap-2">
            {ecn.status === 'DRAFT' && (
              <Button onClick={handleSubmit}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                提交ECN
              </Button>
            )}
            {ecn.status === 'APPROVED' && (
              <Button onClick={handleStartExecution}>
                <Play className="w-4 h-4 mr-2" />
                开始执行
              </Button>
            )}
            {ecn.status === 'EXECUTING' && tasks.every(t => t.status === 'COMPLETED') && (
              <Button onClick={() => setShowVerifyDialog(true)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                验证
              </Button>
            )}
            {ecn.status === 'COMPLETED' && (
              <Button onClick={() => setShowCloseDialog(true)}>
                <XCircle className="w-4 h-4 mr-2" />
                关闭
              </Button>
            )}
            <Button
              variant="outline"
              onClick={() => window.print()}
            >
              <Download className="w-4 h-4 mr-2" />
              打印/导出
            </Button>
            <Button variant="outline" onClick={fetchECNDetail}>
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
          </div>
        }
      />

      {/* Status Flow Indicator */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {[
              { status: 'DRAFT', label: '草稿' },
              { status: 'SUBMITTED', label: '已提交' },
              { status: 'EVALUATING', label: '评估中' },
              { status: 'PENDING_APPROVAL', label: '待审批' },
              { status: 'APPROVED', label: '已批准' },
              { status: 'EXECUTING', label: '执行中' },
              { status: 'COMPLETED', label: '已完成' },
              { status: 'CLOSED', label: '已关闭' },
            ].map((step, index, array) => {
              const isActive = ecn.status === step.status
              const isPast = ['DRAFT', 'SUBMITTED', 'EVALUATING', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTING', 'COMPLETED', 'CLOSED'].indexOf(ecn.status) >= index
              
              return (
                <div key={step.status} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isActive ? 'bg-blue-500' : isPast ? 'bg-green-500' : 'bg-slate-300'
                    } text-white font-bold text-sm`}>
                      {index + 1}
                    </div>
                    <div className={`text-xs mt-2 ${isActive ? 'font-semibold' : 'text-slate-400'}`}>
                      {step.label}
                    </div>
                  </div>
                  {index < array.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-2 ${
                      isPast ? 'bg-green-500' : 'bg-slate-300'
                    }`} />
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="info">基本信息</TabsTrigger>
          <TabsTrigger value="evaluations">评估</TabsTrigger>
          <TabsTrigger value="approvals">审批</TabsTrigger>
          <TabsTrigger value="tasks">执行任务</TabsTrigger>
          <TabsTrigger value="affected">影响分析</TabsTrigger>
          <TabsTrigger value="knowledge">知识库</TabsTrigger>
          <TabsTrigger value="integration">模块集成</TabsTrigger>
          <TabsTrigger value="logs">变更日志</TabsTrigger>
        </TabsList>

        {/* 基本信息 */}
        <TabsContent value="info" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">基本信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm text-slate-500 mb-1">ECN编号</div>
                  <div className="font-mono">{ecn.ecn_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">变更类型</div>
                  <Badge className={typeConfigs[ecn.ecn_type]?.color}>
                    {typeConfigs[ecn.ecn_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">优先级</div>
                  <Badge className={priorityConfigs[ecn.priority]?.color}>
                    {priorityConfigs[ecn.priority]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div>{ecn.project_name || '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">申请人</div>
                  <div>{ecn.applicant_name || '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">申请时间</div>
                  <div>{ecn.applied_at ? formatDate(ecn.applied_at) : '-'}</div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">影响评估</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm text-slate-500 mb-1">成本影响</div>
                  <div className="text-xl font-semibold text-red-600">
                    ¥{ecn.cost_impact || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">工期影响</div>
                  <div className="text-xl font-semibold text-orange-600">
                    {ecn.schedule_impact_days || 0} 天
                  </div>
                </div>
                {ecn.quality_impact && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">质量影响</div>
                    <div>{ecn.quality_impact}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">变更内容</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {ecn.change_reason && (
                <div>
                  <div className="text-sm text-slate-500 mb-2">变更原因</div>
                  <div className="p-3 bg-slate-50 rounded-lg">{ecn.change_reason}</div>
                </div>
              )}
              {ecn.change_description && (
                <div>
                  <div className="text-sm text-slate-500 mb-2">变更描述</div>
                  <div className="p-3 bg-slate-50 rounded-lg whitespace-pre-wrap">
                    {ecn.change_description}
                  </div>
                </div>
              )}
              {ecn.approval_note && (
                <div>
                  <div className="text-sm text-slate-500 mb-2">审批意见</div>
                  <div className="p-3 bg-slate-50 rounded-lg">{ecn.approval_note}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 评估管理 - 优化后的界面 */}
        <TabsContent value="evaluations" className="space-y-4">
          {evaluationSummary && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">评估汇总</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">总成本影响</div>
                    <div className="text-xl font-semibold text-red-600">
                      ¥{evaluationSummary.total_cost_impact || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">最大工期影响</div>
                    <div className="text-xl font-semibold text-orange-600">
                      {evaluationSummary.max_schedule_impact || 0} 天
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">评估完成度</div>
                    <div className="text-xl font-semibold">
                      {evaluationSummary.submitted_count || 0} / {evaluationSummary.total_evaluations || 0}
                    </div>
                    <div className="mt-2">
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all"
                          style={{ width: `${evaluationSummary.total_evaluations > 0 ? (evaluationSummary.submitted_count / evaluationSummary.total_evaluations * 100) : 0}%` }}
                        />
                      </div>
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">通过/驳回</div>
                    <div className="text-xl font-semibold">
                      <span className="text-green-600">{evaluationSummary.approved_count || 0}</span>
                      {' / '}
                      <span className="text-red-600">{evaluationSummary.rejected_count || 0}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">部门评估</CardTitle>
            {(ecn.status === 'SUBMITTED' || ecn.status === 'EVALUATING') && (
              <Button onClick={() => setShowEvaluationDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                创建评估
              </Button>
            )}
          </div>

          {evaluations.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-slate-400">
                暂无评估记录
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {evaluations.map((evaluation) => (
                <Card key={evaluation.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle className="text-base">{evaluation.eval_dept}</CardTitle>
                        {evaluation.evaluated_at && (
                          <CardDescription className="mt-1">
                            评估时间: {formatDate(evaluation.evaluated_at)}
                          </CardDescription>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={evalResultConfigs[evaluation.eval_result]?.color || 'bg-slate-500'}>
                          {evalResultConfigs[evaluation.eval_result]?.label || evaluation.eval_result}
                        </Badge>
                        <Badge className={evaluation.status === 'SUBMITTED' ? 'bg-green-500' : 'bg-amber-500'}>
                          {evaluation.status === 'SUBMITTED' ? '已提交' : '草稿'}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500 mb-1">成本估算</div>
                        <div className="font-semibold text-red-600">
                          {evaluation.cost_estimate > 0 ? `¥${evaluation.cost_estimate}` : '-'}
                        </div>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <div className="text-xs text-slate-500 mb-1">工期估算</div>
                        <div className="font-semibold text-orange-600">
                          {evaluation.schedule_estimate > 0 ? `${evaluation.schedule_estimate} 天` : '-'}
                        </div>
                      </div>
                    </div>
                    <div className="text-sm">
                      <span className="text-slate-500">评估人:</span> {evaluation.evaluator_name || '待分配'}
                    </div>
                    {evaluation.impact_analysis && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">影响分析:</div>
                        <div className="p-2 bg-slate-50 rounded text-sm line-clamp-3">{evaluation.impact_analysis}</div>
                      </div>
                    )}
                    {evaluation.risk_assessment && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">风险评估:</div>
                        <div className="p-2 bg-amber-50 rounded text-sm">{evaluation.risk_assessment}</div>
                      </div>
                    )}
                    {evaluation.eval_opinion && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">评估意见:</div>
                        <div className="p-2 bg-slate-50 rounded text-sm">{evaluation.eval_opinion}</div>
                      </div>
                    )}
                    {evaluation.conditions && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">附加条件:</div>
                        <div className="p-2 bg-blue-50 rounded text-sm">{evaluation.conditions}</div>
                      </div>
                    )}
                    {evaluation.status === 'DRAFT' && (
                      <Button
                        size="sm"
                        className="w-full"
                        onClick={async () => {
                          if (!confirm('确认提交此评估？提交后将无法修改。')) return
                          try {
                            await ecnApi.submitEvaluation(evaluation.id)
                            await fetchECNDetail()
                            alert('评估已提交')
                          } catch (error) {
                            alert('提交失败: ' + (error.response?.data?.detail || error.message))
                          }
                        }}
                      >
                        提交评估
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* 审批流程可视化 - 时间线视图 */}
        <TabsContent value="approvals" className="space-y-4">
          {approvals.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-slate-400">
                暂无审批记录
              </CardContent>
            </Card>
          ) : (
            <div className="relative">
              {/* 时间线 */}
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />
              
              <div className="space-y-6">
                {approvals.map((approval, index) => {
                  const isCompleted = approval.status === 'COMPLETED'
                  const isApproved = approval.approval_result === 'APPROVED'
                  const isRejected = approval.approval_result === 'REJECTED'
                  const isPending = approval.status === 'PENDING'
                  
                  return (
                    <div key={approval.id} className="relative flex items-start gap-4">
                      {/* 时间线节点 */}
                      <div className="relative z-10">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          isApproved ? 'bg-green-500' :
                          isRejected ? 'bg-red-500' :
                          isPending ? 'bg-blue-500' : 'bg-slate-300'
                        } text-white font-bold shadow-lg`}>
                          {isCompleted ? (
                            isApproved ? <CheckCircle2 className="w-5 h-5" /> :
                            isRejected ? <XCircle className="w-5 h-5" /> : index + 1
                          ) : (
                            index + 1
                          )}
                        </div>
                      </div>
                      
                      {/* 审批卡片 */}
                      <Card className="flex-1 shadow-sm">
                        <CardHeader>
                          <div className="flex justify-between items-center">
                            <div>
                              <CardTitle className="text-base">
                                第{approval.approval_level}级审批
                              </CardTitle>
                              <CardDescription className="mt-1">
                                {approval.approval_role}
                              </CardDescription>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={
                                isApproved ? 'bg-green-500' :
                                isRejected ? 'bg-red-500' :
                                isPending ? 'bg-blue-500' : 'bg-slate-500'
                              }>
                                {isApproved ? '已通过' :
                                 isRejected ? '已驳回' :
                                 isPending ? '待审批' : approval.status}
                              </Badge>
                              {approval.is_overdue && (
                                <Badge className="bg-red-500">超期</Badge>
                              )}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="text-sm">
                            <span className="text-slate-500">审批人:</span> {approval.approver_name || '待分配'}
                          </div>
                          {approval.approved_at && (
                            <div className="text-sm">
                              <span className="text-slate-500">审批时间:</span> {formatDate(approval.approved_at)}
                            </div>
                          )}
                          {approval.due_date && (
                            <div className="text-sm">
                              <span className="text-slate-500">审批期限:</span> {formatDate(approval.due_date)}
                            </div>
                          )}
                          {approval.approval_opinion && (
                            <div>
                              <div className="text-sm text-slate-500 mb-1">审批意见:</div>
                              <div className="p-2 bg-slate-50 rounded text-sm">{approval.approval_opinion}</div>
                            </div>
                          )}
                          {isPending && (
                            <div className="flex justify-end gap-2 pt-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  const reason = prompt('请输入驳回原因：')
                                  if (reason) handleReject(approval.id, reason)
                                }}
                              >
                                驳回
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => {
                                  const comment = prompt('请输入审批意见（可选）：') || ''
                                  handleApprove(approval.id, comment)
                                }}
                              >
                                通过
                              </Button>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </TabsContent>

        {/* 执行任务看板 - 优化后的看板视图 */}
        <TabsContent value="tasks" className="space-y-4">
          <div className="flex justify-end gap-2">
            {(ecn.status === 'APPROVED' || ecn.status === 'EXECUTING') && (
              <Button onClick={() => setShowTaskDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                创建任务
              </Button>
            )}
          </div>

          {tasks.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-slate-400">
                暂无执行任务
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {['PENDING', 'IN_PROGRESS', 'COMPLETED'].map((status) => {
                const statusTasks = tasks.filter(t => t.status === status)
                const statusConfig = taskStatusConfigs[status]
                
                return (
                  <Card key={status} className="flex flex-col">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-semibold">
                          {statusConfig?.label || status}
                        </CardTitle>
                        <Badge className={statusConfig?.color}>
                          {statusTasks.length}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="flex-1 space-y-3 overflow-y-auto max-h-[600px]">
                      {statusTasks.length === 0 ? (
                        <div className="text-center py-8 text-slate-400 text-sm">
                          暂无任务
                        </div>
                      ) : (
                        statusTasks.map((task) => (
                          <Card key={task.id} className="p-3 hover:shadow-md transition-shadow">
                            <div className="space-y-2">
                              <div className="font-medium text-sm">{task.task_name}</div>
                              {task.task_dept && (
                                <div className="text-xs text-slate-500">部门: {task.task_dept}</div>
                              )}
                              {task.assignee_name && (
                                <div className="text-xs text-slate-500">负责人: {task.assignee_name}</div>
                              )}
                              {task.planned_start && (
                                <div className="text-xs text-slate-500">
                                  计划: {formatDate(task.planned_start)} - {task.planned_end ? formatDate(task.planned_end) : ''}
                                </div>
                              )}
                              {task.status === 'IN_PROGRESS' && (
                                <div className="space-y-1 pt-2">
                                  <div className="flex justify-between text-xs">
                                    <span className="text-slate-500">进度</span>
                                    <span className="font-semibold">{task.progress_pct || 0}%</span>
                                  </div>
                                  <div className="w-full bg-slate-200 rounded-full h-2">
                                    <div
                                      className="bg-blue-500 h-2 rounded-full transition-all"
                                      style={{ width: `${task.progress_pct || 0}%` }}
                                    />
                                  </div>
                                  <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={task.progress_pct || 0}
                                    onChange={(e) => handleUpdateTaskProgress(task.id, parseInt(e.target.value))}
                                    className="w-full"
                                  />
                                </div>
                              )}
                              {task.status === 'IN_PROGRESS' && (
                                <Button
                                  size="sm"
                                  className="w-full mt-2"
                                  onClick={() => handleCompleteTask(task.id)}
                                >
                                  完成任务
                                </Button>
                              )}
                            </div>
                          </Card>
                        ))
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        {/* 影响分析 */}
        <TabsContent value="affected" className="space-y-4">
          {/* 操作工具栏 */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={handleAnalyzeBomImpact}
                  disabled={analyzingBom || !ecn.machine_id}
                >
                  <GitBranch className="w-4 h-4 mr-2" />
                  {analyzingBom ? '分析中...' : 'BOM影响分析'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleCheckObsoleteRisk}
                  disabled={analyzingBom}
                >
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  检查呆滞料风险
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowResponsibilityDialog(true)}
                >
                  <Users className="w-4 h-4 mr-2" />
                  责任分摊
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    if (rcaAnalysis) {
                      setRcaForm({
                        root_cause: rcaAnalysis.root_cause || '',
                        root_cause_analysis: rcaAnalysis.root_cause_analysis || '',
                        root_cause_category: rcaAnalysis.root_cause_category || '',
                      })
                    }
                    setShowRcaDialog(true)
                  }}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  RCA分析
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* BOM影响分析结果 */}
          {bomImpactSummary && bomImpactSummary.has_impact && (
            <Card className="border-blue-200 bg-blue-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <GitBranch className="w-5 h-5 text-blue-600" />
                  BOM影响分析结果
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">总成本影响</div>
                    <div className="text-xl font-bold text-red-600">
                      ¥{bomImpactSummary.total_cost_impact?.toLocaleString() || 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">受影响物料项</div>
                    <div className="text-xl font-bold">
                      {bomImpactSummary.total_affected_items || 0} 项
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">最大交期影响</div>
                    <div className="text-xl font-bold text-orange-600">
                      {bomImpactSummary.max_schedule_impact_days || 0} 天
                    </div>
                  </div>
                </div>
                {bomImpactSummary.bom_impacts && bomImpactSummary.bom_impacts.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">BOM影响明细：</div>
                    {bomImpactSummary.bom_impacts.map((impact, idx) => (
                      <div key={idx} className="p-2 bg-white rounded text-sm">
                        BOM #{impact.bom_id}: {impact.affected_item_count}项受影响, 
                        成本影响¥{impact.cost_impact?.toLocaleString()}, 
                        交期影响{impact.schedule_impact_days}天
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 呆滞料预警 */}
          {obsoleteAlerts.length > 0 && (
            <Card className="border-red-200 bg-red-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  呆滞料预警
                  <Badge className="bg-red-500">{obsoleteAlerts.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {obsoleteAlerts.map((alert, idx) => (
                    <Card key={idx} className="p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-semibold">{alert.material_name}</div>
                          <div className="text-sm text-slate-500 font-mono">{alert.material_code}</div>
                        </div>
                        <Badge className={
                          alert.risk_level === 'CRITICAL' ? 'bg-red-600' :
                          alert.risk_level === 'HIGH' ? 'bg-red-500' :
                          alert.risk_level === 'MEDIUM' ? 'bg-orange-500' : 'bg-yellow-500'
                        }>
                          {alert.risk_level === 'CRITICAL' ? '严重' :
                           alert.risk_level === 'HIGH' ? '高' :
                           alert.risk_level === 'MEDIUM' ? '中' : '低'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-slate-500">呆滞数量:</span> {alert.obsolete_quantity}
                        </div>
                        <div>
                          <span className="text-slate-500">呆滞成本:</span> 
                          <span className="font-semibold text-red-600 ml-1">¥{alert.obsolete_cost?.toLocaleString()}</span>
                        </div>
                      </div>
                      {alert.analysis && (
                        <div className="mt-2 p-2 bg-slate-50 rounded text-sm">{alert.analysis}</div>
                      )}
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 责任分摊汇总 */}
          {responsibilitySummary && responsibilitySummary.has_responsibility && (
            <Card className="border-green-200 bg-green-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="w-5 h-5 text-green-600" />
                  责任分摊
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {responsibilitySummary.responsibilities?.map((resp, idx) => (
                    <div key={idx} className="flex justify-between items-center p-3 bg-white rounded">
                      <div>
                        <div className="font-semibold">{resp.dept}</div>
                        <div className="text-sm text-slate-500">{resp.responsibility_type === 'PRIMARY' ? '主要责任' : resp.responsibility_type === 'SECONDARY' ? '次要责任' : '支持责任'}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{resp.responsibility_ratio}%</div>
                        <div className="text-sm text-slate-500">¥{resp.cost_allocation?.toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                      <span className="font-semibold">总成本分摊</span>
                      <span className="text-xl font-bold text-green-600">
                        ¥{responsibilitySummary.total_cost_allocation?.toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* RCA分析 */}
          {rcaAnalysis && (rcaAnalysis.root_cause || rcaAnalysis.root_cause_analysis) && (
            <Card className="border-purple-200 bg-purple-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="w-5 h-5 text-purple-600" />
                  RCA分析（根本原因分析）
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {rcaAnalysis.root_cause && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">根本原因类型</div>
                      <div className="font-semibold">{rcaAnalysis.root_cause}</div>
                    </div>
                  )}
                  {rcaAnalysis.root_cause_category && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">原因分类</div>
                      <div>{rcaAnalysis.root_cause_category}</div>
                    </div>
                  )}
                  {rcaAnalysis.root_cause_analysis && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">分析内容</div>
                      <div className="p-3 bg-white rounded whitespace-pre-wrap">{rcaAnalysis.root_cause_analysis}</div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 成本影响汇总 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">成本影响汇总</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500 mb-1">物料成本影响</div>
                  <div className="text-2xl font-bold text-red-600">
                    ¥{affectedMaterials.reduce((sum, m) => sum + (parseFloat(m.cost_impact) || 0), 0).toFixed(2)}
                  </div>
                </div>
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500 mb-1">受影响物料数</div>
                  <div className="text-2xl font-bold">{affectedMaterials.length}</div>
                </div>
                <div className="text-center p-4 bg-slate-50 rounded-lg">
                  <div className="text-sm text-slate-500 mb-1">受影响订单数</div>
                  <div className="text-2xl font-bold">{affectedOrders.length}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-base">受影响物料</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge>{affectedMaterials.length}</Badge>
                    {(ecn.status === 'DRAFT' || ecn.status === 'SUBMITTED' || ecn.status === 'EVALUATING') && (
                      <Button size="sm" onClick={handleAddMaterial}>
                        <Plus className="w-4 h-4 mr-2" />
                        添加物料
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {affectedMaterials.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-sm">暂无受影响物料</div>
                ) : (
                  <div className="space-y-4">
                    {affectedMaterials.map((mat) => (
                      <Card key={mat.id} className="p-4">
                        <div className="space-y-3">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-semibold">{mat.material_name}</div>
                              <div className="text-sm text-slate-500 font-mono">{mat.material_code}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className="bg-blue-500">{mat.change_type}</Badge>
                              {(ecn.status === 'DRAFT' || ecn.status === 'SUBMITTED' || ecn.status === 'EVALUATING') && (
                                <div className="flex gap-1">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleEditMaterial(mat)}
                                  >
                                    <Edit2 className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteMaterial(mat.id)}
                                  >
                                    <XCircle className="w-4 h-4" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                          
                          {/* 变更前后对比 */}
                          {(mat.old_quantity || mat.old_specification || mat.new_quantity || mat.new_specification) && (
                            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg">
                              <div>
                                <div className="text-xs text-slate-500 mb-1">变更前</div>
                                {mat.old_quantity && (
                                  <div className="text-sm">数量: {mat.old_quantity}</div>
                                )}
                                {mat.old_specification && (
                                  <div className="text-sm">规格: {mat.old_specification}</div>
                                )}
                              </div>
                              <div>
                                <div className="text-xs text-slate-500 mb-1">变更后</div>
                                {mat.new_quantity && (
                                  <div className="text-sm">数量: {mat.new_quantity}</div>
                                )}
                                {mat.new_specification && (
                                  <div className="text-sm">规格: {mat.new_specification}</div>
                                )}
                              </div>
                            </div>
                          )}
                          
                          <div className="flex justify-between items-center pt-2 border-t">
                            <div className="text-sm text-slate-500">成本影响</div>
                            <div className={`text-lg font-semibold ${
                              parseFloat(mat.cost_impact) > 0 ? 'text-red-600' : 
                              parseFloat(mat.cost_impact) < 0 ? 'text-green-600' : 'text-slate-600'
                            }`}>
                              {parseFloat(mat.cost_impact) > 0 ? '+' : ''}¥{mat.cost_impact || 0}
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-base">受影响订单</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge>{affectedOrders.length}</Badge>
                    {(ecn.status === 'DRAFT' || ecn.status === 'SUBMITTED' || ecn.status === 'EVALUATING') && (
                      <Button size="sm" onClick={handleAddOrder}>
                        <Plus className="w-4 h-4 mr-2" />
                        添加订单
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {affectedOrders.length === 0 ? (
                  <div className="text-center py-8 text-slate-400 text-sm">暂无受影响订单</div>
                ) : (
                  <div className="space-y-3">
                    {affectedOrders.map((order) => (
                      <Card key={order.id} className="p-4">
                        <div className="space-y-2">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-semibold">{order.order_type === 'PURCHASE' ? '采购订单' : '外协订单'}</div>
                              <div className="text-sm text-slate-500 font-mono">{order.order_no}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={order.status === 'PROCESSED' ? 'bg-green-500' : 'bg-amber-500'}>
                                {order.status === 'PROCESSED' ? '已处理' : '待处理'}
                              </Badge>
                              {(ecn.status === 'DRAFT' || ecn.status === 'SUBMITTED' || ecn.status === 'EVALUATING') && (
                                <div className="flex gap-1">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleEditOrder(order)}
                                  >
                                    <Edit2 className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteOrder(order.id)}
                                  >
                                    <XCircle className="w-4 h-4" />
                                  </Button>
                                </div>
                              )}
                            </div>
                          </div>
                          {order.impact_description && (
                            <div className="text-sm text-slate-600 p-2 bg-slate-50 rounded">
                              {order.impact_description}
                            </div>
                          )}
                          {order.action_type && (
                            <div className="text-sm">
                              <span className="text-slate-500">处理方式:</span> {order.action_type}
                            </div>
                          )}
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 知识库 */}
        <TabsContent value="knowledge" className="space-y-4">
          {/* 操作工具栏 */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  onClick={handleExtractSolution}
                  disabled={loadingKnowledge}
                >
                  <FileText className="w-4 h-4 mr-2" />
                  {loadingKnowledge ? '提取中...' : '提取解决方案'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleFindSimilarEcns}
                  disabled={loadingKnowledge}
                >
                  <Search className="w-4 h-4 mr-2" />
                  {loadingKnowledge ? '查找中...' : '查找相似ECN'}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleRecommendSolutions}
                  disabled={loadingKnowledge}
                >
                  <Lightbulb className="w-4 h-4 mr-2" />
                  {loadingKnowledge ? '推荐中...' : '推荐解决方案'}
                </Button>
                {(ecn.status === 'COMPLETED' || ecn.status === 'CLOSED') && ecn.solution && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSolutionTemplateForm({
                        template_name: `${ecn.ecn_title} - 解决方案模板`,
                        template_category: ecn.ecn_type || '',
                        keywords: [],
                      })
                      setShowSolutionTemplateDialog(true)
                    }}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    创建解决方案模板
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 提取的解决方案 */}
          {extractedSolution && (
            <Card className="border-blue-200 bg-blue-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  提取的解决方案
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">解决方案描述</div>
                    <div className="p-3 bg-white rounded whitespace-pre-wrap">{extractedSolution.solution}</div>
                  </div>
                  {extractedSolution.solution_steps && extractedSolution.solution_steps.length > 0 && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">解决步骤</div>
                      <ol className="list-decimal list-inside space-y-1 p-3 bg-white rounded">
                        {extractedSolution.solution_steps.map((step, idx) => (
                          <li key={idx} className="text-sm">{step}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                  {extractedSolution.keywords && extractedSolution.keywords.length > 0 && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">关键词</div>
                      <div className="flex flex-wrap gap-2">
                        {extractedSolution.keywords.map((kw, idx) => (
                          <Badge key={idx} variant="outline">{kw}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 相似ECN */}
          {similarEcns.length > 0 && (
            <Card className="border-green-200 bg-green-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Search className="w-5 h-5 text-green-600" />
                  相似ECN
                  <Badge className="bg-green-500">{similarEcns.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {similarEcns.map((similar, idx) => (
                    <Card key={idx} className="p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="font-semibold">{similar.ecn_title}</div>
                          <div className="text-sm text-slate-500 font-mono">{similar.ecn_no}</div>
                        </div>
                        <div className="text-right">
                          <Badge className="bg-green-500">
                            相似度: {(similar.similarity_score * 100).toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                      <div className="text-sm text-slate-500 mb-2">
                        {similar.match_reasons?.join('、')}
                      </div>
                      {similar.solution && (
                        <div className="p-2 bg-slate-50 rounded text-sm line-clamp-2">
                          {similar.solution}
                        </div>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        <span>类型: {similar.ecn_type}</span>
                        <span>成本影响: ¥{similar.cost_impact?.toLocaleString()}</span>
                        <span>交期影响: {similar.schedule_impact_days}天</span>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 推荐解决方案 */}
          {solutionRecommendations.length > 0 && (
            <Card className="border-purple-200 bg-purple-50/30">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-purple-600" />
                  推荐解决方案
                  <Badge className="bg-purple-500">{solutionRecommendations.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {solutionRecommendations.map((rec, idx) => (
                    <Card key={idx} className="p-3">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <div className="font-semibold">{rec.template_name}</div>
                          <div className="text-sm text-slate-500">{rec.template_category}</div>
                        </div>
                        <div className="text-right">
                          <Badge className="bg-purple-500">
                            评分: {rec.score}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-sm text-slate-500 mb-2">
                        {rec.match_reasons?.join('、')}
                      </div>
                      <div className="p-2 bg-slate-50 rounded text-sm line-clamp-2 mb-2">
                        {rec.solution_description}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-500 mb-2">
                        <span>成功率: {rec.success_rate}%</span>
                        <span>使用次数: {rec.usage_count}</span>
                        <span>预估成本: ¥{rec.estimated_cost?.toLocaleString()}</span>
                        <span>预估天数: {rec.estimated_days}天</span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleApplySolutionTemplate(rec.template_id)}
                        className="w-full"
                      >
                        应用此方案
                      </Button>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 当前ECN的解决方案 */}
          {ecn.solution && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">当前解决方案</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-3 bg-slate-50 rounded whitespace-pre-wrap">{ecn.solution}</div>
                {ecn.solution_source && (
                  <div className="mt-2 text-sm text-slate-500">
                    来源: {
                      ecn.solution_source === 'MANUAL' ? '手动填写' :
                      ecn.solution_source === 'AUTO_EXTRACT' ? '自动提取' :
                      ecn.solution_source === 'KNOWLEDGE_BASE' ? '知识库' : ecn.solution_source
                    }
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 模块集成 */}
        <TabsContent value="integration" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">模块集成操作</CardTitle>
              <CardDescription>将ECN变更同步到相关模块</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* BOM同步 */}
              <Card className="border-2">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <GitBranch className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-semibold">同步到BOM</div>
                        <div className="text-sm text-slate-500">将物料变更同步到BOM清单</div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          const result = await ecnApi.syncToBOM(id)
                          const message = result.data?.message || result.message || '已同步到BOM'
                          alert(message)
                          await fetchECNDetail()
                        } catch (error) {
                          alert('同步失败: ' + (error.response?.data?.detail || error.message))
                        }
                      }}
                      disabled={ecn.status !== 'APPROVED' && ecn.status !== 'EXECUTING'}
                    >
                      执行同步
                    </Button>
                  </div>
                  {affectedMaterials.length > 0 && (
                    <div className="text-sm text-slate-500">
                      将同步 {affectedMaterials.length} 个物料变更
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 项目同步 */}
              <Card className="border-2">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <div className="font-semibold">同步到项目</div>
                        <div className="text-sm text-slate-500">更新项目成本和工期</div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          const result = await ecnApi.syncToProject(id)
                          const message = result.data?.message || result.message || '已同步到项目'
                          alert(message)
                          await fetchECNDetail()
                        } catch (error) {
                          alert('同步失败: ' + (error.response?.data?.detail || error.message))
                        }
                      }}
                      disabled={!ecn.project_id || (ecn.status !== 'APPROVED' && ecn.status !== 'EXECUTING')}
                    >
                      执行同步
                    </Button>
                  </div>
                  {ecn.cost_impact > 0 && (
                    <div className="text-sm text-slate-500">
                      将更新项目成本: +¥{ecn.cost_impact}
                    </div>
                  )}
                  {ecn.schedule_impact_days > 0 && (
                    <div className="text-sm text-slate-500">
                      将更新项目工期: +{ecn.schedule_impact_days} 天
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 采购同步 */}
              <Card className="border-2">
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                        <DollarSign className="w-5 h-5 text-orange-600" />
                      </div>
                      <div>
                        <div className="font-semibold">同步到采购</div>
                        <div className="text-sm text-slate-500">调整受影响的采购订单</div>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={async () => {
                        try {
                          const result = await ecnApi.syncToPurchase(id)
                          const message = result.data?.message || result.message || '已同步到采购'
                          alert(message)
                          await fetchECNDetail()
                        } catch (error) {
                          alert('同步失败: ' + (error.response?.data?.detail || error.message))
                        }
                      }}
                      disabled={ecn.status !== 'APPROVED' && ecn.status !== 'EXECUTING'}
                    >
                      执行同步
                    </Button>
                  </div>
                  {affectedOrders.filter(o => o.order_type === 'PURCHASE').length > 0 && (
                    <div className="text-sm text-slate-500">
                      将处理 {affectedOrders.filter(o => o.order_type === 'PURCHASE').length} 个采购订单
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* 批量同步 */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">批量同步</CardTitle>
                  <CardDescription>一次性同步到所有相关模块</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    className="w-full"
                    onClick={async () => {
                      if (!confirm('确认要同步到所有相关模块吗？')) return
                      try {
                        const results = []
                        
                        // 同步到BOM
                        if (affectedMaterials.length > 0) {
                          try {
                            await ecnApi.syncToBOM(id)
                            results.push('BOM同步成功')
                          } catch (e) {
                            results.push('BOM同步失败: ' + (e.response?.data?.detail || e.message))
                          }
                        }
                        
                        // 同步到项目
                        if (ecn.project_id) {
                          try {
                            await ecnApi.syncToProject(id)
                            results.push('项目同步成功')
                          } catch (e) {
                            results.push('项目同步失败: ' + (e.response?.data?.detail || e.message))
                          }
                        }
                        
                        // 同步到采购
                        if (affectedOrders.filter(o => o.order_type === 'PURCHASE').length > 0) {
                          try {
                            await ecnApi.syncToPurchase(id)
                            results.push('采购同步成功')
                          } catch (e) {
                            results.push('采购同步失败: ' + (e.response?.data?.detail || e.message))
                          }
                        }
                        
                        alert(results.join('\n'))
                        await fetchECNDetail()
                      } catch (error) {
                        alert('批量同步失败: ' + (error.response?.data?.detail || error.message))
                      }
                    }}
                    disabled={ecn.status !== 'APPROVED' && ecn.status !== 'EXECUTING'}
                  >
                    <Layers className="w-4 h-4 mr-2" />
                    批量同步所有模块
                  </Button>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 变更日志 - 时间线视图 */}
        <TabsContent value="logs" className="space-y-4">
          {/* 日志筛选 */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="搜索日志内容..."
                    value={logSearchKeyword}
                    onChange={(e) => setLogSearchKeyword(e.target.value)}
                    className="max-w-sm"
                  />
                </div>
                <Select value={logFilterType} onValueChange={setLogFilterType}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="日志类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部类型</SelectItem>
                    <SelectItem value="STATUS_CHANGE">状态变更</SelectItem>
                    <SelectItem value="APPROVAL">审批</SelectItem>
                    <SelectItem value="EVALUATION">评估</SelectItem>
                    <SelectItem value="OPERATION">操作</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {filteredLogs.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-slate-400">
                {logs.length === 0 ? '暂无变更日志' : '没有匹配的日志'}
              </CardContent>
            </Card>
          ) : (
            <div className="relative">
              {/* 时间线 */}
              <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />
              
              <div className="space-y-4">
                {filteredLogs.map((log, index) => (
                  <div key={log.id} className="relative flex items-start gap-4">
                    {/* 时间线节点 */}
                    <div className="relative z-10">
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-lg">
                        <History className="w-5 h-5" />
                      </div>
                    </div>
                    
                    {/* 日志卡片 */}
                    <Card className="flex-1 shadow-sm">
                      <CardContent className="pt-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="font-semibold">{log.log_action}</div>
                            <div className="text-sm text-slate-500">
                              {log.created_by_name || `用户${log.created_by || ''}`} · {formatDate(log.created_at)}
                            </div>
                          </div>
                          <Badge className="bg-slate-500">{log.log_type}</Badge>
                        </div>
                        {log.old_status && log.new_status && (
                          <div className="text-sm text-slate-600 mb-2">
                            状态变更: <span className="font-mono">{log.old_status}</span> → <span className="font-mono">{log.new_status}</span>
                          </div>
                        )}
                        {log.log_content && (
                          <div className="p-2 bg-slate-50 rounded text-sm">{log.log_content}</div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* 验证对话框 */}
      <Dialog open={showVerifyDialog} onOpenChange={setShowVerifyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>验证ECN执行结果</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">验证结果</label>
              <Select
                value={verifyForm.verify_result}
                onValueChange={(value) => setVerifyForm({ ...verifyForm, verify_result: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PASS">通过</SelectItem>
                  <SelectItem value="FAIL">不通过</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">验证说明</label>
              <Textarea
                value={verifyForm.verify_note}
                onChange={(e) => setVerifyForm({ ...verifyForm, verify_note: e.target.value })}
                placeholder="请输入验证说明"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVerifyDialog(false)}>
              取消
            </Button>
            <Button onClick={handleVerify}>确认验证</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 关闭对话框 */}
      <Dialog open={showCloseDialog} onOpenChange={setShowCloseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>关闭ECN</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">关闭说明</label>
              <Textarea
                value={closeForm.close_note}
                onChange={(e) => setCloseForm({ ...closeForm, close_note: e.target.value })}
                placeholder="请输入关闭说明"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCloseDialog(false)}>
              取消
            </Button>
            <Button onClick={handleClose}>确认关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 受影响物料对话框 */}
      <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingMaterial ? '编辑受影响物料' : '添加受影响物料'}</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">物料编码 *</label>
                <Input
                  value={materialForm.material_code}
                  onChange={(e) => setMaterialForm({ ...materialForm, material_code: e.target.value })}
                  placeholder="请输入物料编码"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">物料名称 *</label>
                <Input
                  value={materialForm.material_name}
                  onChange={(e) => setMaterialForm({ ...materialForm, material_name: e.target.value })}
                  placeholder="请输入物料名称"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">变更类型 *</label>
              <Select
                value={materialForm.change_type}
                onValueChange={(value) => setMaterialForm({ ...materialForm, change_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ADD">新增</SelectItem>
                  <SelectItem value="DELETE">删除</SelectItem>
                  <SelectItem value="UPDATE">修改</SelectItem>
                  <SelectItem value="REPLACE">替换</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">原数量</label>
                <Input
                  type="number"
                  value={materialForm.old_quantity}
                  onChange={(e) => setMaterialForm({ ...materialForm, old_quantity: e.target.value })}
                  placeholder="变更前的数量"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">新数量</label>
                <Input
                  type="number"
                  value={materialForm.new_quantity}
                  onChange={(e) => setMaterialForm({ ...materialForm, new_quantity: e.target.value })}
                  placeholder="变更后的数量"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">原规格</label>
                <Input
                  value={materialForm.old_specification}
                  onChange={(e) => setMaterialForm({ ...materialForm, old_specification: e.target.value })}
                  placeholder="变更前的规格"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">新规格</label>
                <Input
                  value={materialForm.new_specification}
                  onChange={(e) => setMaterialForm({ ...materialForm, new_specification: e.target.value })}
                  placeholder="变更后的规格"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">成本影响</label>
              <Input
                type="number"
                step="0.01"
                value={materialForm.cost_impact}
                onChange={(e) => setMaterialForm({ ...materialForm, cost_impact: parseFloat(e.target.value) || 0 })}
                placeholder="成本变化金额（正数表示增加，负数表示减少）"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">备注</label>
              <Textarea
                value={materialForm.remark}
                onChange={(e) => setMaterialForm({ ...materialForm, remark: e.target.value })}
                placeholder="请输入备注"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMaterialDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveMaterial}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建评估对话框 */}
      <Dialog open={showEvaluationDialog} onOpenChange={setShowEvaluationDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建评估</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">评估部门 *</label>
              <Input
                value={evaluationForm.eval_dept}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, eval_dept: e.target.value })}
                placeholder="如：机械部、电气部、采购部、PMC等"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">成本估算</label>
                <Input
                  type="number"
                  step="0.01"
                  value={evaluationForm.cost_estimate}
                  onChange={(e) => setEvaluationForm({ ...evaluationForm, cost_estimate: parseFloat(e.target.value) || 0 })}
                  placeholder="成本影响金额"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">工期估算（天）</label>
                <Input
                  type="number"
                  value={evaluationForm.schedule_estimate}
                  onChange={(e) => setEvaluationForm({ ...evaluationForm, schedule_estimate: parseInt(e.target.value) || 0 })}
                  placeholder="工期影响天数"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">影响分析</label>
              <Textarea
                value={evaluationForm.impact_analysis}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, impact_analysis: e.target.value })}
                placeholder="描述变更对本部门的影响"
                rows={4}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">资源需求</label>
              <Textarea
                value={evaluationForm.resource_requirement}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, resource_requirement: e.target.value })}
                placeholder="所需的人力、物料、设备等资源"
                rows={3}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">风险评估</label>
              <Textarea
                value={evaluationForm.risk_assessment}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, risk_assessment: e.target.value })}
                placeholder="评估变更可能带来的风险"
                rows={3}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">评估结论 *</label>
              <Select
                value={evaluationForm.eval_result}
                onValueChange={(value) => setEvaluationForm({ ...evaluationForm, eval_result: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="APPROVED">通过</SelectItem>
                  <SelectItem value="CONDITIONAL">有条件通过</SelectItem>
                  <SelectItem value="REJECTED">不通过</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">评估意见</label>
              <Textarea
                value={evaluationForm.eval_opinion}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, eval_opinion: e.target.value })}
                placeholder="评估意见和建议"
                rows={3}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">附加条件</label>
              <Textarea
                value={evaluationForm.conditions}
                onChange={(e) => setEvaluationForm({ ...evaluationForm, conditions: e.target.value })}
                placeholder="执行变更需要满足的条件"
                rows={2}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEvaluationDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateEvaluation}>创建评估</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建任务对话框 */}
      <Dialog open={showTaskDialog} onOpenChange={setShowTaskDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建执行任务</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">任务名称 *</label>
              <Input
                value={taskForm.task_name}
                onChange={(e) => setTaskForm({ ...taskForm, task_name: e.target.value })}
                placeholder="请输入任务名称"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">任务类型</label>
                <Select
                  value={taskForm.task_type}
                  onValueChange={(value) => setTaskForm({ ...taskForm, task_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择任务类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BOM_UPDATE">BOM更新</SelectItem>
                    <SelectItem value="DRAWING_UPDATE">图纸更新</SelectItem>
                    <SelectItem value="PROGRAM_UPDATE">程序更新</SelectItem>
                    <SelectItem value="PURCHASE_ADJUST">采购调整</SelectItem>
                    <SelectItem value="OTHER">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">责任部门</label>
                <Input
                  value={taskForm.task_dept}
                  onChange={(e) => setTaskForm({ ...taskForm, task_dept: e.target.value })}
                  placeholder="如：机械部、电气部等"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">任务描述</label>
              <Textarea
                value={taskForm.task_description}
                onChange={(e) => setTaskForm({ ...taskForm, task_description: e.target.value })}
                placeholder="详细描述任务内容和要求"
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">计划开始日期</label>
                <Input
                  type="date"
                  value={taskForm.planned_start}
                  onChange={(e) => setTaskForm({ ...taskForm, planned_start: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">计划结束日期</label>
                <Input
                  type="date"
                  value={taskForm.planned_end}
                  onChange={(e) => setTaskForm({ ...taskForm, planned_end: e.target.value })}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTaskDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateTask}>创建任务</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 受影响订单对话框 */}
      <Dialog open={showOrderDialog} onOpenChange={setShowOrderDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingOrder ? '编辑受影响订单' : '添加受影响订单'}</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">订单类型 *</label>
              <Select
                value={orderForm.order_type}
                onValueChange={(value) => setOrderForm({ ...orderForm, order_type: value, order_id: null, order_no: '' })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PURCHASE">采购订单</SelectItem>
                  <SelectItem value="OUTSOURCING">外协订单</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">订单号 *</label>
              <Input
                value={orderForm.order_no}
                onChange={(e) => setOrderForm({ ...orderForm, order_no: e.target.value })}
                placeholder="请输入订单号"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">影响描述</label>
              <Textarea
                value={orderForm.impact_description}
                onChange={(e) => setOrderForm({ ...orderForm, impact_description: e.target.value })}
                placeholder="描述ECN对订单的影响"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">处理方式</label>
              <Select
                value={orderForm.action_type}
                onValueChange={(value) => setOrderForm({ ...orderForm, action_type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择处理方式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CANCEL">取消订单</SelectItem>
                  <SelectItem value="MODIFY">修改订单</SelectItem>
                  <SelectItem value="ADD">新增订单</SelectItem>
                  <SelectItem value="DELAY">延期订单</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">处理说明</label>
              <Textarea
                value={orderForm.action_description}
                onChange={(e) => setOrderForm({ ...orderForm, action_description: e.target.value })}
                placeholder="请输入处理说明"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowOrderDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveOrder}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 责任分摊对话框 */}
      <Dialog open={showResponsibilityDialog} onOpenChange={setShowResponsibilityDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>责任分摊配置</DialogTitle>
            <CardDescription>配置多部门责任分摊比例，总和必须为100%</CardDescription>
          </DialogHeader>
          <DialogBody className="space-y-4">
            {responsibilityForm.map((resp, index) => (
              <Card key={index} className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">责任部门 {index + 1}</div>
                    {responsibilityForm.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newForm = responsibilityForm.filter((_, i) => i !== index)
                          setResponsibilityForm(newForm)
                        }}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">部门名称 *</label>
                      <Input
                        value={resp.dept}
                        onChange={(e) => {
                          const newForm = [...responsibilityForm]
                          newForm[index].dept = e.target.value
                          setResponsibilityForm(newForm)
                        }}
                        placeholder="如：机械部、电气部等"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">责任比例 (%) *</label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={resp.responsibility_ratio}
                        onChange={(e) => {
                          const newForm = [...responsibilityForm]
                          newForm[index].responsibility_ratio = parseFloat(e.target.value) || 0
                          setResponsibilityForm(newForm)
                        }}
                        placeholder="0-100"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">责任类型</label>
                    <Select
                      value={resp.responsibility_type}
                      onValueChange={(value) => {
                        const newForm = [...responsibilityForm]
                        newForm[index].responsibility_type = value
                        setResponsibilityForm(newForm)
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PRIMARY">主要责任</SelectItem>
                        <SelectItem value="SECONDARY">次要责任</SelectItem>
                        <SelectItem value="SUPPORT">支持责任</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">影响描述</label>
                    <Textarea
                      value={resp.impact_description}
                      onChange={(e) => {
                        const newForm = [...responsibilityForm]
                        newForm[index].impact_description = e.target.value
                        setResponsibilityForm(newForm)
                      }}
                      placeholder="描述该部门受到的影响"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">责任范围</label>
                    <Textarea
                      value={resp.responsibility_scope}
                      onChange={(e) => {
                        const newForm = [...responsibilityForm]
                        newForm[index].responsibility_scope = e.target.value
                        setResponsibilityForm(newForm)
                      }}
                      placeholder="描述该部门的责任范围"
                      rows={2}
                    />
                  </div>
                </div>
              </Card>
            ))}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setResponsibilityForm([...responsibilityForm, {
                  dept: '',
                  responsibility_ratio: 0,
                  responsibility_type: 'PRIMARY',
                  impact_description: '',
                  responsibility_scope: '',
                }])
              }}
            >
              <Plus className="w-4 h-4 mr-2" />
              添加责任部门
            </Button>
            <div className="pt-2 border-t">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">责任比例总和</span>
                <span className={`text-lg font-bold ${
                  Math.abs(responsibilityForm.reduce((sum, r) => sum + parseFloat(r.responsibility_ratio || 0), 0) - 100) < 0.01
                    ? 'text-green-600' : 'text-red-600'
                }`}>
                  {responsibilityForm.reduce((sum, r) => sum + parseFloat(r.responsibility_ratio || 0), 0).toFixed(2)}%
                </span>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResponsibilityDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateResponsibility}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* RCA分析对话框 */}
      <Dialog open={showRcaDialog} onOpenChange={setShowRcaDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>RCA分析（根本原因分析）</DialogTitle>
            <CardDescription>分析ECN变更的根本原因，用于问题预防和质量改进</CardDescription>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">根本原因类型</label>
              <Select
                value={rcaForm.root_cause}
                onValueChange={(value) => setRcaForm({ ...rcaForm, root_cause: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择根本原因类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DESIGN_ERROR">设计问题</SelectItem>
                  <SelectItem value="MATERIAL_DEFECT">物料缺陷</SelectItem>
                  <SelectItem value="PROCESS_ERROR">工艺问题</SelectItem>
                  <SelectItem value="EXTERNAL_FACTOR">外部因素</SelectItem>
                  <SelectItem value="COMMUNICATION">沟通问题</SelectItem>
                  <SelectItem value="PLANNING">计划问题</SelectItem>
                  <SelectItem value="OTHER">其他</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">原因分类</label>
              <Input
                value={rcaForm.root_cause_category}
                onChange={(e) => setRcaForm({ ...rcaForm, root_cause_category: e.target.value })}
                placeholder="如：设计缺陷、工艺不当、物料问题等"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">RCA分析内容 *</label>
              <Textarea
                value={rcaForm.root_cause_analysis}
                onChange={(e) => setRcaForm({ ...rcaForm, root_cause_analysis: e.target.value })}
                placeholder="详细分析变更的根本原因，包括：\n1. 问题描述\n2. 根本原因分析\n3. 为什么发生\n4. 如何预防"
                rows={10}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRcaDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveRcaAnalysis}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 创建解决方案模板对话框 */}
      <Dialog open={showSolutionTemplateDialog} onOpenChange={setShowSolutionTemplateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建解决方案模板</DialogTitle>
            <CardDescription>从当前ECN创建可复用的解决方案模板</CardDescription>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">模板名称 *</label>
              <Input
                value={solutionTemplateForm.template_name}
                onChange={(e) => setSolutionTemplateForm({ ...solutionTemplateForm, template_name: e.target.value })}
                placeholder="输入模板名称"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">模板分类</label>
              <Input
                value={solutionTemplateForm.template_category}
                onChange={(e) => setSolutionTemplateForm({ ...solutionTemplateForm, template_category: e.target.value })}
                placeholder="如：设计变更、物料变更等"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">关键词（用逗号分隔）</label>
              <Input
                value={solutionTemplateForm.keywords.join(', ')}
                onChange={(e) => {
                  const keywords = e.target.value.split(',').map(k => k.trim()).filter(k => k)
                  setSolutionTemplateForm({ ...solutionTemplateForm, keywords })
                }}
                placeholder="输入关键词，用逗号分隔"
              />
            </div>
            {ecn.solution && (
              <div>
                <label className="text-sm font-medium mb-2 block">解决方案内容</label>
                <div className="p-3 bg-slate-50 rounded text-sm whitespace-pre-wrap">{ecn.solution}</div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSolutionTemplateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateSolutionTemplate}>创建模板</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
