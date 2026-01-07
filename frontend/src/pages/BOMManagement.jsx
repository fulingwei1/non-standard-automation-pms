/**
 * BOM Management Page - BOM管理页面
 * Features: BOM列表、详情、版本管理、导入导出、发布审批
 */
import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Package,
  Plus,
  Search,
  Filter,
  Download,
  Upload,
  Eye,
  Edit,
  Trash2,
  GitBranch,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  FileText,
  Copy,
  RefreshCw,
  X,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import { formatCurrency, formatDate } from '../lib/utils'
import { bomApi, projectApi, machineApi } from '../services/api'
const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500' },
  REVIEWING: { label: '审核中', color: 'bg-blue-500' },
  APPROVED: { label: '已审批', color: 'bg-emerald-500' },
  RELEASED: { label: '已发布', color: 'bg-violet-500' },
  OBSOLETE: { label: '已废弃', color: 'bg-red-500' },
}
export default function BOMManagement() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const machineId = searchParams.get('machine_id')
  const projectId = searchParams.get('project_id')
  const [loading, setLoading] = useState(true)
  const [boms, setBoms] = useState([])
  const [selectedBom, setSelectedBom] = useState(null)
  const [bomItems, setBomItems] = useState([])
  const [versions, setVersions] = useState([])
  const [projects, setProjects] = useState([])
  const [machines, setMachines] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterProject, setFilterProject] = useState(projectId || '')
  const [filterMachine, setFilterMachine] = useState(machineId || '')
  const [filterStatus, setFilterStatus] = useState('')
  // Dialogs
  const [showBomDetail, setShowBomDetail] = useState(false)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showVersionDialog, setShowVersionDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [showReleaseDialog, setShowReleaseDialog] = useState(false)
  // Form states
  const [newBom, setNewBom] = useState({
    bom_name: '',
    machine_id: machineId ? parseInt(machineId) : null,
    version: '1.0',
    remark: '',
  })
  const [importFile, setImportFile] = useState(null)
  const [releaseNote, setReleaseNote] = useState('')
  useEffect(() => {
    fetchProjects()
    if (filterProject) {
      fetchMachines(filterProject)
    }
  }, [])
  useEffect(() => {
    fetchBOMs()
  }, [filterProject, filterMachine, filterStatus, searchKeyword])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('Failed to fetch projects:', error)
    }
  }
  const fetchMachines = async (projId) => {
    try {
      const res = await machineApi.list({ project_id: projId })
      setMachines(res.data?.items || res.data || [])
    } catch (error) {
      console.error('Failed to fetch machines:', error)
    }
  }
  const fetchBOMs = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      if (filterMachine) params.machine_id = filterMachine
      if (filterStatus) params.status = filterStatus
      if (searchKeyword) params.search = searchKeyword
      const res = await bomApi.list(params)
      const bomList = res.data?.items || res.data || []
      setBoms(bomList)
    } catch (error) {
      console.error('Failed to fetch BOMs:', error)
    } finally {
      setLoading(false)
    }
  }
  const fetchBOMDetail = async (bomId) => {
    try {
      const [bomRes, itemsRes, versionsRes] = await Promise.all([
        bomApi.get(bomId),
        bomApi.getItems(bomId),
        bomApi.getVersions(bomId),
      ])
      setSelectedBom(bomRes.data || bomRes)
      setBomItems(itemsRes.data || itemsRes || [])
      setVersions(versionsRes.data || versionsRes || [])
      setShowBomDetail(true)
    } catch (error) {
      console.error('Failed to fetch BOM detail:', error)
    }
  }
  const handleCreateBOM = async () => {
    if (!newBom.machine_id || !newBom.bom_name) {
      alert('请填写BOM名称并选择机台')
      return
    }
    try {
      await bomApi.create(newBom.machine_id, newBom)
      setShowCreateDialog(false)
      setNewBom({ bom_name: '', machine_id: null, version: '1.0', remark: '' })
      fetchBOMs()
    } catch (error) {
      console.error('Failed to create BOM:', error)
      alert('创建BOM失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleReleaseBOM = async () => {
    if (!selectedBom) return
    try {
      await bomApi.release(selectedBom.id, releaseNote)
      setShowReleaseDialog(false)
      setReleaseNote('')
      fetchBOMDetail(selectedBom.id)
      fetchBOMs()
    } catch (error) {
      console.error('Failed to release BOM:', error)
      alert('发布BOM失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleImport = async () => {
    if (!importFile || !selectedBom) return
    try {
      await bomApi.import(selectedBom.id, importFile)
      setShowImportDialog(false)
      setImportFile(null)
      fetchBOMDetail(selectedBom.id)
      alert('导入成功')
    } catch (error) {
      console.error('Failed to import BOM:', error)
      alert('导入失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const handleExport = async (bomId) => {
    try {
      const res = await bomApi.export(bomId)
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `BOM_${bomId}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export BOM:', error)
      alert('导出失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredBoms = useMemo(() => {
    return boms.filter(bom => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          bom.bom_no?.toLowerCase().includes(keyword) ||
          bom.bom_name?.toLowerCase().includes(keyword) ||
          bom.project_name?.toLowerCase().includes(keyword) ||
          bom.machine_name?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [boms, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="BOM管理"
        description="物料清单管理，支持版本控制、导入导出、发布审批"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索BOM编号、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterProject} onValueChange={(val) => {
              setFilterProject(val)
              setFilterMachine('')
              if (val) fetchMachines(val)
            }}>
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
            <Select value={filterMachine} onValueChange={setFilterMachine} disabled={!filterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择机台" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部机台</SelectItem>
                {machines.map((machine) => (
                  <SelectItem key={machine.id} value={machine.id.toString()}>
                    {machine.machine_name}
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
      {/* BOM List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>BOM列表</CardTitle>
            <CardDescription>
              共 {filteredBoms.length} 个BOM
            </CardDescription>
          </div>
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            新建BOM
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredBoms.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无BOM数据</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>BOM编号</TableHead>
                  <TableHead>BOM名称</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>机台</TableHead>
                  <TableHead>版本</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>物料数量</TableHead>
                  <TableHead>总金额</TableHead>
                  <TableHead>更新时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredBoms.map((bom) => (
                  <TableRow key={bom.id}>
                    <TableCell className="font-mono text-sm">{bom.bom_no}</TableCell>
                    <TableCell className="font-medium">{bom.bom_name}</TableCell>
                    <TableCell>{bom.project_name || '-'}</TableCell>
                    <TableCell>{bom.machine_name || '-'}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{bom.version}</Badge>
                      {bom.is_latest && (
                        <Badge className="ml-2 bg-emerald-500">最新</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[bom.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[bom.status]?.label || bom.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{bom.total_items || 0}</TableCell>
                    <TableCell>{formatCurrency(bom.total_amount || 0)}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {formatDate(bom.updated_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => fetchBOMDetail(bom.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleExport(bom.id)}
                        >
                          <Download className="w-4 h-4" />
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
      {/* BOM Detail Dialog */}
      <Dialog open={showBomDetail} onOpenChange={setShowBomDetail}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedBom?.bom_name} - {selectedBom?.bom_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedBom && (
              <Tabs defaultValue="items" className="w-full">
                <TabsList>
                  <TabsTrigger value="items">BOM明细</TabsTrigger>
                  <TabsTrigger value="versions">版本历史</TabsTrigger>
                  <TabsTrigger value="info">基本信息</TabsTrigger>
                </TabsList>
                <TabsContent value="items" className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-slate-500">
                      共 {bomItems.length} 项物料
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowImportDialog(true)}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        导入
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExport(selectedBom.id)}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        导出
                      </Button>
                      {selectedBom.status === 'APPROVED' && (
                        <Button
                          size="sm"
                          onClick={() => setShowReleaseDialog(true)}
                        >
                          <CheckCircle2 className="w-4 h-4 mr-2" />
                          发布
                        </Button>
                      )}
                    </div>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>序号</TableHead>
                        <TableHead>物料编码</TableHead>
                        <TableHead>物料名称</TableHead>
                        <TableHead>规格</TableHead>
                        <TableHead>单位</TableHead>
                        <TableHead>数量</TableHead>
                        <TableHead>单价</TableHead>
                        <TableHead>金额</TableHead>
                        <TableHead>来源</TableHead>
                        <TableHead>需求日期</TableHead>
                        <TableHead>关键件</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bomItems.map((item, index) => (
                        <TableRow key={item.id}>
                          <TableCell>{item.item_no || index + 1}</TableCell>
                          <TableCell className="font-mono text-sm">
                            {item.material_code}
                          </TableCell>
                          <TableCell>{item.material_name}</TableCell>
                          <TableCell className="text-slate-500">
                            {item.specification || '-'}
                          </TableCell>
                          <TableCell>{item.unit}</TableCell>
                          <TableCell>{item.quantity}</TableCell>
                          <TableCell>{formatCurrency(item.unit_price || 0)}</TableCell>
                          <TableCell className="font-medium">
                            {formatCurrency(item.amount || 0)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">{item.source_type}</Badge>
                          </TableCell>
                          <TableCell className="text-slate-500 text-sm">
                            {item.required_date ? formatDate(item.required_date) : '-'}
                          </TableCell>
                          <TableCell>
                            {item.is_key_item && (
                              <Badge className="bg-amber-500">关键</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
                <TabsContent value="versions" className="space-y-4">
                  <div className="text-sm text-slate-500 mb-4">
                    共 {versions.length} 个版本
                  </div>
                  <div className="space-y-2">
                    {versions.map((version) => (
                      <Card key={version.id}>
                        <CardContent className="pt-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <Badge>{version.version}</Badge>
                              {version.is_latest && (
                                <Badge className="bg-emerald-500">最新</Badge>
                              )}
                              <Badge className={statusConfigs[version.status]?.color}>
                                {statusConfigs[version.status]?.label}
                              </Badge>
                              <span className="text-sm text-slate-500">
                                {formatDate(version.created_at)}
                              </span>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedBom(version)
                                  fetchBOMDetail(version.id)
                                }}
                              >
                                <Eye className="w-4 h-4 mr-2" />
                                查看
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
                <TabsContent value="info" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500 mb-1">BOM编号</div>
                      <div className="font-mono">{selectedBom.bom_no}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">BOM名称</div>
                      <div>{selectedBom.bom_name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">项目</div>
                      <div>{selectedBom.project_name || '-'}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">机台</div>
                      <div>{selectedBom.machine_name || '-'}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">版本</div>
                      <div>{selectedBom.version}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">状态</div>
                      <Badge className={statusConfigs[selectedBom.status]?.color}>
                        {statusConfigs[selectedBom.status]?.label}
                      </Badge>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">物料数量</div>
                      <div>{selectedBom.total_items || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500 mb-1">总金额</div>
                      <div className="font-medium">
                        {formatCurrency(selectedBom.total_amount || 0)}
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBomDetail(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Create BOM Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建BOM</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">项目</label>
                <Select
                  value={newBom.machine_id ? projects.find(p => 
                    machines.find(m => m.id === newBom.machine_id)?.project_id === p.id
                  )?.id?.toString() || '' : ''}
                  onValueChange={(val) => {
                    fetchMachines(val)
                    setNewBom({ ...newBom, machine_id: null })
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">机台</label>
                <Select
                  value={newBom.machine_id?.toString() || ''}
                  onValueChange={(val) => setNewBom({ ...newBom, machine_id: parseInt(val) })}
                  disabled={!newBom.machine_id && machines.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择机台" />
                  </SelectTrigger>
                  <SelectContent>
                    {machines.map((machine) => (
                      <SelectItem key={machine.id} value={machine.id.toString()}>
                        {machine.machine_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">BOM名称</label>
                <Input
                  value={newBom.bom_name}
                  onChange={(e) => setNewBom({ ...newBom, bom_name: e.target.value })}
                  placeholder="请输入BOM名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">版本</label>
                <Input
                  value={newBom.version}
                  onChange={(e) => setNewBom({ ...newBom, version: e.target.value })}
                  placeholder="1.0"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">备注</label>
                <Input
                  value={newBom.remark}
                  onChange={(e) => setNewBom({ ...newBom, remark: e.target.value })}
                  placeholder="备注信息"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateBOM}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入BOM</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">选择文件</label>
                <Input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowImportDialog(false)}>
              取消
            </Button>
            <Button onClick={handleImport} disabled={!importFile}>
              导入
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Release Dialog */}
      <Dialog open={showReleaseDialog} onOpenChange={setShowReleaseDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>发布BOM</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">变更说明</label>
                <Input
                  value={releaseNote}
                  onChange={(e) => setReleaseNote(e.target.value)}
                  placeholder="请输入变更说明"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowReleaseDialog(false)}>
              取消
            </Button>
            <Button onClick={handleReleaseBOM}>发布</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

