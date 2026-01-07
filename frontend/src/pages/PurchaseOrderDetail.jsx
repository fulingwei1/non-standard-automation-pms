/**
 * Purchase Order Detail Page - Complete purchase order management
 * Handles PO lifecycle from creation to receipt and invoice
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ShoppingCart,
  Package,
  Truck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  DollarSign,
  FileText,
  Download,
  Eye,
  Edit,
  Send,
  ChevronRight,
  Calendar,
  Building2,
  BarChart3,
  MapPin,
  Phone,
  Mail,
  Tag,
  Info,
  Zap,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { purchaseApi } from '../services/api'

// Mock purchase order data
const mockPO = {
  id: 'PO-2025-0001',
  poNumber: 'PO-2025-0001',
  projectName: 'BMS老化测试设备',
  supplier: {
    id: 'SUPP-001',
    name: '深圳电子元器件有限公司',
    contact: '张三',
    phone: '13800000001',
    email: 'contact@supplier.com',
    address: '深圳市龙华区',
    paymentTerm: '2/10 N30',
  },
  status: 'confirmed', // draft | submitted | confirmed | shipped | received | invoiced
  issueDate: '2025-11-15',
  requiredDate: '2025-12-01',
  expectedDelivery: '2025-11-25',
  actualDelivery: null,
  totalAmount: 185000,
  taxRate: 13,
  taxAmount: 24050,
  totalWithTax: 209050,
  currency: 'CNY',
  paymentStatus: 'unpaid', // unpaid | partial | paid
  paidAmount: 0,
  invoiceStatus: 'pending', // pending | partial | complete
  invoicedAmount: 0,
  items: [
    {
      id: 'POL-001',
      itemNo: 1,
      materialCode: 'MAT-2025-001',
      description: '32位MCU芯片 STM32F103',
      specification: 'LQFP-100',
      quantity: 500,
      unit: '个',
      unitPrice: 45.5,
      amount: 22750,
      receivedQty: 0,
      status: 'confirmed', // draft | confirmed | shipped | received
      notes: '原厂正品，提供质保',
    },
    {
      id: 'POL-002',
      itemNo: 2,
      materialCode: 'MAT-2025-002',
      description: '电阻 1/4W 10K',
      specification: '1206',
      quantity: 2000,
      unit: '个',
      unitPrice: 0.15,
      amount: 300,
      receivedQty: 0,
      status: 'confirmed',
      notes: '',
    },
    {
      id: 'POL-003',
      itemNo: 3,
      materialCode: 'MAT-2025-003',
      description: '铝电解电容',
      specification: '100uF/16V',
      quantity: 1000,
      unit: '个',
      unitPrice: 0.85,
      amount: 850,
      receivedQty: 0,
      status: 'confirmed',
      notes: '日化品牌',
    },
    {
      id: 'POL-004',
      itemNo: 4,
      materialCode: 'MAT-2025-004',
      description: '电源模块',
      specification: '110-240V/12V 5A',
      quantity: 50,
      unit: '个',
      unitPrice: 280,
      amount: 14000,
      receivedQty: 0,
      status: 'confirmed',
      notes: '含PCB装配',
    },
    {
      id: 'POL-005',
      itemNo: 5,
      materialCode: 'MAT-2025-005',
      description: 'USB连接器',
      specification: 'Type-C',
      quantity: 100,
      unit: '个',
      unitPrice: 3.2,
      amount: 320,
      receivedQty: 0,
      status: 'confirmed',
      notes: '',
    },
    {
      id: 'POL-006',
      itemNo: 6,
      materialCode: 'MAT-2025-006',
      description: '焊锡丝 SAC305',
      specification: '0.8mm',
      quantity: 5,
      unit: 'kg',
      unitPrice: 120,
      amount: 600,
      receivedQty: 0,
      status: 'confirmed',
      notes: '无铅环保焊锡',
    },
    {
      id: 'POL-007',
      itemNo: 7,
      materialCode: 'MAT-2025-007',
      description: '散热片',
      specification: '铝合金 50x50x30mm',
      quantity: 200,
      unit: '个',
      unitPrice: 8.5,
      amount: 1700,
      receivedQty: 0,
      status: 'confirmed',
      notes: '阳极氧化黑色',
    },
    {
      id: 'POL-008',
      itemNo: 8,
      materialCode: 'MAT-2025-008',
      description: '包装材料',
      specification: '防静电袋+气泡膜',
      quantity: 100,
      unit: '套',
      unitPrice: 12,
      amount: 1200,
      receivedQty: 0,
      status: 'confirmed',
      notes: '',
    },
    {
      id: 'POL-009',
      itemNo: 9,
      materialCode: 'MAT-2025-009',
      description: '运输费',
      specification: '快递到指定地址',
      quantity: 1,
      unit: '批',
      unitPrice: 5680,
      amount: 5680,
      receivedQty: 0,
      status: 'confirmed',
      notes: '包括保险费',
    },
  ],
  timeline: [
    {
      stage: 'draft',
      label: '草稿',
      date: '2025-11-14',
      status: 'completed',
      description: '采购订单创建',
    },
    {
      stage: 'submitted',
      label: '已提交',
      date: '2025-11-15',
      status: 'completed',
      description: '订单已提交给供应商',
    },
    {
      stage: 'confirmed',
      label: '已确认',
      date: '2025-11-16',
      status: 'completed',
      description: '供应商已确认订单',
    },
    {
      stage: 'shipped',
      label: '已发货',
      date: null,
      status: 'pending',
      description: '等待供应商发货',
      daysLeft: 9,
    },
    {
      stage: 'received',
      label: '已收货',
      date: null,
      status: 'pending',
      description: '等待物料到达',
      daysLeft: 16,
    },
    {
      stage: 'invoiced',
      label: '已开票',
      date: null,
      status: 'pending',
      description: '等待收票和付款',
    },
  ],
  documents: [
    {
      id: 'DOC-001',
      name: 'PO原件.pdf',
      type: 'pdf',
      size: '256 KB',
      uploadDate: '2025-11-15',
      status: 'active',
    },
    {
      id: 'DOC-002',
      name: '物料规格书.zip',
      type: 'zip',
      size: '3.2 MB',
      uploadDate: '2025-11-15',
      status: 'active',
    },
    {
      id: 'DOC-003',
      name: '报价单.pdf',
      type: 'pdf',
      size: '180 KB',
      uploadDate: '2025-11-14',
      status: 'active',
    },
  ],
  remarks: '重要物料订单，涉及5条生产线，请及时跟进。',
  attachedProject: {
    id: 'PJ250715001',
    name: 'BMS老化测试设备',
    stage: 'S3 采购备料',
  },
}

const statusConfig = {
  draft: { label: '草稿', color: 'bg-slate-500/20 text-slate-400', icon: FileText },
  submitted: { label: '已提交', color: 'bg-blue-500/20 text-blue-400', icon: Send },
  confirmed: { label: '已确认', color: 'bg-purple-500/20 text-purple-400', icon: CheckCircle2 },
  shipped: { label: '已发货', color: 'bg-amber-500/20 text-amber-400', icon: Truck },
  received: { label: '已收货', color: 'bg-emerald-500/20 text-emerald-400', icon: Package },
  invoiced: { label: '已开票', color: 'bg-indigo-500/20 text-indigo-400', icon: FileText },
}

const paymentStatusConfig = {
  unpaid: { label: '未付款', color: 'bg-red-500/20 text-red-400' },
  partial: { label: '部分付款', color: 'bg-amber-500/20 text-amber-400' },
  paid: { label: '已付款', color: 'bg-emerald-500/20 text-emerald-400' },
}

const invoiceStatusConfig = {
  pending: { label: '待开票', color: 'bg-slate-500/20 text-slate-400' },
  partial: { label: '部分开票', color: 'bg-amber-500/20 text-amber-400' },
  complete: { label: '已开票', color: 'bg-emerald-500/20 text-emerald-400' },
}

const POLineItem = ({ item, idx }) => (
  <motion.div variants={fadeIn} className="flex items-center border-b border-slate-700/30 py-3">
    <div className="w-12 text-center text-sm text-slate-500">{item.itemNo}</div>
    <div className="flex-1">
      <p className="font-medium text-slate-100">{item.description}</p>
      <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
        <span>{item.materialCode}</span>
        <span>|</span>
        <span>{item.specification}</span>
      </div>
    </div>
    <div className="w-24 text-right">
      <p className="text-sm text-slate-300">{item.quantity}</p>
      <p className="text-xs text-slate-500">{item.unit}</p>
    </div>
    <div className="w-24 text-right">
      <p className="font-medium text-slate-100">{formatCurrency(item.unitPrice)}</p>
      <p className="text-xs text-slate-500">单价</p>
    </div>
    <div className="w-28 text-right">
      <p className="font-semibold text-amber-400">{formatCurrency(item.amount)}</p>
    </div>
    <div className="w-20">
      <Badge className={cn('text-xs', statusConfig[item.status]?.color || '')}>
        {statusConfig[item.status]?.label || item.status}
      </Badge>
    </div>
  </motion.div>
)

const TimelineStage = ({ stage, idx, total }) => {
  const config = statusConfig[stage.stage] || {}
  const isCompleted = stage.status === 'completed'
  const isPending = stage.status === 'pending'

  return (
    <div className="relative flex flex-col items-center">
      <motion.div
        variants={fadeIn}
        className="flex flex-col items-center w-full mb-4"
      >
        <div
          className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all',
            isCompleted
              ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
              : isPending
              ? 'bg-amber-500/20 border-amber-500 text-amber-400'
              : 'bg-slate-600/30 border-slate-600 text-slate-400'
          )}
        >
          {config.icon ? <config.icon className="w-5 h-5" /> : <CheckCircle2 className="w-5 h-5" />}
        </div>
        <p className="mt-2 font-medium text-sm text-slate-100">{stage.label}</p>
        {stage.date && (
          <p className="text-xs text-slate-500 mt-1">{formatDate(stage.date)}</p>
        )}
        {stage.daysLeft && (
          <p className="text-xs text-amber-400 mt-1">还需 {stage.daysLeft} 天</p>
        )}
        <p className="text-xs text-slate-400 mt-1">{stage.description}</p>
      </motion.div>

      {idx < total - 1 && (
        <div
          className={cn(
            'w-0.5 h-16 -mb-4',
            isCompleted ? 'bg-emerald-500/40' : 'bg-slate-600/30'
          )}
        />
      )}
    </div>
  )
}

export default function PurchaseOrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [po, setPo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  // Map backend status to frontend status
  const mapBackendStatusToFrontend = (backendStatus) => {
    const statusMap = {
      'DRAFT': 'draft',
      'SUBMITTED': 'submitted',
      'CONFIRMED': 'confirmed',
      'SHIPPED': 'shipped',
      'RECEIVED': 'received',
      'INVOICED': 'invoiced',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'draft'
  }

  // Map backend payment status to frontend
  const mapBackendPaymentStatus = (backendStatus) => {
    const statusMap = {
      'UNPAID': 'unpaid',
      'PARTIAL': 'partial',
      'PAID': 'paid',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'unpaid'
  }

  // Load purchase order from API
  const loadPurchaseOrder = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Get order ID from URL params or use id directly
      const orderId = id || parseInt(id)
      if (!orderId) {
        throw new Error('订单ID不能为空')
      }

      const response = await purchaseApi.orders.get(orderId)
      const orderData = response.data || response

      // Load goods receipts for this order
      let receipts = []
      try {
        const receiptsResponse = await purchaseApi.goodsReceipts.list({ purchase_order_id: orderId })
        receipts = receiptsResponse.data?.items || receiptsResponse.data || []
      } catch (err) {
        console.error('Failed to load receipts:', err)
      }

      // Transform backend data to frontend format
      const transformedPO = {
        id: orderData.id?.toString(),
        poNumber: orderData.order_no || orderData.id?.toString(),
        projectName: orderData.project_name || '',
        supplier: {
          id: orderData.supplier_id?.toString(),
          name: orderData.supplier_name || '',
          contact: '',
          phone: '',
          email: '',
          address: '',
          paymentTerm: '',
        },
        status: mapBackendStatusToFrontend(orderData.status),
        issueDate: orderData.order_date || orderData.created_at?.split('T')[0] || '',
        requiredDate: orderData.required_date || '',
        expectedDelivery: orderData.required_date || '',
        actualDelivery: receipts.length > 0 ? receipts[0].receipt_date : null,
        totalAmount: parseFloat(orderData.total_amount || 0),
        taxRate: orderData.tax_amount && orderData.total_amount 
          ? (orderData.tax_amount / orderData.total_amount) * 100 
          : 13,
        taxAmount: parseFloat(orderData.tax_amount || 0),
        totalWithTax: parseFloat(orderData.amount_with_tax || orderData.total_amount || 0),
        currency: 'CNY',
        paymentStatus: mapBackendPaymentStatus(orderData.payment_status),
        paidAmount: parseFloat(orderData.paid_amount || 0),
        invoiceStatus: 'pending', // Default, can be enhanced
        invoicedAmount: 0, // Default, can be enhanced
        items: (orderData.items || []).map((item, index) => ({
          id: item.id?.toString() || `POL-${index + 1}`,
          itemNo: item.item_no || index + 1,
          materialCode: item.material_code || '',
          description: item.material_name || '',
          specification: item.specification || '',
          quantity: item.quantity || 0,
          unit: item.unit || '个',
          unitPrice: parseFloat(item.unit_price || 0),
          amount: parseFloat(item.amount || item.amount_with_tax || 0),
          receivedQty: item.received_qty || 0,
          status: mapBackendStatusToFrontend(item.status || 'confirmed'),
          notes: '',
        })),
        timeline: [
          {
            stage: 'draft',
            label: '草稿',
            date: orderData.created_at?.split('T')[0] || '',
            status: orderData.status === 'DRAFT' ? 'completed' : 'completed',
            description: '采购订单创建',
          },
          {
            stage: 'submitted',
            label: '已提交',
            date: orderData.status !== 'DRAFT' ? orderData.updated_at?.split('T')[0] : null,
            status: ['SUBMITTED', 'CONFIRMED', 'SHIPPED', 'RECEIVED', 'INVOICED'].includes(orderData.status) ? 'completed' : 'pending',
            description: '订单已提交给供应商',
          },
          {
            stage: 'confirmed',
            label: '已确认',
            date: ['CONFIRMED', 'SHIPPED', 'RECEIVED', 'INVOICED'].includes(orderData.status) ? orderData.updated_at?.split('T')[0] : null,
            status: ['CONFIRMED', 'SHIPPED', 'RECEIVED', 'INVOICED'].includes(orderData.status) ? 'completed' : 'pending',
            description: '供应商已确认订单',
          },
          {
            stage: 'shipped',
            label: '已发货',
            date: ['SHIPPED', 'RECEIVED', 'INVOICED'].includes(orderData.status) ? orderData.updated_at?.split('T')[0] : null,
            status: ['SHIPPED', 'RECEIVED', 'INVOICED'].includes(orderData.status) ? 'completed' : 'pending',
            description: '等待供应商发货',
          },
          {
            stage: 'received',
            label: '已收货',
            date: receipts.length > 0 ? receipts[0].receipt_date : null,
            status: receipts.length > 0 ? 'completed' : 'pending',
            description: '等待物料到达',
          },
          {
            stage: 'invoiced',
            label: '已开票',
            date: orderData.status === 'INVOICED' ? orderData.updated_at?.split('T')[0] : null,
            status: orderData.status === 'INVOICED' ? 'completed' : 'pending',
            description: '等待收票和付款',
          },
        ],
        documents: [],
        remarks: orderData.remark || '',
        attachedProject: {
          id: orderData.project_id?.toString(),
          name: orderData.project_name || '',
          stage: '',
        },
      }

      setPo(transformedPO)
    } catch (err) {
      console.error('Failed to load purchase order:', err)
      if (isDemoAccount) {
        // For demo accounts, use mock data on error
        setPo(mockPO)
        setError(null)
      } else {
        setError(err.response?.data?.detail || err.message || '加载采购订单失败')
        setPo(null)
      }
    } finally {
      setLoading(false)
    }
  }, [id, isDemoAccount])

  // Load order when component mounts
  useEffect(() => {
    loadPurchaseOrder()
  }, [loadPurchaseOrder])

  const progress = useMemo(() => {
    if (!po) return 0
    const completedStages = po.timeline.filter(s => s.status === 'completed').length
    return po.timeline.length > 0 ? (completedStages / po.timeline.length) * 100 : 0
  }, [po])

  const totalItems = useMemo(() => {
    if (!po) return 0
    return po.items.reduce((sum, item) => sum + item.amount, 0)
  }, [po])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-slate-400">加载中...</div>
          </div>
        </div>
      </div>
    )
  }

  if (error && !po && !isDemoAccount) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-red-400">{error}</div>
          </div>
        </div>
      </div>
    )
  }

  if (!po) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-16">
            <div className="text-slate-400">采购订单不存在</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6 pb-8">
      <PageHeader
        title={po.poNumber}
        description={po.projectName}
        action={{
          label: '编辑',
          icon: Edit,
          onClick: () => {
            // TODO: Implement edit purchase order
          },
        }}
      />

      {/* PO Header Info */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
      >
        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">供应商</p>
              <p className="text-lg font-semibold text-slate-100 mt-2">{po.supplier.name}</p>
              <p className="text-xs text-slate-500 mt-1">{po.supplier.contact}</p>
              <p className="text-xs text-slate-500">{po.supplier.phone}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">订单状态</p>
              <div className="mt-2">
                <Badge className={cn('text-sm', statusConfig[po.status]?.color || '')}>
                  {statusConfig[po.status]?.label}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-2">PO金额: {formatCurrency(po.totalWithTax)}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">付款状态</p>
              <div className="mt-2">
                <Badge className={cn('text-sm', paymentStatusConfig[po.paymentStatus]?.color || '')}>
                  {paymentStatusConfig[po.paymentStatus]?.label}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-2">已付: {formatCurrency(po.paidAmount)}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">开票状态</p>
              <div className="mt-2">
                <Badge className={cn('text-sm', invoiceStatusConfig[po.invoiceStatus]?.color || '')}>
                  {invoiceStatusConfig[po.invoiceStatus]?.label}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-2">已开: {formatCurrency(po.invoicedAmount)}</p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            订单进度
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-slate-400">完成度</p>
                <p className="text-sm font-medium text-slate-100">{progress.toFixed(0)}%</p>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
            <p className="text-xs text-slate-500">
              {po.timeline.filter(s => s.status === 'completed').length} / {po.timeline.length} 个阶段已完成
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Timeline */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-slate-200">
            <Calendar className="w-5 h-5 text-blue-400" />
            订单生命周期
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between overflow-x-auto py-6 px-2">
            {po.timeline.map((stage, idx) => (
              <TimelineStage key={stage.stage} stage={stage} idx={idx} total={po.timeline.length} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tabs for different sections */}
      <Tabs defaultValue="items" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="items">物料清单</TabsTrigger>
          <TabsTrigger value="supplier">供应商信息</TabsTrigger>
          <TabsTrigger value="documents">文件附件</TabsTrigger>
          <TabsTrigger value="notes">备注</TabsTrigger>
        </TabsList>

        {/* Items Tab */}
        <TabsContent value="items">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-slate-200">
                  <Package className="w-5 h-5 text-blue-400" />
                  订单物料 ({po.items.length} 项)
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-0"
              >
                {/* Header */}
                <div className="flex items-center border-b-2 border-slate-600 py-3 text-sm font-medium text-slate-400">
                  <div className="w-12"></div>
                  <div className="flex-1">物料描述</div>
                  <div className="w-24 text-right">数量</div>
                  <div className="w-24 text-right">单价</div>
                  <div className="w-28 text-right">小计</div>
                  <div className="w-20">状态</div>
                </div>

                {/* Items */}
                {po.items.map((item, idx) => (
                  <POLineItem key={item.id} item={item} idx={idx} />
                ))}

                {/* Summary */}
                <div className="border-t-2 border-slate-600 pt-4 mt-4 space-y-2">
                  <div className="flex justify-end gap-24">
                    <p className="text-sm text-slate-400">小计:</p>
                    <p className="w-28 text-right font-semibold text-slate-100">
                      {formatCurrency(totalItems)}
                    </p>
                  </div>
                  <div className="flex justify-end gap-24">
                    <p className="text-sm text-slate-400">税率 ({po.taxRate}%):</p>
                    <p className="w-28 text-right font-semibold text-slate-100">
                      {formatCurrency(po.taxAmount)}
                    </p>
                  </div>
                  <div className="flex justify-end gap-24 pt-2 border-t border-slate-700">
                    <p className="text-lg font-semibold text-slate-100">合计:</p>
                    <p className="w-28 text-right text-2xl font-bold text-amber-400">
                      {formatCurrency(po.totalWithTax)}
                    </p>
                  </div>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Supplier Tab */}
        <TabsContent value="supplier">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-200">
                <Building2 className="w-5 h-5 text-green-400" />
                供应商详情
              </CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-6"
              >
                <motion.div variants={fadeIn} className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">供应商名称</p>
                    <p className="font-medium text-slate-100">{po.supplier.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">供应商ID</p>
                    <p className="font-medium text-slate-100">{po.supplier.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">联系人</p>
                    <p className="font-medium text-slate-100">{po.supplier.contact}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">联系电话</p>
                    <p className="font-medium text-slate-100 flex items-center gap-2">
                      <Phone className="w-4 h-4" />
                      {po.supplier.phone}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">邮箱</p>
                    <p className="font-medium text-slate-100 flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      {po.supplier.email}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">地址</p>
                    <p className="font-medium text-slate-100 flex items-center gap-2">
                      <MapPin className="w-4 h-4" />
                      {po.supplier.address}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">付款条款</p>
                    <Badge className="bg-slate-700/50 text-slate-300">{po.supplier.paymentTerm}</Badge>
                  </div>
                </motion.div>
              </motion.div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-200">
                <FileText className="w-5 h-5 text-purple-400" />
                附件文件 ({po.documents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-2"
              >
                {po.documents.map(doc => (
                  <motion.div
                    key={doc.id}
                    variants={fadeIn}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-700 bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-blue-400" />
                      <div>
                        <p className="font-medium text-slate-100">{doc.name}</p>
                        <p className="text-xs text-slate-500">{doc.size} • {doc.uploadDate}</p>
                      </div>
                    </div>
                    <Button size="sm" variant="ghost">
                      <Download className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ))}
              </motion.div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notes Tab */}
        <TabsContent value="notes">
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-slate-200">
                <Info className="w-5 h-5 text-amber-400" />
                备注信息
              </CardTitle>
            </CardHeader>
            <CardContent>
              <motion.div variants={fadeIn} className="space-y-4">
                <div>
                  <p className="text-sm text-slate-400 mb-2">备注</p>
                  <p className="text-slate-200 leading-relaxed">{po.remarks}</p>
                </div>
                <div className="pt-4 border-t border-slate-700">
                  <p className="text-sm text-slate-400 mb-2">关联项目</p>
                  <Badge className="bg-slate-700/50 text-slate-200">
                    {po.attachedProject.id} - {po.attachedProject.name}
                  </Badge>
                  <p className="text-xs text-slate-500 mt-1">{po.attachedProject.stage}</p>
                </div>
              </motion.div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Bar */}
      <Card className="bg-gradient-to-r from-slate-800 to-slate-900 border-slate-700">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-2">
            {po.status !== 'draft' && (
              <>
                <Button className="gap-2">
                  <Send className="w-4 h-4" />
                  发送提醒
                </Button>
                <Button variant="outline" className="gap-2">
                  <Eye className="w-4 h-4" />
                  查看发票
                </Button>
                <Button variant="outline" className="gap-2">
                  <Download className="w-4 h-4" />
                  导出PDF
                </Button>
              </>
            )}
            {po.status === 'draft' && (
              <>
                <Button className="gap-2">
                  <Send className="w-4 h-4" />
                  提交订单
                </Button>
                <Button variant="outline" className="gap-2">
                  <Edit className="w-4 h-4" />
                  编辑订单
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  )
}
