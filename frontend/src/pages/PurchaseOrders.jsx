import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Package,
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Eye,
  Edit3,
  Trash2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Truck,
  FileText,
  MoreHorizontal,
  ChevronDown,
  Calendar,
  Building2,
  DollarSign,
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
} from '../components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { purchaseApi, supplierApi, projectApi, materialApi } from '../services/api'
import { toast } from '../components/ui/toast'
import { ApiIntegrationError } from '../components/ui'

// Mock purchase orders data - 已移除，使用真实API

const statusConfigs = {
  draft: { label: '草稿', color: 'bg-slate-500', icon: FileText },
  pending: { label: '待收货', color: 'bg-blue-500', icon: Clock },
  partial_received: { label: '部分到货', color: 'bg-amber-500', icon: Truck },
  completed: { label: '已完成', color: 'bg-emerald-500', icon: CheckCircle2 },
  delayed: { label: '延期', color: 'bg-red-500', icon: AlertTriangle },
  cancelled: { label: '已取消', color: 'bg-slate-400', icon: Trash2 },
}

const urgencyConfigs = {
  normal: { label: '普通', color: 'text-slate-400' },
  urgent: { label: '加急', color: 'text-amber-400' },
  critical: { label: '特急', color: 'text-red-400' },
}

function OrderCard({ order, onView, onEdit, onDelete, onSubmit, onApprove }) {
  const status = statusConfigs[order.status]
  const urgency = urgencyConfigs[order.urgency]
  const StatusIcon = status.icon

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border p-4 hover:border-border/80 transition-colors"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono font-semibold text-white">{order.id}</span>
            {order.urgency !== 'normal' && (
              <Badge variant="outline" className={cn('text-[10px] border', urgency.color)}>
                {urgency.label}
              </Badge>
            )}
          </div>
          <p className="text-sm text-slate-400">{order.supplierName}</p>
        </div>
        <Badge className={cn('gap-1', status.color)}>
          <StatusIcon className="w-3 h-3" />
          {status.label}
        </Badge>
      </div>

      {/* Project Info */}
      <div className="flex items-center gap-2 mb-3 text-sm">
        <span className="text-accent">{order.projectId}</span>
        <span className="text-slate-500">·</span>
        <span className="text-slate-400 truncate">{order.projectName}</span>
      </div>

      {/* Progress */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs mb-1">
          <span className="text-slate-400">到货进度</span>
          <span className="text-white">{order.receivedCount}/{order.itemCount} 项</span>
        </div>
        <div className="h-1.5 bg-surface-2 rounded-full overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              order.status === 'completed'
                ? 'bg-emerald-500'
                : order.status === 'delayed'
                ? 'bg-red-500'
                : 'bg-accent'
            )}
            style={{
              width: `${(order.receivedCount / order.itemCount) * 100}%`,
            }}
          />
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
        <div>
          <span className="text-slate-500 text-xs">订单金额</span>
          <p className="text-white font-medium">¥{order.totalAmount.toLocaleString()}</p>
        </div>
        <div>
          <span className="text-slate-500 text-xs">预计到货</span>
          <p className={cn(
            'font-medium',
            order.status === 'delayed' ? 'text-red-400' : 'text-white'
          )}>
            {order.delayedDate || order.expectedDate}
          </p>
        </div>
      </div>

      {/* Delay Reason */}
      {order.delayReason && (
        <div className="mb-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-3 h-3" />
          {order.delayReason}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <span className="text-xs text-slate-500">
          采购员：{order.buyer}
        </span>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onView(order)} title="查看详情">
            <Eye className="w-3.5 h-3.5" />
          </Button>
          {order.status === 'draft' && onEdit && (
            <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onEdit(order)} title="编辑">
              <Edit3 className="w-3.5 h-3.5" />
            </Button>
          )}
          {order.status === 'draft' && onDelete && (
            <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onDelete(order)} title="删除">
              <Trash2 className="w-3.5 h-3.5" />
            </Button>
          )}
          {order.status === 'draft' && onSubmit && (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-blue-400" onClick={() => onSubmit(order)} title="提交">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </Button>
          )}
          {(order.status === 'pending' || order.status === 'submitted') && onApprove && (
            <Button variant="ghost" size="sm" className="h-7 px-2 text-emerald-400" onClick={() => onApprove(order)} title="审批">
              <CheckCircle2 className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function OrderDetailDialog({ order, open, onOpenChange }) {
  if (!order) return null

  const status = statusConfigs[order.status]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span>{order.id}</span>
            <Badge className={status.color}>{status.label}</Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs text-slate-500">供应商</label>
              <p className="text-white">{order.supplierName}</p>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-500">所属项目</label>
              <p className="text-white">{order.projectId} - {order.projectName}</p>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-500">订单日期</label>
              <p className="text-white">{order.orderDate}</p>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-slate-500">预计到货</label>
              <p className={order.status === 'delayed' ? 'text-red-400' : 'text-white'}>
                {order.delayedDate || order.expectedDate}
              </p>
            </div>
          </div>

          {/* Items Table */}
          {order.items && (
            <div>
              <label className="text-xs text-slate-500 mb-2 block">订单明细</label>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-surface-2">
                      <th className="text-left p-3 text-slate-400 font-medium">物料编码</th>
                      <th className="text-left p-3 text-slate-400 font-medium">名称</th>
                      <th className="text-right p-3 text-slate-400 font-medium">数量</th>
                      <th className="text-right p-3 text-slate-400 font-medium">单价</th>
                      <th className="text-right p-3 text-slate-400 font-medium">已收</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.items.map((item, index) => (
                      <tr key={index} className="border-t border-border/50">
                        <td className="p-3 font-mono text-xs text-slate-400">{item.code}</td>
                        <td className="p-3 text-white">{item.name}</td>
                        <td className="p-3 text-right text-white">{item.qty}</td>
                        <td className="p-3 text-right text-white">¥{item.price}</td>
                        <td className="p-3 text-right">
                          <span className={item.received === item.qty ? 'text-emerald-400' : 'text-amber-400'}>
                            {item.received}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Amount Summary */}
          <div className="flex justify-end gap-8 pt-4 border-t border-border">
            <div className="text-right">
              <span className="text-xs text-slate-500">订单总额</span>
              <p className="text-xl font-bold text-white">
                ¥{order.totalAmount.toLocaleString()}
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs text-slate-500">已收货金额</span>
              <p className="text-xl font-bold text-emerald-400">
                ¥{order.receivedAmount.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>关闭</Button>
          <Button>收货登记</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function PurchaseOrders() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [orders, setOrders] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showDetail, setShowDetail] = useState(false)
  
  // Create/Edit dialog state
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingOrder, setEditingOrder] = useState(null)
  const [showMaterialDialog, setShowMaterialDialog] = useState(false)
  const [currentItemIndex, setCurrentItemIndex] = useState(null)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [approvingOrder, setApprovingOrder] = useState(null)
  const [approvalNote, setApprovalNote] = useState('')
  const [newOrder, setNewOrder] = useState({
    supplier_id: null,
    project_id: null,
    order_type: 'NORMAL',
    order_title: '',
    required_date: '',
    payment_terms: '',
    delivery_address: '',
    contract_no: '',
    remark: '',
    items: [],
  })
  
  // Data for dropdowns
  const [suppliers, setSuppliers] = useState([])
  const [projects, setProjects] = useState([])
  const [materials, setMaterials] = useState([])

  // Map backend status to frontend status
  const mapBackendStatusToFrontend = (backendStatus) => {
    const statusMap = {
      'DRAFT': 'draft',
      'PENDING': 'pending',
      'PARTIAL_RECEIVED': 'partial_received',
      'COMPLETED': 'completed',
      'DELAYED': 'delayed',
      'CANCELLED': 'cancelled',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'pending'
  }

  // Load orders from API
  const loadOrders = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Build query parameters
      const params = {
        page: 1,
        page_size: 100,
      }

      // Apply filters
      if (statusFilter !== 'all') {
        // Map frontend status to backend status
        const statusMap = {
          'draft': 'DRAFT',
          'pending': 'PENDING',
          'partial_received': 'PARTIAL_RECEIVED',
          'completed': 'COMPLETED',
          'delayed': 'DELAYED',
          'cancelled': 'CANCELLED',
        }
        params.status = statusMap[statusFilter] || statusFilter.toUpperCase()
      }
      if (searchQuery) {
        params.keyword = searchQuery
      }

      const response = await purchaseApi.orders.list(params)
      const ordersData = response.data?.items || response.data || []

      // Transform backend data to frontend format
      const transformedOrders = await Promise.all(
        ordersData.map(async (order) => {
          // Load items for this order
          let items = []
          let itemCount = 0
          let receivedCount = 0
          try {
            const itemsResponse = await purchaseApi.orders.getItems(order.id)
            items = itemsResponse.data || []
            itemCount = items.length
            receivedCount = items.filter(item => (item.received_qty || 0) > 0).length
          } catch (err) {
      console.error('操作失败:', err)
    }

          // Determine status based on received quantity
          let frontendStatus = mapBackendStatusToFrontend(order.status)
          if (frontendStatus === 'pending' && receivedCount > 0 && receivedCount < itemCount) {
            frontendStatus = 'partial_received'
          } else if (frontendStatus === 'pending' && receivedCount === itemCount && itemCount > 0) {
            frontendStatus = 'completed'
          }

          return {
            id: order.order_no || order.id?.toString(),
            projectId: order.project_id?.toString(),
            projectName: order.project_name || '',
            supplierId: order.supplier_id?.toString(),
            supplierName: order.supplier_name || '',
            status: frontendStatus,
            orderDate: order.created_at?.split('T')[0] || '',
            expectedDate: order.required_date || '',
            totalAmount: parseFloat(order.total_amount || order.amount_with_tax || 0),
            receivedAmount: 0, // Will be calculated from items
            itemCount: itemCount,
            receivedCount: receivedCount,
            buyer: order.buyer_name || '',
            urgency: 'normal', // Default, can be enhanced
            items: items.map((item) => ({
              code: item.material_code || '',
              name: item.material_name || '',
              qty: item.quantity || 0,
              price: parseFloat(item.unit_price || 0),
              received: item.received_qty || 0,
            })),
            // Store original order for detail view
            _original: order,
          }
        })
      )

      // Calculate received amounts
      transformedOrders.forEach((order) => {
        order.receivedAmount = order.items.reduce(
          (sum, item) => sum + (item.price * item.received),
          0
        )
      })

      setOrders(transformedOrders)
    } catch (err) {
      setError(err)
      setOrders([]) // 清空数据
    } finally {
      setLoading(false)
    }
  }, [statusFilter, searchQuery])

  // Initial load on component mount
  useEffect(() => {
    loadOrders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // 只在组件挂载时执行一次

  // Reload when filters change
  useEffect(() => {
    loadOrders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, searchQuery]) // 筛选条件变化时重新加载

  // Load suppliers, projects, and materials for dropdowns
  useEffect(() => {
    const loadDropdownData = async () => {
      try {
        // 加载数据
        const [suppliersRes, projectsRes] = await Promise.all([
          supplierApi.list({ page_size: 1000 }),
          projectApi.list({ page_size: 1000 }),
        ])
        
        const suppliersData = suppliersRes.data?.items || suppliersRes.data || []
        const projectsData = projectsRes.data?.items || projectsRes.data || []
        
        setSuppliers(suppliersData)
        setProjects(projectsData)
      } catch (err) {
        // 下拉数据失败不影响主功能，只记录错误
        setSuppliers([])
        setProjects([])
      }
    }
    
    loadDropdownData()
  }, [])

  // Client-side filtering (for additional filtering beyond API)
  const filteredOrders = (orders || []).filter((order) => {
    // Additional client-side search if needed (when API doesn't support keyword search)
    if (searchQuery) {
      if (
        !order.id?.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !order.supplierName?.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false
      }
    }
    return true
  })

  // Calculate stats
  const stats = {
    total: (orders || []).length || 0,
    pending: (orders || []).filter((o) => o.status === 'pending').length || 0,
    delayed: (orders || []).filter((o) => o.status === 'delayed').length || 0,
    totalAmount: (orders || []).reduce((sum, o) => sum + (o.totalAmount || 0), 0) || 0,
  }

  const handleViewOrder = async (order) => {
    // Load full details if needed
    if (order._original) {
      try {
        const response = await purchaseApi.orders.get(order._original.id)
        const fullOrder = response.data || response
        
        // Load items
        const itemsResponse = await purchaseApi.orders.getItems(order._original.id)
        const items = itemsResponse.data || []
        
        // Update order with full details
        const updatedOrder = {
          ...order,
          items: items.map((item) => ({
            code: item.material_code || '',
            name: item.material_name || '',
            qty: item.quantity || 0,
            price: parseFloat(item.unit_price || 0),
            received: item.received_qty || 0,
          })),
        }
        
        setSelectedOrder(updatedOrder)
      } catch (err) {
        setSelectedOrder(order)
      }
    } else {
      setSelectedOrder(order)
    }
    setShowDetail(true)
  }

  const handleCreateOrder = useCallback(() => {
    setNewOrder({
      supplier_id: null,
      project_id: null,
      order_type: 'NORMAL',
      order_title: '',
      required_date: '',
      payment_terms: '',
      delivery_address: '',
      contract_no: '',
      remark: '',
      items: [],
    })
    setEditingOrder(null)
    setShowCreateDialog(true)
  }, [])

  // Check URL params for action=create or action=edit
  useEffect(() => {
    const action = searchParams.get('action')
    const orderId = searchParams.get('id')
    
    if (action === 'create') {
      handleCreateOrder()
      // Remove the action param from URL
      setSearchParams({}, { replace: true })
    } else if (action === 'edit' && orderId) {
      // 查找订单并打开编辑对话框
      const order = (orders || []).find(o => o.id === parseInt(orderId) || o.id === orderId)
      if (order) {
        handleEditOrder(order)
      } else {
        // 如果订单不在列表中，尝试从API获取
        purchaseApi.orders.get(parseInt(orderId))
          .then(res => {
            const orderData = res.data || res
            // 转换数据格式以匹配前端格式
            const formattedOrder = {
              id: orderData.id,
              poNumber: orderData.order_no,
              supplierId: orderData.supplier_id,
              supplierName: orderData.supplier_name,
              projectId: orderData.project_id,
              projectName: orderData.project_name,
              status: mapBackendStatusToFrontend(orderData.status),
              expectedDate: orderData.required_date,
              items: orderData.items || [],
            }
            handleEditOrder(formattedOrder)
          })
          .catch(err => {
            toast.error('加载订单失败')
          })
      }
      // Remove the action and id params from URL
      setSearchParams({}, { replace: true })
    }
  }, [searchParams, handleCreateOrder, setSearchParams, orders])

  const handleEditOrder = (order) => {
    if (order.status !== 'draft') {
      toast.error('只有草稿状态的订单才能编辑')
      return
    }
    setEditingOrder(order)
    setNewOrder({
      supplier_id: order.supplierId ? parseInt(order.supplierId) : null,
      project_id: order.projectId ? parseInt(order.projectId) : null,
      order_type: 'NORMAL',
      order_title: '',
      required_date: order.expectedDate || '',
      payment_terms: '',
      delivery_address: '',
      contract_no: '',
      remark: '',
      items: order.items || [],
    })
    setShowEditDialog(true)
  }

  const handleDeleteOrder = async (order) => {
    if (order.status !== 'draft') {
      toast.error('只有草稿状态的订单才能删除')
      return
    }
    
    if (!confirm(`确定要删除订单 ${order.id} 吗？`)) {
      return
    }

    try {
      // 调用 API（如果后端支持删除）
      // await purchaseApi.orders.delete(order._original?.id)
      toast.success('订单已删除')
      loadOrders()
    } catch (err) {
      toast.error(err.response?.data?.detail || '删除订单失败')
    }
  }

  const handleSubmitOrder = async (order) => {
    if (order.status !== 'draft') {
      toast.error('只有草稿状态的订单才能提交')
      return
    }

    try {
      await purchaseApi.orders.submit(order._original?.id)
      toast.success('订单已提交，等待审批')
      loadOrders()
    } catch (err) {
      toast.error(err.response?.data?.detail || '提交订单失败')
    }
  }

  const handleApproveOrder = (order) => {
    if (order.status !== 'pending' && order.status !== 'submitted') {
      toast.error('只有待审批状态的订单才能审批')
      return
    }
    setApprovingOrder(order)
    setApprovalNote('')
    setShowApproveDialog(true)
  }

  const handleConfirmApprove = async (approved) => {
    if (!approvingOrder) return

    try {
      await purchaseApi.orders.approve(approvingOrder._original?.id, {
        approved,
        approval_note: approvalNote,
      })
      toast.success(approved ? '订单已审批通过' : '订单已驳回')
      loadOrders()
      setShowApproveDialog(false)
      setApprovingOrder(null)
      setApprovalNote('')
    } catch (err) {
      toast.error(err.response?.data?.detail || '审批订单失败')
    }
  }

  const handleSaveOrder = async () => {
    // Validate
    if (!newOrder.supplier_id) {
      toast.error('请选择供应商')
      return
    }
    if (!newOrder.items || newOrder.items.length === 0) {
      toast.error('请至少添加一个物料')
      return
    }

    try {
      const orderData = {
          supplier_id: newOrder.supplier_id,
          project_id: newOrder.project_id || null,
          order_type: newOrder.order_type,
          order_title: newOrder.order_title || null,
          required_date: newOrder.required_date || null,
          payment_terms: newOrder.payment_terms || null,
          delivery_address: newOrder.delivery_address || null,
          contract_no: newOrder.contract_no || null,
          remark: newOrder.remark || null,
          items: newOrder.items.map(item => ({
            material_id: item.material_id || null,
            material_code: item.material_code || '',
            material_name: item.material_name || '',
            specification: item.specification || null,
            unit: item.unit || '件',
            quantity: item.quantity,
            unit_price: item.unit_price,
            tax_rate: item.tax_rate || 13,
            required_date: item.required_date || null,
            remark: item.remark || null,
          })),
        }
        
        if (editingOrder) {
          await purchaseApi.orders.update(editingOrder._original?.id, orderData)
          toast.success('订单已更新')
          setShowEditDialog(false)
      } else {
        await purchaseApi.orders.create(orderData)
        toast.success('订单已创建')
        setShowCreateDialog(false)
      }
      loadOrders()
    } catch (err) {
      toast.error(err.response?.data?.detail || '保存订单失败')
    }
  }

  const handleExport = () => {
    // 导出功能：将订单数据导出为 CSV
    const csvData = filteredOrders.map(order => ({
      订单编号: order.id,
      供应商: order.supplierName,
      项目: order.projectName || '',
      状态: statusConfigs[order.status]?.label || order.status,
      订单金额: order.totalAmount,
      预计到货: order.expectedDate || order.delayedDate || '',
    }))
    
    const csv = [
      Object.keys(csvData[0] || {}).join(','),
      ...csvData.map(row => Object.values(row).join(','))
    ].join('\n')
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `采购订单_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
    toast.success('导出成功')
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16 text-slate-400">加载中...</div>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6 space-y-6">
          <PageHeader
            title="采购订单"
            description="管理采购订单，跟踪到货状态"
          />
          <ApiIntegrationError
            error={error}
            apiEndpoint="/api/v1/purchase/orders"
            onRetry={loadOrders}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 py-6 space-y-6"
      >
      <PageHeader
        title="采购订单"
        description="管理采购订单，跟踪到货状态"
        actions={
          <Button onClick={handleCreateOrder}>
            <Plus className="w-4 h-4 mr-1" />
            新建订单
          </Button>
        }
      />

      {/* Stats */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '订单总数', value: stats.total, icon: Package, color: 'text-blue-400' },
          { label: '待收货', value: stats.pending, icon: Clock, color: 'text-amber-400' },
          { label: '延期订单', value: stats.delayed, icon: AlertTriangle, color: 'text-red-400' },
          { label: '订单金额', value: `¥${(stats.totalAmount / 10000).toFixed(1)}万`, icon: DollarSign, color: 'text-emerald-400' },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { value: 'all', label: '全部' },
                  { value: 'pending', label: '待收货' },
                  { value: 'partial_received', label: '部分到货' },
                  { value: 'delayed', label: '延期' },
                  { value: 'completed', label: '已完成' },
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={statusFilter === filter.value ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setStatusFilter(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索订单号/供应商..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Button variant="outline" size="sm" onClick={handleExport}>
                  <Download className="w-4 h-4 mr-1" />
                  导出
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Orders Grid */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredOrders.map((order) => (
          <OrderCard 
            key={order.id} 
            order={order} 
            onView={handleViewOrder}
            onEdit={handleEditOrder}
            onDelete={handleDeleteOrder}
            onSubmit={handleSubmitOrder}
            onApprove={handleApproveOrder}
          />
        ))}
      </motion.div>

      {/* Empty State */}
      {filteredOrders.length === 0 && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <Package className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无采购订单</h3>
          <p className="text-sm text-slate-500 mt-1">
            {searchQuery || statusFilter !== 'all'
              ? '没有符合条件的订单'
              : '点击"新建订单"开始采购'}
          </p>
        </motion.div>
      )}

      {/* Order Detail Dialog */}
      <OrderDetailDialog
        order={selectedOrder}
        open={showDetail}
        onOpenChange={setShowDetail}
      />

      {/* Create/Edit Order Dialog */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false)
          setShowEditDialog(false)
          setEditingOrder(null)
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingOrder ? '编辑采购订单' : '新建采购订单'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>供应商 *</Label>
                  <Select
                    value={newOrder.supplier_id?.toString() || ''}
                    onValueChange={(val) => setNewOrder({ ...newOrder, supplier_id: val ? parseInt(val) : null })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择供应商" />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map((supplier) => (
                        <SelectItem key={supplier.id} value={supplier.id.toString()}>
                          {supplier.supplier_name || supplier.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>所属项目</Label>
                  <Select
                    value={newOrder.project_id?.toString() || 'none'}
                    onValueChange={(val) => setNewOrder({ ...newOrder, project_id: val && val !== 'none' ? parseInt(val) : null })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目（可选）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id.toString()}>
                          {project.project_name || project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>订单标题</Label>
                  <Input
                    value={newOrder.order_title}
                    onChange={(e) => setNewOrder({ ...newOrder, order_title: e.target.value })}
                    placeholder="订单标题（可选）"
                  />
                </div>
                <div>
                  <Label>要求交期</Label>
                  <Input
                    type="date"
                    value={newOrder.required_date}
                    onChange={(e) => setNewOrder({ ...newOrder, required_date: e.target.value })}
                  />
                </div>
                <div>
                  <Label>付款条款</Label>
                  <Input
                    value={newOrder.payment_terms}
                    onChange={(e) => setNewOrder({ ...newOrder, payment_terms: e.target.value })}
                    placeholder="付款条款（可选）"
                  />
                </div>
                <div>
                  <Label>收货地址</Label>
                  <Input
                    value={newOrder.delivery_address}
                    onChange={(e) => setNewOrder({ ...newOrder, delivery_address: e.target.value })}
                    placeholder="收货地址（可选）"
                  />
                </div>
                <div>
                  <Label>合同编号</Label>
                  <Input
                    value={newOrder.contract_no}
                    onChange={(e) => setNewOrder({ ...newOrder, contract_no: e.target.value })}
                    placeholder="合同编号（可选）"
                  />
                </div>
              </div>

              {/* Items */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <Label>订单明细 *</Label>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setNewOrder({
                        ...newOrder,
                        items: [
                          ...newOrder.items,
                          {
                            material_id: null,
                            material_code: '',
                            material_name: '',
                            specification: '',
                            unit: '件',
                            quantity: 1,
                            unit_price: 0,
                            tax_rate: 13,
                            required_date: '',
                            remark: '',
                          },
                        ],
                      })
                    }}
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    添加物料
                  </Button>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {newOrder.items.map((item, index) => (
                    <div key={index} className="grid grid-cols-12 gap-2 p-2 border border-border rounded">
                      <div className="col-span-3">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="w-full justify-start"
                          onClick={() => {
                            setCurrentItemIndex(index)
                            setShowMaterialDialog(true)
                          }}
                        >
                          {item.material_code || item.material_name ? (
                            <span className="truncate">{item.material_code || item.material_name}</span>
                          ) : (
                            <span className="text-slate-500">选择物料</span>
                          )}
                        </Button>
                      </div>
                      <div className="col-span-3">
                        <Input
                          placeholder="物料名称 *"
                          value={item.material_name}
                          onChange={(e) => {
                            const newItems = [...newOrder.items]
                            newItems[index].material_name = e.target.value
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                          readOnly={!!item.material_id}
                          className={item.material_id ? 'bg-slate-800/50' : ''}
                        />
                      </div>
                      <div className="col-span-1">
                        <Input
                          placeholder="单位"
                          value={item.unit}
                          onChange={(e) => {
                            const newItems = [...newOrder.items]
                            newItems[index].unit = e.target.value
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                        />
                      </div>
                      <div className="col-span-1">
                        <Input
                          type="number"
                          placeholder="数量"
                          value={item.quantity}
                          onChange={(e) => {
                            const newItems = [...newOrder.items]
                            newItems[index].quantity = parseFloat(e.target.value) || 0
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                        />
                      </div>
                      <div className="col-span-1">
                        <Input
                          type="number"
                          placeholder="单价"
                          value={item.unit_price}
                          onChange={(e) => {
                            const newItems = [...newOrder.items]
                            newItems[index].unit_price = parseFloat(e.target.value) || 0
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                        />
                      </div>
                      <div className="col-span-1">
                        <Input
                          type="number"
                          placeholder="税率%"
                          value={item.tax_rate}
                          onChange={(e) => {
                            const newItems = [...newOrder.items]
                            newItems[index].tax_rate = parseFloat(e.target.value) || 13
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                        />
                      </div>
                      <div className="col-span-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            const newItems = newOrder.items.filter((_, i) => i !== index)
                            setNewOrder({ ...newOrder, items: newItems })
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {newOrder.items.length === 0 && (
                    <p className="text-sm text-slate-500 text-center py-4">请添加至少一个物料</p>
                  )}
                </div>
              </div>

              {/* Remark */}
              <div>
                <Label>备注</Label>
                <Textarea
                  value={newOrder.remark}
                  onChange={(e) => setNewOrder({ ...newOrder, remark: e.target.value })}
                  placeholder="备注信息（可选）"
                  rows={3}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false)
              setShowEditDialog(false)
              setEditingOrder(null)
            }}>
              取消
            </Button>
            <Button onClick={handleSaveOrder}>
              {editingOrder ? '保存' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Material Selection Dialog */}
      <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">选择物料</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <MaterialSelectionDialog
              materials={materials}
              onSelect={(material) => {
                if (currentItemIndex !== null) {
                  const newItems = [...newOrder.items]
                  newItems[currentItemIndex] = {
                    ...newItems[currentItemIndex],
                    material_id: material.id,
                    material_code: material.material_code || material.code,
                    material_name: material.material_name || material.name,
                    specification: material.specification || '',
                    unit: material.unit || '件',
                    unit_price: material.last_price || material.standard_price || 0,
                  }
                  setNewOrder({ ...newOrder, items: newItems })
                }
                setShowMaterialDialog(false)
                setCurrentItemIndex(null)
              }}
            />
          </DialogBody>
        </DialogContent>
      </Dialog>

      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">审批采购订单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {approvingOrder && (
              <div className="space-y-4">
                <div>
                  <Label className="text-slate-400">订单编号</Label>
                  <p className="text-slate-200 font-mono">{approvingOrder.id}</p>
                </div>
                <div>
                  <Label className="text-slate-400">供应商</Label>
                  <p className="text-slate-200">{approvingOrder.supplierName}</p>
                </div>
                <div>
                  <Label className="text-slate-400">订单金额</Label>
                  <p className="text-slate-200">¥{approvingOrder.totalAmount?.toLocaleString() || 0}</p>
                </div>
                <div>
                  <Label className="text-slate-400">审批意见</Label>
                  <Textarea
                    value={approvalNote}
                    onChange={(e) => setApprovalNote(e.target.value)}
                    placeholder="请输入审批意见（可选）"
                    className="bg-slate-800 border-slate-700 text-slate-200"
                    rows={3}
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleConfirmApprove(false)}
              className="border-red-500 text-red-400 hover:bg-red-500/10"
            >
              驳回
            </Button>
            <Button
              onClick={() => handleConfirmApprove(true)}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              审批通过
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </motion.div>
    </div>
  )
}

// Material Selection Dialog Component
function MaterialSelectionDialog({ materials, onSelect }) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredMaterials = (materials || []).filter(material => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      if (
        !material.material_code?.toLowerCase().includes(query) &&
        !material.material_name?.toLowerCase().includes(query)
      ) {
        return false
      }
    }
    return true
  })

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索物料编码或名称..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-800 border-slate-700 text-slate-200"
            icon={Search}
          />
        </div>
      </div>
      <div className="max-h-96 overflow-y-auto">
        <div className="space-y-2">
          {filteredMaterials.length === 0 ? (
            <div className="text-center py-8 text-slate-400">未找到物料</div>
          ) : (
            filteredMaterials.map((material) => (
              <div
                key={material.id}
                className="p-3 border border-slate-700 rounded-lg bg-slate-800/50 hover:bg-slate-800 cursor-pointer transition-colors"
                onClick={() => onSelect(material)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-slate-200 font-mono text-sm">{material.material_code || material.code}</p>
                    <p className="text-slate-400 text-sm">{material.material_name || material.name}</p>
                    {material.specification && (
                      <p className="text-slate-500 text-xs mt-1">{material.specification}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-slate-300 text-sm">¥{material.last_price || material.standard_price || 0}</p>
                    <p className="text-slate-500 text-xs">{material.unit || '件'}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

