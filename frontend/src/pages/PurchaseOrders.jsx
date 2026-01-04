import { useState } from 'react'
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
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock purchase orders data
const mockPurchaseOrders = [
  {
    id: 'PO250104001',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    supplierId: 'V00015',
    supplierName: '欧姆龙(上海)代理',
    status: 'partial_received',
    orderDate: '2026-01-02',
    expectedDate: '2026-01-08',
    totalAmount: 45680.00,
    receivedAmount: 32500.00,
    itemCount: 12,
    receivedCount: 8,
    buyer: '王采购',
    urgency: 'normal',
    items: [
      { code: 'EL-02-03-0015', name: '光电传感器 E3Z-D82', qty: 12, price: 450, received: 12 },
      { code: 'EL-02-03-0018', name: '接近传感器 E2E-X5', qty: 8, price: 280, received: 0 },
    ],
  },
  {
    id: 'PO250104002',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    supplierId: 'V00023',
    supplierName: 'THK(深圳)销售',
    status: 'pending',
    orderDate: '2026-01-03',
    expectedDate: '2026-01-10',
    totalAmount: 28900.00,
    receivedAmount: 0,
    itemCount: 4,
    receivedCount: 0,
    buyer: '王采购',
    urgency: 'urgent',
    items: [
      { code: 'ME-03-02-0008', name: '精密导轨 HSR25', qty: 4, price: 4200, received: 0 },
      { code: 'ME-03-02-0012', name: '滑块 HSR25R', qty: 8, price: 850, received: 0 },
    ],
  },
  {
    id: 'PO250103005',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    supplierId: 'V00008',
    supplierName: '西门子官方授权',
    status: 'completed',
    orderDate: '2025-12-28',
    expectedDate: '2026-01-05',
    totalAmount: 156800.00,
    receivedAmount: 156800.00,
    itemCount: 6,
    receivedCount: 6,
    buyer: '李采购',
    urgency: 'normal',
  },
  {
    id: 'PO250104003',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    supplierId: 'V00031',
    supplierName: '海康威视代理',
    status: 'delayed',
    orderDate: '2026-01-02',
    expectedDate: '2026-01-08',
    delayedDate: '2026-01-15',
    totalAmount: 18600.00,
    receivedAmount: 0,
    itemCount: 2,
    receivedCount: 0,
    buyer: '王采购',
    urgency: 'urgent',
    delayReason: '供应商产能不足',
  },
]

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

function OrderCard({ order, onView }) {
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
          <Button variant="ghost" size="sm" className="h-7 px-2" onClick={() => onView(order)}>
            <Eye className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-7 px-2">
            <Edit3 className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-7 px-2">
            <MoreHorizontal className="w-3.5 h-3.5" />
          </Button>
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
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showDetail, setShowDetail] = useState(false)

  const filteredOrders = mockPurchaseOrders.filter((order) => {
    if (statusFilter !== 'all' && order.status !== statusFilter) return false
    if (searchQuery && !order.id.includes(searchQuery) && !order.supplierName.includes(searchQuery)) {
      return false
    }
    return true
  })

  // Calculate stats
  const stats = {
    total: mockPurchaseOrders.length,
    pending: mockPurchaseOrders.filter((o) => o.status === 'pending').length,
    delayed: mockPurchaseOrders.filter((o) => o.status === 'delayed').length,
    totalAmount: mockPurchaseOrders.reduce((sum, o) => sum + o.totalAmount, 0),
  }

  const handleViewOrder = (order) => {
    setSelectedOrder(order)
    setShowDetail(true)
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="采购订单"
        description="管理采购订单，跟踪到货状态"
        actions={
          <Button>
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
                <Button variant="outline" size="sm">
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
          <OrderCard key={order.id} order={order} onView={handleViewOrder} />
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
    </motion.div>
  )
}

