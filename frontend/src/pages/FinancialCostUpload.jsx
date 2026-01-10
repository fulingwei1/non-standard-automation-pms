/**
 * Financial Cost Upload Page - 财务历史项目成本上传页面
 * Features: Upload historical project costs (travel, labor, entertainment, etc.)
 */

import { useState, useEffect, useRef, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Trash2,
  Search,
  Filter,
  Calendar,
  DollarSign,
  Users,
  MapPin,
  FileText,
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { financialCostApi } from '../services/api'

export default function FinancialCostUpload() {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [costs, setCosts] = useState([])
  const [filteredCosts, setFilteredCosts] = useState([])
  const [uploadResult, setUploadResult] = useState(null)
  const [showResultDialog, setShowResultDialog] = useState(false)
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [projectId, setProjectId] = useState(null) // 项目ID筛选
  
  // File input ref
  const fileInputRef = useRef(null)
  
  // 从URL参数读取项目ID
  useEffect(() => {
    const projectIdParam = searchParams.get('project_id')
    if (projectIdParam) {
      setProjectId(parseInt(projectIdParam))
    }
  }, [searchParams])
  
  useEffect(() => {
    loadCosts()
  }, [projectId])
  
  useEffect(() => {
    filterCosts()
  }, [costs, searchTerm, typeFilter, categoryFilter, startDate, endDate])
  
  const loadCosts = async () => {
    setLoading(true)
    try {
      const params = {}
      if (projectId) params.project_id = projectId
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      if (typeFilter !== 'all') params.cost_type = typeFilter
      if (categoryFilter !== 'all') params.cost_category = categoryFilter
      
      const res = await financialCostApi.listCosts({ page: 1, page_size: 1000, ...params })
      const items = res.data?.data?.items || res.data?.items || []
      setCosts(items)
    } catch (error) {
      console.error('加载成本记录失败:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const filterCosts = () => {
    let filtered = [...costs]
    
    if (searchTerm) {
      filtered = filtered.filter(c => 
        c.project_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.project_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.cost_item?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.description?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    
    setFilteredCosts(filtered)
  }
  
  const handleDownloadTemplate = async () => {
    try {
      const response = await financialCostApi.downloadTemplate()
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `财务项目成本上传模板_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('下载模板失败:', error)
      alert('下载模板失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      handleUpload(file)
    }
  }
  
  const handleUpload = async (file) => {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('只支持Excel文件(.xlsx, .xls)')
      return
    }
    
    setUploading(true)
    try {
      const res = await financialCostApi.uploadCosts(file)
      const result = res.data?.data || res.data
      setUploadResult(result)
      setShowResultDialog(true)
      
      // 重新加载数据
      await loadCosts()
      
      // 清空文件选择
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      console.error('上传失败:', error)
      const errorDetail = error.response?.data?.detail || error.message
      alert('上传失败: ' + errorDetail)
    } finally {
      setUploading(false)
    }
  }
  
  const handleDelete = async (costId) => {
    if (!confirm('确定要删除这条成本记录吗？')) {
      return
    }
    
    try {
      await financialCostApi.deleteCost(costId)
      await loadCosts()
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  
  // Get unique cost types and categories
  const costTypes = ['LABOR', 'TRAVEL', 'ENTERTAINMENT', 'OTHER']
  const costCategories = useMemo(() => {
    const categories = new Set()
    costs.forEach(c => {
      if (c.cost_category) categories.add(c.cost_category)
    })
    return Array.from(categories)
  }, [costs])
  
  // Cost type labels
  const costTypeLabels = {
    'LABOR': '人工费用',
    'TRAVEL': '出差费用',
    'ENTERTAINMENT': '招待费用',
    'OTHER': '其他费用',
  }
  
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="财务历史项目成本上传"
        description="上传历史项目的非物料成本，包括出差费用、人工费用、招待费用等"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleDownloadTemplate}>
              <Download className="h-4 w-4 mr-2" />
              下载模板
            </Button>
            <Button onClick={() => fileInputRef.current?.click()}>
              <Upload className="h-4 w-4 mr-2" />
              {uploading ? '上传中...' : '上传Excel'}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>
        }
      />
      
      {/* Upload Instructions */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2">
            <div className="flex items-start gap-2">
              <FileSpreadsheet className="h-5 w-5 text-blue-400 mt-0.5" />
              <div>
                <div className="font-medium text-blue-400 mb-1">上传说明</div>
                <ul className="text-sm text-slate-300 space-y-1 list-disc list-inside">
                  <li>请先下载模板，按照模板格式填写成本数据</li>
                  <li>支持的成本类型：人工费用、出差费用、招待费用、其他费用</li>
                  <li>必填字段：项目编号、成本类型、成本分类、金额、发生日期</li>
                  <li>人工费用需填写：人员姓名、工时、时薪</li>
                  <li>出差费用建议填写：地点、参与人员、用途</li>
                  <li>系统会自动识别项目编号，如项目不存在将跳过该行</li>
                </ul>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索项目编号、项目名称、成本项..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="成本类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {costTypes.map(type => (
                  <SelectItem key={type} value={type}>{costTypeLabels[type]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="成本分类" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部分类</SelectItem>
                {costCategories.map(cat => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="开始日期"
              className="w-40"
            />
            <Input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              placeholder="结束日期"
              className="w-40"
            />
            <Button variant="outline" onClick={loadCosts}>
              <Search className="h-4 w-4 mr-2" />
              查询
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Cost List */}
      <Card>
        <CardHeader>
          <CardTitle>成本记录</CardTitle>
          <CardDescription>共 {filteredCosts.length} 条记录</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>项目编号</TableHead>
                <TableHead>项目名称</TableHead>
                <TableHead>成本类型</TableHead>
                <TableHead>成本分类</TableHead>
                <TableHead>成本项</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>发生日期</TableHead>
                <TableHead>上传批次</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCosts.map((cost) => (
                <TableRow key={cost.id}>
                  <TableCell>
                    <div className="font-medium">{cost.project_code}</div>
                  </TableCell>
                  <TableCell>{cost.project_name || '-'}</TableCell>
                  <TableCell>
                    <Badge className={cn(
                      cost.cost_type === 'LABOR' && 'bg-purple-500',
                      cost.cost_type === 'TRAVEL' && 'bg-blue-500',
                      cost.cost_type === 'ENTERTAINMENT' && 'bg-amber-500',
                      cost.cost_type === 'OTHER' && 'bg-slate-500'
                    )}>
                      {costTypeLabels[cost.cost_type] || cost.cost_type}
                    </Badge>
                  </TableCell>
                  <TableCell>{cost.cost_category}</TableCell>
                  <TableCell>{cost.cost_item || '-'}</TableCell>
                  <TableCell className="font-medium">
                    {formatCurrency(cost.amount || 0)}
                  </TableCell>
                  <TableCell>
                    {cost.cost_date ? formatDate(cost.cost_date) : '-'}
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-slate-400">
                      {cost.upload_batch_no || '-'}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(cost.id)}
                      className="text-red-400"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          
          {filteredCosts.length === 0 && !loading && (
            <div className="text-center py-12 text-slate-400">
              暂无成本记录，点击"上传Excel"上传第一条记录
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Upload Result Dialog */}
      <Dialog open={showResultDialog} onOpenChange={setShowResultDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>上传结果</DialogTitle>
            <DialogDescription>Excel文件处理完成</DialogDescription>
          </DialogHeader>
          
          {uploadResult && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                {uploadResult.success_count > 0 && (
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>成功: {uploadResult.success_count} 条</span>
                  </div>
                )}
                {uploadResult.error_count > 0 && (
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle className="h-5 w-5" />
                    <span>失败: {uploadResult.error_count} 条</span>
                  </div>
                )}
              </div>
              
              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3 max-h-60 overflow-y-auto">
                  <div className="font-medium text-red-400 mb-2">错误详情：</div>
                  <ul className="text-sm text-slate-300 space-y-1">
                    {uploadResult.errors.map((error, idx) => (
                      <li key={idx}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {uploadResult.upload_batch_no && (
                <div className="text-sm text-slate-400">
                  上传批次号: {uploadResult.upload_batch_no}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button onClick={() => setShowResultDialog(false)}>
              确定
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
