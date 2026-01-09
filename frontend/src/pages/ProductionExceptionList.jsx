/**
 * Production Exception List Page - 生产异常管理页面
 * Features: 生产异常列表、上报、处理、关闭
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
  CheckCircle2,
  Clock,
  XCircle,
  User,
  Package,
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
  REPORTED: { label: '已上报', color: 'bg-blue-500' },
  IN_PROGRESS: { label: '处理中', color: 'bg-amber-500' },
  RESOLVED: { label: '已解决', color: 'bg-emerald-500' },
  CLOSED: { label: '已关闭', color: 'bg-slate-500' },
}
const typeConfigs = {
  MATERIAL: { label: '物料异常', color: 'bg-amber-500' },
  EQUIPMENT: { label: '设备异常', color: 'bg-red-500' },
  QUALITY: { label: '质量异常', color: 'bg-purple-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}
const levelConfigs = {
  CRITICAL: { label: '严重', color: 'bg-red-500' },
  MAJOR: { label: '重要', color: 'bg-orange-500' },
  MINOR: { label: '一般', color: 'bg-amber-500' },
  LOW: { label: '轻微', color: 'bg-blue-500' },
}
export default function ProductionExceptionList() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [exceptions, setExceptions] = useState([])
  const [projects, setProjects] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterProject, setFilterProject] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterLevel, setFilterLevel] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showHandleDialog, setShowHandleDialog] = useState(false)
  const [selectedException, setSelectedException] = useState(null)
  // Form states
  const [newException, setNewException] = useState({
    exception_type: 'MATERIAL',
    exception_level: 'MINOR',
    title: '',
    description: '',
    work_order_id: null,
    project_id: null,
    workshop_id: null,
    equipment_id: null,
    impact_hours: 0,
    impact_cost: 0,
    remark: '',
  })
  const [handleData, setHandleData] = useState({
    handle_plan: '',
    handle_result: '',
  })
  useEffect(() => {
    fetchProjects()
    fetchExceptions()
  }, [filterProject, filterType, filterLevel, filterStatus, searchKeyword])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  const fetchExceptions = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      if (filterType) params.exception_type = filterType
      if (filterLevel) params.exception_level = filterLevel
      if (filterStatus) params.status = filterStatus
      if (searchKeyword) params.search = searchKeyword
      const res = await productionApi.exceptions.list(params)
      const excList = res.data?.items || res.data || []
      setExceptions(excList)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }
  const handleCreateException = async () => {
    if (!newException.title) {
      alert('请填写异常标题')
      return
    }
    try {
      await productionApi.exceptions.create(newException)
      setShowCreateDialog(false)
      setNewException({
        exception_type: 'MATERIAL',
        exception_level: 'MINOR',
        title: '',
        description: '',
        work_order_id: null,
        project_id: null,
        workshop_id: null,
        equipment_id: null,
        impact_hours: 0,
        impact_cost: 0,
        remark: '',
      })
      fetchExceptions()
    } catch (error) {
      alert('上报异常失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleViewDetail = async (excId) => {
    try {
      const res = await productionApi.exceptions.get(excId)
      setSelectedException(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  const handleException = async () => {
    if (!selectedException) return
    try {
      await productionApi.exceptions.handle(selectedException.id, handleData)
      setShowHandleDialog(false)
      setHandleData({
        handle_plan: '',
        handle_result: '',
      })
      fetchExceptions()
      if (showDetailDialog) {
        handleViewDetail(selectedException.id)
      }
    } catch (error) {
      alert('处理异常失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleClose = async (excId) => {
    if (!confirm('确认关闭此异常？')) return
    try {
      await productionApi.exceptions.close(excId)
      fetchExceptions()
      if (showDetailDialog) {
        handleViewDetail(excId)
      }
    } catch (error) {
      alert('关闭异常失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredExceptions = useMemo(() => {
    return exceptions.filter(exc => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          exc.exception_no?.toLowerCase().includes(keyword) ||
          exc.title?.toLowerCase().includes(keyword) ||
          exc.description?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [exceptions, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="生产异常管理"
        description="生产异常列表、上报、处理、关闭"
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
                <SelectItem value="all">全部项目</SelectItem>
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
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterLevel} onValueChange={setFilterLevel}>
              <SelectTrigger>
                <SelectValue placeholder="选择级别" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部级别</SelectItem>
                {Object.entries(levelConfigs).map(([key, config]) => (
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
          上报异常
        </Button>
      </div>
      {/* Exception List */}
      <Card>
        <CardHeader>
          <CardTitle>生产异常列表</CardTitle>
          <CardDescription>
            共 {filteredExceptions.length} 个异常
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredExceptions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无异常</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>异常编号</TableHead>
                  <TableHead>异常标题</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>级别</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>工单号</TableHead>
                  <TableHead>上报时间</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExceptions.map((exc) => (
                  <TableRow key={exc.id}>
                    <TableCell className="font-mono text-sm">
                      {exc.exception_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {exc.title}
                    </TableCell>
                    <TableCell>
                      <Badge className={typeConfigs[exc.exception_type]?.color || 'bg-slate-500'}>
                        {typeConfigs[exc.exception_type]?.label || exc.exception_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={levelConfigs[exc.exception_level]?.color || 'bg-slate-500'}>
                        {levelConfigs[exc.exception_level]?.label || exc.exception_level}
                      </Badge>
                    </TableCell>
                    <TableCell>{exc.project_name || '-'}</TableCell>
                    <TableCell className="font-mono text-sm">
                      {exc.work_order_no || '-'}
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {exc.report_time ? formatDate(exc.report_time) : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[exc.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[exc.status]?.label || exc.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(exc.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {(exc.status === 'REPORTED' || exc.status === 'IN_PROGRESS') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedException(exc)
                              setShowHandleDialog(true)
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        )}
                        {exc.status === 'RESOLVED' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleClose(exc.id)}
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
      {/* Create Exception Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>上报生产异常</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">异常标题 *</label>
                <Input
                  value={newException.title}
                  onChange={(e) => setNewException({ ...newException, title: e.target.value })}
                  placeholder="请输入异常标题"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">异常类型</label>
                  <Select
                    value={newException.exception_type}
                    onValueChange={(val) => setNewException({ ...newException, exception_type: val })}
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
                <div>
                  <label className="text-sm font-medium mb-2 block">异常级别</label>
                  <Select
                    value={newException.exception_level}
                    onValueChange={(val) => setNewException({ ...newException, exception_level: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(levelConfigs).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
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
                <label className="text-sm font-medium mb-2 block">异常描述</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newException.description}
                  onChange={(e) => setNewException({ ...newException, description: e.target.value })}
                  placeholder="详细描述异常情况..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">影响工时（小时）</label>
                  <Input
                    type="number"
                    value={newException.impact_hours}
                    onChange={(e) => setNewException({ ...newException, impact_hours: parseFloat(e.target.value) || 0 })}
                    placeholder="0"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">影响成本（元）</label>
                  <Input
                    type="number"
                    value={newException.impact_cost}
                    onChange={(e) => setNewException({ ...newException, impact_cost: parseFloat(e.target.value) || 0 })}
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
            <Button onClick={handleCreateException}>上报</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Exception Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedException?.title} - {selectedException?.exception_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedException && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常编号</div>
                    <div className="font-mono">{selectedException.exception_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedException.status]?.color}>
                      {statusConfigs[selectedException.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常类型</div>
                    <Badge className={typeConfigs[selectedException.exception_type]?.color}>
                      {typeConfigs[selectedException.exception_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常级别</div>
                    <Badge className={levelConfigs[selectedException.exception_level]?.color}>
                      {levelConfigs[selectedException.exception_level]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedException.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工单号</div>
                    <div className="font-mono">{selectedException.work_order_no || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">上报人</div>
                    <div>{selectedException.reporter_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">上报时间</div>
                    <div>{selectedException.report_time ? formatDate(selectedException.report_time) : '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">影响工时</div>
                    <div>{selectedException.impact_hours || 0} 小时</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">影响成本</div>
                    <div>¥{selectedException.impact_cost || 0}</div>
                  </div>
                </div>
                {selectedException.description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">异常描述</div>
                    <div>{selectedException.description}</div>
                  </div>
                )}
                {selectedException.handle_plan && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">处理方案</div>
                    <div>{selectedException.handle_plan}</div>
                  </div>
                )}
                {selectedException.handle_result && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">处理结果</div>
                    <div>{selectedException.handle_result}</div>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedException && (selectedException.status === 'REPORTED' || selectedException.status === 'IN_PROGRESS') && (
              <Button onClick={() => {
                setShowDetailDialog(false)
                setShowHandleDialog(true)
              }}>
                <Edit className="w-4 h-4 mr-2" />
                处理异常
              </Button>
            )}
            {selectedException && selectedException.status === 'RESOLVED' && (
              <Button onClick={() => handleClose(selectedException.id)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                关闭异常
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Handle Exception Dialog */}
      <Dialog open={showHandleDialog} onOpenChange={setShowHandleDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>处理生产异常</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedException && (
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常标题</div>
                  <div className="font-medium">{selectedException.title}</div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">处理方案</label>
                  <textarea
                    className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={handleData.handle_plan}
                    onChange={(e) => setHandleData({ ...handleData, handle_plan: e.target.value })}
                    placeholder="填写处理方案..."
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">处理结果</label>
                  <textarea
                    className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={handleData.handle_result}
                    onChange={(e) => setHandleData({ ...handleData, handle_result: e.target.value })}
                    placeholder="填写处理结果..."
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

