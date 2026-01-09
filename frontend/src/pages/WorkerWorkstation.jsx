/**
 * Worker Workstation Page - 工人工作台页面
 * Features: 我的工单、报工提交（开工/进度/完工）、我的报工记录
 */
import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Wrench,
  Clock,
  CheckCircle2,
  PlayCircle,
  PauseCircle,
  TrendingUp,
  FileText,
  User,
  Calendar,
  Package,
  AlertTriangle,
  RefreshCw,
  Plus,
  Camera,
  QrCode,
  Scan,
  X,
  Calculator,
  Zap,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
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
import { Progress } from '../components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs'
import { cn, formatDate } from '../lib/utils'
import { productionApi } from '../services/api'
import { toast } from '../components/ui/toast'

const statusConfigs = {
  PENDING: { label: '待派工', color: 'bg-slate-500' },
  ASSIGNED: { label: '已派工', color: 'bg-blue-500' },
  STARTED: { label: '已开始', color: 'bg-amber-500' },
  IN_PROGRESS: { label: '进行中', color: 'bg-amber-500' },
  PAUSED: { label: '已暂停', color: 'bg-purple-500' },
  COMPLETED: { label: '已完成', color: 'bg-emerald-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}

const reportTypeConfigs = {
  START: { label: '开工', color: 'bg-blue-500' },
  PROGRESS: { label: '进度', color: 'bg-amber-500' },
  COMPLETE: { label: '完工', color: 'bg-emerald-500' },
}

export default function WorkerWorkstation() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [myWorkOrders, setMyWorkOrders] = useState([])
  const [myReports, setMyReports] = useState([])
  const [workerId, setWorkerId] = useState(null)
  const [error, setError] = useState(null)
  // Filters
  const [filterStatus, setFilterStatus] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('created_at') // created_at, status, plan_end_date
  const [sortOrder, setSortOrder] = useState('desc') // asc, desc
  // Dialogs
  const [showStartDialog, setShowStartDialog] = useState(false)
  const [showProgressDialog, setShowProgressDialog] = useState(false)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState(null)
  // Form states
  const [startData, setStartData] = useState({
    report_note: '',
  })
  const [progressData, setProgressData] = useState({
    progress_percent: 0,
    work_hours: 0,
    report_note: '',
  })
  const [completeData, setCompleteData] = useState({
    completed_qty: 0,
    qualified_qty: 0,
    defect_qty: 0,
    work_hours: 0,
    report_note: '',
  })
  // 扫码相关
  const [showScanDialog, setShowScanDialog] = useState(false)
  const [scanInput, setScanInput] = useState('')
  // 拍照相关
  const [photos, setPhotos] = useState([])
  const [recognizing, setRecognizing] = useState(false)
  // 快捷操作
  const [quickStartOrder, setQuickStartOrder] = useState(null)

  // 获取当前用户对应的 worker_id
  useEffect(() => {
    const fetchWorkerId = async () => {
      try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
        if (!currentUser.id) {
          return
        }
        
        // 获取所有 workers，查找当前用户对应的 worker
        const res = await productionApi.workers.list({ page_size: 1000 })
        const workers = res.data?.items || res.data || []
        const worker = workers.find(w => w.user_id === currentUser.id)
        
        if (worker) {
          setWorkerId(worker.id)
        } else {
          const message = '当前用户未关联工人信息，无法查看工单'
          setError(message)
          toast.warning(message)
        }
      } catch (error) {
        const message = '获取工人信息失败: ' + (error.response?.data?.detail || error.message)
        setError(message)
        toast.error(message)
      }
    }
    
    fetchWorkerId()
  }, [])

  useEffect(() => {
    if (workerId !== null) {
      fetchMyWorkOrders()
      fetchMyReports()
    }
  }, [filterStatus, workerId])

  // 快捷键支持
  useEffect(() => {
    const handleKeyDown = (e) => {
      // ESC 关闭对话框
      if (e.key === 'Escape') {
        if (showStartDialog) setShowStartDialog(false)
        if (showProgressDialog) setShowProgressDialog(false)
        if (showCompleteDialog) setShowCompleteDialog(false)
        if (showScanDialog) setShowScanDialog(false)
      }
      // Ctrl/Cmd + K 打开搜索
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        // 可以添加搜索框聚焦逻辑
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showStartDialog, showProgressDialog, showCompleteDialog, showScanDialog])

  const fetchMyWorkOrders = async () => {
    if (!workerId) {
      setMyWorkOrders([])
      setLoading(false)
      return
    }
    
    try {
      setLoading(true)
      
      // 如果指定了状态筛选，直接使用该状态
      if (filterStatus) {
        const params = { 
          page: 1, 
          page_size: 100,
          assigned_to: workerId,
          status: filterStatus,
        }
        const res = await productionApi.workOrders.list(params)
        const orders = res.data?.items || res.data || []
        setMyWorkOrders(orders)
      } else {
        // 如果没有指定状态筛选，获取所有已分配给当前工人的工单
        // 然后过滤出进行中的工单（ASSIGNED, STARTED, IN_PROGRESS, PAUSED）
        const params = { 
          page: 1, 
          page_size: 1000, // 获取更多数据以确保不遗漏
          assigned_to: workerId,
        }
        const res = await productionApi.workOrders.list(params)
        const allOrders = res.data?.items || res.data || []
        
        // 过滤出进行中的工单
        const activeOrders = allOrders.filter(order => 
          order.status === 'ASSIGNED' || 
          order.status === 'STARTED' || 
          order.status === 'IN_PROGRESS' ||
          order.status === 'PAUSED' ||
          order.status === 'COMPLETED' // 也显示已完成的工单，方便查看历史
        )
        setMyWorkOrders(activeOrders)
      }
    } catch (error) {
      setMyWorkOrders([])
      const message = '获取工单列表失败: ' + (error.response?.data?.detail || error.message)
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const fetchMyReports = async () => {
    try {
      const res = await productionApi.workReports.my({ page: 1, page_size: 100 })
      const reports = res.data?.items || res.data || []
      // 按时间倒序排序
      reports.sort((a, b) => {
        const timeA = new Date(a.report_time || a.created_at || 0).getTime()
        const timeB = new Date(b.report_time || b.created_at || 0).getTime()
        return timeB - timeA
      })
      setMyReports(reports)
    } catch (error) {
      toast.error('获取报工记录失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 扫码查找工单
  const handleScanWorkOrder = async (workOrderNo) => {
    if (!workOrderNo || !workOrderNo.trim()) {
      toast.warning('请输入工单号')
      return null
    }
    
    try {
      const res = await productionApi.workOrders.list({ search: workOrderNo.trim(), page_size: 10 })
      const orders = res.data?.items || res.data || []
      const order = orders.find(o => o.work_order_no === workOrderNo.trim())
      
      if (!order) {
        toast.error('未找到工单: ' + workOrderNo)
        return null
      }
      
      // 检查工单是否属于当前用户
      if (workerId && order.assigned_to !== workerId) {
        toast.warning('该工单不属于您，无法操作')
        return null
      }
      
      if (order.status !== 'ASSIGNED') {
        toast.warning(`工单状态为"${statusConfigs[order.status]?.label}"，无法开工`)
        return null
      }
      
      return order
    } catch (error) {
      toast.error('查找工单失败: ' + (error.response?.data?.detail || error.message))
      return null
    }
  }

  // 快速开工（无需填写）
  const handleQuickStart = async (order) => {
    if (!order) return
    if (submitting) return // 防止重复提交
    
    try {
      setSubmitting(true)
      await productionApi.workReports.start({
        work_order_id: order.id,
        report_note: '',
      })
      await fetchMyWorkOrders()
      await fetchMyReports()
      toast.success('开工成功')
    } catch (error) {
      toast.error('开工失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  const handleStart = async () => {
    if (!selectedOrder) return
    if (submitting) return // 防止重复提交
    
    try {
      setSubmitting(true)
      await productionApi.workReports.start({
        work_order_id: selectedOrder.id,
        report_note: startData.report_note || '',
      })
      setShowStartDialog(false)
      setStartData({ report_note: '' })
      await fetchMyWorkOrders()
      await fetchMyReports()
      toast.success('开工成功')
    } catch (error) {
      toast.error('开工失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  // 自动计算进度（基于完成数量）
  const calculateProgress = (completedQty, planQty) => {
    if (!planQty || planQty === 0) return 0
    return Math.round((completedQty / planQty) * 100)
  }

  // 自动计算工时（基于开始时间）
  const calculateWorkHours = (startTime) => {
    if (!startTime) return 0
    const start = new Date(startTime)
    const now = new Date()
    const diffMs = now - start
    const diffHours = diffMs / (1000 * 60 * 60)
    return Math.round(diffHours * 10) / 10 // 保留1位小数
  }

  // 拍照识别数量（OCR功能）
  // 当前为模拟实现，实际使用时需要集成真实的OCR服务
  // 集成步骤：
  // 1. 在后端创建OCR API端点（如 /api/v1/ocr/recognize-quantity）
  // 2. 集成OCR服务（如百度OCR、腾讯OCR、阿里云OCR等）
  // 3. 将图片发送到后端，后端调用OCR服务识别
  // 4. 返回识别结果（完成数量、合格数量等）
  const handlePhotoRecognition = async (file) => {
    setRecognizing(true)
    try {
      // 方案1：如果有后端OCR API，使用以下代码
      // const formData = new FormData()
      // formData.append('file', file)
      // formData.append('work_order_id', selectedOrder?.id)
      // const res = await productionApi.ocr.recognizeQuantity(formData)
      // const { completed_qty, qualified_qty } = res.data
      
      // 方案2：当前模拟实现（用于演示）
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const planQty = selectedOrder?.plan_qty || 10
      const mockRecognizedQty = Math.floor(Math.random() * planQty) + 1
      const mockQualifiedQty = mockRecognizedQty - Math.floor(Math.random() * 2)
      
      setCompleteData(prev => ({
        ...prev,
        completed_qty: Math.min(mockRecognizedQty, planQty),
        qualified_qty: Math.max(0, Math.min(mockQualifiedQty, mockRecognizedQty)),
      }))
      
      toast.success(`识别完成：完成数量 ${Math.min(mockRecognizedQty, planQty)}（模拟数据）`)
    } catch (error) {
      toast.error('图片识别失败，请手动输入数量')
    } finally {
      setRecognizing(false)
    }
  }

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    // 创建预览
    const reader = new FileReader()
    reader.onload = (event) => {
      const photoUrl = event.target.result
      setPhotos(prev => [...prev, { url: photoUrl, file }])
      
      // 自动识别数量
      if (selectedOrder) {
        handlePhotoRecognition(file)
      }
    }
    reader.readAsDataURL(file)
  }

  const handleProgress = async () => {
    if (!selectedOrder) return
    if (submitting) return // 防止重复提交
    
    // 如果只填写了完成数量，自动计算进度
    let progressPercent = progressData.progress_percent
    if (!progressPercent && selectedOrder.plan_qty) {
      // 可以基于已完成数量计算
      progressPercent = selectedOrder.progress || 0
    }
    
    // 如果只填写了进度，自动计算工时（基于开始时间）
    let workHours = progressData.work_hours
    if (!workHours && selectedOrder.actual_start_time) {
      workHours = calculateWorkHours(selectedOrder.actual_start_time)
    }
    
    // 验证：至少需要填写进度或工时
    if (!progressPercent && !workHours) {
      toast.warning('请填写进度或工时')
      return
    }
    
    // 验证进度范围
    if (progressPercent < 0 || progressPercent > 100) {
      toast.warning('进度必须在 0-100% 之间')
      return
    }
    
    try {
      setSubmitting(true)
      await productionApi.workReports.progress({
        work_order_id: selectedOrder.id,
        progress_percent: progressPercent || 0,
        work_hours: workHours || 0,
        report_note: progressData.report_note || '',
      })
      setShowProgressDialog(false)
      setProgressData({
        progress_percent: 0,
        work_hours: 0,
        report_note: '',
      })
      await fetchMyWorkOrders()
      await fetchMyReports()
      toast.success('进度上报成功')
    } catch (error) {
      toast.error('进度上报失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  // 快捷数量选择
  const handleQuickQuantity = (type, value) => {
    if (!selectedOrder) return
    const planQty = selectedOrder.plan_qty || 0
    
    if (type === 'completed') {
      const qty = value === 'all' ? planQty : value
      const progress = calculateProgress(qty, planQty)
      setCompleteData(prev => ({
        ...prev,
        completed_qty: qty,
        qualified_qty: qty, // 默认全部合格
        defect_qty: 0,
      }))
      // 同时更新进度
      setProgressData(prev => ({
        ...prev,
        progress_percent: progress,
      }))
    } else if (type === 'qualified') {
      setCompleteData(prev => ({
        ...prev,
        qualified_qty: value === 'all' ? prev.completed_qty : value,
        defect_qty: prev.completed_qty - (value === 'all' ? prev.completed_qty : value),
      }))
    }
  }

  const handleComplete = async () => {
    if (!selectedOrder) return
    if (submitting) return // 防止重复提交
    
    // 表单验证
    if (!completeData.completed_qty || completeData.completed_qty <= 0) {
      toast.warning('请填写完成数量')
      return
    }
    
    if (completeData.completed_qty > selectedOrder.plan_qty) {
      toast.warning(`完成数量不能超过计划数量 ${selectedOrder.plan_qty}`)
      return
    }
    
    if (completeData.qualified_qty > completeData.completed_qty) {
      toast.warning('合格数量不能超过完成数量')
      return
    }
    
    if (completeData.qualified_qty < 0) {
      toast.warning('合格数量不能为负数')
      return
    }
    
    // 自动计算不良数量
    const defectQty = completeData.defect_qty || (completeData.completed_qty - completeData.qualified_qty)
    
    // 自动计算工时（如果未填写）
    let workHours = completeData.work_hours
    if (!workHours && selectedOrder.actual_start_time) {
      workHours = calculateWorkHours(selectedOrder.actual_start_time)
    }
    
    if (!workHours || workHours <= 0) {
      toast.warning('请填写工时')
      return
    }
    
    try {
      setSubmitting(true)
      await productionApi.workReports.complete({
        work_order_id: selectedOrder.id,
        completed_qty: completeData.completed_qty,
        qualified_qty: completeData.qualified_qty,
        defect_qty: defectQty,
        work_hours: workHours,
        report_note: completeData.report_note || '',
      })
      setShowCompleteDialog(false)
      setCompleteData({
        completed_qty: 0,
        qualified_qty: 0,
        defect_qty: 0,
        work_hours: 0,
        report_note: '',
      })
      setPhotos([])
      await fetchMyWorkOrders()
      await fetchMyReports()
      toast.success('完工报工成功')
    } catch (error) {
      toast.error('完工报工失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSubmitting(false)
    }
  }

  // 过滤和排序工单
  const filteredAndSortedOrders = useMemo(() => {
    let filtered = [...myWorkOrders]

    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(order => 
        order.work_order_no?.toLowerCase().includes(query) ||
        order.task_name?.toLowerCase().includes(query) ||
        order.project_name?.toLowerCase().includes(query) ||
        order.workshop_name?.toLowerCase().includes(query) ||
        order.workstation_name?.toLowerCase().includes(query)
      )
    }

    // 排序
    filtered.sort((a, b) => {
      let aValue, bValue
      
      switch (sortBy) {
        case 'created_at':
          aValue = new Date(a.created_at || 0).getTime()
          bValue = new Date(b.created_at || 0).getTime()
          break
        case 'plan_end_date':
          aValue = new Date(a.plan_end_date || 0).getTime()
          bValue = new Date(b.plan_end_date || 0).getTime()
          break
        case 'status':
          aValue = a.status || ''
          bValue = b.status || ''
          break
        case 'progress':
          aValue = a.progress || 0
          bValue = b.progress || 0
          break
        default:
          return 0
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0
      } else {
        return aValue < bValue ? 1 : aValue > bValue ? -1 : 0
      }
    })

    return filtered
  }, [myWorkOrders, searchQuery, sortBy, sortOrder])

  const stats = useMemo(() => {
    return {
      total: myWorkOrders.length,
      assigned: myWorkOrders.filter(o => o.status === 'ASSIGNED').length,
      inProgress: myWorkOrders.filter(o => o.status === 'STARTED' || o.status === 'IN_PROGRESS').length,
      completed: myWorkOrders.filter(o => o.status === 'COMPLETED').length,
    }
  }, [myWorkOrders])

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="我的工作台"
        description="查看我的工单、提交报工、查看报工记录"
      />
      {/* 快捷操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => setShowScanDialog(true)}
                className="flex items-center gap-2"
                title="扫码或输入工单号快速开工"
              >
                <QrCode className="w-4 h-4" />
                扫码开工
              </Button>
              <Button
                variant="outline"
                onClick={fetchMyWorkOrders}
                disabled={loading}
                className="flex items-center gap-2"
                title="刷新工单列表"
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                刷新
              </Button>
            </div>
            {workerId && (
              <div className="text-xs text-slate-500">
                提示：按 ESC 关闭对话框 | 使用搜索框快速查找工单
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">我的工单</div>
                <div className="text-2xl font-bold">{stats.total}</div>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">待开工</div>
                <div className="text-2xl font-bold text-blue-600">{stats.assigned}</div>
              </div>
              <Clock className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">进行中</div>
                <div className="text-2xl font-bold text-amber-600">{stats.inProgress}</div>
              </div>
              <PlayCircle className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">已完成</div>
                <div className="text-2xl font-bold text-emerald-600">{stats.completed}</div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Tabs */}
      <Tabs defaultValue="orders" className="space-y-4">
        <TabsList>
          <TabsTrigger value="orders">我的工单</TabsTrigger>
          <TabsTrigger value="reports">我的报工</TabsTrigger>
        </TabsList>
        {/* My Work Orders */}
        <TabsContent value="orders" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>我的工单</CardTitle>
                  <CardDescription>
                    共 {filteredAndSortedOrders.length} 个工单
                    {searchQuery && ` (搜索: ${searchQuery})`}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      type="text"
                      placeholder="搜索工单号、任务名称..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 w-64"
                    />
                  </div>
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="筛选状态" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="ASSIGNED">待开工</SelectItem>
                      <SelectItem value="STARTED">已开始</SelectItem>
                      <SelectItem value="IN_PROGRESS">进行中</SelectItem>
                      <SelectItem value="PAUSED">已暂停</SelectItem>
                      <SelectItem value="COMPLETED">已完成</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="排序" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="created_at">创建时间</SelectItem>
                      <SelectItem value="plan_end_date">计划完成</SelectItem>
                      <SelectItem value="status">状态</SelectItem>
                      <SelectItem value="progress">进度</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    title={sortOrder === 'asc' ? '升序' : '降序'}
                  >
                    {sortOrder === 'asc' ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                  </Button>
                  <Button variant="outline" size="sm" onClick={fetchMyWorkOrders} disabled={loading}>
                    <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {error && !loading && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}
              {loading ? (
                <div className="text-center py-8 text-slate-400">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  加载中...
                </div>
              ) : myWorkOrders.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <Package className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p className="text-slate-500">暂无工单</p>
                  {workerId === null && (
                    <p className="text-xs text-slate-400 mt-2">请先关联工人信息</p>
                  )}
                </div>
              ) : filteredAndSortedOrders.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <Search className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p className="text-slate-500">未找到匹配的工单</p>
                  {searchQuery && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSearchQuery('')}
                      className="mt-2"
                    >
                      清除搜索
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredAndSortedOrders.map((order) => (
                    <Card key={order.id} className="hover:bg-slate-50 transition-colors">
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-3">
                              <Badge className={statusConfigs[order.status]?.color || 'bg-slate-500'}>
                                {statusConfigs[order.status]?.label || order.status}
                              </Badge>
                              <span className="font-mono text-sm">{order.work_order_no}</span>
                              <span className="font-medium">{order.task_name}</span>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                              <div>
                                <div className="text-slate-500">项目</div>
                                <div className="font-medium">{order.project_name || '-'}</div>
                              </div>
                              <div>
                                <div className="text-slate-500">车间/工位</div>
                                <div>{order.workshop_name || '-'} / {order.workstation_name || '-'}</div>
                              </div>
                              <div>
                                <div className="text-slate-500">计划数量</div>
                                <div className="font-medium">{order.plan_qty || 0}</div>
                              </div>
                              <div>
                                <div className="text-slate-500">完成数量</div>
                                <div className="font-medium text-emerald-600">
                                  {order.completed_qty || 0} / {order.plan_qty || 0}
                                </div>
                              </div>
                            </div>
                            {(order.plan_start_date || order.plan_end_date) && (
                              <div className="flex items-center gap-4 text-xs text-slate-500 mb-2">
                                {order.plan_start_date && (
                                  <div className="flex items-center gap-1">
                                    <Calendar className="w-3 h-3" />
                                    <span>计划: {formatDate(order.plan_start_date)}</span>
                                  </div>
                                )}
                                {order.plan_end_date && (
                                  <div className="flex items-center gap-1">
                                    <span>至 {formatDate(order.plan_end_date)}</span>
                                  </div>
                                )}
                              </div>
                            )}
                            {order.progress !== undefined && (
                              <div className="space-y-1">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-slate-500">进度</span>
                                  <span className="font-medium">{order.progress}%</span>
                                </div>
                                <Progress value={order.progress} className="h-2" />
                              </div>
                            )}
                          </div>
                          <div className="ml-4 flex flex-col gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => navigate(`/work-orders/${order.id}`)}
                            >
                              <FileText className="w-4 h-4 mr-1" />
                              详情
                            </Button>
                            {order.status === 'ASSIGNED' && (
                              <>
                                <Button
                                  size="sm"
                                  onClick={() => handleQuickStart(order)}
                                  disabled={submitting}
                                  className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50"
                                >
                                  <Zap className="w-4 h-4 mr-1" />
                                  {submitting ? '处理中...' : '快速开工'}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedOrder(order)
                                    setShowStartDialog(true)
                                  }}
                                >
                                  <PlayCircle className="w-4 h-4 mr-1" />
                                  开工
                                </Button>
                              </>
                            )}
                            {(order.status === 'STARTED' || order.status === 'IN_PROGRESS' || order.status === 'PAUSED') && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedOrder(order)
                                    // 自动填充：从工单带出当前进度和已用工时
                                    const autoProgress = order.progress || 0
                                    const autoHours = order.actual_start_time 
                                      ? calculateWorkHours(order.actual_start_time)
                                      : 0
                                    setProgressData({
                                      progress_percent: autoProgress,
                                      work_hours: autoHours,
                                      report_note: '',
                                    })
                                    setShowProgressDialog(true)
                                  }}
                                >
                                  <TrendingUp className="w-4 h-4 mr-1" />
                                  报进度
                                </Button>
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setSelectedOrder(order)
                                    // 自动填充：从工单带出已完成数量和工时
                                    const autoHours = order.actual_start_time 
                                      ? calculateWorkHours(order.actual_start_time)
                                      : 0
                                    setCompleteData({
                                      completed_qty: order.completed_qty || 0,
                                      qualified_qty: order.qualified_qty || order.completed_qty || 0,
                                      defect_qty: 0,
                                      work_hours: autoHours,
                                      report_note: '',
                                    })
                                    setPhotos([])
                                    setShowCompleteDialog(true)
                                  }}
                                >
                                  <CheckCircle2 className="w-4 h-4 mr-1" />
                                  完工
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        {/* My Reports */}
        <TabsContent value="reports" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>我的报工记录</CardTitle>
                  <CardDescription>
                    共 {myReports.length} 条报工记录
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchMyReports} disabled={loading}>
                  <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {myReports.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p className="text-slate-500">暂无报工记录</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>报工单号</TableHead>
                      <TableHead>工单号</TableHead>
                      <TableHead>报工类型</TableHead>
                      <TableHead>报工时间</TableHead>
                      <TableHead>进度</TableHead>
                      <TableHead>完成数量</TableHead>
                      <TableHead>合格数量</TableHead>
                      <TableHead>不良数量</TableHead>
                      <TableHead>工时</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>备注</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {myReports.map((report) => (
                      <TableRow key={report.id}>
                        <TableCell className="font-mono text-sm">
                          {report.report_no}
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {report.work_order_no || '-'}
                        </TableCell>
                        <TableCell>
                          <Badge className={reportTypeConfigs[report.report_type]?.color || 'bg-slate-500'}>
                            {reportTypeConfigs[report.report_type]?.label || report.report_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-500 text-sm">
                          {report.report_time ? (
                            <div>
                              <div>{formatDate(report.report_time)}</div>
                              {report.report_time && (
                                <div className="text-xs text-slate-400">
                                  {new Date(report.report_time).toLocaleTimeString('zh-CN', { 
                                    hour: '2-digit', 
                                    minute: '2-digit' 
                                  })}
                                </div>
                              )}
                            </div>
                          ) : '-'}
                        </TableCell>
                        <TableCell>
                          {report.progress_percent !== undefined ? `${report.progress_percent}%` : '-'}
                        </TableCell>
                        <TableCell className="font-medium">
                          {report.completed_qty || 0}
                        </TableCell>
                        <TableCell className="text-emerald-600 font-medium">
                          {report.qualified_qty || 0}
                        </TableCell>
                        <TableCell className="text-red-600 font-medium">
                          {report.defect_qty || 0}
                        </TableCell>
                        <TableCell>
                          {report.work_hours ? `${report.work_hours.toFixed(1)}h` : '-'}
                        </TableCell>
                        <TableCell>
                          <Badge 
                            variant={report.status === 'APPROVED' ? 'default' : 'outline'}
                            className={report.status === 'APPROVED' ? 'bg-emerald-500' : ''}
                          >
                            {report.status === 'APPROVED' ? '已审批' : '待审批'}
                          </Badge>
                          {report.approved_at && (
                            <div className="text-xs text-slate-400 mt-1">
                              {formatDate(report.approved_at)}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-slate-500 max-w-xs truncate" title={report.report_note || ''}>
                          {report.report_note || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
      {/* Start Dialog */}
      <Dialog open={showStartDialog} onOpenChange={setShowStartDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>开工报工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">{selectedOrder.work_order_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">任务名称</div>
                  <div className="font-medium">{selectedOrder.task_name}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">开工说明</label>
                  <textarea
                    className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={startData.report_note}
                    onChange={(e) => setStartData({ ...startData, report_note: e.target.value })}
                    placeholder="开工说明（可选）..."
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowStartDialog(false)}>
              取消
            </Button>
            <Button onClick={handleStart} disabled={submitting}>
              <PlayCircle className="w-4 h-4 mr-2" />
              {submitting ? '提交中...' : '确认开工'}
            </Button>
            <div className="text-xs text-slate-400 mt-2">
              提示：按 ESC 键可关闭对话框
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Progress Dialog */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>进度报工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">{selectedOrder.work_order_no}</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">进度 (%)</label>
                    <div className="flex gap-2">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={progressData.progress_percent}
                        onChange={(e) => setProgressData({ ...progressData, progress_percent: parseInt(e.target.value) || 0 })}
                        placeholder="0-100"
                        className="flex-1"
                      />
                      <div className="flex gap-1">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setProgressData({ ...progressData, progress_percent: 25 })}
                        >
                          25%
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setProgressData({ ...progressData, progress_percent: 50 })}
                        >
                          50%
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setProgressData({ ...progressData, progress_percent: 75 })}
                        >
                          75%
                        </Button>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      工时 (小时)
                      {selectedOrder?.actual_start_time && (
                        <span className="text-xs text-slate-500 ml-2">
                          已用: {calculateWorkHours(selectedOrder.actual_start_time)}h
                        </span>
                      )}
                    </label>
                    <Input
                      type="number"
                      min="0"
                      step="0.5"
                      value={progressData.work_hours}
                      onChange={(e) => setProgressData({ ...progressData, work_hours: parseFloat(e.target.value) || 0 })}
                      placeholder="0"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">进度说明</label>
                  <textarea
                    className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={progressData.report_note}
                    onChange={(e) => setProgressData({ ...progressData, report_note: e.target.value })}
                    placeholder="进度说明（可选）..."
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowProgressDialog(false)}>
              取消
            </Button>
            <Button onClick={handleProgress} disabled={submitting}>
              <TrendingUp className="w-4 h-4 mr-2" />
              {submitting ? '提交中...' : '提交进度'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>完工报工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedOrder && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">{selectedOrder.work_order_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划数量</div>
                  <div className="font-medium">{selectedOrder.plan_qty || 0}</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">完成数量 *</label>
                    <div className="space-y-2">
                      <Input
                        type="number"
                        min="0"
                        max={selectedOrder.plan_qty || 0}
                        value={completeData.completed_qty}
                        onChange={(e) => {
                          const qty = parseInt(e.target.value) || 0
                          setCompleteData({ 
                            ...completeData, 
                            completed_qty: qty,
                            qualified_qty: Math.min(completeData.qualified_qty, qty)
                          })
                        }}
                        placeholder="0"
                      />
                      <div className="flex gap-1">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickQuantity('completed', selectedOrder.plan_qty)}
                        >
                          全部完成
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleQuickQuantity('completed', Math.floor((selectedOrder.plan_qty || 0) / 2))}
                        >
                          一半
                        </Button>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">合格数量</label>
                    <div className="space-y-2">
                      <Input
                        type="number"
                        min="0"
                        max={completeData.completed_qty}
                        value={completeData.qualified_qty}
                        onChange={(e) => {
                          const qty = parseInt(e.target.value) || 0
                          setCompleteData({ 
                            ...completeData, 
                            qualified_qty: qty,
                            defect_qty: completeData.completed_qty - qty
                          })
                        }}
                        placeholder="0"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickQuantity('qualified', 'all')}
                      >
                        全部合格
                      </Button>
                    </div>
                  </div>
                </div>
                {/* 拍照识别数量 */}
                <div>
                  <label className="text-sm font-medium mb-2 block">拍照识别数量（可选）</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handlePhotoUpload}
                      className="hidden"
                      id="photo-upload-complete"
                    />
                    <label
                      htmlFor="photo-upload-complete"
                      className="flex items-center gap-2 px-4 py-2 border rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
                    >
                      <Camera className="w-4 h-4" />
                      {recognizing ? '识别中...' : '拍照识别'}
                    </label>
                    {photos.length > 0 && (
                      <div className="flex gap-2">
                        {photos.map((photo, idx) => (
                          <div key={idx} className="relative w-16 h-16 rounded overflow-hidden">
                            <img src={photo.url} alt={`Photo ${idx + 1}`} className="w-full h-full object-cover" />
                            <button
                              type="button"
                              onClick={() => setPhotos(prev => prev.filter((_, i) => i !== idx))}
                              className="absolute top-0 right-0 p-0.5 bg-red-500 text-white rounded-bl"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                {/* 自动计算的不良数量 */}
                {completeData.completed_qty > 0 && (
                  <div className="text-sm text-slate-500">
                    不良数量: {completeData.completed_qty - completeData.qualified_qty}（自动计算）
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    工时 (小时)
                    {selectedOrder?.actual_start_time && (
                      <span className="text-xs text-slate-500 ml-2">
                        已用: {calculateWorkHours(selectedOrder.actual_start_time)}h（自动填充）
                      </span>
                    )}
                  </label>
                  <Input
                    type="number"
                    min="0"
                    step="0.5"
                    value={completeData.work_hours}
                    onChange={(e) => setCompleteData({ ...completeData, work_hours: parseFloat(e.target.value) || 0 })}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">完工说明</label>
                  <textarea
                    className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={completeData.report_note}
                    onChange={(e) => setCompleteData({ ...completeData, report_note: e.target.value })}
                    placeholder="完工说明（可选）..."
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)}>
              取消
            </Button>
            <Button onClick={handleComplete} disabled={submitting}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              {submitting ? '提交中...' : '确认完工'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* 扫码对话框 */}
      <Dialog open={showScanDialog} onOpenChange={setShowScanDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>扫码开工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">工单号</label>
                <div className="flex gap-2">
                  <Input
                    value={scanInput}
                    onChange={(e) => setScanInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleScanWorkOrder(scanInput).then(order => {
                          if (order) {
                            handleQuickStart(order)
                            setShowScanDialog(false)
                            setScanInput('')
                          }
                        })
                      }
                    }}
                    placeholder="扫描或输入工单号"
                    autoFocus
                  />
                  <Button
                    onClick={async () => {
                      const order = await handleScanWorkOrder(scanInput)
                      if (order) {
                        await handleQuickStart(order)
                        setShowScanDialog(false)
                        setScanInput('')
                      }
                    }}
                    disabled={submitting || !scanInput.trim()}
                  >
                    <Scan className="w-4 h-4 mr-2" />
                    {submitting ? '处理中...' : '确认'}
                  </Button>
                </div>
              </div>
              <div className="text-xs text-slate-500 space-y-1">
                <div>提示：扫描工单二维码或手动输入工单号</div>
                <div>按回车键或点击确认按钮快速开工</div>
                <div>按 ESC 键关闭对话框</div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowScanDialog(false)
              setScanInput('')
            }}>
              取消
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}


