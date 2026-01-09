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
  FileText,
  Upload,
  Download,
  History,
  Layers,
  Zap,
  Code,
  FileCode,
  FileCheck,
  FileX,
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs'
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
  const [detailTab, setDetailTab] = useState('info')
  const [machineDocuments, setMachineDocuments] = useState(null)
  const [loadingDocuments, setLoadingDocuments] = useState(false)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadForm, setUploadForm] = useState({
    doc_type: 'OTHER',
    doc_name: '',
    doc_no: '',
    version: '1.0',
    description: '',
    machine_stage: '',
  })
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
      alert('创建机台失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleViewDetail = async (machineId) => {
    try {
      const res = await machineApi.get(machineId)
      setSelectedMachine(res.data || res)
      setShowDetailDialog(true)
      setDetailTab('info')
      // 加载文档
      fetchMachineDocuments(machineId)
    } catch (error) {
    }
  }

  const fetchMachineDocuments = async (machineId) => {
    try {
      setLoadingDocuments(true)
      const res = await machineApi.getDocuments(machineId, { group_by_type: true })
      const data = res.data?.data || res.data || {}
      setMachineDocuments(data)
    } catch (error) {
      setMachineDocuments(null)
    } finally {
      setLoadingDocuments(false)
    }
  }

  const handleUploadDocument = async () => {
    if (!uploadFile) {
      alert('请选择要上传的文件')
      return
    }
    if (!selectedMachine) {
      alert('请先选择机台')
      return
    }

    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('doc_type', uploadForm.doc_type)
      formData.append('doc_name', uploadForm.doc_name || uploadFile.name)
      formData.append('doc_no', uploadForm.doc_no || '')
      formData.append('version', uploadForm.version || '1.0')
      if (uploadForm.description) {
        formData.append('description', uploadForm.description)
      }
      if (uploadForm.machine_stage) {
        formData.append('machine_stage', uploadForm.machine_stage)
      }

      await machineApi.uploadDocument(selectedMachine.id, formData)
      alert('文档上传成功')
      setShowUploadDialog(false)
      setUploadFile(null)
      setUploadForm({
        doc_type: 'OTHER',
        doc_name: '',
        doc_no: '',
        version: '1.0',
        description: '',
        machine_stage: '',
      })
      // 重新加载文档
      fetchMachineDocuments(selectedMachine.id)
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || '上传失败'
      // 如果是权限错误，提供更友好的提示
      if (error.response?.status === 403) {
        alert(`上传失败：${errorMessage}\n\n如需上传此类型文档，请联系管理员分配相应角色权限。`)
      } else {
        alert(`上传失败：${errorMessage}`)
      }
    }
  }

  const handleDownloadDocument = async (doc) => {
    try {
      const response = await machineApi.downloadDocument(selectedMachine.id, doc.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', doc.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || '下载失败'
      // 如果是权限错误，提供更友好的提示
      if (error.response?.status === 403) {
        alert(`下载失败：${errorMessage}\n\n如需下载此文档，请联系管理员分配相应角色权限。`)
      } else {
        alert(`下载失败：${errorMessage}`)
      }
    }
  }

  const docTypeConfigs = {
    CIRCUIT_DIAGRAM: { label: '电路图', icon: Zap, color: 'text-yellow-500' },
    PLC_PROGRAM: { label: 'PLC程序', icon: Code, color: 'text-blue-500' },
    LABELWORK_PROGRAM: { label: 'Labelwork程序', icon: FileCode, color: 'text-purple-500' },
    BOM_DOCUMENT: { label: 'BOM文档', icon: Layers, color: 'text-green-500' },
    FAT_DOCUMENT: { label: 'FAT文档', icon: FileCheck, color: 'text-emerald-500' },
    SAT_DOCUMENT: { label: 'SAT文档', icon: FileCheck, color: 'text-teal-500' },
    OTHER: { label: '其他文档', icon: FileText, color: 'text-slate-500' },
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
                <SelectItem value="all">全部状态</SelectItem>
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
                <SelectItem value="all">全部健康度</SelectItem>
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
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>机台详情 - {selectedMachine?.machine_code}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedMachine && (
              <Tabs value={detailTab} onValueChange={setDetailTab} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="info">基本信息</TabsTrigger>
                  <TabsTrigger value="documents">文档档案</TabsTrigger>
                  <TabsTrigger value="bom">BOM清单</TabsTrigger>
                  <TabsTrigger value="service">服务历史</TabsTrigger>
                </TabsList>

                {/* 基本信息标签页 */}
                <TabsContent value="info" className="space-y-4 mt-4">
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
                    {selectedMachine.stage && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">生命周期阶段</div>
                        <div>{selectedMachine.stage}</div>
                      </div>
                    )}
                  </div>
                  {selectedMachine.description && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">描述</div>
                      <div>{selectedMachine.description}</div>
                    </div>
                  )}
                </TabsContent>

                {/* 文档档案标签页 */}
                <TabsContent value="documents" className="space-y-4 mt-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">设备文档档案</h3>
                    <Button onClick={() => setShowUploadDialog(true)} size="sm">
                      <Upload className="w-4 h-4 mr-2" />
                      上传文档
                    </Button>
                  </div>

                  {loadingDocuments ? (
                    <div className="text-center py-8 text-slate-400">加载中...</div>
                  ) : machineDocuments?.documents_by_type && Object.keys(machineDocuments.documents_by_type).length > 0 ? (
                    <div className="space-y-6">
                      {machineDocuments.filtered_count > 0 && (
                        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-sm text-amber-800 dark:text-amber-200">
                          <p className="flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            提示：有 {machineDocuments.filtered_count} 个文档因权限限制未显示。如需查看，请联系管理员分配相应角色权限。
                          </p>
                        </div>
                      )}
                      {Object.entries(machineDocuments.documents_by_type).map(([docType, docs]) => {
                        const config = docTypeConfigs[docType] || docTypeConfigs.OTHER
                        const Icon = config.icon
                        return (
                          <Card key={docType}>
                            <CardHeader>
                              <CardTitle className="flex items-center gap-2">
                                <Icon className={cn("w-5 h-5", config.color)} />
                                {config.label}
                                <Badge variant="outline" className="ml-2">
                                  {docs.length} 个文档
                                </Badge>
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {docs.map((doc) => (
                                  <div
                                    key={doc.id}
                                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50"
                                  >
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2">
                                        <FileText className="w-4 h-4 text-slate-500" />
                                        <span className="font-medium">{doc.doc_name}</span>
                                        {doc.version && (
                                          <Badge variant="outline" className="text-xs">
                                            v{doc.version}
                                          </Badge>
                                        )}
                                        {doc.doc_no && (
                                          <span className="text-xs text-slate-500 font-mono">
                                            {doc.doc_no}
                                          </span>
                                        )}
                                      </div>
                                      {doc.description && (
                                        <div className="text-sm text-slate-500 mt-1">
                                          {doc.description}
                                        </div>
                                      )}
                                      <div className="text-xs text-slate-400 mt-1">
                                        {formatDate(doc.created_at)}
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => handleDownloadDocument(doc)}
                                      >
                                        <Download className="w-4 h-4" />
                                      </Button>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={async () => {
                                          try {
                                            const versions = await machineApi.getDocumentVersions(
                                              selectedMachine.id,
                                              doc.id
                                            )
                                            const versionList = versions.data || versions
                                            if (versionList.length === 0) {
                                              alert('该文档暂无版本记录')
                                            } else {
                                              const versionInfo = versionList.map(v => 
                                                `v${v.version} - ${formatDate(v.created_at)}`
                                              ).join('\n')
                                              alert(`该文档共有 ${versionList.length} 个版本：\n\n${versionInfo}`)
                                            }
                                          } catch (error) {
                                            const errorMessage = error.response?.data?.detail || error.message || '获取版本失败'
                                            if (error.response?.status === 403) {
                                              alert(`获取版本失败：${errorMessage}\n\n如需查看此文档版本，请联系管理员分配相应角色权限。`)
                                            } else {
                                              alert(`获取版本失败：${errorMessage}`)
                                            }
                                          }
                                        }}
                                      >
                                        <History className="w-4 h-4" />
                                      </Button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-400 space-y-2">
                      <p>暂无可见文档</p>
                      {machineDocuments?.filtered_count > 0 && (
                        <p className="text-sm text-amber-600 mt-2">
                          提示：有 {machineDocuments.filtered_count} 个文档因权限限制未显示。
                          <br />
                          如需查看，请联系管理员分配相应角色权限。
                        </p>
                      )}
                      <Button 
                        onClick={() => setShowUploadDialog(true)} 
                        size="sm" 
                        className="mt-4"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        上传文档
                      </Button>
                    </div>
                  )}
                </TabsContent>

                {/* BOM清单标签页 */}
                <TabsContent value="bom" className="space-y-4 mt-4">
                  <div className="text-center py-8">
                    <Button onClick={() => navigate(`/bom?machine_id=${selectedMachine.id}`)}>
                      <Box className="w-4 h-4 mr-2" />
                      查看BOM清单
                    </Button>
                  </div>
                </TabsContent>

                {/* 服务历史标签页 */}
                <TabsContent value="service" className="space-y-4 mt-4">
                  <div className="text-center py-8 text-slate-400">
                    服务历史记录功能开发中...
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Upload Document Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>上传设备文档</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">选择文件 *</label>
                <Input
                  type="file"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">文档类型 *</label>
                <Select
                  value={uploadForm.doc_type}
                  onValueChange={(val) => setUploadForm({ ...uploadForm, doc_type: val })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(docTypeConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">文档名称</label>
                <Input
                  value={uploadForm.doc_name}
                  onChange={(e) => setUploadForm({ ...uploadForm, doc_name: e.target.value })}
                  placeholder="留空则使用文件名"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">文档编号</label>
                <Input
                  value={uploadForm.doc_no}
                  onChange={(e) => setUploadForm({ ...uploadForm, doc_no: e.target.value })}
                  placeholder="用于版本管理"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">版本号</label>
                <Input
                  value={uploadForm.version}
                  onChange={(e) => setUploadForm({ ...uploadForm, version: e.target.value })}
                  placeholder="1.0"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">关联生命周期阶段</label>
                <Select
                  value={uploadForm.machine_stage}
                  onValueChange={(val) => setUploadForm({ ...uploadForm, machine_stage: val })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择阶段（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">不关联</SelectItem>
                    <SelectItem value="S1">S1 - 需求进入</SelectItem>
                    <SelectItem value="S2">S2 - 方案设计</SelectItem>
                    <SelectItem value="S3">S3 - 采购备料</SelectItem>
                    <SelectItem value="S4">S4 - 加工制造</SelectItem>
                    <SelectItem value="S5">S5 - 装配调试</SelectItem>
                    <SelectItem value="S6">S6 - 出厂验收(FAT)</SelectItem>
                    <SelectItem value="S7">S7 - 包装发运</SelectItem>
                    <SelectItem value="S8">S8 - 现场安装(SAT)</SelectItem>
                    <SelectItem value="S9">S9 - 质保结项</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="文档描述"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUploadDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUploadDocument}>上传</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

