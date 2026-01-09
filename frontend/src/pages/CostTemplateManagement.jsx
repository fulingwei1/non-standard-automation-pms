/**
 * Cost Template Management Page - 成本模板管理页面
 * Features: Template list, create, edit, delete, preview
 */

import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Copy,
  Layers,
  FileText,
  Calendar,
  User,
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
  Button,
  Badge,
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesTemplateApi } from '../services/api'

export default function CostTemplateManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [templates, setTemplates] = useState([])
  const [filteredTemplates, setFilteredTemplates] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [equipmentFilter, setEquipmentFilter] = useState('all')
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  
  // Form state
  const [formData, setFormData] = useState({
    template_code: '',
    template_name: '',
    template_type: 'STANDARD',
    equipment_type: '',
    industry: '',
    description: '',
    cost_structure: {
      categories: [],
    },
    is_active: true,
  })
  
  useEffect(() => {
    loadTemplates()
  }, [])
  
  useEffect(() => {
    filterTemplates()
  }, [templates, searchTerm, typeFilter, equipmentFilter])
  
  const loadTemplates = async () => {
    setLoading(true)
    try {
      const res = await salesTemplateApi.listCostTemplates({ page: 1, page_size: 1000 })
      const items = res.data?.data?.items || res.data?.items || []
      setTemplates(items)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const filterTemplates = () => {
    let filtered = [...templates]
    
    if (searchTerm) {
      filtered = filtered.filter(t => 
        t.template_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.template_code?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    if (typeFilter !== 'all') {
      filtered = filtered.filter(t => t.template_type === typeFilter)
    }
    
    if (equipmentFilter !== 'all') {
      filtered = filtered.filter(t => t.equipment_type === equipmentFilter)
    }
    
    setFilteredTemplates(filtered)
  }
  
  const handleCreate = () => {
    setFormData({
      template_code: '',
      template_name: '',
      template_type: 'STANDARD',
      equipment_type: '',
      industry: '',
      description: '',
      cost_structure: {
        categories: [],
      },
      is_active: true,
    })
    setShowCreateDialog(true)
  }
  
  const handleEdit = (template) => {
    setSelectedTemplate(template)
    setFormData({
      template_code: template.template_code || '',
      template_name: template.template_name || '',
      template_type: template.template_type || 'STANDARD',
      equipment_type: template.equipment_type || '',
      industry: template.industry || '',
      description: template.description || '',
      cost_structure: template.cost_structure || { categories: [] },
      is_active: template.is_active !== false,
    })
    setShowEditDialog(true)
  }
  
  const handlePreview = (template) => {
    setSelectedTemplate(template)
    setShowPreviewDialog(true)
  }
  
  const handleDelete = (template) => {
    setSelectedTemplate(template)
    setShowDeleteDialog(true)
  }
  
  const handleSave = async () => {
    try {
      setLoading(true)
      if (selectedTemplate) {
        await salesTemplateApi.updateCostTemplate(selectedTemplate.id, formData)
      } else {
        await salesTemplateApi.createCostTemplate(formData)
      }
      await loadTemplates()
      setShowCreateDialog(false)
      setShowEditDialog(false)
      setSelectedTemplate(null)
    } catch (error) {
      alert('保存模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const handleConfirmDelete = async () => {
    try {
      setLoading(true)
      await salesTemplateApi.deleteCostTemplate(selectedTemplate.id)
      await loadTemplates()
      setShowDeleteDialog(false)
      setSelectedTemplate(null)
    } catch (error) {
      alert('删除模板失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }
  
  const addCategory = () => {
    setFormData({
      ...formData,
      cost_structure: {
        categories: [
          ...(formData.cost_structure?.categories || []),
          {
            category: '',
            items: [],
          },
        ],
      },
    })
  }
  
  const addItem = (categoryIndex) => {
    const categories = [...(formData.cost_structure?.categories || [])]
    categories[categoryIndex].items = [
      ...(categories[categoryIndex].items || []),
      {
        item_name: '',
        specification: '',
        unit: '',
        default_qty: 1,
        default_unit_price: 0,
        default_cost: 0,
        lead_time_days: 0,
      },
    ]
    setFormData({
      ...formData,
      cost_structure: {
        categories,
      },
    })
  }
  
  const updateCategory = (index, field, value) => {
    const categories = [...(formData.cost_structure?.categories || [])]
    categories[index][field] = value
    setFormData({
      ...formData,
      cost_structure: {
        categories,
      },
    })
  }
  
  const updateItem = (categoryIndex, itemIndex, field, value) => {
    const categories = [...(formData.cost_structure?.categories || [])]
    categories[categoryIndex].items[itemIndex][field] = value
    setFormData({
      ...formData,
      cost_structure: {
        categories,
      },
    })
  }
  
  const removeCategory = (index) => {
    const categories = [...(formData.cost_structure?.categories || [])]
    categories.splice(index, 1)
    setFormData({
      ...formData,
      cost_structure: {
        categories,
      },
    })
  }
  
  const removeItem = (categoryIndex, itemIndex) => {
    const categories = [...(formData.cost_structure?.categories || [])]
    categories[categoryIndex].items.splice(itemIndex, 1)
    setFormData({
      ...formData,
      cost_structure: {
        categories,
      },
    })
  }
  
  // Get unique equipment types
  const equipmentTypes = useMemo(() => {
    const types = new Set()
    templates.forEach(t => {
      if (t.equipment_type) types.add(t.equipment_type)
    })
    return Array.from(types)
  }, [templates])
  
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="成本模板管理"
        description="管理报价成本模板，快速生成报价成本"
        actions={
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            新建模板
          </Button>
        }
      />
      
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索模板名称或编码..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="模板类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="STANDARD">标准模板</SelectItem>
                <SelectItem value="CUSTOM">自定义模板</SelectItem>
                <SelectItem value="PROJECT">项目模板</SelectItem>
              </SelectContent>
            </Select>
            <Select value={equipmentFilter} onValueChange={setEquipmentFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="设备类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部设备</SelectItem>
                {equipmentTypes.map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      
      {/* Template List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => (
          <Card key={template.id} className="hover:border-slate-600 transition-colors">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{template.template_name}</CardTitle>
                  <CardDescription className="mt-1">{template.template_code}</CardDescription>
                </div>
                <Badge className={template.is_active ? 'bg-green-500' : 'bg-slate-500'}>
                  {template.is_active ? '启用' : '禁用'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm text-slate-400">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  <span>类型: {template.template_type === 'STANDARD' ? '标准' :
                               template.template_type === 'CUSTOM' ? '自定义' :
                               '项目'}</span>
                </div>
                {template.equipment_type && (
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    <span>设备: {template.equipment_type}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  <span>总成本: {formatCurrency(template.total_cost || 0)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span>使用次数: {template.usage_count || 0}</span>
                </div>
              </div>
              
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePreview(template)}
                  className="flex-1"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  预览
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleEdit(template)}
                  className="flex-1"
                >
                  <Edit className="h-4 w-4 mr-1" />
                  编辑
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(template)}
                  className="text-red-400 hover:text-red-300"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {filteredTemplates.length === 0 && !loading && (
        <Card>
          <CardContent className="py-12 text-center text-slate-400">
            暂无模板，点击"新建模板"创建第一个模板
          </CardContent>
        </Card>
      )}
      
      {/* Create/Edit Dialog */}
      <Dialog open={showCreateDialog || showEditDialog} onOpenChange={(open) => {
        if (!open) {
          setShowCreateDialog(false)
          setShowEditDialog(false)
          setSelectedTemplate(null)
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedTemplate ? '编辑模板' : '新建模板'}</DialogTitle>
            <DialogDescription>创建或编辑成本模板</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>模板编码 *</Label>
                <Input
                  value={formData.template_code}
                  onChange={(e) => setFormData({ ...formData, template_code: e.target.value })}
                  placeholder="TPL-ICT-001"
                />
              </div>
              <div>
                <Label>模板名称 *</Label>
                <Input
                  value={formData.template_name}
                  onChange={(e) => setFormData({ ...formData, template_name: e.target.value })}
                  placeholder="ICT测试设备标准模板"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>模板类型</Label>
                <Select
                  value={formData.template_type}
                  onValueChange={(value) => setFormData({ ...formData, template_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="STANDARD">标准模板</SelectItem>
                    <SelectItem value="CUSTOM">自定义模板</SelectItem>
                    <SelectItem value="PROJECT">项目模板</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>设备类型</Label>
                <Input
                  value={formData.equipment_type}
                  onChange={(e) => setFormData({ ...formData, equipment_type: e.target.value })}
                  placeholder="ICT"
                />
              </div>
              <div>
                <Label>行业</Label>
                <Input
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  placeholder="消费电子"
                />
              </div>
            </div>
            
            <div>
              <Label>模板说明</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="模板说明..."
                rows={3}
              />
            </div>
            
            {/* Cost Structure */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>成本结构</Label>
                <Button variant="outline" size="sm" onClick={addCategory}>
                  <Plus className="h-4 w-4 mr-1" />
                  添加分类
                </Button>
              </div>
              
              <div className="space-y-4 border border-slate-700 rounded-lg p-4">
                {formData.cost_structure?.categories?.map((category, catIndex) => (
                  <div key={catIndex} className="border border-slate-600 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Input
                        value={category.category}
                        onChange={(e) => updateCategory(catIndex, 'category', e.target.value)}
                        placeholder="分类名称（如：硬件成本）"
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => addItem(catIndex)}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        添加项
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => removeCategory(catIndex)}
                        className="text-red-400"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    
                    <div className="space-y-2">
                      {category.items?.map((item, itemIndex) => (
                        <div key={itemIndex} className="grid grid-cols-7 gap-2 items-end">
                          <Input
                            value={item.item_name}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'item_name', e.target.value)}
                            placeholder="项目名称"
                          />
                          <Input
                            value={item.specification}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'specification', e.target.value)}
                            placeholder="规格型号"
                          />
                          <Input
                            value={item.unit}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'unit', e.target.value)}
                            placeholder="单位"
                          />
                          <Input
                            type="number"
                            value={item.default_qty}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'default_qty', parseFloat(e.target.value) || 0)}
                            placeholder="数量"
                          />
                          <Input
                            type="number"
                            value={item.default_unit_price}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'default_unit_price', parseFloat(e.target.value) || 0)}
                            placeholder="单价"
                          />
                          <Input
                            type="number"
                            value={item.default_cost}
                            onChange={(e) => updateItem(catIndex, itemIndex, 'default_cost', parseFloat(e.target.value) || 0)}
                            placeholder="成本"
                          />
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => removeItem(catIndex, itemIndex)}
                            className="text-red-400"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                
                {(!formData.cost_structure?.categories || formData.cost_structure.categories.length === 0) && (
                  <div className="text-center py-8 text-slate-400">
                    点击"添加分类"开始构建成本结构
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false)
              setShowEditDialog(false)
              setSelectedTemplate(null)
            }}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={!formData.template_code || !formData.template_name}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>模板预览</DialogTitle>
            <DialogDescription>{selectedTemplate?.template_name}</DialogDescription>
          </DialogHeader>
          
          {selectedTemplate && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><strong>模板编码:</strong> {selectedTemplate.template_code}</div>
                <div><strong>模板类型:</strong> {selectedTemplate.template_type}</div>
                <div><strong>设备类型:</strong> {selectedTemplate.equipment_type || '-'}</div>
                <div><strong>总成本:</strong> {formatCurrency(selectedTemplate.total_cost || 0)}</div>
              </div>
              
              {selectedTemplate.cost_structure && (
                <div className="space-y-4">
                  {selectedTemplate.cost_structure.categories?.map((category, catIndex) => (
                    <div key={catIndex} className="border border-slate-700 rounded-lg p-4">
                      <h4 className="font-semibold mb-2">{category.category}</h4>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>项目名称</TableHead>
                            <TableHead>规格型号</TableHead>
                            <TableHead>单位</TableHead>
                            <TableHead>数量</TableHead>
                            <TableHead>单价</TableHead>
                            <TableHead>成本</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {category.items?.map((item, itemIndex) => (
                            <TableRow key={itemIndex}>
                              <TableCell>{item.item_name}</TableCell>
                              <TableCell>{item.specification || '-'}</TableCell>
                              <TableCell>{item.unit || '-'}</TableCell>
                              <TableCell>{item.default_qty}</TableCell>
                              <TableCell>{formatCurrency(item.default_unit_price || 0)}</TableCell>
                              <TableCell>{formatCurrency(item.default_cost || 0)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPreviewDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除模板 "{selectedTemplate?.template_name}" 吗？此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
