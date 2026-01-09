import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { rdProjectApi } from '../services/api'
import { formatDate } from '../lib/utils'

// Format file size
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '../components/ui'
import {
  ArrowLeft,
  Plus,
  Upload,
  FileText,
  Download,
  Trash2,
  Eye,
  Calendar,
  User,
  AlertCircle,
  File,
  FileImage,
  FileVideo,
  FileCode,
  FileSpreadsheet,
} from 'lucide-react'

const docTypeMap = {
  REQUIREMENT: { label: '需求文档', color: 'primary' },
  DESIGN: { label: '设计文档', color: 'blue' },
  SPECIFICATION: { label: '规格文档', color: 'purple' },
  TEST: { label: '测试文档', color: 'emerald' },
  REPORT: { label: '报告文档', color: 'amber' },
  OTHER: { label: '其他', color: 'gray' },
}

const statusMap = {
  DRAFT: { label: '草稿', color: 'secondary' },
  REVIEW: { label: '评审中', color: 'warning' },
  APPROVED: { label: '已批准', color: 'success' },
  RELEASED: { label: '已发布', color: 'success' },
}

const getFileIcon = (fileName) => {
  const ext = fileName?.split('.').pop()?.toLowerCase() || ''
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) {
    return FileImage
  }
  if (['mp4', 'avi', 'mov', 'wmv', 'flv'].includes(ext)) {
    return FileVideo
  }
  if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c'].includes(ext)) {
    return FileCode
  }
  if (['xls', 'xlsx', 'csv'].includes(ext)) {
    return FileSpreadsheet
  }
  return FileText
}

export default function RdProjectDocuments() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [documents, setDocuments] = useState([])
  const [formOpen, setFormOpen] = useState(false)
  const [uploadFile, setUploadFile] = useState(null)
  const [formData, setFormData] = useState({
    doc_type: 'OTHER',
    doc_category: '',
    doc_name: '',
    doc_no: '',
    version: '1.0',
    description: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [filterType, setFilterType] = useState('')
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0,
  })

  useEffect(() => {
    if (id) {
      fetchProject()
      fetchDocuments()
    }
  }, [id, pagination.page, filterType])

  const fetchProject = async () => {
    try {
      const response = await rdProjectApi.get(id)
      const projectData = response.data?.data || response.data || response
      setProject(projectData)
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  const fetchDocuments = async () => {
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
      }
      if (filterType) params.doc_type = filterType

      const response = await rdProjectApi.getDocuments(id, params)
      const data = response.data?.data || response.data || response
      
      if (data.items) {
        setDocuments(data.items || [])
        setPagination({
          page: data.page || 1,
          page_size: data.page_size || 20,
          total: data.total || 0,
          pages: data.pages || 0,
        })
      } else {
        setDocuments(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      setDocuments([])
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setUploadFile(file)
      if (!formData.doc_name) {
        setFormData({ ...formData, doc_name: file.name })
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!uploadFile) {
      alert('请选择要上传的文件')
      return
    }

    // 检查文件大小（最大50MB）
    if (uploadFile.size > 50 * 1024 * 1024) {
      alert('文件大小不能超过 50MB')
      return
    }

    setFormLoading(true)
    try {
      // 使用FormData上传文件
      const uploadFormData = new FormData()
      uploadFormData.append('file', uploadFile)
      uploadFormData.append('doc_type', formData.doc_type || 'OTHER')
      uploadFormData.append('doc_category', formData.doc_category || '')
      uploadFormData.append('doc_name', formData.doc_name || uploadFile.name)
      uploadFormData.append('doc_no', formData.doc_no || '')
      uploadFormData.append('version', formData.version || '1.0')
      if (formData.description) {
        uploadFormData.append('description', formData.description)
      }

      await rdProjectApi.uploadDocument(id, uploadFormData)
      setFormOpen(false)
      setUploadFile(null)
      setFormData({
        doc_type: 'OTHER',
        doc_category: '',
        doc_name: '',
        doc_no: '',
        version: '1.0',
        description: '',
      })
      fetchDocuments()
      alert('文档上传成功')
    } catch (err) {
      alert('上传文档失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setFormLoading(false)
    }
  }

  const handleDownload = async (doc) => {
    try {
      const response = await rdProjectApi.downloadDocument(id, doc.id)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', doc.file_name)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      alert('下载失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  if (loading) {
    return <div className="text-center py-12">加载中...</div>
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">研发项目不存在</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/rd-projects')}>
          返回列表
        </Button>
      </div>
    )
  }

  const filteredDocuments = filterType
    ? documents.filter((doc) => doc.doc_type === filterType)
    : documents

  return (
    <motion.div initial="hidden" animate="visible">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/rd-projects/${id}`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">研发项目文档管理</h1>
            <p className="text-sm text-slate-400 mt-1">{project.project_name}</p>
          </div>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          上传文档
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="文档类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(docTypeMap).map(([key, value]) => (
                  <SelectItem key={key} value={key}>
                    {value.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">文档列表</h3>
          {filteredDocuments.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocuments.map((doc) => {
                const docType = docTypeMap[doc.doc_type] || docTypeMap.OTHER
                const status = statusMap[doc.status] || statusMap.DRAFT
                const FileIcon = getFileIcon(doc.file_name)

                return (
                  <div
                    key={doc.id}
                    className="p-4 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors border border-white/5"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="p-2 rounded-lg bg-primary/20">
                        <FileIcon className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex gap-1">
                        <Badge variant={docType.color} className="text-xs">
                          {docType.label}
                        </Badge>
                        <Badge variant={status.color} className="text-xs">
                          {status.label}
                        </Badge>
                      </div>
                    </div>
                    <h4 className="font-semibold text-white mb-2 line-clamp-2">
                      {doc.doc_name}
                    </h4>
                    {doc.doc_no && (
                      <p className="text-xs text-slate-500 mb-2">编号: {doc.doc_no}</p>
                    )}
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <span>版本: {doc.version}</span>
                      {doc.file_size && <span>{formatFileSize(doc.file_size)}</span>}
                    </div>
                    {doc.description && (
                      <p className="text-sm text-slate-500 mb-3 line-clamp-2">
                        {doc.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between pt-3 border-t border-white/5">
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleDownload(doc)}>
                          <Download className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>暂无文档</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setFormOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                上传第一个文档
              </Button>
            </div>
          )}

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                disabled={pagination.page <= 1}
              >
                上一页
              </Button>
              <span className="text-sm text-slate-400">
                第 {pagination.page} / {pagination.pages} 页，共 {pagination.total} 条
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                disabled={pagination.page >= pagination.pages}
              >
                下一页
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Form Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>上传文档</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <DialogBody className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  选择文件 <span className="text-red-500">*</span>
                </label>
                <div className="flex items-center gap-4">
                  <Input
                    type="file"
                    onChange={handleFileSelect}
                    className="flex-1"
                  />
                  {uploadFile && (
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <File className="h-4 w-4" />
                      <span>{uploadFile.name}</span>
                      <span className="text-xs">({formatFileSize(uploadFile.size)})</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    文档类型 <span className="text-red-500">*</span>
                  </label>
                  <Select
                    value={formData.doc_type}
                    onValueChange={(value) =>
                      setFormData({ ...formData, doc_type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(docTypeMap).map(([key, value]) => (
                        <SelectItem key={key} value={key}>
                          {value.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    版本号
                  </label>
                  <Input
                    value={formData.version}
                    onChange={(e) =>
                      setFormData({ ...formData, version: e.target.value })
                    }
                    placeholder="1.0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    文档名称 <span className="text-red-500">*</span>
                  </label>
                  <Input
                    value={formData.doc_name}
                    onChange={(e) =>
                      setFormData({ ...formData, doc_name: e.target.value })
                    }
                    placeholder="请输入文档名称"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    文档编号
                  </label>
                  <Input
                    value={formData.doc_no}
                    onChange={(e) =>
                      setFormData({ ...formData, doc_no: e.target.value })
                    }
                    placeholder="可选"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  文档描述
                </label>
                <textarea
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={3}
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="请输入文档描述"
                />
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setFormOpen(false)}
              >
                取消
              </Button>
              <Button type="submit" loading={formLoading}>
                <Upload className="h-4 w-4 mr-2" />
                上传
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

