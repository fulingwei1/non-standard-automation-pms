/**
 * ECN Type Management Page - ECN类型配置管理页面
 * Features: ECN类型列表、创建、编辑、删除、审批矩阵配置
 */
import { useState, useEffect } from 'react'
import {
  Plus,
  Search,
  FileEdit,
  X,
  Settings,
  CheckCircle2,
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
import { ecnApi } from '../services/api'

const deptOptions = [
  '机械部', '电气部', '软件部', '采购部', 'PMC部', '质量部', '生产部'
]

export default function ECNTypeManagement() {
  const [loading, setLoading] = useState(true)
  const [ecnTypes, setEcnTypes] = useState([])
  const [searchKeyword, setSearchKeyword] = useState('')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingType, setEditingType] = useState(null)
  const [typeForm, setTypeForm] = useState({
    type_code: '',
    type_name: '',
    description: '',
    required_depts: [],
    optional_depts: [],
    approval_matrix: null,
    is_active: true,
  })

  useEffect(() => {
    fetchECNTypes()
  }, [])

  const fetchECNTypes = async () => {
    try {
      setLoading(true)
      const res = await ecnApi.getEcnTypes({ is_active: null })
      setEcnTypes(res.data || res || [])
    } catch (error) {
      console.error('Failed to fetch ECN types:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingType(null)
    setTypeForm({
      type_code: '',
      type_name: '',
      description: '',
      required_depts: [],
      optional_depts: [],
      approval_matrix: null,
      is_active: true,
    })
    setShowCreateDialog(true)
  }

  const handleEdit = (type) => {
    setEditingType(type)
    setTypeForm({
      type_code: type.type_code,
      type_name: type.type_name,
      description: type.description || '',
      required_depts: type.required_depts || [],
      optional_depts: type.optional_depts || [],
      approval_matrix: type.approval_matrix || null,
      is_active: type.is_active !== false,
    })
    setShowEditDialog(true)
  }

  const handleSave = async () => {
    if (!typeForm.type_code) {
      alert('请填写类型编码')
      return
    }
    if (!typeForm.type_name) {
      alert('请填写类型名称')
      return
    }
    try {
      const data = {
        ...typeForm,
        required_depts: typeForm.required_depts.length > 0 ? typeForm.required_depts : null,
        optional_depts: typeForm.optional_depts.length > 0 ? typeForm.optional_depts : null,
      }
      if (editingType) {
        await ecnApi.updateEcnType(editingType.id, data)
      } else {
        await ecnApi.createEcnType(data)
      }
      setShowCreateDialog(false)
      setShowEditDialog(false)
      fetchECNTypes()
    } catch (error) {
      console.error('Failed to save ECN type:', error)
      alert('保存失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleDelete = async (typeId) => {
    if (!confirm('确认删除此ECN类型配置？')) return
    try {
      await ecnApi.deleteEcnType(typeId)
      fetchECNTypes()
    } catch (error) {
      console.error('Failed to delete ECN type:', error)
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const toggleDept = (dept, isRequired) => {
    if (isRequired) {
      const newDepts = typeForm.required_depts.includes(dept)
        ? typeForm.required_depts.filter(d => d !== dept)
        : [...typeForm.required_depts, dept]
      setTypeForm({ ...typeForm, required_depts: newDepts })
    } else {
      const newDepts = typeForm.optional_depts.includes(dept)
        ? typeForm.optional_depts.filter(d => d !== dept)
        : [...typeForm.optional_depts, dept]
      setTypeForm({ ...typeForm, optional_depts: newDepts })
    }
  }

  const filteredTypes = ecnTypes.filter(type => {
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase()
      return (
        type.type_code?.toLowerCase().includes(keyword) ||
        type.type_name?.toLowerCase().includes(keyword)
      )
    }
    return true
  })

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="ECN类型配置管理"
        description="管理ECN类型配置，包括评估部门、审批矩阵等"
      />
      
      {/* Search Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索类型编码、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button onClick={handleCreate}>
              <Plus className="w-4 h-4 mr-2" />
              新建类型
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* ECN Types List */}
      <Card>
        <CardHeader>
          <CardTitle>ECN类型列表</CardTitle>
          <CardDescription>
            共 {filteredTypes.length} 个类型配置
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredTypes.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无类型配置</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>类型编码</TableHead>
                  <TableHead>类型名称</TableHead>
                  <TableHead>必需评估部门</TableHead>
                  <TableHead>可选评估部门</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTypes.map((type) => (
                  <TableRow key={type.id}>
                    <TableCell className="font-mono text-sm">{type.type_code}</TableCell>
                    <TableCell className="font-medium">{type.type_name}</TableCell>
                    <TableCell>
                      {type.required_depts && type.required_depts.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {type.required_depts.map((dept) => (
                            <Badge key={dept} className="bg-blue-500">{dept}</Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {type.optional_depts && type.optional_depts.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {type.optional_depts.map((dept) => (
                            <Badge key={dept} className="bg-slate-500">{dept}</Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={type.is_active ? 'bg-green-500' : 'bg-gray-500'}>
                        {type.is_active ? '启用' : '禁用'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(type)}
                        >
                          <FileEdit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(type.id)}
                        >
                          <X className="w-4 h-4" />
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
      
      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false)
          setShowEditDialog(false)
        }
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingType ? '编辑ECN类型' : '新建ECN类型'}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">类型编码 *</label>
                  <Input
                    value={typeForm.type_code}
                    onChange={(e) => setTypeForm({ ...typeForm, type_code: e.target.value.toUpperCase() })}
                    placeholder="如：DESIGN"
                    disabled={!!editingType}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">类型名称 *</label>
                  <Input
                    value={typeForm.type_name}
                    onChange={(e) => setTypeForm({ ...typeForm, type_name: e.target.value })}
                    placeholder="如：设计变更"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Textarea
                  value={typeForm.description}
                  onChange={(e) => setTypeForm({ ...typeForm, description: e.target.value })}
                  rows={2}
                  placeholder="类型描述"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">必需评估部门</label>
                <div className="flex flex-wrap gap-2 p-3 border rounded-lg">
                  {deptOptions.map((dept) => (
                    <Button
                      key={dept}
                      type="button"
                      variant={typeForm.required_depts.includes(dept) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleDept(dept, true)}
                    >
                      {dept}
                      {typeForm.required_depts.includes(dept) && (
                        <CheckCircle2 className="w-3 h-3 ml-1" />
                      )}
                    </Button>
                  ))}
                </div>
                {typeForm.required_depts.length > 0 && (
                  <div className="text-xs text-slate-500 mt-1">
                    已选择: {typeForm.required_depts.join(', ')}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">可选评估部门</label>
                <div className="flex flex-wrap gap-2 p-3 border rounded-lg">
                  {deptOptions.map((dept) => (
                    <Button
                      key={dept}
                      type="button"
                      variant={typeForm.optional_depts.includes(dept) ? "default" : "outline"}
                      size="sm"
                      onClick={() => toggleDept(dept, false)}
                    >
                      {dept}
                      {typeForm.optional_depts.includes(dept) && (
                        <CheckCircle2 className="w-3 h-3 ml-1" />
                      )}
                    </Button>
                  ))}
                </div>
                {typeForm.optional_depts.length > 0 && (
                  <div className="text-xs text-slate-500 mt-1">
                    已选择: {typeForm.optional_depts.join(', ')}
                  </div>
                )}
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">状态</label>
                <Select
                  value={typeForm.is_active ? 'true' : 'false'}
                  onValueChange={(val) => setTypeForm({ ...typeForm, is_active: val === 'true' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="true">启用</SelectItem>
                    <SelectItem value="false">禁用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">审批矩阵配置（JSON格式）</label>
                <Textarea
                  value={typeForm.approval_matrix ? JSON.stringify(typeForm.approval_matrix, null, 2) : ''}
                  onChange={(e) => {
                    try {
                      const matrix = e.target.value ? JSON.parse(e.target.value) : null
                      setTypeForm({ ...typeForm, approval_matrix: matrix })
                    } catch (err) {
                      // 忽略JSON解析错误，允许用户继续输入
                    }
                  }}
                  rows={6}
                  placeholder='{"cost_threshold": 10000, "schedule_threshold": 7}'
                  className="font-mono text-xs"
                />
                <div className="text-xs text-slate-500 mt-1">
                  审批矩阵配置为JSON格式，用于自动创建审批记录
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false)
              setShowEditDialog(false)
            }}>
              取消
            </Button>
            <Button onClick={handleSave}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}






