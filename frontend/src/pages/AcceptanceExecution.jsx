/**
 * Acceptance Execution Page - 验收执行页面
 * Features: 验收检查项执行、问题管理、验收完成
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ClipboardCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Plus,
  FileText,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
import { cn, formatDate } from '../lib/utils'
import { acceptanceApi } from '../services/api'
const resultStatusConfigs = {
  PENDING: { label: '待检查', color: 'bg-slate-500' },
  PASSED: { label: '通过', color: 'bg-emerald-500' },
  FAILED: { label: '不通过', color: 'bg-red-500' },
  NA: { label: '不适用', color: 'bg-gray-500' },
}
const overallResultConfigs = {
  PASS: { label: '通过', color: 'bg-emerald-500' },
  FAIL: { label: '不通过', color: 'bg-red-500' },
  CONDITIONAL: { label: '有条件通过', color: 'bg-amber-500' },
}
export default function AcceptanceExecution() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [order, setOrder] = useState(null)
  const [items, setItems] = useState([])
  const [issues, setIssues] = useState([])
  // Dialogs
  const [showItemDialog, setShowItemDialog] = useState(false)
  const [showIssueDialog, setShowIssueDialog] = useState(false)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)
  // Form states
  const [itemResult, setItemResult] = useState({
    result_status: 'PASSED',
    actual_value: '',
    deviation: '',
    remark: '',
  })
  const [newIssue, setNewIssue] = useState({
    item_id: null,
    category: '',
    severity: 'MINOR',
    description: '',
    photos: [],
  })
  const [completeData, setCompleteData] = useState({
    overall_result: 'PASS',
    conclusion: '',
    conditions: '',
  })
  useEffect(() => {
    if (id) {
      fetchOrderDetail()
      fetchItems()
      fetchIssues()
    }
  }, [id])
  const fetchOrderDetail = async () => {
    try {
      const res = await acceptanceApi.orders.get(id)
      setOrder(res.data || res)
    } catch (error) {
      console.error('Failed to fetch order detail:', error)
    }
  }
  const fetchItems = async () => {
    try {
      const res = await acceptanceApi.orders.getItems(id)
      const itemList = res.data || res || []
      setItems(itemList)
    } catch (error) {
      console.error('Failed to fetch items:', error)
    } finally {
      setLoading(false)
    }
  }
  const fetchIssues = async () => {
    try {
      const res = await acceptanceApi.issues.list(id)
      const issueList = res.data || res || []
      setIssues(issueList)
    } catch (error) {
      console.error('Failed to fetch issues:', error)
    }
  }
  const handleUpdateItem = async () => {
    if (!selectedItem) return
    try {
      await acceptanceApi.orders.updateItem(selectedItem.id, itemResult)
      setShowItemDialog(false)
      setSelectedItem(null)
      setItemResult({
        result_status: 'PASSED',
        actual_value: '',
        deviation: '',
        remark: '',
      })
      fetchItems()
      fetchOrderDetail()
    } catch (error) {
      console.error('Failed to update item:', error)
      alert('更新检查项失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleCreateIssue = async () => {
    if (!newIssue.description) {
      alert('请填写问题描述')
      return
    }
    try {
      await acceptanceApi.issues.create(id, newIssue)
      setShowIssueDialog(false)
      setNewIssue({
        item_id: null,
        category: '',
        severity: 'MINOR',
        description: '',
        photos: [],
      })
      fetchIssues()
    } catch (error) {
      console.error('Failed to create issue:', error)
      alert('创建问题失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleComplete = async () => {
    if (!completeData.overall_result) {
      alert('请选择总体结果')
      return
    }
    try {
      await acceptanceApi.orders.complete(id, completeData)
      alert('验收完成')
      navigate('/acceptance-orders')
    } catch (error) {
      console.error('Failed to complete acceptance:', error)
      alert('完成验收失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  // Group items by category
  const itemsByCategory = items.reduce((acc, item) => {
    const category = item.category_name || '其他'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(item)
    return acc
  }, {})
  const passedCount = items.filter(i => i.result_status === 'PASSED').length
  const failedCount = items.filter(i => i.result_status === 'FAILED').length
  const pendingCount = items.filter(i => i.result_status === 'PENDING').length
  const totalChecked = items.length - pendingCount
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    )
  }
  if (!order) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">验收单不存在</div>
      </div>
    )
  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/acceptance-orders')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回列表
          </Button>
          <PageHeader
            title={`验收执行 - ${order.order_no}`}
            description="验收检查项执行、问题管理"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchOrderDetail()
              fetchItems()
              fetchIssues()
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          {order.status === 'IN_PROGRESS' && (
            <Button onClick={() => setShowCompleteDialog(true)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              完成验收
            </Button>
          )}
        </div>
      </div>
      {/* Order Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">总项数</div>
                <div className="text-2xl font-bold">{items.length}</div>
              </div>
              <ClipboardCheck className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">通过</div>
                <div className="text-2xl font-bold text-emerald-600">{passedCount}</div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">不通过</div>
                <div className="text-2xl font-bold text-red-600">{failedCount}</div>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">通过率</div>
                <div className="text-2xl font-bold">
                  {totalChecked > 0 ? ((passedCount / totalChecked) * 100).toFixed(1) : 0}%
                </div>
              </div>
              <Progress 
                value={totalChecked > 0 ? (passedCount / totalChecked) * 100 : 0} 
                className="w-16 h-16" 
              />
            </div>
          </CardContent>
        </Card>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Check Items by Category */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>检查项</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowIssueDialog(true)}
              >
                <Plus className="w-4 h-4 mr-2" />
                上报问题
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {Object.entries(itemsByCategory).map(([category, categoryItems]) => (
                <div key={category}>
                  <div className="font-medium mb-3 flex items-center justify-between">
                    <span>{category}</span>
                    <Badge variant="outline">
                      {categoryItems.filter(i => i.result_status === 'PASSED').length} / {categoryItems.length}
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {categoryItems.map((item) => (
                      <div
                        key={item.id}
                        className={cn(
                          "border rounded-lg p-3 cursor-pointer hover:bg-slate-50 transition-colors",
                          item.result_status === 'PASSED' && 'bg-emerald-50 border-emerald-200',
                          item.result_status === 'FAILED' && 'bg-red-50 border-red-200',
                          item.result_status === 'PENDING' && 'bg-slate-50 border-slate-200'
                        )}
                        onClick={() => {
                          setSelectedItem(item)
                          setItemResult({
                            result_status: item.result_status || 'PASSED',
                            actual_value: item.actual_value || '',
                            deviation: item.deviation || '',
                            remark: item.remark || '',
                          })
                          setShowItemDialog(true)
                        }}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="font-medium text-sm">{item.item_name}</div>
                            <div className="text-xs text-slate-500 mt-1">
                              {item.item_code} {item.is_key_item && <Badge variant="destructive" className="ml-1">关键项</Badge>}
                            </div>
                          </div>
                          <Badge className={resultStatusConfigs[item.result_status]?.color || 'bg-slate-500'}>
                            {resultStatusConfigs[item.result_status]?.label || item.result_status}
                          </Badge>
                        </div>
                        {item.acceptance_criteria && (
                          <div className="text-xs text-slate-500 mb-1">
                            验收标准: {item.acceptance_criteria}
                          </div>
                        )}
                        {item.standard_value && (
                          <div className="text-xs text-slate-500 mb-1">
                            标准值: {item.standard_value}
                            {item.unit && ` ${item.unit}`}
                          </div>
                        )}
                        {item.actual_value && (
                          <div className="text-xs font-medium">
                            实际值: {item.actual_value}
                            {item.unit && ` ${item.unit}`}
                          </div>
                        )}
                        {item.checked_at && (
                          <div className="text-xs text-slate-400 mt-1">
                            检查时间: {formatDate(item.checked_at)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        {/* Issues List */}
        <Card>
          <CardHeader>
            <CardTitle>问题列表</CardTitle>
          </CardHeader>
          <CardContent>
            {issues.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无问题</div>
            ) : (
              <div className="space-y-3">
                {issues.map((issue) => (
                  <div
                    key={issue.id}
                    className="border rounded-lg p-3"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="font-medium text-sm">{issue.item_name || '通用问题'}</div>
                        <div className="text-xs text-slate-500 mt-1">
                          {issue.category}
                        </div>
                      </div>
                      <Badge
                        className={cn(
                          issue.severity === 'CRITICAL' && 'bg-red-500',
                          issue.severity === 'MAJOR' && 'bg-orange-500',
                          issue.severity === 'MINOR' && 'bg-amber-500',
                          'bg-slate-500'
                        )}
                      >
                        {issue.severity === 'CRITICAL' ? '严重' :
                         issue.severity === 'MAJOR' ? '重要' :
                         issue.severity === 'MINOR' ? '一般' : issue.severity}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-600 mt-2">
                      {issue.description}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {issue.status === 'OPEN' ? '待处理' :
                       issue.status === 'IN_PROGRESS' ? '处理中' :
                       issue.status === 'RESOLVED' ? '已解决' : issue.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      {/* Update Item Dialog */}
      <Dialog open={showItemDialog} onOpenChange={setShowItemDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {selectedItem?.item_name} - 检查结果
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedItem && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">验收标准</div>
                  <div>{selectedItem.acceptance_criteria || '-'}</div>
                </div>
                {selectedItem.standard_value && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">标准值</div>
                    <div>{selectedItem.standard_value} {selectedItem.unit || ''}</div>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium mb-2 block">检查结果 *</label>
                  <Select
                    value={itemResult.result_status}
                    onValueChange={(val) => setItemResult({ ...itemResult, result_status: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(resultStatusConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {selectedItem.standard_value && (
                  <div>
                    <label className="text-sm font-medium mb-2 block">实际值</label>
                    <Input
                      value={itemResult.actual_value}
                      onChange={(e) => setItemResult({ ...itemResult, actual_value: e.target.value })}
                      placeholder="填写实际测量值"
                    />
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium mb-2 block">偏差</label>
                  <Input
                    value={itemResult.deviation}
                    onChange={(e) => setItemResult({ ...itemResult, deviation: e.target.value })}
                    placeholder="偏差说明"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">备注</label>
                  <Input
                    value={itemResult.remark}
                    onChange={(e) => setItemResult({ ...itemResult, remark: e.target.value })}
                    placeholder="备注说明"
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowItemDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdateItem}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Create Issue Dialog */}
      <Dialog open={showIssueDialog} onOpenChange={setShowIssueDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>上报问题</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">关联检查项</label>
                <Select
                  value={newIssue.item_id?.toString() || ''}
                  onValueChange={(val) => setNewIssue({ ...newIssue, item_id: val ? parseInt(val) : null })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择检查项" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">无</SelectItem>
                    {items.map((item) => (
                      <SelectItem key={item.id} value={item.id.toString()}>
                        {item.item_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">问题分类</label>
                <Input
                  value={newIssue.category}
                  onChange={(e) => setNewIssue({ ...newIssue, category: e.target.value })}
                  placeholder="问题分类"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">严重程度</label>
                <Select
                  value={newIssue.severity}
                  onValueChange={(val) => setNewIssue({ ...newIssue, severity: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CRITICAL">严重</SelectItem>
                    <SelectItem value="MAJOR">重要</SelectItem>
                    <SelectItem value="MINOR">一般</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">问题描述 *</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newIssue.description}
                  onChange={(e) => setNewIssue({ ...newIssue, description: e.target.value })}
                  placeholder="详细描述问题..."
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowIssueDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateIssue}>提交</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>完成验收</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">总体结果 *</label>
                <Select
                  value={completeData.overall_result}
                  onValueChange={(val) => setCompleteData({ ...completeData, overall_result: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(overallResultConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">验收结论</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={completeData.conclusion}
                  onChange={(e) => setCompleteData({ ...completeData, conclusion: e.target.value })}
                  placeholder="验收结论..."
                />
              </div>
              {completeData.overall_result === 'CONDITIONAL' && (
                <div>
                  <label className="text-sm font-medium mb-2 block">通过条件</label>
                  <textarea
                    className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={completeData.conditions}
                    onChange={(e) => setCompleteData({ ...completeData, conditions: e.target.value })}
                    placeholder="通过条件..."
                  />
                </div>
              )}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)}>
              取消
            </Button>
            <Button onClick={handleComplete}>完成验收</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

