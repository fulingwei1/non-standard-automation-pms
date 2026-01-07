import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { pmoApi, projectApi } from '../services/api'
import { formatDate, formatTime } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonCard,
} from '../components/ui'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui'
import {
  Plus,
  Search,
  Calendar,
  Clock,
  MapPin,
  Users,
  FileText,
  CheckCircle2,
  XCircle,
  Eye,
  Edit,
  ArrowRight,
  Briefcase,
  AlertCircle,
} from 'lucide-react'

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
}

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const getMeetingTypeLabel = (type) => {
  const labels = {
    KICKOFF: '项目启动会',
    WEEKLY: '周例会',
    MILESTONE_REVIEW: '里程碑评审',
    CHANGE_REVIEW: '变更评审',
    RISK_REVIEW: '风险评审',
    CLOSURE: '结项评审会',
    OTHER: '其他',
  }
  return labels[type] || type
}

const getStatusBadge = (status) => {
  const badges = {
    SCHEDULED: { label: '已安排', variant: 'info', color: 'text-blue-400' },
    ONGOING: { label: '进行中', variant: 'warning', color: 'text-yellow-400' },
    COMPLETED: { label: '已完成', variant: 'success', color: 'text-emerald-400' },
    CANCELLED: { label: '已取消', variant: 'secondary', color: 'text-slate-400' },
  }
  return badges[status] || badges.SCHEDULED
}

export default function MeetingManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [meetings, setMeetings] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [keyword, setKeyword] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [projectFilter, setProjectFilter] = useState('')
  const [projectList, setProjectList] = useState([])

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [updateDialog, setUpdateDialog] = useState({ open: false, meetingId: null })
  const [minutesDialog, setMinutesDialog] = useState({ open: false, meetingId: null })
  const [detailDialog, setDetailDialog] = useState({ open: false, meeting: null })

  useEffect(() => {
    fetchData()
    fetchProjectList()
  }, [page, keyword, typeFilter, statusFilter, projectFilter])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page,
        page_size: pageSize,
      }
      if (keyword) {
        params.keyword = keyword
      }
      if (typeFilter) {
        params.meeting_type = typeFilter
      }
      if (statusFilter) {
        params.status = statusFilter
      }
      if (projectFilter) {
        params.project_id = parseInt(projectFilter)
      }
      const res = await pmoApi.meetings.list(params)
      const data = res.data || res
      // Handle PaginatedResponse format
      if (data && typeof data === 'object' && 'items' in data) {
        setMeetings(data.items || [])
        setTotal(data.total || 0)
      } else if (Array.isArray(data)) {
        setMeetings(data)
        setTotal(data.length)
      } else {
        setMeetings([])
        setTotal(0)
      }
    } catch (err) {
      console.error('Failed to fetch meetings:', err)
      setError(err.response?.data?.detail || err.message || '加载会议数据失败')
      setMeetings([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const fetchProjectList = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 100 })
      const data = res.data || res
      // Handle PaginatedResponse format
      if (data && typeof data === 'object' && 'items' in data) {
        setProjectList(data.items || [])
      } else if (Array.isArray(data)) {
        setProjectList(data)
      } else {
        setProjectList([])
      }
    } catch (err) {
      console.error('Failed to fetch projects:', err)
      setProjectList([])
    }
  }

  const handleCreate = async (formData) => {
    try {
      await pmoApi.meetings.create(formData)
      setCreateDialogOpen(false)
      fetchData()
    } catch (err) {
      console.error('Failed to create meeting:', err)
      alert('创建失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleUpdate = async (meetingId, formData) => {
    try {
      await pmoApi.meetings.update(meetingId, formData)
      setUpdateDialog({ open: false, meetingId: null })
      fetchData()
    } catch (err) {
      console.error('Failed to update meeting:', err)
      alert('更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleMinutes = async (meetingId, formData) => {
    try {
      await pmoApi.meetings.updateMinutes(meetingId, formData)
      setMinutesDialog({ open: false, meetingId: null })
      fetchData()
    } catch (err) {
      console.error('Failed to update minutes:', err)
      alert('更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="会议管理"
        description="项目会议安排与纪要管理"
        action={
          <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            新建会议
          </Button>
        }
      />

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Input
              placeholder="搜索会议名称..."
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              className="w-full"
              icon={Search}
            />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部类型</option>
              <option value="KICKOFF">项目启动会</option>
              <option value="WEEKLY">周例会</option>
              <option value="MILESTONE_REVIEW">里程碑评审</option>
              <option value="CHANGE_REVIEW">变更评审</option>
              <option value="RISK_REVIEW">风险评审</option>
              <option value="CLOSURE">结项评审会</option>
              <option value="OTHER">其他</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部状态</option>
              <option value="SCHEDULED">已安排</option>
              <option value="ONGOING">进行中</option>
              <option value="COMPLETED">已完成</option>
              <option value="CANCELLED">已取消</option>
            </select>
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value)}
              className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">全部项目</option>
              {projectList.map((proj) => (
                <option key={proj.id} value={proj.id}>
                  {proj.project_name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="mb-6 border-red-500/30 bg-red-500/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-red-400">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
              <Button
                size="sm"
                variant="outline"
                onClick={fetchData}
                className="border-red-500/30 text-red-400 hover:bg-red-500/20"
              >
                重试
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Meeting List */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4">
          {Array(5)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      ) : error ? null : meetings.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {meetings.map((meeting) => {
            const statusBadge = getStatusBadge(meeting.status)
            const isPast = new Date(meeting.meeting_date) < new Date()

            return (
              <motion.div key={meeting.id} variants={staggerChild}>
                <Card className="hover:bg-white/[0.02] transition-colors">
                  <CardContent className="p-5">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20">
                          <Calendar className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-white">
                              {meeting.meeting_name}
                            </h3>
                            <Badge variant={statusBadge.variant}>
                              {statusBadge.label}
                            </Badge>
                            <Badge variant="secondary">
                              {getMeetingTypeLabel(meeting.meeting_type)}
                            </Badge>
                          </div>
                          {meeting.project_id && (
                            <p className="text-xs text-slate-500 mt-1">
                              项目ID: {meeting.project_id}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Meeting Info */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 text-sm">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        <div>
                          <span className="text-slate-400">日期</span>
                          <p className="text-white">
                            {formatDate(meeting.meeting_date)}
                          </p>
                        </div>
                      </div>
                      {meeting.start_time && (
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-slate-400" />
                          <div>
                            <span className="text-slate-400">时间</span>
                            <p className="text-white">
                              {formatTime(meeting.start_time)}
                              {meeting.end_time && ` - ${formatTime(meeting.end_time)}`}
                            </p>
                          </div>
                        </div>
                      )}
                      {meeting.location && (
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-slate-400" />
                          <div>
                            <span className="text-slate-400">地点</span>
                            <p className="text-white">{meeting.location}</p>
                          </div>
                        </div>
                      )}
                      {meeting.organizer_name && (
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-slate-400" />
                          <div>
                            <span className="text-slate-400">组织者</span>
                            <p className="text-white">{meeting.organizer_name}</p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Agenda */}
                    {meeting.agenda && (
                      <div className="mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                        <span className="text-xs text-slate-400">会议议程</span>
                        <p className="text-sm text-white mt-1 line-clamp-2">
                          {meeting.agenda}
                        </p>
                      </div>
                    )}

                    {/* Action Items Count */}
                    {meeting.action_items && meeting.action_items.length > 0 && (
                      <div className="mb-4 flex items-center gap-2 text-sm text-slate-400">
                        <FileText className="h-4 w-4" />
                        <span>
                          待办事项: {meeting.action_items.length} 项
                        </span>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <div className="flex items-center gap-2 flex-wrap">
                        {meeting.status === 'SCHEDULED' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              setUpdateDialog({ open: true, meetingId: meeting.id })
                            }
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            编辑
                          </Button>
                        )}
                        {meeting.status !== 'COMPLETED' && meeting.status !== 'CANCELLED' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              setMinutesDialog({ open: true, meetingId: meeting.id })
                            }
                          >
                            <FileText className="h-4 w-4 mr-2" />
                            记录纪要
                          </Button>
                        )}
                        {meeting.project_id && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/projects/${meeting.project_id}`)}
                          >
                            <Briefcase className="h-4 w-4 mr-2" />
                            查看项目
                          </Button>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setDetailDialog({ open: true, meeting })}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      ) : !error ? (
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无会议数据
          </CardContent>
        </Card>
      ) : null}

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex items-center justify-center gap-2 mt-6">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            上一页
          </Button>
          <span className="text-sm text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(total / pageSize)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* Create Dialog */}
      <CreateMeetingDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate}
        projectList={projectList}
      />

      {/* Update Dialog */}
      <UpdateMeetingDialog
        open={updateDialog.open}
        onOpenChange={(open) => setUpdateDialog({ open, meetingId: null })}
        onSubmit={(data) => handleUpdate(updateDialog.meetingId, data)}
        meetingId={updateDialog.meetingId}
        projectList={projectList}
      />

      {/* Minutes Dialog */}
      <MeetingMinutesDialog
        open={minutesDialog.open}
        onOpenChange={(open) => setMinutesDialog({ open, meetingId: null })}
        onSubmit={(data) => handleMinutes(minutesDialog.meetingId, data)}
        meetingId={minutesDialog.meetingId}
      />

      {/* Detail Dialog */}
      <MeetingDetailDialog
        open={detailDialog.open}
        onOpenChange={(open) => setDetailDialog({ open, meeting: null })}
        meeting={detailDialog.meeting}
      />
    </motion.div>
  )
}

// Create Meeting Dialog
function CreateMeetingDialog({ open, onOpenChange, onSubmit, projectList }) {
  const [formData, setFormData] = useState({
    project_id: '',
    meeting_type: 'WEEKLY',
    meeting_name: '',
    meeting_date: '',
    start_time: '',
    end_time: '',
    location: '',
    organizer_id: '',
    attendees: [],
    agenda: '',
  })

  const handleSubmit = () => {
    if (!formData.meeting_name.trim() || !formData.meeting_date) {
      alert('请填写会议名称和日期')
      return
    }
    const submitData = {
      ...formData,
      project_id: formData.project_id ? parseInt(formData.project_id) : null,
      organizer_id: formData.organizer_id ? parseInt(formData.organizer_id) : null,
      start_time: formData.start_time || null,
      end_time: formData.end_time || null,
    }
    onSubmit(submitData)
    setFormData({
      project_id: '',
      meeting_type: 'WEEKLY',
      meeting_name: '',
      meeting_date: '',
      start_time: '',
      end_time: '',
      location: '',
      organizer_id: '',
      attendees: [],
      agenda: '',
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>新建会议</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  会议名称 <span className="text-red-400">*</span>
                </label>
                <Input
                  value={formData.meeting_name}
                  onChange={(e) =>
                    setFormData({ ...formData, meeting_name: e.target.value })
                  }
                  placeholder="请输入会议名称"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  会议类型 <span className="text-red-400">*</span>
                </label>
                <select
                  value={formData.meeting_type}
                  onChange={(e) =>
                    setFormData({ ...formData, meeting_type: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="KICKOFF">项目启动会</option>
                  <option value="WEEKLY">周例会</option>
                  <option value="MILESTONE_REVIEW">里程碑评审</option>
                  <option value="CHANGE_REVIEW">变更评审</option>
                  <option value="RISK_REVIEW">风险评审</option>
                  <option value="CLOSURE">结项评审会</option>
                  <option value="OTHER">其他</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  关联项目
                </label>
                <select
                  value={formData.project_id}
                  onChange={(e) =>
                    setFormData({ ...formData, project_id: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">不关联项目（跨项目会议）</option>
                  {projectList.map((proj) => (
                    <option key={proj.id} value={proj.id}>
                      {proj.project_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  会议日期 <span className="text-red-400">*</span>
                </label>
                <Input
                  type="date"
                  value={formData.meeting_date}
                  onChange={(e) =>
                    setFormData({ ...formData, meeting_date: e.target.value })
                  }
                />
              </div>
      </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  开始时间
                </label>
                <Input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) =>
                    setFormData({ ...formData, start_time: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  结束时间
                </label>
                <Input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) =>
                    setFormData({ ...formData, end_time: e.target.value })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议地点
              </label>
              <Input
                value={formData.location}
                onChange={(e) =>
                  setFormData({ ...formData, location: e.target.value })
                }
                placeholder="请输入会议地点"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议议程
              </label>
              <textarea
                value={formData.agenda}
                onChange={(e) =>
                  setFormData({ ...formData, agenda: e.target.value })
                }
                placeholder="请输入会议议程"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>创建</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Update Meeting Dialog
function UpdateMeetingDialog({
  open,
  onOpenChange,
  onSubmit,
  meetingId,
  projectList,
}) {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    meeting_name: '',
    meeting_date: '',
    start_time: '',
    end_time: '',
    location: '',
    organizer_id: '',
    agenda: '',
    status: 'SCHEDULED',
  })

  useEffect(() => {
    if (open && meetingId) {
      fetchMeeting()
    }
  }, [open, meetingId])

  const fetchMeeting = async () => {
    try {
      setLoading(true)
      const res = await pmoApi.meetings.get(meetingId)
      const data = res.data || res
      setFormData({
        meeting_name: data.meeting_name || '',
        meeting_date: data.meeting_date || '',
        start_time: data.start_time || '',
        end_time: data.end_time || '',
        location: data.location || '',
        organizer_id: data.organizer_id || '',
        agenda: data.agenda || '',
        status: data.status || 'SCHEDULED',
      })
    } catch (err) {
      console.error('Failed to fetch meeting:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = () => {
    if (!formData.meeting_name.trim() || !formData.meeting_date) {
      alert('请填写会议名称和日期')
      return
    }
    const submitData = {
      ...formData,
      organizer_id: formData.organizer_id ? parseInt(formData.organizer_id) : null,
      start_time: formData.start_time || null,
      end_time: formData.end_time || null,
    }
    onSubmit(submitData)
  }

  if (loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <div className="p-8 text-center text-slate-400">加载中...</div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>编辑会议</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议名称 <span className="text-red-400">*</span>
              </label>
              <Input
                value={formData.meeting_name}
                onChange={(e) =>
                  setFormData({ ...formData, meeting_name: e.target.value })
                }
                placeholder="请输入会议名称"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  会议日期 <span className="text-red-400">*</span>
                </label>
                <Input
                  type="date"
                  value={formData.meeting_date}
                  onChange={(e) =>
                    setFormData({ ...formData, meeting_date: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  状态
                </label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({ ...formData, status: e.target.value })
                  }
                  className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="SCHEDULED">已安排</option>
                  <option value="ONGOING">进行中</option>
                  <option value="COMPLETED">已完成</option>
                  <option value="CANCELLED">已取消</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  开始时间
                </label>
                <Input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) =>
                    setFormData({ ...formData, start_time: e.target.value })
                  }
                />
                      </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  结束时间
                </label>
                <Input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) =>
                    setFormData({ ...formData, end_time: e.target.value })
                  }
                />
                        </div>
                        </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议地点
              </label>
              <Input
                value={formData.location}
                onChange={(e) =>
                  setFormData({ ...formData, location: e.target.value })
                }
                placeholder="请输入会议地点"
              />
                        </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议议程
              </label>
              <textarea
                value={formData.agenda}
                onChange={(e) =>
                  setFormData({ ...formData, agenda: e.target.value })
                }
                placeholder="请输入会议议程"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
                        </div>
                      </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Meeting Minutes Dialog
function MeetingMinutesDialog({ open, onOpenChange, onSubmit, meetingId }) {
  const [formData, setFormData] = useState({
    minutes: '',
    decisions: '',
    action_items: [],
  })

  const [newActionItem, setNewActionItem] = useState({
    description: '',
    owner: '',
    due_date: '',
  })

  const handleAddActionItem = () => {
    if (!newActionItem.description.trim()) {
      alert('请填写待办事项描述')
      return
    }
    setFormData({
      ...formData,
      action_items: [
        ...formData.action_items,
        {
          ...newActionItem,
          id: Date.now(),
          status: 'PENDING',
        },
      ],
    })
    setNewActionItem({ description: '', owner: '', due_date: '' })
  }

  const handleRemoveActionItem = (index) => {
    setFormData({
      ...formData,
      action_items: formData.action_items.filter((_, i) => i !== index),
    })
  }

  const handleSubmit = () => {
    if (!formData.minutes.trim()) {
      alert('请填写会议纪要')
      return
    }
    onSubmit(formData)
    setFormData({ minutes: '', decisions: '', action_items: [] })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>记录会议纪要</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议纪要 <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.minutes}
                onChange={(e) =>
                  setFormData({ ...formData, minutes: e.target.value })
                }
                placeholder="请详细记录会议内容"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={6}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                会议决议
              </label>
              <textarea
                value={formData.decisions}
                onChange={(e) =>
                  setFormData({ ...formData, decisions: e.target.value })
                }
                placeholder="请记录会议决议"
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={4}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                待办事项
              </label>
              <div className="space-y-3">
                {formData.action_items.map((item, index) => (
                  <div
                    key={item.id || index}
                    className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <p className="text-white">{item.description}</p>
                      <div className="flex items-center gap-4 mt-1 text-xs text-slate-400">
                        {item.owner && <span>负责人: {item.owner}</span>}
                        {item.due_date && <span>截止: {item.due_date}</span>}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRemoveActionItem(index)}
                    >
                      <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                ))}

                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                  <Input
                    value={newActionItem.description}
                    onChange={(e) =>
                      setNewActionItem({
                        ...newActionItem,
                        description: e.target.value,
                      })
                    }
                    placeholder="待办事项描述"
                    className="mb-2"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      value={newActionItem.owner}
                      onChange={(e) =>
                        setNewActionItem({ ...newActionItem, owner: e.target.value })
                      }
                      placeholder="负责人"
                    />
                    <Input
                      type="date"
                      value={newActionItem.due_date}
                      onChange={(e) =>
                        setNewActionItem({ ...newActionItem, due_date: e.target.value })
                      }
                      placeholder="截止日期"
                    />
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAddActionItem}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    添加待办
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>提交</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Meeting Detail Dialog
function MeetingDetailDialog({ open, onOpenChange, meeting }) {
  if (!meeting) return null

  const statusBadge = getStatusBadge(meeting.status)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>会议详情 - {meeting.meeting_name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">会议类型</span>
                <p className="text-white font-medium">
                  {getMeetingTypeLabel(meeting.meeting_type)}
                </p>
              </div>
                    <div>
                <span className="text-sm text-slate-400">状态</span>
                <p className="mt-1">
                  <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
                </p>
                    </div>
              <div>
                <span className="text-sm text-slate-400">会议日期</span>
                <p className="text-white font-medium">
                  {formatDate(meeting.meeting_date)}
                </p>
                  </div>
              {meeting.start_time && (
                <div>
                  <span className="text-sm text-slate-400">时间</span>
                  <p className="text-white font-medium">
                    {formatTime(meeting.start_time)}
                    {meeting.end_time && ` - ${formatTime(meeting.end_time)}`}
                  </p>
                    </div>
                  )}
              {meeting.location && (
                <div>
                  <span className="text-sm text-slate-400">地点</span>
                  <p className="text-white font-medium">{meeting.location}</p>
          </div>
              )}
              {meeting.organizer_name && (
                <div>
                  <span className="text-sm text-slate-400">组织者</span>
                  <p className="text-white font-medium">{meeting.organizer_name}</p>
                </div>
              )}
            </div>

            {/* Agenda */}
            {meeting.agenda && (
              <div>
                <h4 className="text-sm font-medium text-white mb-2">会议议程</h4>
                <p className="text-white whitespace-pre-wrap">{meeting.agenda}</p>
              </div>
            )}

            {/* Minutes */}
            {meeting.minutes && (
              <div>
                <h4 className="text-sm font-medium text-white mb-2">会议纪要</h4>
                <p className="text-white whitespace-pre-wrap">{meeting.minutes}</p>
              </div>
            )}

            {/* Decisions */}
            {meeting.decisions && (
              <div>
                <h4 className="text-sm font-medium text-white mb-2">会议决议</h4>
                <p className="text-white whitespace-pre-wrap">{meeting.decisions}</p>
                        </div>
            )}

            {/* Action Items */}
            {meeting.action_items && meeting.action_items.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-white mb-2">待办事项</h4>
                <div className="space-y-2">
                  {meeting.action_items.map((item, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-xl bg-white/[0.02] border border-white/5"
                    >
                      <p className="text-white">{item.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                        {item.owner && <span>负责人: {item.owner}</span>}
                        {item.due_date && <span>截止: {item.due_date}</span>}
                        {item.status && (
                          <Badge
                            variant={
                              item.status === 'COMPLETED' ? 'success' : 'secondary'
                            }
                          >
                            {item.status === 'COMPLETED' ? '已完成' : '待办'}
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                  </div>
            )}

            {/* Attendees */}
            {meeting.attendees && meeting.attendees.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-white mb-2">参会人员</h4>
                <div className="flex flex-wrap gap-2">
                  {meeting.attendees.map((attendee, index) => (
                    <Badge key={index} variant="secondary">
                      {attendee.name || attendee}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
