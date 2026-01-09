/**
 * Installation Dispatch Management Page - 安装调试派工管理页面
 * Features: 安装调试派工单管理、批量派工、进度跟踪
 */

import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Plus, Search, Filter, Eye, Edit, Users, CheckSquare, Square,
  Clock, AlertTriangle, Calendar, MapPin, User, Settings,
  Play, CheckCircle2, XCircle, RefreshCw, Download,
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
import { Textarea } from '../components/ui/textarea'
import { cn, formatDate } from '../lib/utils'
import { installationDispatchApi, userApi, projectApi, machineApi } from '../services/api'
import { toast } from '../components/ui/toast'

const statusConfig = {
  PENDING: { label: '待派工', color: 'bg-slate-500', textColor: 'text-slate-400' },
  ASSIGNED: { label: '已派工', color: 'bg-blue-500', textColor: 'text-blue-400' },
  IN_PROGRESS: { label: '进行中', color: 'bg-amber-500', textColor: 'text-amber-400' },
  COMPLETED: { label: '已完成', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  CANCELLED: { label: '已取消', color: 'bg-red-500', textColor: 'text-red-400' },
}

const priorityConfig = {
  LOW: { label: '低', color: 'text-slate-400', bg: 'bg-slate-500/20' },
  NORMAL: { label: '普通', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  HIGH: { label: '高', color: 'text-amber-400', bg: 'bg-amber-500/20' },
  URGENT: { label: '紧急', color: 'text-red-400', bg: 'bg-red-500/20' },
}

const taskTypeConfig = {
  INSTALLATION: { label: '安装', icon: '🔧' },
  DEBUGGING: { label: '调试', icon: '⚙️' },
  TRAINING: { label: '培训', icon: '👥' },
  MAINTENANCE: { label: '维护', icon: '🔨' },
  REPAIR: { label: '维修', icon: '🛠️' },
  OTHER: { label: '其他', icon: '📋' },
}

export default function InstallationDispatchManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [orders, setOrders] = useState([])
  const [users, setUsers] = useState([])
  const [projects, setProjects] = useState([])
  const [machines, setMachines] = useState([])
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    assigned: 0,
    in_progress: 0,
    completed: 0,
    cancelled: 0,
    urgent: 0,
  })
  
  // Filters
  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  const [filterProject, setFilterProject] = useState('')
  const [filterTaskType, setFilterTaskType] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  
  // Selection
  const [selectedOrders, setSelectedOrders] = useState(new Set())
  const [showAssignDialog, setShowAssignDialog] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showProgressDialog, setShowProgressDialog] = useState(false)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [progressData, setProgressData] = useState({ progress: 0, execution_notes: '' })
  const [completeData, setCompleteData] = useState({
    actual_hours: '',
    execution_notes: '',
    issues_found: '',
    solution_provided: '',
    photos: [],
  })
  
  const [assignData, setAssignData] = useState({
    assigned_to_id: null,
    remark: '',
  })
  
  const [createData, setCreateData] = useState({
    project_id: '',
    machine_id: '',
    customer_id: '',
    task_type: 'INSTALLATION',
    task_title: '',
    task_description: '',
    location: '',
    scheduled_date: '',
    estimated_hours: '',
    priority: 'NORMAL',
    customer_contact: '',
    customer_phone: '',
    customer_address: '',
    remark: '',
  })

  useEffect(() => {
    fetchUsers()
    fetchProjects()
    fetchOrders()
    fetchStatistics()
  }, [filterStatus, filterPriority, filterProject, filterTaskType, searchQuery])

  useEffect(() => {
    if (createData.project_id) {
      fetchMachines(createData.project_id)
    } else {
      setMachines([])
    }
  }, [createData.project_id])

  const fetchUsers = async () => {
    try {
      const res = await userApi.list({ page_size: 1000 })
      setUsers(res.data?.items || res.data || [])
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const fetchMachines = async (projectId) => {
    try {
      const res = await machineApi.list({ project_id: projectId, page_size: 1000 })
      setMachines(res.data?.items || res.data || [])
    } catch (error) {
      setMachines([])
    }
  }

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterStatus) params.status = filterStatus
      if (filterPriority) params.priority = filterPriority
      if (filterProject) params.project_id = filterProject
      if (filterTaskType) params.task_type = filterTaskType
      if (searchQuery) params.keyword = searchQuery
      
      const res = await installationDispatchApi.orders.list(params)
      const orderList = res.data?.items || res.data || []
      setOrders(orderList)
    } catch (error) {
      toast.error('加载派工单失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const res = await installationDispatchApi.statistics()
      setStats(res.data || {})
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const handleSelectOrder = (orderId) => {
    const newSelected = new Set(selectedOrders)
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId)
    } else {
      newSelected.add(orderId)
    }
    setSelectedOrders(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedOrders.size === pendingOrders.length) {
      setSelectedOrders(new Set())
    } else {
      setSelectedOrders(new Set(pendingOrders.map(o => o.id)))
    }
  }

  const handleBatchAssign = async () => {
    if (selectedOrders.size === 0) {
      toast.error('请选择要派工的派工单')
      return
    }
    if (!assignData.assigned_to_id) {
      toast.error('请选择派工人员')
      return
    }
    try {
      await installationDispatchApi.orders.batchAssign({
        order_ids: Array.from(selectedOrders),
        assigned_to_id: assignData.assigned_to_id,
        remark: assignData.remark,
      })
      setShowAssignDialog(false)
      setSelectedOrders(new Set())
      setAssignData({ assigned_to_id: null, remark: '' })
      fetchOrders()
      fetchStatistics()
      toast.success(`成功派工 ${selectedOrders.size} 个派工单`)
    } catch (error) {
      toast.error('派工失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCreate = async () => {
    try {
      // 从项目获取customer_id
      const selectedProject = projects.find(p => p.id.toString() === createData.project_id)
      if (!selectedProject) {
        toast.error('请选择项目')
        return
      }
      
      const createPayload = {
        ...createData,
        project_id: parseInt(createData.project_id),
        customer_id: selectedProject.customer_id,
        machine_id: createData.machine_id ? parseInt(createData.machine_id) : null,
        estimated_hours: createData.estimated_hours ? parseFloat(createData.estimated_hours) : null,
      }
      
      await installationDispatchApi.orders.create(createPayload)
      setShowCreateDialog(false)
      setCreateData({
        project_id: '',
        machine_id: '',
        customer_id: '',
        task_type: 'INSTALLATION',
        task_title: '',
        task_description: '',
        location: '',
        scheduled_date: '',
        estimated_hours: '',
        priority: 'NORMAL',
        customer_contact: '',
        customer_phone: '',
        customer_address: '',
        remark: '',
      })
      fetchOrders()
      fetchStatistics()
      toast.success('创建派工单成功')
    } catch (error) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleViewDetail = async (orderId) => {
    try {
      const res = await installationDispatchApi.orders.get(orderId)
      setSelectedOrder(res.data)
      setShowDetailDialog(true)
    } catch (error) {
      toast.error('加载详情失败')
    }
  }

  const handleStart = async () => {
    if (!selectedOrder) return
    try {
      await installationDispatchApi.orders.start(selectedOrder.id, {})
      toast.success('任务已开始')
      handleViewDetail(selectedOrder.id)
      fetchOrders()
      fetchStatistics()
    } catch (error) {
      toast.error('开始任务失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleUpdateProgress = async (progress, notes) => {
    if (!selectedOrder) return
    try {
      await installationDispatchApi.orders.progress(selectedOrder.id, {
        progress: progress,
        execution_notes: notes,
      })
      toast.success('进度已更新')
      handleViewDetail(selectedOrder.id)
      fetchOrders()
    } catch (error) {
      toast.error('更新进度失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleComplete = async (completeData) => {
    if (!selectedOrder) return
    try {
      await installationDispatchApi.orders.complete(selectedOrder.id, completeData)
      toast.success('任务已完成')
      setShowDetailDialog(false)
      setSelectedOrder(null)
      fetchOrders()
      fetchStatistics()
    } catch (error) {
      toast.error('完成任务失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleAssign = async (assignData) => {
    if (!selectedOrder) return
    try {
      await installationDispatchApi.orders.assign(selectedOrder.id, assignData)
      toast.success('派工成功')
      handleViewDetail(selectedOrder.id)
      fetchOrders()
      fetchStatistics()
    } catch (error) {
      toast.error('派工失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const pendingOrders = useMemo(() => {
    return orders.filter(o => o.status === 'PENDING')
  }, [orders])

  const filteredOrders = useMemo(() => {
    let filtered = orders
    if (filterStatus) {
      filtered = filtered.filter(o => o.status === filterStatus)
    }
    if (filterPriority) {
      filtered = filtered.filter(o => o.priority === filterPriority)
    }
    if (filterProject) {
      filtered = filtered.filter(o => o.project_id === parseInt(filterProject))
    }
    if (filterTaskType) {
      filtered = filtered.filter(o => o.task_type === filterTaskType)
    }
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(o => 
        o.order_no?.toLowerCase().includes(query) ||
        o.task_title?.toLowerCase().includes(query)
      )
    }
    return filtered
  }, [orders, filterStatus, filterPriority, filterProject, filterTaskType, searchQuery])

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="安装调试派工管理"
        description="管理现场安装调试任务派工、进度跟踪"
      />
      
      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-sm text-slate-500">总数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-slate-500">{stats.pending}</div>
            <div className="text-sm text-slate-500">待派工</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-500">{stats.assigned}</div>
            <div className="text-sm text-slate-500">已派工</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-amber-500">{stats.in_progress}</div>
            <div className="text-sm text-slate-500">进行中</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-emerald-500">{stats.completed}</div>
            <div className="text-sm text-slate-500">已完成</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-500">{stats.cancelled}</div>
            <div className="text-sm text-slate-500">已取消</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-500">{stats.urgent}</div>
            <div className="text-sm text-slate-500">紧急</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
            <div className="lg:col-span-2">
              <Input
                placeholder="搜索派工单号或任务标题..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="PENDING">待派工</SelectItem>
                <SelectItem value="ASSIGNED">已派工</SelectItem>
                <SelectItem value="IN_PROGRESS">进行中</SelectItem>
                <SelectItem value="COMPLETED">已完成</SelectItem>
                <SelectItem value="CANCELLED">已取消</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部优先级</SelectItem>
                <SelectItem value="LOW">低</SelectItem>
                <SelectItem value="NORMAL">普通</SelectItem>
                <SelectItem value="HIGH">高</SelectItem>
                <SelectItem value="URGENT">紧急</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterTaskType} onValueChange={setFilterTaskType}>
              <SelectTrigger>
                <SelectValue placeholder="任务类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="INSTALLATION">安装</SelectItem>
                <SelectItem value="DEBUGGING">调试</SelectItem>
                <SelectItem value="TRAINING">培训</SelectItem>
                <SelectItem value="MAINTENANCE">维护</SelectItem>
                <SelectItem value="REPAIR">维修</SelectItem>
                <SelectItem value="OTHER">其他</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((p) => (
                  <SelectItem key={p.id} value={p.id.toString()}>
                    {p.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Action Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">
            已选择 {selectedOrders.size} 个派工单
          </span>
          {selectedOrders.size > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedOrders(new Set())}
            >
              清空选择
            </Button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => {
              fetchOrders()
              fetchStatistics()
            }}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
          <Button
            onClick={() => setShowCreateDialog(true)}
          >
            <Plus className="w-4 h-4 mr-2" />
            创建派工单
          </Button>
          <Button
            onClick={() => setShowAssignDialog(true)}
            disabled={selectedOrders.size === 0}
          >
            <Users className="w-4 h-4 mr-2" />
            批量派工 ({selectedOrders.size})
          </Button>
        </div>
      </div>

      {/* Order List */}
      <Card>
        <CardHeader>
          <CardTitle>派工单列表</CardTitle>
          <CardDescription>
            共 {filteredOrders.length} 个派工单
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无派工单</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleSelectAll}
                    >
                      {selectedOrders.size === pendingOrders.length && pendingOrders.length > 0 ? (
                        <CheckSquare className="w-4 h-4" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                    </Button>
                  </TableHead>
                  <TableHead>派工单号</TableHead>
                  <TableHead>任务标题</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>任务类型</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>派工人员</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => {
                  const status = statusConfig[order.status] || statusConfig.PENDING
                  const priority = priorityConfig[order.priority] || priorityConfig.NORMAL
                  const taskType = taskTypeConfig[order.task_type] || taskTypeConfig.OTHER
                  return (
                    <TableRow
                      key={order.id}
                      className={cn(
                        selectedOrders.has(order.id) && 'bg-blue-50'
                      )}
                    >
                      <TableCell>
                        {order.status === 'PENDING' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSelectOrder(order.id)}
                          >
                            {selectedOrders.has(order.id) ? (
                              <CheckSquare className="w-4 h-4" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </Button>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {order.order_no}
                      </TableCell>
                      <TableCell className="font-medium">
                        {order.task_title}
                      </TableCell>
                      <TableCell>{order.project_name || '-'}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {taskType.icon} {taskType.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-500 text-sm">
                        {order.scheduled_date ? formatDate(order.scheduled_date) : '-'}
                      </TableCell>
                      <TableCell>{order.assigned_to_name || '-'}</TableCell>
                      <TableCell>
                        <Badge className={status.color}>
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={cn(priority.color, priority.bg)}>
                          {priority.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-200 rounded-full h-2">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${order.progress || 0}%` }}
                            />
                          </div>
                          <span className="text-sm text-slate-500">{order.progress || 0}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(order.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Batch Assign Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量派工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-2">
                  已选择 {selectedOrders.size} 个派工单
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">选择派工人员 *</label>
                <Select
                  value={assignData.assigned_to_id?.toString() || ''}
                  onValueChange={(val) => setAssignData({ ...assignData, assigned_to_id: val ? parseInt(val) : null })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择派工人员" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id.toString()}>
                        {user.real_name || user.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">派工备注</label>
                <Textarea
                  value={assignData.remark}
                  onChange={(e) => setAssignData({ ...assignData, remark: e.target.value })}
                  placeholder="派工备注"
                  rows={3}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignDialog(false)}>
              取消
            </Button>
            <Button onClick={handleBatchAssign} disabled={!assignData.assigned_to_id}>
              确认派工
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建安装调试派工单</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">项目 *</label>
                  <Select
                    value={createData.project_id}
                    onValueChange={(val) => setCreateData({ ...createData, project_id: val, machine_id: '' })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      {projects.map((p) => (
                        <SelectItem key={p.id} value={p.id.toString()}>
                          {p.project_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">机台（可选）</label>
                  <Select
                    value={createData.machine_id}
                    onValueChange={(val) => setCreateData({ ...createData, machine_id: val })}
                    disabled={!createData.project_id}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={createData.project_id ? "选择机台" : "请先选择项目"} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">不选择机台</SelectItem>
                      {machines.map((m) => (
                        <SelectItem key={m.id} value={m.id.toString()}>
                          {m.machine_no} - {m.machine_name || ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">任务类型 *</label>
                <Select
                  value={createData.task_type}
                  onValueChange={(val) => setCreateData({ ...createData, task_type: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择任务类型" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="INSTALLATION">安装</SelectItem>
                    <SelectItem value="DEBUGGING">调试</SelectItem>
                    <SelectItem value="TRAINING">培训</SelectItem>
                    <SelectItem value="MAINTENANCE">维护</SelectItem>
                    <SelectItem value="REPAIR">维修</SelectItem>
                    <SelectItem value="OTHER">其他</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">任务标题 *</label>
                <Input
                  value={createData.task_title}
                  onChange={(e) => setCreateData({ ...createData, task_title: e.target.value })}
                  placeholder="任务标题"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">任务描述</label>
                <Textarea
                  value={createData.task_description}
                  onChange={(e) => setCreateData({ ...createData, task_description: e.target.value })}
                  placeholder="任务描述"
                  rows={3}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">计划日期 *</label>
                  <Input
                    type="date"
                    value={createData.scheduled_date}
                    onChange={(e) => setCreateData({ ...createData, scheduled_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">预计工时（小时）</label>
                  <Input
                    type="number"
                    value={createData.estimated_hours}
                    onChange={(e) => setCreateData({ ...createData, estimated_hours: e.target.value })}
                    placeholder="8.0"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">现场地点</label>
                <Input
                  value={createData.location}
                  onChange={(e) => setCreateData({ ...createData, location: e.target.value })}
                  placeholder="现场地点"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">优先级</label>
                <Select
                  value={createData.priority}
                  onValueChange={(val) => setCreateData({ ...createData, priority: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择优先级" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">低</SelectItem>
                    <SelectItem value="NORMAL">普通</SelectItem>
                    <SelectItem value="HIGH">高</SelectItem>
                    <SelectItem value="URGENT">紧急</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate} disabled={!createData.project_id || !createData.task_title || !createData.scheduled_date}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      {selectedOrder && (
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>派工单详情</DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500">派工单号</div>
                    <div className="font-mono">{selectedOrder.order_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500">状态</div>
                    <Badge className={statusConfig[selectedOrder.status]?.color}>
                      {statusConfig[selectedOrder.status]?.label}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500">任务标题</div>
                  <div className="font-medium">{selectedOrder.task_title}</div>
                </div>
                {selectedOrder.task_description && (
                  <div>
                    <div className="text-sm text-slate-500">任务描述</div>
                    <div>{selectedOrder.task_description}</div>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500">项目</div>
                    <div>{selectedOrder.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500">计划日期</div>
                    <div>{selectedOrder.scheduled_date ? formatDate(selectedOrder.scheduled_date) : '-'}</div>
                  </div>
                </div>
                {selectedOrder.assigned_to_name && (
                  <div>
                    <div className="text-sm text-slate-500">派工人员</div>
                    <div>{selectedOrder.assigned_to_name}</div>
                  </div>
                )}
                {selectedOrder.progress !== undefined && (
                  <div>
                    <div className="text-sm text-slate-500 mb-2">进度</div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${selectedOrder.progress || 0}%` }}
                        />
                      </div>
                      <span className="text-sm text-slate-500">{selectedOrder.progress || 0}%</span>
                    </div>
                  </div>
                )}
              </div>
            </DialogBody>
            <DialogFooter className="flex justify-between">
              <div className="flex gap-2">
                {selectedOrder.status === 'PENDING' && (
                  <Button onClick={() => {
                    setShowAssignDialog(true)
                    setAssignData({ assigned_to_id: selectedOrder.assigned_to_id, remark: '' })
                  }}>
                    <Users className="w-4 h-4 mr-2" />
                    派工
                  </Button>
                )}
                {selectedOrder.status === 'ASSIGNED' && (
                  <Button onClick={handleStart}>
                    <Play className="w-4 h-4 mr-2" />
                    开始任务
                  </Button>
                )}
                {selectedOrder.status === 'IN_PROGRESS' && (
                  <>
                    <Button variant="outline" onClick={() => {
                      setShowProgressDialog(true)
                      setProgressData({ progress: selectedOrder.progress || 0, execution_notes: selectedOrder.execution_notes || '' })
                    }}>
                      <Clock className="w-4 h-4 mr-2" />
                      更新进度
                    </Button>
                    <Button onClick={() => {
                      setShowCompleteDialog(true)
                      setCompleteData({
                        actual_hours: '',
                        execution_notes: '',
                        issues_found: '',
                        solution_provided: '',
                        photos: [],
                      })
                    }}>
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      完成任务
                    </Button>
                  </>
                )}
              </div>
              <Button variant="outline" onClick={() => {
                setShowDetailDialog(false)
                setSelectedOrder(null)
              }}>
                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Progress Dialog */}
      <Dialog open={showProgressDialog} onOpenChange={setShowProgressDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>更新进度</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">进度百分比 *</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={progressData.progress}
                  onChange={(e) => setProgressData({ ...progressData, progress: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">执行说明</label>
                <Textarea
                  value={progressData.execution_notes}
                  onChange={(e) => setProgressData({ ...progressData, execution_notes: e.target.value })}
                  placeholder="记录执行情况..."
                  rows={4}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowProgressDialog(false)}>取消</Button>
            <Button onClick={async () => {
              await handleUpdateProgress(progressData.progress, progressData.execution_notes)
              setShowProgressDialog(false)
            }}>更新</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>完成任务</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">实际工时（小时）</label>
                  <Input
                    type="number"
                    value={completeData.actual_hours}
                    onChange={(e) => setCompleteData({ ...completeData, actual_hours: e.target.value })}
                    placeholder="8.0"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">执行说明</label>
                <Textarea
                  value={completeData.execution_notes}
                  onChange={(e) => setCompleteData({ ...completeData, execution_notes: e.target.value })}
                  placeholder="记录任务完成情况..."
                  rows={4}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">发现的问题</label>
                <Textarea
                  value={completeData.issues_found}
                  onChange={(e) => setCompleteData({ ...completeData, issues_found: e.target.value })}
                  placeholder="记录发现的问题..."
                  rows={3}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">提供的解决方案</label>
                <Textarea
                  value={completeData.solution_provided}
                  onChange={(e) => setCompleteData({ ...completeData, solution_provided: e.target.value })}
                  placeholder="记录提供的解决方案..."
                  rows={3}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteDialog(false)}>取消</Button>
            <Button onClick={async () => {
              await handleComplete(completeData)
              setShowCompleteDialog(false)
            }}>完成</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Dialog in Detail */}
      <Dialog open={showAssignDialog && selectedOrder} onOpenChange={(open) => {
        if (!open) setShowAssignDialog(false)
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>派工</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">选择派工人员 *</label>
                <Select
                  value={assignData.assigned_to_id?.toString() || ''}
                  onValueChange={(val) => setAssignData({ ...assignData, assigned_to_id: val ? parseInt(val) : null })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择派工人员" />
                  </SelectTrigger>
                  <SelectContent>
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id.toString()}>
                        {user.real_name || user.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">派工备注</label>
                <Textarea
                  value={assignData.remark}
                  onChange={(e) => setAssignData({ ...assignData, remark: e.target.value })}
                  placeholder="派工备注"
                  rows={3}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignDialog(false)}>取消</Button>
            <Button onClick={async () => {
              if (!assignData.assigned_to_id) {
                toast.error('请选择派工人员')
                return
              }
              await handleAssign(assignData)
              setShowAssignDialog(false)
            }} disabled={!assignData.assigned_to_id}>确认派工</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
