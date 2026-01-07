/**
 * Machine Management Page - 机台管理页面
 * Features: 机台列表、详情、创建、更新、进度管理
 */
import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Plus,
  Search,
  Filter,
  Edit,
  Eye,
  Box,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Settings,
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
import { machineApi, projectApi } from '../services/api'
const statusConfigs = {
  DESIGNING: { label: '设计中', color: 'bg-blue-500' },
  PROCURING: { label: '采购中', color: 'bg-amber-500' },
  PRODUCING: { label: '生产中', color: 'bg-purple-500' },
  ASSEMBLING: { label: '装配中', color: 'bg-violet-500' },
  TESTING: { label: '调试中', color: 'bg-cyan-500' },
  COMPLETED: { label: '已完成', color: 'bg-emerald-500' },
}
const healthConfigs = {
  H1: { label: '健康', color: 'bg-emerald-500' },
  H2: { label: '正常', color: 'bg-blue-500' },
  H3: { label: '警告', color: 'bg-amber-500' },
  H4: { label: '危险', color: 'bg-red-500' },
}
export default function MachineManagement() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [machines, setMachines] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterHealth, setFilterHealth] = useState('')
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedMachine, setSelectedMachine] = useState(null)
  // Form state
  const [newMachine, setNewMachine] = useState({
    machine_code: '',
    machine_name: '',
    machine_type: '',
    stage: 'DESIGNING',
    status: 'DESIGNING',
    health: 'H2',
    description: '',
  })
  useEffect(() => {
    if (id) {
      fetchProject()
      fetchMachines()
    }
  }, [id, filterStatus, filterHealth])
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id)
      setProject(res.data || res)
    } catch (error) {
      console.error('Failed to fetch project:', error)
    }
  }
  const fetchMachines = async () => {
    try {
      setLoading(true)
      const params = { project_id: id }
      if (filterStatus) params.status = filterStatus
      if (filterHealth) params.health = filterHealth
      if (searchKeyword) params.search = searchKeyword
      const res = await machineApi.list(params)
      const machineList = res.data?.items || res.data || []
      setMachines(machineList)
    } catch (error) {
      console.error('Failed to fetch machines:', error)
    } finally {
      setLoading(false)
    }
  }
  const handleCreateMachine = async () => {
    if (!newMachine.machine_code || !newMachine.machine_name) {
      alert('请填写机台编码和名称')
      return
    }
    try {
      await machineApi.create({
        ...newMachine,
        project_id: parseInt(id),
      })
      setShowCreateDialog(false)
      setNewMachine({
        machine_code: '',
        machine_name: '',
        machine_type: '',
        stage: 'DESIGNING',
        status: 'DESIGNING',
        health: 'H2',
        description: '',
      })
      fetchMachines()
    } catch (error) {
      console.error('Failed to create machine:', error)
      alert('创建机台失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleViewDetail = async (machineId) => {
    try {
      const res = await machineApi.get(machineId)
      setSelectedMachine(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch machine detail:', error)
    }
  }
  const filteredMachines = useMemo(() => {
    return machines.filter(machine => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          machine.machine_code?.toLowerCase().includes(keyword) ||
          machine.machine_name?.toLowerCase().includes(keyword) ||
          machine.machine_type?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [machines, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回项目
          </Button>
          <PageHeader
            title={`${project?.project_name || '项目'} - 机台管理`}
            description="机台列表、详情、创建、进度管理"
          />
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建机台
        </Button>
      </div>
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索机台编码、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
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
            <Select value={filterHealth} onValueChange={setFilterHealth}>
              <SelectTrigger>
                <SelectValue placeholder="选择健康度" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部健康度</SelectItem>
                {Object.entries(healthConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Machine List */}
      <Card>
        <CardHeader>
          <CardTitle>机台列表</CardTitle>
          <CardDescription>
            共 {filteredMachines.length} 个机台
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredMachines.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无机台数据</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>机台编码</TableHead>
                  <TableHead>机台名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>健康度</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>更新时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredMachines.map((machine) => (
                  <TableRow key={machine.id}>
                    <TableCell className="font-mono text-sm">
                      {machine.machine_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {machine.machine_name}
                    </TableCell>
                    <TableCell>{machine.machine_type || '-'}</TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[machine.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[machine.status]?.label || machine.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={healthConfigs[machine.health]?.color || 'bg-slate-500'}>
                        {healthConfigs[machine.health]?.label || machine.health}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span>{machine.progress || 0}%</span>
                        </div>
                        <Progress value={machine.progress || 0} className="h-1.5" />
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {formatDate(machine.updated_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(machine.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/bom?machine_id=${machine.id}`)}
                        >
                          <Box className="w-4 h-4" />
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
      {/* Create Machine Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建机台</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">机台编码 *</label>
                <Input
                  value={newMachine.machine_code}
                  onChange={(e) => setNewMachine({ ...newMachine, machine_code: e.target.value })}
                  placeholder="请输入机台编码"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">机台名称 *</label>
                <Input
                  value={newMachine.machine_name}
                  onChange={(e) => setNewMachine({ ...newMachine, machine_name: e.target.value })}
                  placeholder="请输入机台名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">机台类型</label>
                <Input
                  value={newMachine.machine_type}
                  onChange={(e) => setNewMachine({ ...newMachine, machine_type: e.target.value })}
                  placeholder="机台类型"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">状态</label>
                <Select
                  value={newMachine.status}
                  onValueChange={(val) => setNewMachine({ ...newMachine, status: val, stage: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(statusConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">健康度</label>
                <Select
                  value={newMachine.health}
                  onValueChange={(val) => setNewMachine({ ...newMachine, health: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(healthConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={newMachine.description}
                  onChange={(e) => setNewMachine({ ...newMachine, description: e.target.value })}
                  placeholder="机台描述"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateMachine}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Machine Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>机台详情</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedMachine && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">机台编码</div>
                    <div className="font-mono">{selectedMachine.machine_code}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">机台名称</div>
                    <div>{selectedMachine.machine_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">机台类型</div>
                    <div>{selectedMachine.machine_type || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedMachine.status]?.color}>
                      {statusConfigs[selectedMachine.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">健康度</div>
                    <Badge className={healthConfigs[selectedMachine.health]?.color}>
                      {healthConfigs[selectedMachine.health]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">进度</div>
                    <div className="space-y-1">
                      <div className="text-lg font-bold">{selectedMachine.progress || 0}%</div>
                      <Progress value={selectedMachine.progress || 0} className="h-2" />
                    </div>
                  </div>
                </div>
                {selectedMachine.description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedMachine.description}</div>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            <Button onClick={() => navigate(`/bom?machine_id=${selectedMachine?.id}`)}>
              <Box className="w-4 h-4 mr-2" />
              查看BOM
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

