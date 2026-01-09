/**
 * Arrival Management Page - 到货管理页面
 * Features: 收货记录、到货状态更新、质检
 */
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Truck,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  Package,
  AlertTriangle,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import { formatDate, formatCurrency } from '../lib/utils'
import { purchaseApi } from '../services/api'
const statusConfigs = {
  PENDING: { label: '待收货', color: 'bg-slate-500' },
  IN_TRANSIT: { label: '运输中', color: 'bg-blue-500' },
  ARRIVED: { label: '已到货', color: 'bg-amber-500' },
  INSPECTING: { label: '质检中', color: 'bg-purple-500' },
  QUALIFIED: { label: '合格', color: 'bg-emerald-500' },
  UNQUALIFIED: { label: '不合格', color: 'bg-red-500' },
  RECEIVED: { label: '已入库', color: 'bg-violet-500' },
}
export default function ArrivalManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [receipts, setReceipts] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterProject, setFilterProject] = useState('all')
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showReceiveDialog, setShowReceiveDialog] = useState(false)
  const [selectedReceipt, setSelectedReceipt] = useState(null)
  const [receiptItems, setReceiptItems] = useState([])
  // Form state
  const [receiveData, setReceiveData] = useState({
    received_qty: 0,
    quality_status: 'QUALIFIED',
    note: '',
  })
  useEffect(() => {
    fetchReceipts()
  }, [filterStatus, filterProject, searchKeyword])
  const fetchReceipts = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterStatus && filterStatus !== 'all') params.status = filterStatus
      if (filterProject && filterProject !== 'all') params.project_id = filterProject
      if (searchKeyword) params.search = searchKeyword
      const res = await purchaseApi.receipts.list(params)
      const receiptList = res.data?.items || res.data || []
      setReceipts(receiptList)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }
  const fetchReceiptDetail = async (receiptId) => {
    try {
      const [receiptRes, itemsRes] = await Promise.all([
        purchaseApi.receipts.get(receiptId),
        purchaseApi.receipts.getItems(receiptId),
      ])
      setSelectedReceipt(receiptRes.data || receiptRes)
      setReceiptItems(itemsRes.data || itemsRes || [])
      setShowDetailDialog(true)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  const handleReceive = async () => {
    if (!selectedReceipt) return
    try {
      await purchaseApi.receipts.receive(selectedReceipt.id, receiveData)
      setShowReceiveDialog(false)
      setReceiveData({ received_qty: 0, quality_status: 'QUALIFIED', note: '' })
      fetchReceipts()
      if (showDetailDialog) {
        fetchReceiptDetail(selectedReceipt.id)
      }
    } catch (error) {
      alert('收货失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredReceipts = useMemo(() => {
    return receipts.filter(receipt => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          receipt.receipt_no?.toLowerCase().includes(keyword) ||
          receipt.purchase_order_no?.toLowerCase().includes(keyword) ||
          receipt.project_name?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [receipts, searchKeyword])
  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  // Mock data for demo accounts
  useEffect(() => {
    if (isDemoAccount && receipts.length === 0) {
      setReceipts([
        {
          id: 1,
          receipt_no: 'GR-250115-001',
          order_no: 'PO-250115-001',
          purchase_order_no: 'PO-250115-001',
          supplier_name: '欧姆龙(上海)代理',
          project_name: 'BMS老化测试设备',
          item_count: 2,
          total_amount: 6102,
          receipt_date: '2025-01-15',
          status: 'PENDING',
          inspect_status: 'PENDING',
        },
        {
          id: 2,
          receipt_no: 'GR-250115-002',
          order_no: 'PO-250115-002',
          purchase_order_no: 'PO-250115-002',
          supplier_name: 'THK(深圳)销售',
          project_name: 'BMS老化测试设备',
          item_count: 1,
          total_amount: 18984,
          receipt_date: '2025-01-15',
          status: 'RECEIVED',
          inspect_status: 'QUALIFIED',
        },
      ])
      setLoading(false)
    }
  }, [isDemoAccount])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="收货管理"
          description="收货单管理，支持创建收货单、质检、入库"
          actions={
            <Button onClick={() => navigate('/purchases/receipts/new')} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              新建收货单
            </Button>
          }
        />
        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索收货单号、采购单号..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-slate-900/50 border-slate-700 text-slate-200"
                  icon={Search}
                />
              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  {Object.entries(statusConfigs)
                    .filter(([key]) => key && key !== '')
                    .map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
              <Select value={filterProject} onValueChange={setFilterProject}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
        {/* Receipt List */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">收货记录</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredReceipts.length} 条记录
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredReceipts.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无收货记录</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-400">收货单号</TableHead>
                    <TableHead className="text-slate-400">采购单号</TableHead>
                    <TableHead className="text-slate-400">项目</TableHead>
                    <TableHead className="text-slate-400">供应商</TableHead>
                    <TableHead className="text-slate-400">物料数量</TableHead>
                    <TableHead className="text-slate-400">总金额</TableHead>
                    <TableHead className="text-slate-400">收货日期</TableHead>
                    <TableHead className="text-slate-400">状态</TableHead>
                    <TableHead className="text-slate-400">质检状态</TableHead>
                    <TableHead className="text-right text-slate-400">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredReceipts.map((receipt) => (
                    <TableRow key={receipt.id} className="border-slate-700">
                      <TableCell className="font-mono text-sm text-slate-200">
                        {receipt.receipt_no}
                      </TableCell>
                      <TableCell className="font-mono text-sm text-slate-300">
                        {receipt.order_no || receipt.purchase_order_no || '-'}
                      </TableCell>
                      <TableCell className="text-slate-300">{receipt.project_name || '-'}</TableCell>
                      <TableCell className="text-slate-300">{receipt.supplier_name || '-'}</TableCell>
                      <TableCell className="text-slate-300">{receipt.item_count || receipt.items?.length || 0} 项</TableCell>
                      <TableCell className="text-slate-200 font-medium">{formatCurrency(receipt.total_amount || 0)}</TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {receipt.receipt_date ? formatDate(receipt.receipt_date) : '-'}
                      </TableCell>
                      <TableCell>
                        <Badge className={statusConfigs[receipt.status]?.color || 'bg-slate-500'}>
                          {statusConfigs[receipt.status]?.label || receipt.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={
                          receipt.inspect_status === 'QUALIFIED' ? 'bg-emerald-500' :
                          receipt.inspect_status === 'UNQUALIFIED' ? 'bg-red-500' :
                          receipt.inspect_status === 'INSPECTING' ? 'bg-purple-500' :
                          'bg-slate-500'
                        }>
                          {receipt.inspect_status === 'QUALIFIED' ? '合格' :
                           receipt.inspect_status === 'UNQUALIFIED' ? '不合格' :
                           receipt.inspect_status === 'INSPECTING' ? '质检中' :
                           receipt.inspect_status === 'PARTIAL' ? '部分合格' :
                           '待质检'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/purchases/receipts/${receipt.id}`)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      {/* Receipt Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">
              {selectedReceipt?.receipt_no} - 收货明细
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedReceipt && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-400 mb-1">采购单号</div>
                    <div className="font-mono text-slate-200">{selectedReceipt.purchase_order_no || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">供应商</div>
                    <div className="text-slate-200">{selectedReceipt.supplier_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">项目</div>
                    <div className="text-slate-200">{selectedReceipt.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedReceipt.status]?.color}>
                      {statusConfigs[selectedReceipt.status]?.label}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium mb-3 text-slate-200">物料明细</div>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-400">物料编码</TableHead>
                        <TableHead className="text-slate-400">物料名称</TableHead>
                        <TableHead className="text-slate-400">规格</TableHead>
                        <TableHead className="text-slate-400">单位</TableHead>
                        <TableHead className="text-slate-400">订单数量</TableHead>
                        <TableHead className="text-slate-400">已收货</TableHead>
                        <TableHead className="text-slate-400">本次收货</TableHead>
                        <TableHead className="text-slate-400">单价</TableHead>
                        <TableHead className="text-slate-400">金额</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {receiptItems.map((item) => (
                        <TableRow key={item.id} className="border-slate-700">
                          <TableCell className="font-mono text-sm text-slate-300">
                            {item.material_code}
                          </TableCell>
                          <TableCell className="text-slate-200">{item.material_name}</TableCell>
                          <TableCell className="text-slate-400">
                            {item.specification || '-'}
                          </TableCell>
                          <TableCell className="text-slate-300">{item.unit}</TableCell>
                          <TableCell className="text-slate-300">{item.order_qty}</TableCell>
                          <TableCell className="text-slate-300">{item.received_qty || 0}</TableCell>
                          <TableCell className="font-medium text-slate-200">
                            {item.current_received_qty || 0}
                          </TableCell>
                          <TableCell className="text-slate-300">{formatCurrency(item.unit_price || 0)}</TableCell>
                          <TableCell className="font-medium text-slate-200">
                            {formatCurrency(item.amount || 0)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)} className="bg-slate-800 hover:bg-slate-700 text-slate-200">
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Receive Dialog */}
      <Dialog open={showReceiveDialog} onOpenChange={setShowReceiveDialog}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-200">确认收货</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedReceipt && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">收货单号</div>
                  <div className="font-mono text-slate-200">{selectedReceipt.receipt_no}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-400">收货数量</label>
                  <Input
                    type="number"
                    value={receiveData.received_qty}
                    onChange={(e) => setReceiveData({ ...receiveData, received_qty: parseFloat(e.target.value) || 0 })}
                    placeholder="请输入收货数量"
                    className="bg-slate-800 border-slate-700 text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-400">质检结果</label>
                  <Select
                    value={receiveData.quality_status}
                    onValueChange={(val) => setReceiveData({ ...receiveData, quality_status: val })}
                  >
                    <SelectTrigger className="bg-slate-800 border-slate-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="QUALIFIED">合格</SelectItem>
                      <SelectItem value="UNQUALIFIED">不合格</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block text-slate-400">备注</label>
                  <Input
                    value={receiveData.note}
                    onChange={(e) => setReceiveData({ ...receiveData, note: e.target.value })}
                    placeholder="备注信息"
                    className="bg-slate-800 border-slate-700 text-slate-200"
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReceiveDialog(false)} className="bg-slate-800 hover:bg-slate-700 text-slate-200">
              取消
            </Button>
            <Button onClick={handleReceive} className="bg-blue-600 hover:bg-blue-700">确认收货</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </div>
  )
}
