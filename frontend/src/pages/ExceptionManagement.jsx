/**
 * Exception Management Page - 异常管理页面
 * Features: 异常事件列表、创建、处理、升级、统计分析
 */
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowUp,
  User,
  Calendar,
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
import { formatDate } from '../lib/utils'
import { exceptionApi, projectApi } from '../services/api'
const statusConfigs = {
  OPEN: { label: '待处理', color: 'bg-blue-500' },
  PROCESSING: { label: '处理中', color: 'bg-amber-500' },
  RESOLVED: { label: '已解决', color: 'bg-emerald-500' },
  CLOSED: { label: '已关闭', color: 'bg-slate-500' },
}
const severityConfigs = {
  LOW: { label: '低', color: 'bg-slate-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  CRITICAL: { label: '严重', color: 'bg-red-500' },
}
const typeConfigs = {
  SCHEDULE: { label: '进度异常', color: 'bg-blue-500' },
  QUALITY: { label: '质量异常', color: 'bg-red-500' },
  COST: { label: '成本异常', color: 'bg-amber-500' },
  RESOURCE: { label: '资源异常', color: 'bg-purple-500' },
  MATERIAL: { label: '物料异常', color: 'bg-cyan-500' },
  EQUIPMENT: { label: '设备异常', color: 'bg-violet-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}
export default function ExceptionManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [exceptions, setExceptions] = useState([])
  const [projects, setProjects] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterProject, setFilterProject] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showHandleDialog, setShowHandleDialog] = useState(false)
  const [selectedException, setSelectedException] = useState(null)
  // Form states
  const [newException, setNewException] = useState({
    project_id: null,
    machine_id: null,
    event_type: 'OTHER',
    severity: 'MEDIUM',
    event_title: '',
    event_description: '',
    impact_scope: 'LOCAL',
    schedule_impact: 0,
    cost_impact: 0,
    responsible_user_id: null,
    due_date: '',
  })
  const [handleData, setHandleData] = useState({
    action_type: 'HANDLE',
    action_description: '',
    next_status: 'PROCESSING',
  })
  useEffect(() => {
    fetchProjects()
    fetchExceptions()
  }, [filterProject, filterType, filterSeverity, filterStatus, searchKeyword])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    }
  }
  const fetchExceptions = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      if (filterType) params.event_type = filterType
      if (filterSeverity) params.severity = filterSeverity
      if (filterStatus) params.status = filterStatus
      if (searchKeyword) params.keyword = searchKeyword
      const res = await exceptionApi.list(params)
      const exceptionList = res.data?.items || res.data || []
      setExceptions(exceptionList)
    } catch (error) {
      console.error('Failed to fetch exceptions:', error)
      // 如果是演示账号，使用空数组
      const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
      if (isDemoAccount) {
        setExceptions([])
      } else {
        setExceptions([])
      }
    } finally {
      setLoading(false)
    }
  }
  const handleCreateException = async () => {
    if (!newException.event_title) {
      alert('请填写异常标题')
      return
    }
    try {
      await exceptionApi.create(newException)
      setShowCreateDialog(false)
      setNewException({
        project_id: null,
        machine_id: null,
        event_type: 'OTHER',
        severity: 'MEDIUM',
        event_title: '',
        event_description: '',
        impact_scope: 'LOCAL',
        schedule_impact: 0,
        cost_impact: 0,
        responsible_user_id: null,
        due_date: '',
      })
      fetchExceptions()
    } catch (error) {
      console.error('Failed to create exception:', error)
      const errorMessage = error.response?.data?.detail || error.message || '创建异常失败，请稍后重试'
      alert(errorMessage)
    }
  }
  const handleViewDetail = async (exceptionId) => {
    try {
      const res = await exceptionApi.get(exceptionId)
      setSelectedException(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch exception detail:', error)
    }
  }
  const handleException = async () => {
    if (!selectedException) return
    try {
      // Use update method to update status and add action description
      await exceptionApi.update(selectedException.id, {
        status: handleData.next_status,
        action_description: handleData.action_description || '',
        action_type: handleData.action_type,
      })
      setShowHandleDialog(false)
      setHandleData({
        action_type: 'HANDLE',
        action_description: '',
        next_status: 'PROCESSING',
      })
      fetchExceptions()
      if (showDetailDialog) {
        handleViewDetail(selectedException.id)
      }
    } catch (error) {
      console.error('Failed to handle exception:', error)
      const errorMessage = error.response?.data?.detail || error.message || '处理异常失败，请稍后重试'
      alert(errorMessage)
    }
  }
  const filteredExceptions = useMemo(() => {
    return exceptions.filter(exception => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          exception.event_no?.toLowerCase().includes(keyword) ||
          exception.event_title?.toLowerCase().includes(keyword) ||
          exception.event_description?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [exceptions, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="异常管理"
        description="异常事件管理，支持创建、处理、升级、统计分析"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索异常编号、标题..."
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
                <SelectItem value="">全部项目</SelectItem>
                {projects.map((proj) => (
                  <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterSeverity} onValueChange={setFilterSeverity}>
              <SelectTrigger>
                <SelectValue placeholder="选择严重程度" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部</SelectItem>
                {Object.entries(severityConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
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
          新建异常
        </Button>
      </div>
      {/* Exception List */}
      <Card>
        <CardHeader>
          <CardTitle>异常事件列表</CardTitle>
          <CardDescription>
            共 {filteredExceptions.length} 个异常事件
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredExceptions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无异常事件</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>异常编号</TableHead>
                  <TableHead>异常标题</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>严重程度</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>发现时间</TableHead>
                  <TableHead>责任人</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExceptions.map((exception) => (
                  <TableRow key={exception.id}>
                    <TableCell className="font-mono text-sm">
                      {exception.event_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {exception.event_title}
                    </TableCell>
                    <TableCell>{exception.project_name || '-'}</TableCell>
                    <TableCell>
                      <Badge className={typeConfigs[exception.event_type]?.color || 'bg-slate-500'}>
                        {typeConfigs[exception.event_type]?.label || exception.event_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={severityConfigs[exception.severity]?.color || 'bg-slate-500'}>
                        {severityConfigs[exception.severity]?.label || exception.severity}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[exception.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[exception.status]?.label || exception.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {exception.discovered_at ? formatDate(exception.discovered_at) : '-'}
                    </TableCell>
                    <TableCell>
                      {exception.responsible_user_name ? (
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-slate-400" />
                          <span className="text-sm">{exception.responsible_user_name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">未分配</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(exception.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {exception.status === 'OPEN' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedException(exception)
                              setShowHandleDialog(true)
                            }}
                          >
                            <Edit className="w-4 h-4" />
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
      {/* Create Exception Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建异常事件</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">异常标题 *</label>
                <Input
                  value={newException.event_title}
                  onChange={(e) => setNewException({ ...newException, event_title: e.target.value })}
                  placeholder="请输入异常标题"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">项目</label>
                  <Select
                    value={newException.project_id?.toString() || ''}
                    onValueChange={(val) => setNewException({ ...newException, project_id: val ? parseInt(val) : null })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">无</SelectItem>
                      {projects.map((proj) => (
                        <SelectItem key={proj.id} value={proj.id.toString()}>
                          {proj.project_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">异常类型</label>
                  <Select
                    value={newException.event_type}
                    onValueChange={(val) => setNewException({ ...newException, event_type: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">严重程度</label>
                  <Select
                    value={newException.severity}
                    onValueChange={(val) => setNewException({ ...newException, severity: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(severityConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">影响范围</label>
                  <Select
                    value={newException.impact_scope}
                    onValueChange={(val) => setNewException({ ...newException, impact_scope: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LOCAL">局部</SelectItem>
                      <SelectItem value="PROJECT">项目级</SelectItem>
                      <SelectItem value="SYSTEM">系统级</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">异常描述</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newException.event_description}
                  onChange={(e) => setNewException({ ...newException, event_description: e.target.value })}
                  placeholder="详细描述异常情况..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">进度影响（天）</label>
                  <Input
                    type="number"
                    value={newException.schedule_impact}
                    onChange={(e) => setNewException({ ...newException, schedule_impact: parseFloat(e.target.value) || 0 })}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">成本影响（元）</label>
                  <Input
                    type="number"
                    value={newException.cost_impact}
                    onChange={(e) => setNewException({ ...newException, cost_impact: parseFloat(e.target.value) || 0 })}
                    placeholder="0"
                  />
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateException}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Exception Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedException?.event_title} - {selectedException?.event_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedException && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常编号</div>
                    <div className="font-mono">{selectedException.event_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedException.status]?.color}>
                      {statusConfigs[selectedException.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedException.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常类型</div>
                    <Badge className={typeConfigs[selectedException.event_type]?.color}>
                      {typeConfigs[selectedException.event_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">严重程度</div>
                    <Badge className={severityConfigs[selectedException.severity]?.color}>
                      {severityConfigs[selectedException.severity]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">发现时间</div>
                    <div>{selectedException.discovered_at ? formatDate(selectedException.discovered_at) : '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">进度影响</div>
                    <div>{selectedException.schedule_impact || 0} 天</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">成本影响</div>
                    <div>¥{selectedException.cost_impact || 0}</div>
                  </div>
                </div>
                {selectedException.event_description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常描述</div>
                    <div>{selectedException.event_description}</div>
                  </div>
                )}
                {selectedException.impact_description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">影响说明</div>
                    <div>{selectedException.impact_description}</div>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedException && selectedException.status === 'OPEN' && (
              <Button onClick={() => {
                setShowDetailDialog(false)
                setShowHandleDialog(true)
              }}>
                <Edit className="w-4 h-4 mr-2" />
                处理异常
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Handle Exception Dialog */}
      <Dialog open={showHandleDialog} onOpenChange={setShowHandleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>处理异常</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedException && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常标题</div>
                  <div className="font-medium">{selectedException.event_title}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">处理状态</label>
                  <Select
                    value={handleData.next_status}
                    onValueChange={(val) => setHandleData({ ...handleData, next_status: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PROCESSING">处理中</SelectItem>
                      <SelectItem value="RESOLVED">已解决</SelectItem>
                      <SelectItem value="CLOSED">已关闭</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">处理说明</label>
                  <textarea
                    className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={handleData.action_description}
                    onChange={(e) => setHandleData({ ...handleData, action_description: e.target.value })}
                    placeholder="填写处理措施和结果..."
                  />
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowHandleDialog(false)}>
              取消
            </Button>
            <Button onClick={handleException}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

