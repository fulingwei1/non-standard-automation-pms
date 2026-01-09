import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { rdProjectApi } from '../services/api'
import { formatDate } from '../lib/utils'
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
} from '../components/ui'
import {
  ArrowLeft,
  Plus,
  Clock,
  Calendar,
  User,
  FileText,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Edit2,
  Trash2,
} from 'lucide-react'

const statusMap = {
  DRAFT: { label: '草稿', color: 'secondary' },
  PENDING: { label: '待审核', color: 'warning' },
  APPROVED: { label: '已通过', color: 'success' },
  REJECTED: { label: '已驳回', color: 'danger' },
}

export default function RdProjectWorklogs() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [worklogs, setWorklogs] = useState([])
  const [formOpen, setFormOpen] = useState(false)
  const [formData, setFormData] = useState({
    work_date: new Date().toISOString().split('T')[0],
    work_hours: '',
    work_type: 'NORMAL',
    description: '',
  })
  const [formLoading, setFormLoading] = useState(false)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 0,
  })

  useEffect(() => {
    if (id) {
      fetchProject()
      fetchWorklogs()
    }
  }, [id, pagination.page])

  const fetchProject = async () => {
    try {
      const response = await rdProjectApi.get(id)
      const projectData = response.data?.data || response.data || response
      setProject(projectData)
    } catch (err) {
      console.error('操作失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchWorklogs = async () => {
    try {
      const response = await rdProjectApi.getWorklogs(id, {
        page: pagination.page,
        page_size: pagination.page_size,
      })
      const data = response.data?.data || response.data || response
      
      if (data.items) {
        setWorklogs(data.items || [])
        setPagination({
          page: data.page || 1,
          page_size: data.page_size || 20,
          total: data.total || 0,
          pages: data.pages || 0,
        })
      } else {
        setWorklogs(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      setWorklogs([])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    try {
      await rdProjectApi.createWorklog(id, formData)
      setFormOpen(false)
      setFormData({
        work_date: new Date().toISOString().split('T')[0],
        work_hours: '',
        work_type: 'NORMAL',
        description: '',
      })
      fetchWorklogs()
    } catch (err) {
      alert('创建工作日志失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setFormLoading(false)
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
            <h1 className="text-2xl font-bold text-white">研发人员工作日志</h1>
            <p className="text-sm text-slate-400 mt-1">{project.project_name}</p>
          </div>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          记录工作日志
        </Button>
      </div>

      {/* Summary */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">总记录数</p>
              <p className="text-2xl font-semibold text-white">{pagination.total}</p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">总工时</p>
              <p className="text-2xl font-semibold text-primary">
                {worklogs.reduce((sum, log) => sum + parseFloat(log.work_hours || 0), 0).toFixed(1)} 小时
              </p>
            </div>
            <div className="p-4 rounded-lg bg-white/[0.03]">
              <p className="text-sm text-slate-400 mb-1">参与人数</p>
              <p className="text-2xl font-semibold text-white">
                {new Set(worklogs.map(log => log.user_id)).size} 人
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Worklogs List */}
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">工作日志列表</h3>
          {worklogs.length > 0 ? (
            <div className="space-y-3">
              {worklogs.map((log) => {
                const status = statusMap[log.status] || statusMap.DRAFT
                return (
                  <div
                    key={log.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="p-2 rounded-lg bg-primary/20">
                        <Clock className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium text-white">{log.user_name || '未知用户'}</p>
                          <Badge variant={status.color}>{status.label}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            <span>{formatDate(log.work_date)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            <span>{log.work_hours} 小时</span>
                          </div>
                          {log.work_type !== 'NORMAL' && (
                            <Badge variant="outline" className="text-xs">
                              {log.work_type === 'OVERTIME' ? '加班' : log.work_type}
                            </Badge>
                          )}
                        </div>
                        {log.description && (
                          <p className="text-sm text-slate-500 mt-2 line-clamp-2">
                            {log.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {log.status === 'DRAFT' && (
                        <>
                          <Button variant="ghost" size="icon">
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
              <p>暂无工作日志</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => setFormOpen(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                记录第一条工作日志
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

      {/* Create Form Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>记录工作日志</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <DialogBody className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    工作日期 <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="date"
                    value={formData.work_date}
                    onChange={(e) =>
                      setFormData({ ...formData, work_date: e.target.value })
                    }
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    工作小时数 <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="number"
                    step="0.5"
                    min="0"
                    max="24"
                    value={formData.work_hours}
                    onChange={(e) =>
                      setFormData({ ...formData, work_hours: e.target.value })
                    }
                    placeholder="0.0"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    工作类型
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
                    value={formData.work_type}
                    onChange={(e) =>
                      setFormData({ ...formData, work_type: e.target.value })
                    }
                  >
                    <option value="NORMAL">正常</option>
                    <option value="OVERTIME">加班</option>
                    <option value="LEAVE">请假</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  工作内容
                </label>
                <textarea
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary"
                  rows={4}
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="请描述今天的工作内容..."
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
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}





