import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Package,
  Edit,
  ClipboardCheck,
  Truck,
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
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
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
import { Badge } from '../components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn } from '../lib/animations'
import { purchaseApi } from '../services/api'
import { toast } from '../components/ui/toast'
import { LoadingCard } from '../components/common'
import { ErrorMessage } from '../components/common'

const statusConfigs = {
  PENDING: { label: '待收货', color: 'bg-slate-500' },
  RECEIVED: { label: '已收货', color: 'bg-emerald-500' },
  REJECTED: { label: '已拒收', color: 'bg-red-500' },
}

const inspectStatusConfigs = {
  PENDING: { label: '待质检', color: 'bg-slate-500' },
  INSPECTING: { label: '质检中', color: 'bg-purple-500' },
  QUALIFIED: { label: '合格', color: 'bg-emerald-500' },
  UNQUALIFIED: { label: '不合格', color: 'bg-red-500' },
  PARTIAL: { label: '部分合格', color: 'bg-amber-500' },
}

export default function GoodsReceiptDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [receipt, setReceipt] = useState(null)
  const [items, setItems] = useState([])
  
  const [showInspectDialog, setShowInspectDialog] = useState(false)
  const [inspectingItem, setInspectingItem] = useState(null)
  const [inspectData, setInspectData] = useState({
    inspect_qty: 0,
    qualified_qty: 0,
    rejected_qty: 0,
    inspect_result: 'QUALIFIED',
  })
  
  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  useEffect(() => {
    loadReceipt()
  }, [id])

  const loadReceipt = async () => {
    try {
      setLoading(true)
      setError(null)
      
      if (isDemoAccount) {
        // Mock data
        setReceipt({
          id: parseInt(id),
          receipt_no: 'GR-250115-001',
          order_id: 1,
          order_no: 'PO-250115-001',
          supplier_name: '欧姆龙(上海)代理',
          receipt_date: '2025-01-15',
          receipt_type: 'NORMAL',
          status: 'RECEIVED',
          inspect_status: 'INSPECTING',
        })
        setItems([
          {
            id: 1,
            material_code: 'EL-02-03-0015',
            material_name: '光电传感器 E3Z-D82',
            delivery_qty: 12,
            received_qty: 12,
            inspect_qty: 0,
            qualified_qty: 0,
            rejected_qty: 0,
            inspect_result: null,
          },
          {
            id: 2,
            material_code: 'EL-02-03-0016',
            material_name: '接近开关 E2E-X10D1-N',
            delivery_qty: 8,
            received_qty: 8,
            inspect_qty: 8,
            qualified_qty: 7,
            rejected_qty: 1,
            inspect_result: 'PARTIAL',
          },
        ])
      } else {
        const [receiptRes, itemsRes] = await Promise.all([
          purchaseApi.receipts.get(id),
          purchaseApi.receipts.getItems(id),
        ])
        setReceipt(receiptRes.data || receiptRes)
        setItems(itemsRes.data || itemsRes || [])
      }
    } catch (err) {
      console.error('Failed to load receipt:', err)
      setError(err.response?.data?.detail || '加载收货单失败')
    } finally {
      setLoading(false)
    }
  }

  const handleOpenInspect = (item) => {
    setInspectingItem(item)
    setInspectData({
      inspect_qty: item.received_qty || item.delivery_qty || 0,
      qualified_qty: item.qualified_qty || 0,
      rejected_qty: item.rejected_qty || 0,
      inspect_result: item.inspect_result || 'QUALIFIED',
    })
    setShowInspectDialog(true)
  }

  const handleInspect = async () => {
    if (!inspectingItem) return
    
    if (inspectData.inspect_qty > inspectingItem.received_qty) {
      toast.error('送检数量不能超过收货数量')
      return
    }
    
    if (inspectData.qualified_qty + inspectData.rejected_qty !== inspectData.inspect_qty) {
      toast.error('合格数量 + 不合格数量必须等于送检数量')
      return
    }
    
    try {
      setLoading(true)
      
      if (isDemoAccount) {
        // Mock update
        const updatedItems = items.map(item =>
          item.id === inspectingItem.id
            ? {
                ...item,
                inspect_qty: inspectData.inspect_qty,
                qualified_qty: inspectData.qualified_qty,
                rejected_qty: inspectData.rejected_qty,
                inspect_result: inspectData.inspect_result,
              }
            : item
        )
        setItems(updatedItems)
        toast.success('质检结果已更新（演示模式）')
      } else {
        await purchaseApi.receipts.inspectItem(id, inspectingItem.id, {
          inspect_qty: inspectData.inspect_qty,
          qualified_qty: inspectData.qualified_qty,
          rejected_qty: inspectData.rejected_qty,
          inspect_result: inspectData.inspect_result,
        })
        toast.success('质检结果已更新')
        loadReceipt()
      }
      
      setShowInspectDialog(false)
      setInspectingItem(null)
    } catch (err) {
      console.error('Failed to update inspect:', err)
      toast.error(err.response?.data?.detail || '更新质检结果失败')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateStatus = async (status) => {
    try {
      setLoading(true)
      
      if (isDemoAccount) {
        setReceipt({ ...receipt, status })
        toast.success('状态已更新（演示模式）')
      } else {
        await purchaseApi.receipts.updateStatus(id, status)
        toast.success('状态已更新')
        loadReceipt()
      }
    } catch (err) {
      console.error('Failed to update status:', err)
      toast.error(err.response?.data?.detail || '更新状态失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !receipt) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <LoadingCard />
        </div>
      </div>
    )
  }

  if (error && !receipt) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage message={error} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title={`收货单 ${receipt?.receipt_no || ''}`}
          description="收货单详情及质检管理"
          actions={
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => navigate('/purchases/receipts')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
            </div>
          }
        />

        {error && <ErrorMessage message={error} />}

        {receipt && (
          <motion.div variants={fadeIn} className="space-y-6">
            {/* Receipt Info */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">收货单信息</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-slate-400">收货单号</Label>
                    <p className="text-slate-200 font-mono">{receipt.receipt_no}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">采购单号</Label>
                    <p className="text-slate-200 font-mono">{receipt.order_no}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">供应商</Label>
                    <p className="text-slate-200">{receipt.supplier_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">收货日期</Label>
                    <p className="text-slate-200">{formatDate(receipt.receipt_date)}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">收货状态</Label>
                    <Badge className={statusConfigs[receipt.status]?.color || 'bg-slate-500'}>
                      {statusConfigs[receipt.status]?.label || receipt.status}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-slate-400">质检状态</Label>
                    <Badge className={inspectStatusConfigs[receipt.inspect_status]?.color || 'bg-slate-500'}>
                      {inspectStatusConfigs[receipt.inspect_status]?.label || receipt.inspect_status}
                    </Badge>
                  </div>
                </div>
                
                {/* Status Actions */}
                <div className="mt-4 flex gap-2">
                  {receipt.status === 'PENDING' && (
                    <>
                      <Button
                        size="sm"
                        onClick={() => handleUpdateStatus('RECEIVED')}
                        className="bg-emerald-600 hover:bg-emerald-700"
                      >
                        <CheckCircle2 className="w-4 h-4 mr-1" />
                        确认收货
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleUpdateStatus('REJECTED')}
                      >
                        <XCircle className="w-4 h-4 mr-1" />
                        拒收
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Items */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">收货明细</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-400">物料编码</TableHead>
                      <TableHead className="text-slate-400">物料名称</TableHead>
                      <TableHead className="text-slate-400">送货数量</TableHead>
                      <TableHead className="text-slate-400">收货数量</TableHead>
                      <TableHead className="text-slate-400">送检数量</TableHead>
                      <TableHead className="text-slate-400">合格数量</TableHead>
                      <TableHead className="text-slate-400">不合格数量</TableHead>
                      <TableHead className="text-slate-400">质检结果</TableHead>
                      <TableHead className="text-slate-400">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((item) => (
                      <TableRow key={item.id} className="border-slate-700">
                        <TableCell className="font-mono text-sm text-slate-200">{item.material_code}</TableCell>
                        <TableCell className="text-slate-300">{item.material_name}</TableCell>
                        <TableCell className="text-slate-300">{item.delivery_qty}</TableCell>
                        <TableCell className="text-slate-300">{item.received_qty || 0}</TableCell>
                        <TableCell className="text-slate-300">{item.inspect_qty || 0}</TableCell>
                        <TableCell className="text-slate-300">{item.qualified_qty || 0}</TableCell>
                        <TableCell className="text-slate-300">{item.rejected_qty || 0}</TableCell>
                        <TableCell>
                          {item.inspect_result ? (
                            <Badge className={
                              item.inspect_result === 'QUALIFIED' ? 'bg-emerald-500' :
                              item.inspect_result === 'UNQUALIFIED' ? 'bg-red-500' :
                              'bg-amber-500'
                            }>
                              {item.inspect_result === 'QUALIFIED' ? '合格' :
                               item.inspect_result === 'UNQUALIFIED' ? '不合格' :
                               '部分合格'}
                            </Badge>
                          ) : (
                            <span className="text-slate-500">待质检</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {receipt.status === 'RECEIVED' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleOpenInspect(item)}
                            >
                              <ClipboardCheck className="w-4 h-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Inspect Dialog */}
        <Dialog open={showInspectDialog} onOpenChange={setShowInspectDialog}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">质检</DialogTitle>
            </DialogHeader>
            <DialogBody>
              {inspectingItem && (
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-400">物料</Label>
                    <p className="text-slate-200">{inspectingItem.material_code} - {inspectingItem.material_name}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">收货数量</Label>
                    <p className="text-slate-200">{inspectingItem.received_qty || 0}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">送检数量 *</Label>
                    <Input
                      type="number"
                      value={inspectData.inspect_qty}
                      onChange={(e) => {
                        const qty = parseFloat(e.target.value) || 0
                        setInspectData({
                          ...inspectData,
                          inspect_qty: qty,
                          rejected_qty: qty - inspectData.qualified_qty,
                        })
                      }}
                      max={inspectingItem.received_qty}
                      min={0}
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400">合格数量 *</Label>
                    <Input
                      type="number"
                      value={inspectData.qualified_qty}
                      onChange={(e) => {
                        const qty = parseFloat(e.target.value) || 0
                        setInspectData({
                          ...inspectData,
                          qualified_qty: qty,
                          rejected_qty: inspectData.inspect_qty - qty,
                        })
                      }}
                      max={inspectData.inspect_qty}
                      min={0}
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400">不合格数量</Label>
                    <Input
                      type="number"
                      value={inspectData.rejected_qty}
                      readOnly
                      className="bg-slate-800/50 border-slate-700 text-slate-400"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400">质检结果</Label>
                    <Select
                      value={inspectData.inspect_result}
                      onValueChange={(val) => setInspectData({ ...inspectData, inspect_result: val })}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="QUALIFIED">合格</SelectItem>
                        <SelectItem value="UNQUALIFIED">不合格</SelectItem>
                        <SelectItem value="PARTIAL">部分合格</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </DialogBody>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowInspectDialog(false)}>
                取消
              </Button>
              <Button onClick={handleInspect} disabled={loading}>
                {loading ? '保存中...' : '保存'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}


