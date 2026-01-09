/**
 * Material Tracking Page - Real-time material inventory and arrival tracking
 * Monitors material status from purchase to receipt and usage
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Package,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  Plus,
  MapPin,
  Calendar,
  Truck,
  Boxes,
  BarChart3,
  Eye,
  Download,
  AlertCircle,
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
  Input,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { materialApi, purchaseApi } from '../services/api'
import { toast } from '../components/ui/toast'

// Mock material tracking data
const mockMaterials = [
  {
    id: 'MAT-001',
    code: 'MAT-2025-001',
    name: '32位MCU芯片 STM32F103',
    category: '半导体',
    supplier: '深圳电子元器件有限公司',
    poNumber: 'PO-2025-0001',
    totalQuantity: 500,
    arrivedQuantity: 250,
    usedQuantity: 50,
    remainingQuantity: 200,
    status: 'partial-arrived', // not-arrived | partial-arrived | fully-arrived | in-use | completed
    poDate: '2025-11-15',
    expectedDate: '2025-11-25',
    actualArrivalDate: '2025-11-24',
    location: '仓库A-01',
    batch: 'BATCH-20251124-001',
    qualityStatus: 'qualified', // qualified | pending-inspection | rejected
    storageCondition: 'normal', // normal | temperature-controlled | moisture-controlled
    unitPrice: 45.5,
    totalValue: 22750,
    arrivedValue: 11375,
    usedValue: 2275,
    project: 'BMS老化测试设备',
    nextAction: '继续到货',
    daysUntilExpiry: 180,
  },
  {
    id: 'MAT-002',
    code: 'MAT-2025-002',
    name: '电阻 1/4W 10K',
    category: '被动元件',
    supplier: '深圳元器件供应商',
    poNumber: 'PO-2025-0001',
    totalQuantity: 2000,
    arrivedQuantity: 2000,
    usedQuantity: 500,
    remainingQuantity: 1500,
    status: 'fully-arrived',
    poDate: '2025-11-15',
    expectedDate: '2025-11-20',
    actualArrivalDate: '2025-11-19',
    location: '仓库B-05',
    batch: 'BATCH-20251119-002',
    qualityStatus: 'qualified',
    storageCondition: 'normal',
    unitPrice: 0.15,
    totalValue: 300,
    arrivedValue: 300,
    usedValue: 75,
    project: 'BMS老化测试设备',
    nextAction: '按需领取',
    daysUntilExpiry: 365,
  },
  {
    id: 'MAT-003',
    code: 'MAT-2025-003',
    name: '铝电解电容 100uF/16V',
    category: '被动元件',
    supplier: '日本太阳诱电代理',
    poNumber: 'PO-2025-0002',
    totalQuantity: 1000,
    arrivedQuantity: 500,
    usedQuantity: 100,
    remainingQuantity: 400,
    status: 'partial-arrived',
    poDate: '2025-11-16',
    expectedDate: '2025-12-01',
    actualArrivalDate: '2025-11-28',
    location: '仓库C-03',
    batch: 'BATCH-20251128-003',
    qualityStatus: 'qualified',
    storageCondition: 'temperature-controlled',
    unitPrice: 0.85,
    totalValue: 850,
    arrivedValue: 425,
    usedValue: 85,
    project: 'BMS老化测试设备',
    nextAction: '等待后续到货',
    daysUntilExpiry: 240,
  },
  {
    id: 'MAT-004',
    code: 'MAT-2025-004',
    name: '电源模块 110-240V/12V 5A',
    category: '模块',
    supplier: '深圳电源厂商',
    poNumber: 'PO-2025-0003',
    totalQuantity: 50,
    arrivedQuantity: 0,
    usedQuantity: 0,
    remainingQuantity: 0,
    status: 'not-arrived',
    poDate: '2025-11-18',
    expectedDate: '2025-12-05',
    actualArrivalDate: null,
    location: null,
    batch: null,
    qualityStatus: null,
    storageCondition: null,
    unitPrice: 280,
    totalValue: 14000,
    arrivedValue: 0,
    usedValue: 0,
    project: 'BMS老化测试设备',
    nextAction: '跟进供应商',
    daysUntilExpiry: null,
  },
  {
    id: 'MAT-005',
    code: 'MAT-2025-005',
    name: 'USB连接器 Type-C',
    category: '连接器',
    supplier: '连接器制造商',
    poNumber: 'PO-2025-0001',
    totalQuantity: 100,
    arrivedQuantity: 100,
    usedQuantity: 80,
    remainingQuantity: 20,
    status: 'in-use',
    poDate: '2025-11-15',
    expectedDate: '2025-11-22',
    actualArrivalDate: '2025-11-21',
    location: '仓库A-10',
    batch: 'BATCH-20251121-005',
    qualityStatus: 'qualified',
    storageCondition: 'normal',
    unitPrice: 3.2,
    totalValue: 320,
    arrivedValue: 320,
    usedValue: 256,
    project: 'BMS老化测试设备',
    nextAction: '适时补货',
    daysUntilExpiry: 365,
  },
]

const statusConfig = {
  'not-arrived': {
    label: '未到货',
    color: 'bg-red-500/20 text-red-400',
    icon: AlertTriangle,
    description: '采购订单已下达，等待物料到达',
  },
  'partial-arrived': {
    label: '部分到货',
    color: 'bg-amber-500/20 text-amber-400',
    icon: Truck,
    description: '物料已部分到达，继续等待后续',
  },
  'fully-arrived': {
    label: '全部到货',
    color: 'bg-emerald-500/20 text-emerald-400',
    icon: CheckCircle2,
    description: '采购的全部物料已到达仓库',
  },
  'in-use': {
    label: '使用中',
    color: 'bg-blue-500/20 text-blue-400',
    icon: Zap,
    description: '物料正在生产中使用',
  },
  'completed': {
    label: '已完成',
    color: 'bg-slate-500/20 text-slate-400',
    icon: CheckCircle2,
    description: '物料已全部使用或返库',
  },
}

const qualityStatusConfig = {
  'qualified': { label: '合格', color: 'bg-emerald-500/20 text-emerald-400' },
  'pending-inspection': { label: '待检验', color: 'bg-amber-500/20 text-amber-400' },
  'rejected': { label: '不合格', color: 'bg-red-500/20 text-red-400' },
}

const MaterialRow = ({ material, onView }) => {
  const statusCfg = statusConfig[material.status]
  const StatusIcon = statusCfg.icon
  const arrivalProgress = (material.arrivedQuantity / material.totalQuantity) * 100
  const usageProgress = (material.usedQuantity / material.arrivedQuantity) * 100

  return (
    <motion.div
      variants={fadeIn}
      className="group rounded-lg border border-slate-700/50 bg-slate-800/40 p-4 hover:bg-slate-800/60 transition-all"
    >
      <div className="space-y-3">
        {/* Header Row */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-100">{material.name}</h3>
            <p className="text-sm text-slate-500 mt-1">
              {material.code} • {material.category} • {material.supplier}
            </p>
          </div>
          <Badge className={cn('text-sm', statusCfg.color)}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {statusCfg.label}
          </Badge>
        </div>

        {/* Quantity and Value Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-slate-400 mb-1">订购数量</p>
            <p className="font-semibold text-slate-100">{material.totalQuantity}</p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">已到数量</p>
            <p className="font-semibold text-emerald-400">{material.arrivedQuantity}</p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">已用数量</p>
            <p className="font-semibold text-blue-400">{material.usedQuantity}</p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">剩余数量</p>
            <p className="font-semibold text-amber-400">{material.remainingQuantity}</p>
          </div>
        </div>

        {/* Progress Bars */}
        <div className="space-y-2">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-400">到货进度</span>
              <span className="text-xs font-medium text-slate-300">{arrivalProgress.toFixed(0)}%</span>
            </div>
            <Progress value={arrivalProgress} className="h-1.5" />
          </div>
          {material.arrivedQuantity > 0 && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">使用进度</span>
                <span className="text-xs font-medium text-slate-300">
                  {usageProgress.toFixed(0)}%
                </span>
              </div>
              <Progress value={usageProgress} className="h-1.5" />
            </div>
          )}
        </div>

        {/* Timeline and Status */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm pt-2 border-t border-slate-700/30">
          <div>
            <p className="text-slate-500 text-xs mb-1">预期日期</p>
            <p className="text-slate-300">{formatDate(material.expectedDate)}</p>
          </div>
          {material.actualArrivalDate && (
            <div>
              <p className="text-slate-500 text-xs mb-1">实际日期</p>
              <p className="text-slate-300">{formatDate(material.actualArrivalDate)}</p>
            </div>
          )}
          <div>
            <p className="text-slate-500 text-xs mb-1">位置</p>
            <p className="text-slate-300">{material.location || '—'}</p>
          </div>
          {material.daysUntilExpiry && (
            <div>
              <p className="text-slate-500 text-xs mb-1">保质期</p>
              <p className={cn('text-sm font-medium', material.daysUntilExpiry < 30 ? 'text-red-400' : 'text-slate-300')}>
                {material.daysUntilExpiry} 天
              </p>
            </div>
          )}
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-700/30">
          <div className="flex gap-2">
            {material.qualityStatus && (
              <Badge className={cn('text-xs', qualityStatusConfig[material.qualityStatus]?.color)}>
                {qualityStatusConfig[material.qualityStatus]?.label}
              </Badge>
            )}
            <Badge className="bg-slate-700/50 text-slate-300 text-xs">
              {material.nextAction}
            </Badge>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0"
            onClick={() => onView(material)}
          >
            <Eye className="w-4 h-4 text-blue-400" />
          </Button>
        </div>
      </div>
    </motion.div>
  )
}

export default function MaterialTracking() {
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [categories, setCategories] = useState([])

  // Map backend status to frontend status
  const mapMaterialStatus = (material, purchaseItems) => {
    // Find related purchase order items
    const relatedItems = purchaseItems.filter(item => 
      item.material_code === material.material_code
    )
    
    if (relatedItems.length === 0) {
      return 'not-arrived'
    }
    
    const totalQty = relatedItems.reduce((sum, item) => sum + (item.quantity || 0), 0)
    const receivedQty = relatedItems.reduce((sum, item) => sum + (item.received_quantity || 0), 0)
    
    if (receivedQty === 0) {
      return 'not-arrived'
    } else if (receivedQty < totalQty) {
      return 'partial-arrived'
    } else {
      return 'fully-arrived'
    }
  }

  // Load materials from API
  const loadMaterials = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Load materials
      const materialsResponse = await materialApi.list({
        page: 1,
        page_size: 100,
        keyword: searchText || undefined,
        is_active: true,
      })
      const materialsData = materialsResponse.data?.items || materialsResponse.data || []

      // Load purchase order items to get arrival status
      const purchaseResponse = await purchaseApi.orders.list({ page: 1, page_size: 100 })
      const purchaseOrders = purchaseResponse.data?.items || purchaseResponse.data || []
      
      // Get all purchase order items
      const allPurchaseItems = []
      for (const order of purchaseOrders) {
        try {
          const itemsResponse = await purchaseApi.orders.getItems(order.id)
          const items = itemsResponse.data || []
          allPurchaseItems.push(...items)
        } catch (err) {
        }
      }

      // Transform materials data
      const transformedMaterials = materialsData.map(material => {
        const status = mapMaterialStatus(material, allPurchaseItems)
        const relatedItems = allPurchaseItems.filter(item => 
          item.material_code === material.material_code
        )
        
        const totalQuantity = relatedItems.reduce((sum, item) => sum + (item.quantity || 0), 0)
        const arrivedQuantity = relatedItems.reduce((sum, item) => sum + (item.received_quantity || 0), 0)
        const unitPrice = material.last_price || material.standard_price || 0
        
        return {
          id: material.id?.toString(),
          code: material.material_code || '',
          name: material.material_name || '',
          category: material.category_name || '',
          supplier: '', // Will be filled from purchase order
          poNumber: relatedItems.length > 0 ? relatedItems[0].order_no : '',
          totalQuantity,
          arrivedQuantity,
          usedQuantity: 0, // Not available from current API
          remainingQuantity: arrivedQuantity,
          status,
          poDate: '',
          expectedDate: '',
          actualArrivalDate: '',
          location: '',
          batch: '',
          qualityStatus: 'qualified',
          storageCondition: 'normal',
          unitPrice,
          totalValue: totalQuantity * unitPrice,
          arrivedValue: arrivedQuantity * unitPrice,
          usedValue: 0,
          project: '',
          nextAction: status === 'not-arrived' ? '等待到货' : status === 'partial-arrived' ? '继续到货' : '按需领取',
          daysUntilExpiry: 365,
        }
      })

      setMaterials(transformedMaterials)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载物料列表失败')
      setMaterials([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [searchText])

  // Load materials when component mounts or search changes
  useEffect(() => {
    loadMaterials()
  }, [loadMaterials])

  // Load material categories
  useEffect(() => {
    const loadCategories = async () => {
      try {
        const res = await materialApi.categories.list()
        setCategories(res.data?.items || res.data || [])
      } catch (err) {
      }
    }
    loadCategories()
  }, [])

  const filteredMaterials = useMemo(() => {
    return materials.filter(m => {
      const matchSearch =
        m.name.toLowerCase().includes(searchText.toLowerCase()) ||
        m.code.toLowerCase().includes(searchText.toLowerCase()) ||
        m.supplier.toLowerCase().includes(searchText.toLowerCase())

      const matchStatus = filterStatus === 'all' || m.status === filterStatus

      return matchSearch && matchStatus
    })
  }, [materials, searchText, filterStatus])

  const stats = useMemo(() => {
    return {
      total: materials.length,
      fullArrived: materials.filter(m => m.status === 'fully-arrived').length,
      notArrived: materials.filter(m => m.status === 'not-arrived').length,
      totalValue: materials.reduce((sum, m) => sum + m.totalValue, 0),
      arrivedValue: materials.reduce((sum, m) => sum + m.arrivedValue, 0),
      usedValue: materials.reduce((sum, m) => sum + m.usedValue, 0),
    }
  }, [materials])

  if (loading) {
    return (
      <div className="space-y-6 pb-8">
        <PageHeader
          title="物料跟踪"
          description="实时监控物料采购、到货和使用状态"
        />
        <div className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </div>
      </div>
    )
  }

  if (error && materials.length === 0) {
    return (
      <div className="space-y-6 pb-8">
        <PageHeader
          title="物料跟踪"
          description="实时监控物料采购、到货和使用状态"
        />
        <div className="text-center py-16">
          <div className="text-red-400">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="物料跟踪"
        description="实时监控物料采购、到货和使用状态"
        action={{
          label: '新建物料',
          icon: Plus,
          onClick: () => {
            setShowCreateDialog(true)
          },
        }}
      />
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5"
      >
        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">物料总数</p>
              <p className="text-3xl font-bold text-blue-400 mt-2">{stats.total}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">全部到货</p>
              <p className="text-3xl font-bold text-emerald-400 mt-2">{stats.fullArrived}</p>
              <p className="text-xs text-slate-500 mt-1">{((stats.fullArrived / stats.total) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">未到货</p>
              <p className="text-3xl font-bold text-red-400 mt-2">{stats.notArrived}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">合同金额</p>
              <p className="text-2xl font-bold text-amber-400 mt-2">{formatCurrency(stats.totalValue)}</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-slate-400">已到金额</p>
              <p className="text-2xl font-bold text-emerald-400 mt-2">{formatCurrency(stats.arrivedValue)}</p>
              <p className="text-xs text-slate-500 mt-1">{((stats.arrivedValue / stats.totalValue) * 100).toFixed(1)}%</p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Search and Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索物料名、物料码、供应商..."
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterStatus === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilterStatus('all')}
              >
                全部状态
              </Button>
              {Object.entries(statusConfig).map(([key, cfg]) => (
                <Button
                  key={key}
                  variant={filterStatus === key ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setFilterStatus(key)}
                  className={cn(filterStatus === key && cfg.color)}
                >
                  {cfg.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Materials Grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4"
      >
        <AnimatePresence>
          {filteredMaterials.length > 0 ? (
            filteredMaterials.map(material => (
              <MaterialRow
                key={material.id}
                material={material}
                onView={(m) => {
                  // Handle view material if needed
                }}
              />
            ))
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="py-12 text-center"
            >
              <Package className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">没有符合条件的物料</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Alert Summary */}
      {materials.some(m => m.status === 'not-arrived' && m.daysUntilExpiry) && (
        <Card className="bg-red-500/5 border-red-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-5 h-5" />
              待处理提醒
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {materials
                .filter(m => m.status === 'not-arrived')
                .map(m => (
                  <li key={m.id} className="text-sm text-slate-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    {m.name} - 预期到货: {formatDate(m.expectedDate)}
                  </li>
                ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Create Material Dialog */}
      {showCreateDialog && (
        <CreateMaterialDialog
          categories={categories}
          onClose={() => setShowCreateDialog(false)}
          onSuccess={() => {
            setShowCreateDialog(false)
            loadMaterials()
            toast.success('物料创建成功')
          }}
        />
      )}
    </div>
  )
}

// Create Material Dialog Component
function CreateMaterialDialog({ categories, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    material_code: '',
    material_name: '',
    category_id: null,
    specification: '',
    brand: '',
    unit: '件',
    drawing_no: '',
    material_type: '',
    source_type: 'PURCHASE',
    standard_price: 0,
    safety_stock: 0,
    lead_time_days: 0,
    min_order_qty: 1,
    default_supplier_id: null,
    is_key_material: false,
    remark: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    // Validation
    const newErrors = {}
    if (!formData.material_code.trim()) {
      newErrors.material_code = '请输入物料编码'
    }
    if (!formData.material_name.trim()) {
      newErrors.material_name = '请输入物料名称'
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    try {
      setLoading(true)
      const submitData = {
        ...formData,
        category_id: formData.category_id || undefined,
        default_supplier_id: formData.default_supplier_id || undefined,
        standard_price: parseFloat(formData.standard_price) || 0,
        safety_stock: parseFloat(formData.safety_stock) || 0,
        min_order_qty: parseFloat(formData.min_order_qty) || 1,
      }
      await materialApi.create(submitData)
      onSuccess()
    } catch (error) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle>新建物料</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="required">
                物料编码 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.material_code}
                onChange={(e) => setFormData({ ...formData, material_code: e.target.value })}
                placeholder="请输入物料编码"
                className={errors.material_code ? 'border-red-400' : ''}
              />
              {errors.material_code && (
                <div className="text-sm text-red-400 mt-1">{errors.material_code}</div>
              )}
            </div>
            <div>
              <Label className="required">
                物料名称 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.material_name}
                onChange={(e) => setFormData({ ...formData, material_name: e.target.value })}
                placeholder="请输入物料名称"
                className={errors.material_name ? 'border-red-400' : ''}
              />
              {errors.material_name && (
                <div className="text-sm text-red-400 mt-1">{errors.material_name}</div>
              )}
            </div>
            <div>
              <Label>物料分类</Label>
              <Select
                value={formData.category_id?.toString() || ''}
                onValueChange={(value) => setFormData({ ...formData, category_id: value ? parseInt(value) : null })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="请选择物料分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">无分类</SelectItem>
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.category_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>规格型号</Label>
              <Input
                value={formData.specification}
                onChange={(e) => setFormData({ ...formData, specification: e.target.value })}
                placeholder="请输入规格型号"
              />
            </div>
            <div>
              <Label>品牌</Label>
              <Input
                value={formData.brand}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                placeholder="请输入品牌"
              />
            </div>
            <div>
              <Label>单位</Label>
              <Input
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                placeholder="如：件、个、根等"
              />
            </div>
            <div>
              <Label>图号</Label>
              <Input
                value={formData.drawing_no}
                onChange={(e) => setFormData({ ...formData, drawing_no: e.target.value })}
                placeholder="请输入图号"
              />
            </div>
            <div>
              <Label>物料类型</Label>
              <Input
                value={formData.material_type}
                onChange={(e) => setFormData({ ...formData, material_type: e.target.value })}
                placeholder="如：标准件、机械件、电气件等"
              />
            </div>
            <div>
              <Label>来源类型</Label>
              <Select
                value={formData.source_type}
                onValueChange={(value) => setFormData({ ...formData, source_type: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PURCHASE">采购</SelectItem>
                  <SelectItem value="SELF_MADE">自制</SelectItem>
                  <SelectItem value="OUTSOURCING">外协</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>标准价格</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.standard_price}
                onChange={(e) => setFormData({ ...formData, standard_price: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div>
              <Label>安全库存</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.safety_stock}
                onChange={(e) => setFormData({ ...formData, safety_stock: e.target.value })}
                placeholder="0"
              />
            </div>
            <div>
              <Label>交期（天）</Label>
              <Input
                type="number"
                value={formData.lead_time_days}
                onChange={(e) => setFormData({ ...formData, lead_time_days: parseInt(e.target.value) || 0 })}
                placeholder="0"
              />
            </div>
            <div>
              <Label>最小订购量</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.min_order_qty}
                onChange={(e) => setFormData({ ...formData, min_order_qty: e.target.value })}
                placeholder="1"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_key_material"
                checked={formData.is_key_material}
                onChange={(e) => setFormData({ ...formData, is_key_material: e.target.checked })}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500"
              />
              <Label htmlFor="is_key_material" className="cursor-pointer">
                关键物料
              </Label>
            </div>
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={formData.remark}
              onChange={(e) => setFormData({ ...formData, remark: e.target.value })}
              placeholder="请输入备注信息"
              rows={3}
              className="bg-slate-800/50 border-slate-700"
            />
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? '创建中...' : '创建物料'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
