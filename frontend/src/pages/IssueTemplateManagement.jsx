/**
 * Issue Template Management Page - 问题模板管理页面
 * Features: 问题模板列表、创建、编辑、删除、从模板创建问题
 */
import { useState, useEffect, useMemo } from 'react'
import {
  FileText,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Copy,
  Tag,
  AlertCircle,
  CheckCircle2,
  XCircle,
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
  DialogFooter,
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import { formatDate } from '../lib/utils'
import { issueTemplateApi, issueApi, projectApi, machineApi } from '../services/api'
import { cn } from '../lib/utils'

const categoryConfigs = {
  PROJECT: { label: '项目问题', color: 'bg-blue-500' },
  TASK: { label: '任务问题', color: 'bg-purple-500' },
  ACCEPTANCE: { label: '验收问题', color: 'bg-emerald-500' },
}

const issueTypeConfigs = {
  DEFECT: { label: '缺陷', color: 'bg-red-500' },
  RISK: { label: '风险', color: 'bg-orange-500' },
  BLOCKER: { label: '阻塞', color: 'bg-red-600' },
  TASK: { label: '任务', color: 'bg-blue-500' },
}

const severityConfigs = {
  CRITICAL: { label: '严重', color: 'bg-red-500' },
  MAJOR: { label: '重要', color: 'bg-orange-500' },
  MINOR: { label: '一般', color: 'bg-blue-500' },
}

const priorityConfigs = {
  URGENT: { label: '紧急', color: 'bg-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  MEDIUM: { label: '中', color: 'bg-yellow-500' },
  LOW: { label: '低', color: 'bg-blue-500' },
}

export default function IssueTemplateManagement() {
  const [loading, setLoading] = useState(true)
  const [templates, setTemplates] = useState([])
  const [projects, setProjects] = useState([])
  const [machines, setMachines] = useState([])
  
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterCategory, setFilterCategory] = useState('all')
  const [filterActive, setFilterActive] = useState('all')
  
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [showCreateIssueDialog, setShowCreateIssueDialog] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  
  // Form state
  const [templateForm, setTemplateForm] = useState({
    template_name: '',
    template_code: '',
    category: 'PROJECT',
    issue_type: 'DEFECT',
    default_severity: 'MINOR',
    default_priority: 'MEDIUM',
    default_impact_level: '',
    title_template: '',
    description_template: '',
    solution_template: '',
    default_tags: [],
    default_impact_scope: '',
    default_is_blocking: false,
    is_active: true,
    remark: '',
  })

  const [createIssueForm, setCreateIssueForm] = useState({
    project_id: '',
    machine_id: '',
    task_id: '',
    assignee_id: '',
    due_date: '',
    severity: '',
    priority: '',
    title: '',
    description: '',
  })

  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    loadTemplates()
    loadProjects()
  }, [])

  useEffect(() => {
    if (createIssueForm.project_id) {
      loadMachines(createIssueForm.project_id)
    }
  }, [createIssueForm.project_id])

  const loadTemplates = async () => {
    try {
      setLoading(true)
      const params = { page: 1, page_size: 100 }
      if (searchKeyword) params.keyword = searchKeyword
      if (filterCategory !== 'all') params.category = filterCategory
      if (filterActive !== 'all') params.is_active = filterActive === 'active'
      
      const res = await issueTemplateApi.list(params)
      const items = res.data?.items || res.data?.data?.items || res.data || []
      setTemplates(items)
    } catch (error) {
      console.error('Failed to load templates:', error)
      setTemplates([])
    } finally {
      setLoading(false)
    }
  }

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      const items = res.data?.items || res.data?.data?.items || res.data || []
      setProjects(items)
    } catch (error) {
      console.error('Failed to load projects:', error)
    }
  }

  const loadMachines = async (projectId) => {
    try {
      const res = await machineApi.list({ project_id: projectId, page_size: 1000 })
      const items = res.data?.items || res.data?.data?.items || res.data || []
      setMachines(items)
    } catch (error) {
      console.error('Failed to load machines:', error)
      setMachines([])
    }
  }

  useEffect(() => {
    loadTemplates()
  }, [searchKeyword, filterCategory, filterActive])

  const handleCreate = () => {
    setTemplateForm({
      template_name: '',
      template_code: '',
      category: 'PROJECT',
      issue_type: 'DEFECT',
      default_severity: 'MINOR',
      default_priority: 'MEDIUM',
      default_impact_level: '',
      title_template: '',
      description_template: '',
      solution_template: '',
      default_tags: [],
      default_impact_scope: '',
      default_is_blocking: false,
      is_active: true,
      remark: '',
    })
    setTagInput('')
    setShowCreateDialog(true)
  }

  const handleEdit = (template) => {
    setSelectedTemplate(template)
    setTemplateForm({
      template_name: template.template_name || '',
      template_code: template.template_code || '',
      category: template.category || 'PROJECT',
      issue_type: template.issue_type || 'DEFECT',
      default_severity: template.default_severity || 'MINOR',
      default_priority: template.default_priority || 'MEDIUM',
      default_impact_level: template.default_impact_level || '',
      title_template: template.title_template || '',
      description_template: template.description_template || '',
      solution_template: template.solution_template || '',
      default_tags: Array.isArray(template.default_tags) ? template.default_tags : (template.default_tags ? JSON.parse(template.default_tags) : []),
      default_impact_scope: template.default_impact_scope || '',
      default_is_blocking: template.default_is_blocking || false,
      is_active: template.is_active !== false,
      remark: template.remark || '',
    })
    setTagInput(template.default_tags ? (Array.isArray(template.default_tags) ? template.default_tags.join(',') : JSON.parse(template.default_tags).join(',')) : '')
    setShowEditDialog(true)
  }

  const handleViewDetail = async (templateId) => {
    try {
      const res = await issueTemplateApi.get(templateId)
      setSelectedTemplate(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch template detail:', error)
    }
  }

  const handleDelete = (template) => {
    setSelectedTemplate(template)
    setShowDeleteDialog(true)
  }

  const handleCreateIssue = (template) => {
    setSelectedTemplate(template)
    setCreateIssueForm({
      project_id: '',
      machine_id: '',
      task_id: '',
      assignee_id: '',
      due_date: '',
      severity: '',
      priority: '',
      title: '',
      description: '',
    })
    setShowCreateIssueDialog(true)
  }

  const handleSaveTemplate = async () => {
    if (!templateForm.template_name || !templateForm.template_code) {
      alert('请填写模板名称和模板编码')
      return
    }

    try {
      setLoading(true)
      // 处理标签
      const tags = tagInput ? tagInput.split(',').map(t => t.trim()).filter(t => t) : []
      
      const formData = {
        ...templateForm,
        default_tags: tags,
      }

      if (selectedTemplate) {
        await issueTemplateApi.update(selectedTemplate.id, formData)
      } else {
        await issueTemplateApi.create(formData)
      }
      
      setShowCreateDialog(false)
      setShowEditDialog(false)
      setSelectedTemplate(null)
      await loadTemplates()
    } catch (error) {
      console.error('Failed to save template:', error)
      alert('保存模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmDelete = async () => {
    try {
      setLoading(true)
      await issueTemplateApi.delete(selectedTemplate.id)
      setShowDeleteDialog(false)
      setSelectedTemplate(null)
      await loadTemplates()
    } catch (error) {
      console.error('Failed to delete template:', error)
      alert('删除模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmCreateIssue = async () => {
    if (!selectedTemplate) return

    try {
      setLoading(true)
      const formData = {
        ...createIssueForm,
        project_id: createIssueForm.project_id ? parseInt(createIssueForm.project_id) : null,
        machine_id: createIssueForm.machine_id ? parseInt(createIssueForm.machine_id) : null,
        task_id: createIssueForm.task_id ? parseInt(createIssueForm.task_id) : null,
        assignee_id: createIssueForm.assignee_id ? parseInt(createIssueForm.assignee_id) : null,
        severity: createIssueForm.severity || null,
        priority: createIssueForm.priority || null,
        title: createIssueForm.title || null,
        description: createIssueForm.description || null,
      }

      await issueTemplateApi.createIssue(selectedTemplate.id, formData)
      setShowCreateIssueDialog(false)
      setSelectedTemplate(null)
      alert('问题创建成功')
    } catch (error) {
      console.error('Failed to create issue from template:', error)
      alert('创建问题失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          template.template_name?.toLowerCase().includes(keyword) ||
          template.template_code?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [templates, searchKeyword])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题模板管理"
        description="管理问题模板，快速创建常见问题类型"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <Card className="bg-surface-50 border-white/5">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索模板名称、编码..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-surface-100 border-white/10 text-white"
                />
              </div>
              <Select value={filterCategory} onValueChange={setFilterCategory}>
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue placeholder="选择分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部分类</SelectItem>
                  {Object.entries(categoryConfigs).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      {config.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterActive} onValueChange={setFilterActive}>
                <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="active">启用</SelectItem>
                  <SelectItem value="inactive">禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Action Bar */}
        <div className="flex justify-end">
          <Button onClick={handleCreate} className="bg-primary hover:bg-primary/90">
            <Plus className="w-4 h-4 mr-2" />
            新建模板
          </Button>
        </div>

        {/* Template List */}
        <Card className="bg-surface-50 border-white/5">
          <CardHeader>
            <CardTitle className="text-white">问题模板列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredTemplates.length} 个模板
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredTemplates.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无模板</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-white/10">
                    <TableHead className="text-slate-300">模板名称</TableHead>
                    <TableHead className="text-slate-300">模板编码</TableHead>
                    <TableHead className="text-slate-300">分类</TableHead>
                    <TableHead className="text-slate-300">问题类型</TableHead>
                    <TableHead className="text-slate-300">默认优先级</TableHead>
                    <TableHead className="text-slate-300">使用次数</TableHead>
                    <TableHead className="text-slate-300">状态</TableHead>
                    <TableHead className="text-slate-300">创建时间</TableHead>
                    <TableHead className="text-right text-slate-300">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTemplates.map((template) => (
                    <TableRow key={template.id} className="border-white/10 hover:bg-surface-100/50">
                      <TableCell className="font-medium text-white">
                        {template.template_name}
                      </TableCell>
                      <TableCell className="text-slate-300">{template.template_code}</TableCell>
                      <TableCell>
                        <Badge className={categoryConfigs[template.category]?.color || 'bg-slate-500'}>
                          {categoryConfigs[template.category]?.label || template.category}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={issueTypeConfigs[template.issue_type]?.color || 'bg-slate-500'}>
                          {issueTypeConfigs[template.issue_type]?.label || template.issue_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={priorityConfigs[template.default_priority]?.color || 'bg-slate-500'}>
                          {priorityConfigs[template.default_priority]?.label || template.default_priority}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-300">{template.usage_count || 0}</TableCell>
                      <TableCell>
                        {template.is_active ? (
                          <Badge className="bg-green-500">启用</Badge>
                        ) : (
                          <Badge className="bg-gray-500">禁用</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {template.created_at ? formatDate(template.created_at) : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(template.id)}
                            className="text-slate-300 hover:text-white"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(template)}
                            className="text-slate-300 hover:text-white"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCreateIssue(template)}
                            className="text-slate-300 hover:text-white"
                          >
                            <Copy className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(template)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="w-4 h-4" />
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
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false)
          setShowEditDialog(false)
          setSelectedTemplate(null)
        }
      }}>
        <DialogContent className="bg-surface-50 border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">
              {selectedTemplate ? '编辑模板' : '新建模板'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">模板名称 *</Label>
                <Input
                  value={templateForm.template_name}
                  onChange={(e) => setTemplateForm({ ...templateForm, template_name: e.target.value })}
                  className="bg-surface-100 border-white/10 text-white"
                  placeholder="例如：温度控制问题模板"
                />
              </div>
              <div>
                <Label className="text-slate-300">模板编码 *</Label>
                <Input
                  value={templateForm.template_code}
                  onChange={(e) => setTemplateForm({ ...templateForm, template_code: e.target.value })}
                  className="bg-surface-100 border-white/10 text-white"
                  placeholder="例如：TEMP_CTRL_001"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">分类</Label>
                <Select
                  value={templateForm.category}
                  onValueChange={(value) => setTemplateForm({ ...templateForm, category: value })}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(categoryConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">问题类型</Label>
                <Select
                  value={templateForm.issue_type}
                  onValueChange={(value) => setTemplateForm({ ...templateForm, issue_type: value })}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(issueTypeConfigs).map(([key, config]) => (
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
                <Label className="text-slate-300">默认严重程度</Label>
                <Select
                  value={templateForm.default_severity}
                  onValueChange={(value) => setTemplateForm({ ...templateForm, default_severity: value })}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10 text-white">
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
                <Label className="text-slate-300">默认优先级</Label>
                <Select
                  value={templateForm.default_priority}
                  onValueChange={(value) => setTemplateForm({ ...templateForm, default_priority: value })}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10 text-white">
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
              <Label className="text-slate-300">标题模板 *</Label>
              <Input
                value={templateForm.title_template}
                onChange={(e) => setTemplateForm({ ...templateForm, title_template: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
                placeholder="例如：{project_name} - 温度控制问题"
              />
              <p className="text-xs text-slate-400 mt-1">
                支持变量：{'{project_name}'}, {'{machine_code}'}, {'{date}'}
              </p>
            </div>

            <div>
              <Label className="text-slate-300">描述模板</Label>
              <Textarea
                value={templateForm.description_template}
                onChange={(e) => setTemplateForm({ ...templateForm, description_template: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
                rows={4}
                placeholder="例如：项目 {project_code} 在 {date} 发现温度控制问题..."
              />
            </div>

            <div>
              <Label className="text-slate-300">解决方案模板</Label>
              <Textarea
                value={templateForm.solution_template}
                onChange={(e) => setTemplateForm({ ...templateForm, solution_template: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
                rows={3}
                placeholder="解决方案描述..."
              />
            </div>

            <div>
              <Label className="text-slate-300">默认标签（逗号分隔）</Label>
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                className="bg-surface-100 border-white/10 text-white"
                placeholder="例如：温度控制,FAT"
              />
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_blocking"
                  checked={templateForm.default_is_blocking}
                  onChange={(e) => setTemplateForm({ ...templateForm, default_is_blocking: e.target.checked })}
                  className="w-4 h-4"
                />
                <Label htmlFor="is_blocking" className="text-slate-300 cursor-pointer">
                  默认是否阻塞
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={templateForm.is_active}
                  onChange={(e) => setTemplateForm({ ...templateForm, is_active: e.target.checked })}
                  className="w-4 h-4"
                />
                <Label htmlFor="is_active" className="text-slate-300 cursor-pointer">
                  启用
                </Label>
              </div>
            </div>

            <div>
              <Label className="text-slate-300">备注</Label>
              <Textarea
                value={templateForm.remark}
                onChange={(e) => setTemplateForm({ ...templateForm, remark: e.target.value })}
                className="bg-surface-100 border-white/10 text-white"
                rows={2}
                placeholder="备注说明..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false)
                setShowEditDialog(false)
                setSelectedTemplate(null)
              }}
              className="border-white/10 text-slate-300"
            >
              取消
            </Button>
            <Button onClick={handleSaveTemplate} className="bg-primary hover:bg-primary/90">
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-surface-50 border-white/10 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">模板详情</DialogTitle>
          </DialogHeader>
          {selectedTemplate && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-400">模板名称</Label>
                  <p className="text-white">{selectedTemplate.template_name}</p>
                </div>
                <div>
                  <Label className="text-slate-400">模板编码</Label>
                  <p className="text-white">{selectedTemplate.template_code}</p>
                </div>
                <div>
                  <Label className="text-slate-400">分类</Label>
                  <Badge className={categoryConfigs[selectedTemplate.category]?.color || 'bg-slate-500'}>
                    {categoryConfigs[selectedTemplate.category]?.label || selectedTemplate.category}
                  </Badge>
                </div>
                <div>
                  <Label className="text-slate-400">问题类型</Label>
                  <Badge className={issueTypeConfigs[selectedTemplate.issue_type]?.color || 'bg-slate-500'}>
                    {issueTypeConfigs[selectedTemplate.issue_type]?.label || selectedTemplate.issue_type}
                  </Badge>
                </div>
                <div>
                  <Label className="text-slate-400">使用次数</Label>
                  <p className="text-white">{selectedTemplate.usage_count || 0}</p>
                </div>
                <div>
                  <Label className="text-slate-400">最后使用时间</Label>
                  <p className="text-white">
                    {selectedTemplate.last_used_at ? formatDate(selectedTemplate.last_used_at) : '未使用'}
                  </p>
                </div>
              </div>
              <div>
                <Label className="text-slate-400">标题模板</Label>
                <p className="text-white bg-surface-100 p-2 rounded">{selectedTemplate.title_template}</p>
              </div>
              {selectedTemplate.description_template && (
                <div>
                  <Label className="text-slate-400">描述模板</Label>
                  <p className="text-white bg-surface-100 p-2 rounded whitespace-pre-wrap">
                    {selectedTemplate.description_template}
                  </p>
                </div>
              )}
              {selectedTemplate.solution_template && (
                <div>
                  <Label className="text-slate-400">解决方案模板</Label>
                  <p className="text-white bg-surface-100 p-2 rounded whitespace-pre-wrap">
                    {selectedTemplate.solution_template}
                  </p>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)} className="border-white/10 text-slate-300">
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="bg-surface-50 border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white">确认删除</DialogTitle>
          </DialogHeader>
          <p className="text-slate-300">
            确定要删除模板 "{selectedTemplate?.template_name}" 吗？删除后无法恢复。
          </p>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              className="border-white/10 text-slate-300"
            >
              取消
            </Button>
            <Button onClick={handleConfirmDelete} className="bg-red-500 hover:bg-red-600">
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Issue Dialog */}
      <Dialog open={showCreateIssueDialog} onOpenChange={setShowCreateIssueDialog}>
        <DialogContent className="bg-surface-50 border-white/10 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-white">从模板创建问题</DialogTitle>
          </DialogHeader>
          {selectedTemplate && (
            <div className="space-y-4">
              <div className="p-3 bg-surface-100 rounded border border-white/10">
                <p className="text-sm text-slate-400">模板：{selectedTemplate.template_name}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">关联项目</Label>
                  <Select
                    value={createIssueForm.project_id}
                    onValueChange={(value) => setCreateIssueForm({ ...createIssueForm, project_id: value, machine_id: '' })}
                  >
                    <SelectTrigger className="bg-surface-100 border-white/10 text-white">
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">不关联</SelectItem>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id.toString()}>
                          {project.project_name} ({project.project_code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-slate-300">关联机台</Label>
                  <Select
                    value={createIssueForm.machine_id}
                    onValueChange={(value) => setCreateIssueForm({ ...createIssueForm, machine_id: value })}
                    disabled={!createIssueForm.project_id}
                  >
                    <SelectTrigger className="bg-surface-100 border-white/10 text-white" disabled={!createIssueForm.project_id}>
                      <SelectValue placeholder={createIssueForm.project_id ? "选择机台" : "请先选择项目"} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">不关联</SelectItem>
                      {machines.map((machine) => (
                        <SelectItem key={machine.id} value={machine.id.toString()}>
                          {machine.machine_name} ({machine.machine_code})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label className="text-slate-300">要求完成日期</Label>
                <Input
                  type="date"
                  value={createIssueForm.due_date}
                  onChange={(e) => setCreateIssueForm({ ...createIssueForm, due_date: e.target.value })}
                  className="bg-surface-100 border-white/10 text-white"
                />
              </div>
              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded">
                <p className="text-sm text-blue-300">
                  提示：标题和描述将使用模板的默认值，您可以在创建后编辑。
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateIssueDialog(false)}
              className="border-white/10 text-slate-300"
            >
              取消
            </Button>
            <Button onClick={handleConfirmCreateIssue} className="bg-primary hover:bg-primary/90">
              创建问题
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
