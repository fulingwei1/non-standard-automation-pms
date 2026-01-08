/**
 * Material Requisition List Page - 领料单管理页面
 * Features: 领料单列表、创建、审批、发料
 */
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Package,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  TrendingUp,
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
import { productionApi, projectApi } from '../services/api'
const statusConfigs = {
  PENDING: { label: '待审批', color: 'bg-blue-500' },
  APPROVED: { label: '已批准', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
  ISSUED: { label: '已发料', color: 'bg-violet-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}
export default function MaterialRequisitionList() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [requisitions, setRequisitions] = useState([])
  const [projects, setProjects] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterProject, setFilterProject] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [selectedRequisition, setSelectedRequisition] = useState(null)
  // Form states
  const [newRequisition, setNewRequisition] = useState({
    work_order_id: null,
    project_id: null,
    apply_reason: '',
    items: [],
  })
  const [approveData, setApproveData] = useState({
    approved_qty: {},
    approve_comment: '',
  })
  useEffect(() => {
    fetchProjects()
    fetchRequisitions()
  }, [filterProject, filterStatus, searchKeyword])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    }
  }
  const fetchRequisitions = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      if (filterStatus) params.status = filterStatus
      if (searchKeyword) params.search = searchKeyword
      const res = await productionApi.materialRequisitions.list(params)
      const reqList = res.data?.items || res.data || []
      setRequisitions(reqList)
    } catch (error) {
      console.error('Failed to fetch requisitions:', error)
    } finally {
      setLoading(false)
    }
  }
  const handleCreateRequisition = async () => {
    if (!newRequisition.apply_reason || newRequisition.items.length === 0) {
      alert('请填写申请原因和物料明细')
      return
    }
    try {
      await productionApi.materialRequisitions.create(newRequisition)
      setShowCreateDialog(false)
      setNewRequisition({
        work_order_id: null,
        project_id: null,
        apply_reason: '',
        items: [],
      })
      fetchRequisitions()
    } catch (error) {
      console.error('Failed to create requisition:', error)
      alert('创建领料单失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleViewDetail = async (reqId) => {
    try {
      const res = await productionApi.materialRequisitions.get(reqId)
      setSelectedRequisition(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch requisition detail:', error)
    }
  }
  const handleApprove = async () => {
    if (!selectedRequisition) return
    try {
      await productionApi.materialRequisitions.approve(selectedRequisition.id, approveData)
      setShowApproveDialog(false)
      setApproveData({
        approved_qty: {},
        approve_comment: '',
      })
      fetchRequisitions()
      if (showDetailDialog) {
        handleViewDetail(selectedRequisition.id)
      }
    } catch (error) {
      console.error('Failed to approve requisition:', error)
      alert('审批失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredRequisitions = useMemo(() => {
    return requisitions.filter(req => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          req.requisition_no?.toLowerCase().includes(keyword) ||
          req.work_order_no?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [requisitions, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="领料单管理"
        description="领料单列表、创建、审批、发料"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索领料单号、工单号..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((proj) => (
                  <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建领料单
        </Button>
      </div>
      {/* Requisition List */}
      <Card>
        <CardHeader>
          <CardTitle>领料单列表</CardTitle>
          <CardDescription>
            共 {filteredRequisitions.length} 个领料单
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredRequisitions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无领料单</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>领料单号</TableHead>
                  <TableHead>工单号</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>申请原因</TableHead>
                  <TableHead>物料项数</TableHead>
                  <TableHead>申请时间</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRequisitions.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell className="font-mono text-sm">
                      {req.requisition_no}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {req.work_order_no || '-'}
                    </TableCell>
                    <TableCell>{req.project_name || '-'}</TableCell>
                    <TableCell className="max-w-xs truncate">
                      {req.apply_reason || '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{req.items?.length || 0} 项</Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {req.apply_time ? formatDate(req.apply_time) : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[req.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[req.status]?.label || req.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(req.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {req.status === 'PENDING' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedRequisition(req)
                              setShowApproveDialog(true)
                            }}
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {/* Create Requisition Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建领料单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">项目</label>
                <Select
                  value={newRequisition.project_id?.toString() || ''}
                  onValueChange={(val) => setNewRequisition({ ...newRequisition, project_id: val ? parseInt(val) : null })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">无</SelectItem>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">申请原因 *</label>
                <Input
                  value={newRequisition.apply_reason}
                  onChange={(e) => setNewRequisition({ ...newRequisition, apply_reason: e.target.value })}
                  placeholder="填写申请原因"
                />
              </div>
              <div className="text-sm text-slate-500">
                物料明细需要单独添加，创建后可在详情页添加物料项
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateRequisition}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Requisition Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedRequisition?.requisition_no} - 领料单详情
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedRequisition && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">领料单号</div>
                    <div className="font-mono">{selectedRequisition.requisition_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedRequisition.status]?.color}>
                      {statusConfigs[selectedRequisition.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工单号</div>
                    <div className="font-mono">{selectedRequisition.work_order_no || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedRequisition.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">申请时间</div>
                    <div>{selectedRequisition.apply_time ? formatDate(selectedRequisition.apply_time) : '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">申请原因</div>
                    <div>{selectedRequisition.apply_reason || '-'}</div>
                  </div>
                </div>
                {selectedRequisition.items && selectedRequisition.items.length > 0 && (
                  <div>
                    <div className="text-sm font-medium mb-3">物料明细</div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>物料编码</TableHead>
                          <TableHead>物料名称</TableHead>
                          <TableHead>申请数量</TableHead>
                          <TableHead>批准数量</TableHead>
                          <TableHead>已发数量</TableHead>
                          <TableHead>单位</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedRequisition.items.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell className="font-mono text-sm">
                              {item.material_code}
                            </TableCell>
                            <TableCell>{item.material_name}</TableCell>
                            <TableCell>{item.request_qty}</TableCell>
                            <TableCell className="font-medium">
                              {item.approved_qty || '-'}
                            </TableCell>
                            <TableCell className="font-medium text-emerald-600">
                              {item.issued_qty || 0}
                            </TableCell>
                            <TableCell>{item.unit}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedRequisition && selectedRequisition.status === 'PENDING' && (
              <Button onClick={() => {
                setShowDetailDialog(false)
                setShowApproveDialog(true)
              }}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                审批
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Approve Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>审批领料单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedRequisition && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">领料单号</div>
                  <div className="font-mono">{selectedRequisition.requisition_no}</div>
                </div>
                {selectedRequisition.items && selectedRequisition.items.length > 0 && (
                  <div>
                    <div className="text-sm font-medium mb-2">批准数量</div>
                    <div className="space-y-2">
                      {selectedRequisition.items.map((item) => (
                        <div key={item.id} className="flex items-center gap-2">
                          <div className="flex-1 text-sm">
                            {item.material_name} (申请: {item.request_qty})
                          </div>
                          <Input
                            type="number"
                            className="w-24"
                            value={approveData.approved_qty[item.id] || item.request_qty}
                            onChange={(e) => setApproveData({
                              ...approveData,
                              approved_qty: {
                                ...approveData.approved_qty,
                                [item.id]: parseFloat(e.target.value) || 0
                              }
                            })}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div>
                  <label className="text-sm font-medium mb-2 block">审批意见</label>
                  <Input
                    value={approveData.approve_comment}
                    onChange={(e) => setApproveData({ ...approveData, approve_comment: e.target.value })}
                    placeholder="审批意见"
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
              取消
            </Button>
            <Button onClick={handleApprove}>批准</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

