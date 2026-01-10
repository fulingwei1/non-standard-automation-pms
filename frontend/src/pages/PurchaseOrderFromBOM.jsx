import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Package,
  ArrowLeft,
  Search,
  CheckCircle2,
  Edit,
  X,
  Plus,
  ShoppingCart,
  Building2,
  DollarSign,
  FileText,
  AlertCircle,
  ChevronDown,
  ChevronUp,
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
import { Label } from '../components/ui/label'
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
import { Textarea } from '../components/ui/textarea'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { purchaseApi, bomApi, projectApi, supplierApi } from '../services/api'
import { toast } from '../components/ui/toast'
import { LoadingCard } from '../components/common'
import { ErrorMessage } from '../components/common'
import { EmptyState } from '../components/common'

export default function PurchaseOrderFromBOM() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [step, setStep] = useState(1) // 1: 选择BOM, 2: 预览订单, 3: 完成

  // Step 1: BOM selection
  const [boms, setBoms] = useState([])
  const [selectedBomId, setSelectedBomId] = useState(null)
  const [selectedBom, setSelectedBom] = useState(null)
  const [defaultSupplierId, setDefaultSupplierId] = useState(null)
  const [suppliers, setSuppliers] = useState([])

  // Step 2: Preview
  const [preview, setPreview] = useState(null)
  const [editingOrderIndex, setEditingOrderIndex] = useState(null)
  const [editingOrder, setEditingOrder] = useState(null)

  // Step 3: Result
  const [createdOrders, setCreatedOrders] = useState([])

  // Check if demo account  // Load BOMs
  useEffect(() => {
    const loadBOMs = async () => {
      try {
        // Load released BOMs
        const res = await bomApi.list({ status: 'RELEASED', page_size: 1000 })
        const data = res.data?.data || res.data
        setBoms(data?.items || data || [])
      } catch (err) {
        console.error('Failed to load BOMs:', err)
      }
    }
    loadBOMs()
  }, [])

  // Load suppliers
  useEffect(() => {
    const loadSuppliers = async () => {
      try {
        const res = await supplierApi.list({ page_size: 1000 })
        setSuppliers(res.data?.items || res.data || [])
      } catch (err) {
        console.error('Failed to load suppliers:', err)
      }
    }
    loadSuppliers()
  }, [])

  // Generate preview
  const handleGeneratePreview = async () => {
    if (!selectedBomId) {
      toast.error('请选择BOM')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const params = {
        bom_id: parseInt(selectedBomId),
        create_orders: false, // Preview only
      }
      if (defaultSupplierId) {
        params.supplier_id = defaultSupplierId
      }
      const res = await purchaseApi.orders.createFromBOM(params)
      const data = res.data?.data || res.data
      setPreview(data)
      setSelectedBom(boms.find(b => b.id === parseInt(selectedBomId)))
      setStep(2)
    } catch (err) {
      console.error('Failed to generate preview:', err)
      setError(err.response?.data?.detail || '生成预览失败')
      toast.error(err.response?.data?.detail || '生成预览失败')
    } finally {
      setLoading(false)
    }
  }

  // Edit order
  const handleEditOrder = (index) => {
    setEditingOrderIndex(index)
    setEditingOrder({ ...preview.preview[index] })
  }

  // Save edited order
  const handleSaveEditedOrder = () => {
    const newPreview = { ...preview }
    newPreview.preview[editingOrderIndex] = editingOrder
    setPreview(newPreview)
    setEditingOrderIndex(null)
    setEditingOrder(null)
    toast.success('订单信息已更新')
  }

  // Create orders
  const handleCreateOrders = async () => {
    if (!preview || !preview.preview || preview.preview.length === 0) {
      toast.error('没有可创建的订单')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const params = {
        bom_id: preview.bom_id,
        create_orders: true,
      }
      if (defaultSupplierId) {
        params.supplier_id = defaultSupplierId
      }
      const res = await purchaseApi.orders.createFromBOM(params)
      const data = res.data?.data || res.data
      setCreatedOrders(data.created_orders || [])
      setStep(3)
      toast.success(`已创建${data.created_orders?.length || 0}个采购订单`)
    } catch (err) {
      console.error('Failed to create orders:', err)
      setError(err.response?.data?.detail || '创建订单失败')
      toast.error(err.response?.data?.detail || '创建订单失败')
    } finally {
      setLoading(false)
    }
  }

  // Reset
  const handleReset = () => {
    setStep(1)
    setSelectedBomId(null)
    setSelectedBom(null)
    setPreview(null)
    setCreatedOrders([])
    setEditingOrderIndex(null)
    setEditingOrder(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="从BOM生成采购订单"
          description="根据BOM物料清单，按供应商分组批量创建采购订单"
          actions={
            <Button variant="outline" onClick={() => navigate('/purchases')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
          }
        />

        {error && <ErrorMessage message={error} />}

        {/* Step 1: Select BOM */}
        {step === 1 && (
          <motion.div variants={fadeIn} className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">选择BOM</CardTitle>
                <CardDescription className="text-slate-400">
                  选择要生成采购订单的BOM，系统将按供应商自动分组物料
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {boms.length === 0 ? (
                  <EmptyState
                    icon={Package}
                    title="暂无已发布的BOM"
                    description="请先在BOM管理中发布BOM，然后才能生成采购订单"
                  />
                ) : (
                  <>
                    <div>
                      <Label className="text-slate-400">BOM *</Label>
                      <Select
                        value={selectedBomId?.toString() || ''}
                        onValueChange={setSelectedBomId}
                      >
                        <SelectTrigger className="bg-slate-900/50 border-slate-700">
                          <SelectValue placeholder="选择BOM" />
                        </SelectTrigger>
                        <SelectContent>
                          {boms.map(bom => (
                            <SelectItem key={bom.id} value={bom.id.toString()}>
                              {bom.bom_no} - {bom.project_name || bom.machine_name || ''}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                <div>
                  <Label className="text-slate-400">默认供应商（可选）</Label>
                  <Select
                    value={defaultSupplierId?.toString() || ''}
                    onValueChange={(val) => setDefaultSupplierId(val ? parseInt(val) : null)}
                  >
                    <SelectTrigger className="bg-slate-900/50 border-slate-700">
                      <SelectValue placeholder="选择默认供应商（可选）" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {suppliers.map(supplier => (
                        <SelectItem key={supplier.id} value={supplier.id.toString()}>
                          {supplier.supplier_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500 mt-1">
                    如果BOM物料没有指定供应商，将使用此默认供应商
                  </p>
                </div>
                <div className="flex gap-2 pt-4">
                  <Button
                    onClick={handleGeneratePreview}
                    disabled={!selectedBomId || loading}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? '生成中...' : '生成预览'}
                  </Button>
                </div>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Step 2: Preview Orders */}
        {step === 2 && preview && (
          <motion.div variants={fadeIn} className="space-y-6">
            {/* Summary */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">预览汇总</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <Label className="text-slate-400">BOM编号</Label>
                    <p className="text-slate-200 font-mono">{preview.bom_no}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">订单数量</Label>
                    <p className="text-slate-200 text-2xl font-bold">{preview.summary?.total_orders || 0}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">物料数量</Label>
                    <p className="text-slate-200 text-2xl font-bold">{preview.summary?.total_items || 0}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400">总金额（含税）</Label>
                    <p className="text-slate-200 text-2xl font-bold text-emerald-400">
                      ¥{preview.summary?.total_amount_with_tax?.toFixed(2) || '0.00'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Orders Preview */}
            <div className="space-y-4">
              {preview.preview?.map((order, index) => (
                <Card key={index} className="bg-slate-800/50 border-slate-700/50">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-slate-200">
                          订单 {index + 1}: {order.supplier_name}
                        </CardTitle>
                        <CardDescription className="text-slate-400">
                          {order.order_title}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditOrder(index)}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          编辑
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <Label className="text-slate-400">供应商</Label>
                          <p className="text-slate-200">{order.supplier_name}</p>
                        </div>
                        <div>
                          <Label className="text-slate-400">项目</Label>
                          <p className="text-slate-200">{order.project_name || '-'}</p>
                        </div>
                        <div>
                          <Label className="text-slate-400">物料数量</Label>
                          <p className="text-slate-200">{order.item_count}</p>
                        </div>
                        <div>
                          <Label className="text-slate-400">总金额</Label>
                          <p className="text-slate-200">¥{order.total_amount?.toFixed(2)}</p>
                        </div>
                        <div>
                          <Label className="text-slate-400">税额</Label>
                          <p className="text-slate-200">¥{order.tax_amount?.toFixed(2)}</p>
                        </div>
                        <div>
                          <Label className="text-slate-400">含税金额</Label>
                          <p className="text-slate-200 text-emerald-400 font-bold">
                            ¥{order.amount_with_tax?.toFixed(2)}
                          </p>
                        </div>
                      </div>

                      {/* Items Table */}
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow className="border-slate-700">
                              <TableHead className="text-slate-400">序号</TableHead>
                              <TableHead className="text-slate-400">物料编码</TableHead>
                              <TableHead className="text-slate-400">物料名称</TableHead>
                              <TableHead className="text-slate-400">规格</TableHead>
                              <TableHead className="text-slate-400">单位</TableHead>
                              <TableHead className="text-slate-400 text-right">数量</TableHead>
                              <TableHead className="text-slate-400 text-right">单价</TableHead>
                              <TableHead className="text-slate-400 text-right">金额</TableHead>
                              <TableHead className="text-slate-400 text-right">税额</TableHead>
                              <TableHead className="text-slate-400 text-right">含税金额</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {order.items?.map((item, itemIndex) => (
                              <TableRow key={itemIndex} className="border-slate-700">
                                <TableCell className="text-slate-300">{item.item_no}</TableCell>
                                <TableCell className="text-slate-300 font-mono text-xs">{item.material_code}</TableCell>
                                <TableCell className="text-slate-300">{item.material_name}</TableCell>
                                <TableCell className="text-slate-400 text-sm">{item.specification || '-'}</TableCell>
                                <TableCell className="text-slate-300">{item.unit}</TableCell>
                                <TableCell className="text-slate-300 text-right">{item.quantity}</TableCell>
                                <TableCell className="text-slate-300 text-right">¥{item.unit_price?.toFixed(2)}</TableCell>
                                <TableCell className="text-slate-300 text-right">¥{item.amount?.toFixed(2)}</TableCell>
                                <TableCell className="text-slate-300 text-right">¥{item.tax_amount?.toFixed(2)}</TableCell>
                                <TableCell className="text-slate-200 text-right font-medium">¥{item.amount_with_tax?.toFixed(2)}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={handleReset}>
                重新选择
              </Button>
              <Button
                onClick={handleCreateOrders}
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {loading ? '创建中...' : `创建 ${preview.preview?.length || 0} 个采购订单`}
              </Button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Result */}
        {step === 3 && createdOrders && (
          <motion.div variants={fadeIn} className="max-w-2xl mx-auto">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  创建成功
                </CardTitle>
                <CardDescription className="text-slate-400">
                  已成功创建 {createdOrders.length} 个采购订单
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  {createdOrders.map((order, index) => (
                    <div
                      key={index}
                      className="p-3 border border-slate-700 rounded-lg bg-slate-900/30 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-slate-200 font-mono">{order.order_no}</p>
                        <p className="text-slate-400 text-sm">{order.supplier_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-200 font-bold">¥{order.total_amount?.toFixed(2)}</p>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => navigate(`/purchases/${order.order_id}`)}
                        >
                          查看
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 pt-4">
                  <Button variant="outline" onClick={handleReset} className="flex-1">
                    继续创建
                  </Button>
                  <Button
                    onClick={() => navigate('/purchases')}
                    className="flex-1 bg-blue-600 hover:bg-blue-700"
                  >
                    查看订单列表
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Edit Order Dialog */}
        {editingOrder && (
          <Dialog open={!!editingOrder} onOpenChange={() => setEditingOrder(null)}>
            <DialogContent className="max-w-2xl bg-slate-900 border-slate-700">
              <DialogHeader>
                <DialogTitle className="text-slate-200">编辑订单信息</DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-400">订单标题</Label>
                    <Input
                      value={editingOrder.order_title}
                      onChange={(e) => setEditingOrder({ ...editingOrder, order_title: e.target.value })}
                      className="bg-slate-800 border-slate-700 text-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-400">备注</Label>
                    <Textarea
                      value={editingOrder.remark || ''}
                      onChange={(e) => setEditingOrder({ ...editingOrder, remark: e.target.value })}
                      className="bg-slate-800 border-slate-700 text-slate-200"
                      rows={3}
                    />
                  </div>
                </div>
              </DialogBody>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditingOrder(null)}>
                  取消
                </Button>
                <Button onClick={handleSaveEditedOrder}>
                  保存
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </div>
  )
}

