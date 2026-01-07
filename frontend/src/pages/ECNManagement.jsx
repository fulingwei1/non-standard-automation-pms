/**
 * ECN Management Page - ECN管理页面
 * Features: ECN列表、详情、创建、评估、审批、执行
 */
import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FileEdit,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  GitBranch,
  User,
  Calendar,
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
import { formatDate } from '../lib/utils'
import { ecnApi, projectApi } from '../services/api'
const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500' },
  SUBMITTED: { label: '已提交', color: 'bg-blue-500' },
  EVALUATING: { label: '评估中', color: 'bg-amber-500' },
  APPROVING: { label: '审批中', color: 'bg-purple-500' },
  APPROVED: { label: '已批准', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
  EXECUTING: { label: '执行中', color: 'bg-violet-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}
const typeConfigs = {
  DESIGN: { label: '设计变更', color: 'bg-blue-500' },
  MATERIAL: { label: '物料变更', color: 'bg-amber-500' },
  PROCESS: { label: '工艺变更', color: 'bg-purple-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}
const priorityConfigs = {
  URGENT: { label: '紧急', color: 'bg-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500' },
  LOW: { label: '低', color: 'bg-blue-500' },
}
export default function ECNManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [ecns, setEcns] = useState([])
  const [projects, setProjects] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterProject, setFilterProject] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterPriority, setFilterPriority] = useState('')
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedECN, setSelectedECN] = useState(null)
  // Form state
  const [newECN, setNewECN] = useState({
    ecn_title: '',
    ecn_type: 'DESIGN',
    project_id: null,
    machine_id: null,
    priority: 'MEDIUM',
    change_reason: '',
    change_description: '',
    impact_analysis: '',
  })
  useEffect(() => {
    fetchProjects()
    fetchECNs()
  }, [filterProject, filterType, filterStatus, filterPriority, searchKeyword])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    }
  }
  const fetchECNs = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      if (filterType) params.ecn_type = filterType
      if (filterStatus) params.status = filterStatus
      if (filterPriority) params.priority = filterPriority
      if (searchKeyword) params.keyword = searchKeyword
      const res = await ecnApi.list(params)
      const ecnList = res.data?.items || res.data || []
      setEcns(ecnList)
    } catch (error) {
      console.error('Failed to fetch ECNs:', error)
    } finally {
      setLoading(false)
    }
  }
  const handleCreateECN = async () => {
    if (!newECN.ecn_title) {
      alert('请填写ECN标题')
      return
    }
    try {
      await ecnApi.create(newECN)
      setShowCreateDialog(false)
      setNewECN({
        ecn_title: '',
        ecn_type: 'DESIGN',
        project_id: null,
        machine_id: null,
        priority: 'MEDIUM',
        change_reason: '',
        change_description: '',
        impact_analysis: '',
      })
      fetchECNs()
    } catch (error) {
      console.error('Failed to create ECN:', error)
      alert('创建ECN失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleViewDetail = async (ecnId) => {
    try {
      const res = await ecnApi.get(ecnId)
      setSelectedECN(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch ECN detail:', error)
    }
  }
  const handleSubmit = async (ecnId) => {
    if (!confirm('确认提交此ECN？')) return
    try {
      await ecnApi.submit(ecnId)
      fetchECNs()
      if (showDetailDialog) {
        handleViewDetail(ecnId)
      }
    } catch (error) {
      console.error('Failed to submit ECN:', error)
      alert('提交失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredECNs = useMemo(() => {
    return ecns.filter(ecn => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          ecn.ecn_no?.toLowerCase().includes(keyword) ||
          ecn.ecn_title?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [ecns, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="ECN管理"
        description="设计变更管理，支持创建、评估、审批、执行"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索ECN编号、标题..."
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
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger>
                <SelectValue placeholder="选择优先级" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部优先级</SelectItem>
                {Object.entries(priorityConfigs).map(([key, config]) => (
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
          新建ECN
        </Button>
      </div>
      {/* ECN List */}
      <Card>
        <CardHeader>
          <CardTitle>ECN列表</CardTitle>
          <CardDescription>
            共 {filteredECNs.length} 个ECN
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredECNs.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无ECN</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ECN编号</TableHead>
                  <TableHead>ECN标题</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>优先级</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>申请人</TableHead>
                  <TableHead>申请时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredECNs.map((ecn) => (
                  <TableRow key={ecn.id}>
                    <TableCell className="font-mono text-sm">
                      {ecn.ecn_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {ecn.ecn_title}
                    </TableCell>
                    <TableCell>{ecn.project_name || '-'}</TableCell>
                    <TableCell>
                      <Badge className={typeConfigs[ecn.ecn_type]?.color || 'bg-slate-500'}>
                        {typeConfigs[ecn.ecn_type]?.label || ecn.ecn_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={priorityConfigs[ecn.priority]?.color || 'bg-slate-500'}>
                        {priorityConfigs[ecn.priority]?.label || ecn.priority}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[ecn.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[ecn.status]?.label || ecn.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{ecn.applicant_name || '-'}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {ecn.applied_at ? formatDate(ecn.applied_at) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(ecn.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {ecn.status === 'DRAFT' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSubmit(ecn.id)}
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
      {/* Create ECN Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建ECN</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">ECN标题 *</label>
                <Input
                  value={newECN.ecn_title}
                  onChange={(e) => setNewECN({ ...newECN, ecn_title: e.target.value })}
                  placeholder="请输入ECN标题"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">变更类型</label>
                  <Select
                    value={newECN.ecn_type}
                    onValueChange={(val) => setNewECN({ ...newECN, ecn_type: val })}
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
                  <label className="text-sm font-medium mb-2 block">优先级</label>
                  <Select
                    value={newECN.priority}
                    onValueChange={(val) => setNewECN({ ...newECN, priority: val })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(priorityConfigs).map(([key, config]) => (
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
                  value={newECN.project_id?.toString() || ''}
                  onValueChange={(val) => setNewECN({ ...newECN, project_id: val ? parseInt(val) : null })}
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
                <label className="text-sm font-medium mb-2 block">变更原因</label>
                <Input
                  value={newECN.change_reason}
                  onChange={(e) => setNewECN({ ...newECN, change_reason: e.target.value })}
                  placeholder="填写变更原因"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">变更描述</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newECN.change_description}
                  onChange={(e) => setNewECN({ ...newECN, change_description: e.target.value })}
                  placeholder="详细描述变更内容..."
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">影响分析</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newECN.impact_analysis}
                  onChange={(e) => setNewECN({ ...newECN, impact_analysis: e.target.value })}
                  placeholder="分析变更影响..."
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateECN}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* ECN Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedECN?.ecn_title} - {selectedECN?.ecn_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedECN && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">ECN编号</div>
                    <div className="font-mono">{selectedECN.ecn_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedECN.status]?.color}>
                      {statusConfigs[selectedECN.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedECN.project_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">变更类型</div>
                    <Badge className={typeConfigs[selectedECN.ecn_type]?.color}>
                      {typeConfigs[selectedECN.ecn_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">优先级</div>
                    <Badge className={priorityConfigs[selectedECN.priority]?.color}>
                      {priorityConfigs[selectedECN.priority]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">申请人</div>
                    <div>{selectedECN.applicant_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">申请时间</div>
                    <div>{selectedECN.applied_at ? formatDate(selectedECN.applied_at) : '-'}</div>
                  </div>
                </div>
                {selectedECN.change_reason && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">变更原因</div>
                    <div>{selectedECN.change_reason}</div>
                  </div>
                )}
                {selectedECN.change_description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">变更描述</div>
                    <div>{selectedECN.change_description}</div>
                  </div>
                )}
                {selectedECN.impact_analysis && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">影响分析</div>
                    <div>{selectedECN.impact_analysis}</div>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedECN && selectedECN.status === 'DRAFT' && (
              <Button onClick={() => handleSubmit(selectedECN.id)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                提交ECN
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

