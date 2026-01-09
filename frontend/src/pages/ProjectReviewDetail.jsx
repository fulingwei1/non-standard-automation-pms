/**
 * 项目复盘报告详情页面
 * 展示复盘报告的完整信息，包括经验教训和最佳实践
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { projectReviewApi, projectApi } from '../services/api'
import { formatDate, formatCurrency } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  SkeletonCard,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui'
import { Input, InputWithLabel, Textarea } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Checkbox } from '../components/ui/checkbox'
import {
  ArrowLeft,
  Edit,
  Trash2,
  CheckCircle2,
  Archive,
  Plus,
  FileText,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign,
  Target,
  AlertCircle,
  Lightbulb,
  BookOpen,
  Users,
  Calendar,
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

const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: '草稿', variant: 'secondary', color: 'text-slate-400' },
    PUBLISHED: { label: '已发布', variant: 'success', color: 'text-emerald-400' },
    ARCHIVED: { label: '已归档', variant: 'info', color: 'text-blue-400' },
  }
  return badges[status] || badges.DRAFT
}

const getReviewTypeLabel = (type) => {
  const types = {
    POST_MORTEM: '结项复盘',
    MID_TERM: '中期复盘',
    QUARTERLY: '季度复盘',
  }
  return types[type] || type
}

const getLessonTypeBadge = (type) => {
  const badges = {
    SUCCESS: { label: '成功经验', variant: 'success', icon: CheckCircle2 },
    FAILURE: { label: '失败教训', variant: 'destructive', icon: AlertCircle },
  }
  return badges[type] || badges.SUCCESS
}

export default function ProjectReviewDetail() {
  const { reviewId } = useParams()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [review, setReview] = useState(null)
  const [lessons, setLessons] = useState([])
  const [bestPractices, setBestPractices] = useState([])
  const [activeTab, setActiveTab] = useState('overview')

  // 对话框
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [lessonDialog, setLessonDialog] = useState({ open: false, lesson: null })
  const [practiceDialog, setPracticeDialog] = useState({ open: false, practice: null })
  const [selectedLessons, setSelectedLessons] = useState([])
  
  // 经验教训表单数据
  const [lessonForm, setLessonForm] = useState({
    lesson_type: 'SUCCESS',
    title: '',
    description: '',
    root_cause: '',
    impact: '',
    improvement_action: '',
    responsible_person: '',
    due_date: '',
    category: '',
    tags: '',
    priority: 'MEDIUM',
    status: 'OPEN',
  })
  
  // 最佳实践表单数据
  const [practiceForm, setPracticeForm] = useState({
    title: '',
    description: '',
    context: '',
    implementation: '',
    benefits: '',
    category: '',
    tags: '',
    is_reusable: true,
    applicable_project_types: '',
    applicable_stages: '',
    validation_status: 'PENDING',
  })
  
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (reviewId) {
      fetchReview()
      fetchLessons()
      fetchBestPractices()
    }
  }, [reviewId])

  const fetchReview = async () => {
    try {
      setLoading(true)
      const res = await projectReviewApi.get(reviewId)
      const data = res.data || res
      setReview(data)
    } catch (err) {
      if (err.response?.status === 404) {
        navigate('/projects/reviews')
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchLessons = async () => {
    try {
      const res = await projectReviewApi.getLessons(reviewId, { page: 1, page_size: 100 })
      const data = res.data || res
      setLessons(data.items || data || [])
    } catch (err) {
      setLessons([])
    }
  }

  const fetchBestPractices = async () => {
    try {
      const res = await projectReviewApi.getBestPractices(reviewId, { page: 1, page_size: 100 })
      const data = res.data || res
      setBestPractices(data.items || data || [])
    } catch (err) {
      setBestPractices([])
    }
  }

  const handleDelete = async () => {
    try {
      await projectReviewApi.delete(reviewId)
      navigate('/projects/reviews')
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handlePublish = async () => {
    try {
      await projectReviewApi.publish(reviewId)
      fetchReview()
    } catch (err) {
      alert('发布失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleArchive = async () => {
    try {
      await projectReviewApi.archive(reviewId)
      fetchReview()
    } catch (err) {
      alert('归档失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const [deleteLessonDialog, setDeleteLessonDialog] = useState({ open: false, lessonId: null, title: '' })
  const [deletePracticeDialog, setDeletePracticeDialog] = useState({ open: false, practiceId: null, title: '' })

  const handleDeleteLesson = async (lessonId) => {
    const lesson = lessons.find(l => l.id === lessonId)
    if (lesson) {
      setDeleteLessonDialog({ open: true, lessonId, title: lesson.title })
    }
  }

  const confirmDeleteLesson = async () => {
    try {
      await projectReviewApi.deleteLesson(deleteLessonDialog.lessonId)
      setDeleteLessonDialog({ open: false, lessonId: null, title: '' })
      fetchLessons()
      alert('经验教训已删除')
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeletePractice = async (practiceId) => {
    const practice = bestPractices.find(p => p.id === practiceId)
    if (practice) {
      setDeletePracticeDialog({ open: true, practiceId, title: practice.title })
    }
  }

  const confirmDeletePractice = async () => {
    try {
      await projectReviewApi.deleteBestPractice(deletePracticeDialog.practiceId)
      setDeletePracticeDialog({ open: false, practiceId: null, title: '' })
      fetchBestPractices()
      alert('最佳实践已删除')
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleUpdateLessonStatus = async (lessonId, newStatus) => {
    try {
      await projectReviewApi.updateLessonStatus(lessonId, newStatus)
      fetchLessons()
    } catch (err) {
      alert('更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleBatchUpdateLessons = async (updateData) => {
    if (selectedLessons.length === 0) {
      alert('请先选择要更新的经验教训')
      return
    }
    try {
      await projectReviewApi.batchUpdateLessons(selectedLessons, updateData)
      setSelectedLessons([])
      fetchLessons()
      alert('批量更新成功')
    } catch (err) {
      alert('批量更新失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  // 打开经验教训对话框
  const handleOpenLessonDialog = (lesson = null) => {
    if (lesson) {
      setLessonForm({
        lesson_type: lesson.lesson_type || 'SUCCESS',
        title: lesson.title || '',
        description: lesson.description || '',
        root_cause: lesson.root_cause || '',
        impact: lesson.impact || '',
        improvement_action: lesson.improvement_action || '',
        responsible_person: lesson.responsible_person || '',
        due_date: lesson.due_date ? lesson.due_date.split('T')[0] : '',
        category: lesson.category || '',
        tags: lesson.tags ? (Array.isArray(lesson.tags) ? lesson.tags.join(',') : lesson.tags) : '',
        priority: lesson.priority || 'MEDIUM',
        status: lesson.status || 'OPEN',
      })
    } else {
      setLessonForm({
        lesson_type: 'SUCCESS',
        title: '',
        description: '',
        root_cause: '',
        impact: '',
        improvement_action: '',
        responsible_person: '',
        due_date: '',
        category: '',
        tags: '',
        priority: 'MEDIUM',
        status: 'OPEN',
      })
    }
    setLessonDialog({ open: true, lesson })
  }

  // 保存经验教训
  const handleSaveLesson = async () => {
    if (!lessonForm.title || !lessonForm.description) {
      alert('请填写标题和描述')
      return
    }
    
    try {
      setSaving(true)
      const data = {
        review_id: parseInt(reviewId),
        project_id: review.project_id,
        lesson_type: lessonForm.lesson_type,
        title: lessonForm.title,
        description: lessonForm.description,
        root_cause: lessonForm.root_cause || null,
        impact: lessonForm.impact || null,
        improvement_action: lessonForm.improvement_action || null,
        responsible_person: lessonForm.responsible_person || null,
        due_date: lessonForm.due_date || null,
        category: lessonForm.category || null,
        tags: lessonForm.tags ? lessonForm.tags.split(',').map(t => t.trim()).filter(t => t) : null,
        priority: lessonForm.priority,
        status: lessonForm.status,
      }
      
      if (lessonDialog.lesson) {
        await projectReviewApi.updateLesson(lessonDialog.lesson.id, data)
        alert('经验教训已更新')
      } else {
        await projectReviewApi.createLesson(reviewId, data)
        alert('经验教训已创建')
      }
      
      setLessonDialog({ open: false, lesson: null })
      fetchLessons()
    } catch (err) {
      alert('保存失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  // 打开最佳实践对话框
  const handleOpenPracticeDialog = (practice = null) => {
    if (practice) {
      setPracticeForm({
        title: practice.title || '',
        description: practice.description || '',
        context: practice.context || '',
        implementation: practice.implementation || '',
        benefits: practice.benefits || '',
        category: practice.category || '',
        tags: practice.tags ? (Array.isArray(practice.tags) ? practice.tags.join(',') : practice.tags) : '',
        is_reusable: practice.is_reusable !== false,
        applicable_project_types: practice.applicable_project_types 
          ? (Array.isArray(practice.applicable_project_types) 
              ? practice.applicable_project_types.join(',') 
              : practice.applicable_project_types)
          : '',
        applicable_stages: practice.applicable_stages
          ? (Array.isArray(practice.applicable_stages)
              ? practice.applicable_stages.join(',')
              : practice.applicable_stages)
          : '',
        validation_status: practice.validation_status || 'PENDING',
      })
    } else {
      setPracticeForm({
        title: '',
        description: '',
        context: '',
        implementation: '',
        benefits: '',
        category: '',
        tags: '',
        is_reusable: true,
        applicable_project_types: '',
        applicable_stages: '',
        validation_status: 'PENDING',
      })
    }
    setPracticeDialog({ open: true, practice })
  }

  // 保存最佳实践
  const handleSavePractice = async () => {
    if (!practiceForm.title || !practiceForm.description) {
      alert('请填写标题和描述')
      return
    }
    
    try {
      setSaving(true)
      const data = {
        review_id: parseInt(reviewId),
        project_id: review.project_id,
        title: practiceForm.title,
        description: practiceForm.description,
        context: practiceForm.context || null,
        implementation: practiceForm.implementation || null,
        benefits: practiceForm.benefits || null,
        category: practiceForm.category || null,
        tags: practiceForm.tags ? practiceForm.tags.split(',').map(t => t.trim()).filter(t => t) : null,
        is_reusable: practiceForm.is_reusable,
        applicable_project_types: practiceForm.applicable_project_types
          ? practiceForm.applicable_project_types.split(',').map(t => t.trim()).filter(t => t)
          : null,
        applicable_stages: practiceForm.applicable_stages
          ? practiceForm.applicable_stages.split(',').map(t => t.trim()).filter(t => t)
          : null,
        validation_status: practiceForm.validation_status,
      }
      
      if (practiceDialog.practice) {
        await projectReviewApi.updateBestPractice(practiceDialog.practice.id, data)
        alert('最佳实践已更新')
      } else {
        await projectReviewApi.createBestPractice(reviewId, data)
        alert('最佳实践已创建')
      }
      
      setPracticeDialog({ open: false, practice: null })
      fetchBestPractices()
    } catch (err) {
      alert('保存失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    )
  }

  if (!review) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-slate-400">复盘报告不存在</p>
          <Button onClick={() => navigate('/projects/reviews')} className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回列表
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title={`项目复盘报告 - ${review.project_name || review.project_code}`}
        description={`复盘编号: ${review.review_no} | ${getReviewTypeLabel(review.review_type)}`}
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/projects/reviews')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回列表
            </Button>
            {review.status === 'DRAFT' && (
              <>
                <Button
                  variant="outline"
                  onClick={() => navigate(`/projects/reviews/${reviewId}/edit`)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  编辑
                </Button>
                <Button onClick={handlePublish}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  发布
                </Button>
                <Button variant="destructive" onClick={() => setDeleteDialog(true)}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  删除
                </Button>
              </>
            )}
            {review.status === 'PUBLISHED' && (
              <Button variant="outline" onClick={handleArchive}>
                <Archive className="h-4 w-4 mr-2" />
                归档
              </Button>
            )}
          </div>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="lessons">经验教训 ({lessons.length})</TabsTrigger>
          <TabsTrigger value="practices">最佳实践 ({bestPractices.length})</TabsTrigger>
        </TabsList>

        {/* 概览标签页 */}
        <TabsContent value="overview" className="space-y-6">
          {/* 状态卡片 */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-500/10 ring-1 ring-blue-500/20">
                    <FileText className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">复盘状态</h3>
                    <p className="text-sm text-slate-400">
                      {getStatusBadge(review.status).label}
                    </p>
                  </div>
                </div>
                <Badge variant={getStatusBadge(review.status).variant}>
                  {getStatusBadge(review.status).label}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* 项目周期对比 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">进度偏差</span>
                  {review.schedule_variance !== null && (
                    <div
                      className={cn(
                        'flex items-center gap-1',
                        review.schedule_variance >= 0
                          ? 'text-red-400'
                          : 'text-emerald-400'
                      )}
                    >
                      {review.schedule_variance >= 0 ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : (
                        <TrendingDown className="h-4 w-4" />
                      )}
                      <span className="text-sm font-medium">
                        {review.schedule_variance >= 0 ? '+' : ''}
                        {review.schedule_variance} 天
                      </span>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">计划工期</span>
                    <span className="text-white">{review.plan_duration || 0} 天</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">实际工期</span>
                    <span className="text-white">{review.actual_duration || 0} 天</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">成本偏差</span>
                  {review.cost_variance !== null && (
                    <div
                      className={cn(
                        'flex items-center gap-1',
                        review.cost_variance >= 0
                          ? 'text-red-400'
                          : 'text-emerald-400'
                      )}
                    >
                      {review.cost_variance >= 0 ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : (
                        <TrendingDown className="h-4 w-4" />
                      )}
                      <span className="text-sm font-medium">
                        {review.cost_variance >= 0 ? '+' : ''}
                        {formatCurrency(review.cost_variance)}
                      </span>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">预算金额</span>
                    <span className="text-white">
                      {review.budget_amount ? formatCurrency(review.budget_amount) : '未设置'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">实际成本</span>
                    <span className="text-white">
                      {review.actual_cost ? formatCurrency(review.actual_cost) : '未设置'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-400">质量指标</span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">质量问题数</span>
                    <span className="text-white">{review.quality_issues || 0} 个</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">变更次数</span>
                    <span className="text-white">{review.change_count || 0} 次</span>
                  </div>
                  {review.customer_satisfaction !== null && (
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">客户满意度</span>
                      <span className="text-white">{review.customer_satisfaction}/5</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 复盘内容 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {review.success_factors && (
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    <h3 className="text-lg font-semibold text-white">成功因素</h3>
                  </div>
                  <p className="text-white whitespace-pre-wrap">{review.success_factors}</p>
                </CardContent>
              </Card>
            )}

            {review.problems && (
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                    <h3 className="text-lg font-semibold text-white">问题与教训</h3>
                  </div>
                  <p className="text-white whitespace-pre-wrap">{review.problems}</p>
                </CardContent>
              </Card>
            )}

            {review.improvements && (
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Target className="h-5 w-5 text-blue-400" />
                    <h3 className="text-lg font-semibold text-white">改进建议</h3>
                  </div>
                  <p className="text-white whitespace-pre-wrap">{review.improvements}</p>
                </CardContent>
              </Card>
            )}

            {review.best_practices && (
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-yellow-400" />
                    <h3 className="text-lg font-semibold text-white">最佳实践</h3>
                  </div>
                  <p className="text-white whitespace-pre-wrap">{review.best_practices}</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* 复盘结论 */}
          {review.conclusion && (
            <Card>
              <CardContent className="p-5">
                <h3 className="text-lg font-semibold text-white mb-4">复盘结论</h3>
                <p className="text-white whitespace-pre-wrap">{review.conclusion}</p>
              </CardContent>
            </Card>
          )}

          {/* 参与人信息 */}
          <Card>
            <CardContent className="p-5">
              <h3 className="text-lg font-semibold text-white mb-4">参与人</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-slate-500" />
                  <span className="text-sm text-slate-400">复盘负责人:</span>
                  <span className="text-white">{review.reviewer_name}</span>
                </div>
                {review.participant_names && (
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-slate-500" />
                    <span className="text-sm text-slate-400">参与人:</span>
                    <span className="text-white">{review.participant_names}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-slate-500" />
                  <span className="text-sm text-slate-400">复盘日期:</span>
                  <span className="text-white">{formatDate(review.review_date)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 经验教训标签页 */}
        <TabsContent value="lessons" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">经验教训</h3>
            {review.status === 'DRAFT' && (
              <Button
                size="sm"
                onClick={() => handleOpenLessonDialog(null)}
              >
                <Plus className="h-4 w-4 mr-2" />
                添加经验教训
              </Button>
            )}
          </div>

          {lessons.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <BookOpen className="h-12 w-12 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-400">暂无经验教训</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {lessons.map((lesson) => {
                const badge = getLessonTypeBadge(lesson.lesson_type)
                const Icon = badge.icon
                return (
                  <motion.div key={lesson.id} variants={staggerChild}>
                    <Card className={cn(selectedLessons.includes(lesson.id) && 'ring-2 ring-primary')}>
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            {review.status === 'DRAFT' && (
                              <input
                                type="checkbox"
                                checked={selectedLessons.includes(lesson.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSelectedLessons([...selectedLessons, lesson.id])
                                  } else {
                                    setSelectedLessons(selectedLessons.filter(id => id !== lesson.id))
                                  }
                                }}
                                className="h-4 w-4 rounded border-border"
                              />
                            )}
                            <div
                              className={cn(
                                'p-2 rounded-lg',
                                lesson.lesson_type === 'SUCCESS'
                                  ? 'bg-emerald-500/20'
                                  : 'bg-red-500/20'
                              )}
                            >
                              <Icon
                                className={cn(
                                  'h-5 w-5',
                                  lesson.lesson_type === 'SUCCESS'
                                    ? 'text-emerald-400'
                                    : 'text-red-400'
                                )}
                              />
                            </div>
                            <div>
                              <h4 className="font-semibold text-white">{lesson.title}</h4>
                              <Badge variant={badge.variant} className="mt-1">
                                {badge.label}
                              </Badge>
                            </div>
                          </div>
                          {review.status === 'DRAFT' && (
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleOpenLessonDialog(lesson)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDeleteLesson(lesson.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          )}
                        </div>
                        <p className="text-white mb-3">{lesson.description}</p>
                        {lesson.root_cause && (
                          <div className="mb-2">
                            <span className="text-sm text-slate-400">根本原因: </span>
                            <span className="text-white text-sm">{lesson.root_cause}</span>
                          </div>
                        )}
                        {lesson.impact && (
                          <div className="mb-2">
                            <span className="text-sm text-slate-400">影响范围: </span>
                            <span className="text-white text-sm">{lesson.impact}</span>
                          </div>
                        )}
                        {lesson.improvement_action && (
                          <div className="mb-2">
                            <span className="text-sm text-slate-400">改进措施: </span>
                            <span className="text-white text-sm">{lesson.improvement_action}</span>
                          </div>
                        )}
                        {(lesson.responsible_person || lesson.due_date) && (
                          <div className="mb-2 flex items-center gap-4 text-sm">
                            {lesson.responsible_person && (
                              <span className="text-slate-400">
                                责任人: <span className="text-white">{lesson.responsible_person}</span>
                              </span>
                            )}
                            {lesson.due_date && (
                              <span className="text-slate-400">
                                完成日期: <span className="text-white">{formatDate(lesson.due_date)}</span>
                              </span>
                            )}
                          </div>
                        )}
                        <div className="mt-3 flex items-center gap-2 flex-wrap">
                          {lesson.status && (
                            <Badge variant="outline">
                              {lesson.status === 'OPEN' ? '待处理' :
                               lesson.status === 'IN_PROGRESS' ? '进行中' :
                               lesson.status === 'RESOLVED' ? '已解决' :
                               lesson.status === 'CLOSED' ? '已关闭' : lesson.status}
                            </Badge>
                          )}
                          {lesson.priority && (
                            <Badge variant="outline">
                              {lesson.priority === 'LOW' ? '低优先级' :
                               lesson.priority === 'MEDIUM' ? '中优先级' :
                               lesson.priority === 'HIGH' ? '高优先级' : lesson.priority}
                            </Badge>
                          )}
                          {lesson.category && (
                            <Badge variant="outline">{lesson.category}</Badge>
                          )}
                          {lesson.tags && Array.isArray(lesson.tags) && lesson.tags.length > 0 && (
                            lesson.tags.map((tag, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))
                          )}
                          {lesson.status !== 'RESOLVED' && lesson.status !== 'CLOSED' && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleUpdateLessonStatus(lesson.id, 'RESOLVED')}
                            >
                              <CheckCircle2 className="h-4 w-4 mr-2" />
                              标记已解决
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          )}
        </TabsContent>

        {/* 最佳实践标签页 */}
        <TabsContent value="practices" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">最佳实践</h3>
            {review.status === 'DRAFT' && (
              <Button
                size="sm"
                onClick={() => handleOpenPracticeDialog(null)}
              >
                <Plus className="h-4 w-4 mr-2" />
                添加最佳实践
              </Button>
            )}
          </div>

          {bestPractices.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Lightbulb className="h-12 w-12 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-400">暂无最佳实践</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {bestPractices.map((practice) => (
                <motion.div key={practice.id} variants={staggerChild}>
                  <Card>
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <Lightbulb className="h-5 w-5 text-yellow-400" />
                            <h4 className="font-semibold text-white">{practice.title}</h4>
                            {practice.is_reusable && (
                              <Badge variant="success">可复用</Badge>
                            )}
                            {practice.validation_status === 'VALIDATED' && (
                              <Badge variant="success">已验证</Badge>
                            )}
                          </div>
                          <p className="text-white mb-2">{practice.description}</p>
                          {practice.context && (
                            <div className="mb-2">
                              <span className="text-sm text-slate-400">适用场景: </span>
                              <span className="text-white text-sm">{practice.context}</span>
                            </div>
                          )}
                          {practice.implementation && (
                            <div className="mb-2">
                              <span className="text-sm text-slate-400">实施方法: </span>
                              <span className="text-white text-sm">{practice.implementation}</span>
                            </div>
                          )}
                          {practice.benefits && (
                            <div className="mb-2">
                              <span className="text-sm text-slate-400">带来的收益: </span>
                              <span className="text-white text-sm">{practice.benefits}</span>
                            </div>
                          )}
                          <div className="mt-3 flex items-center gap-2 flex-wrap">
                            {practice.category && (
                              <Badge variant="outline">{practice.category}</Badge>
                            )}
                            {practice.validation_status && (
                              <Badge variant={practice.validation_status === 'VALIDATED' ? 'success' : 'outline'}>
                                {practice.validation_status === 'PENDING' ? '待验证' :
                                 practice.validation_status === 'VALIDATED' ? '已验证' :
                                 practice.validation_status === 'REJECTED' ? '已拒绝' : practice.validation_status}
                              </Badge>
                            )}
                            {practice.tags && Array.isArray(practice.tags) && practice.tags.length > 0 && (
                              practice.tags.map((tag, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))
                            )}
                            {practice.applicable_project_types && Array.isArray(practice.applicable_project_types) && practice.applicable_project_types.length > 0 && (
                              <Badge variant="outline" className="text-xs">
                                适用: {practice.applicable_project_types.join(', ')}
                              </Badge>
                            )}
                            {practice.applicable_stages && Array.isArray(practice.applicable_stages) && practice.applicable_stages.length > 0 && (
                              <Badge variant="outline" className="text-xs">
                                阶段: {practice.applicable_stages.join(', ')}
                              </Badge>
                            )}
                            {practice.reuse_count > 0 && (
                              <Badge variant="outline" className="text-xs">
                                复用 {practice.reuse_count} 次
                              </Badge>
                            )}
                          </div>
                        </div>
                        {review.status === 'DRAFT' && (
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleOpenPracticeDialog(practice)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeletePractice(practice.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">
              确定要删除复盘报告 "{review.review_no}" 吗？此操作不可恢复。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialog(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 经验教训对话框 */}
      <Dialog
        open={lessonDialog.open}
        onClose={() => setLessonDialog({ open: false, lesson: null })}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {lessonDialog.lesson ? '编辑经验教训' : '添加经验教训'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>类型 <span className="text-red-400">*</span></Label>
                <select
                  value={lessonForm.lesson_type}
                  onChange={(e) => setLessonForm({ ...lessonForm, lesson_type: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="SUCCESS">成功经验</option>
                  <option value="FAILURE">失败教训</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label>优先级</Label>
                <select
                  value={lessonForm.priority}
                  onChange={(e) => setLessonForm({ ...lessonForm, priority: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="LOW">低</option>
                  <option value="MEDIUM">中</option>
                  <option value="HIGH">高</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>标题 <span className="text-red-400">*</span></Label>
              <Input
                value={lessonForm.title}
                onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })}
                placeholder="请输入经验教训标题"
              />
            </div>

            <div className="space-y-2">
              <Label>描述 <span className="text-red-400">*</span></Label>
              <Textarea
                value={lessonForm.description}
                onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })}
                placeholder="请详细描述经验教训的内容"
                rows={4}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>根本原因</Label>
                <Textarea
                  value={lessonForm.root_cause}
                  onChange={(e) => setLessonForm({ ...lessonForm, root_cause: e.target.value })}
                  placeholder="分析问题的根本原因"
                  rows={3}
                />
              </div>
              
              <div className="space-y-2">
                <Label>影响范围</Label>
                <Textarea
                  value={lessonForm.impact}
                  onChange={(e) => setLessonForm({ ...lessonForm, impact: e.target.value })}
                  placeholder="描述影响的范围和程度"
                  rows={3}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>改进措施</Label>
              <Textarea
                value={lessonForm.improvement_action}
                onChange={(e) => setLessonForm({ ...lessonForm, improvement_action: e.target.value })}
                placeholder="提出具体的改进措施"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>责任人</Label>
                <Input
                  value={lessonForm.responsible_person}
                  onChange={(e) => setLessonForm({ ...lessonForm, responsible_person: e.target.value })}
                  placeholder="责任人姓名"
                />
              </div>
              
              <div className="space-y-2">
                <Label>完成日期</Label>
                <Input
                  type="date"
                  value={lessonForm.due_date}
                  onChange={(e) => setLessonForm({ ...lessonForm, due_date: e.target.value })}
                />
              </div>
              
              <div className="space-y-2">
                <Label>状态</Label>
                <select
                  value={lessonForm.status}
                  onChange={(e) => setLessonForm({ ...lessonForm, status: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="OPEN">待处理</option>
                  <option value="IN_PROGRESS">进行中</option>
                  <option value="RESOLVED">已解决</option>
                  <option value="CLOSED">已关闭</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>分类</Label>
                <select
                  value={lessonForm.category}
                  onChange={(e) => setLessonForm({ ...lessonForm, category: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">请选择分类</option>
                  <option value="进度">进度</option>
                  <option value="成本">成本</option>
                  <option value="质量">质量</option>
                  <option value="沟通">沟通</option>
                  <option value="技术">技术</option>
                  <option value="管理">管理</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label>标签（用逗号分隔）</Label>
                <Input
                  value={lessonForm.tags}
                  onChange={(e) => setLessonForm({ ...lessonForm, tags: e.target.value })}
                  placeholder="例如：技术难点,沟通问题"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setLessonDialog({ open: false, lesson: null })}
              disabled={saving}
            >
              取消
            </Button>
            <Button onClick={handleSaveLesson} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 最佳实践对话框 */}
      <Dialog
        open={practiceDialog.open}
        onClose={() => setPracticeDialog({ open: false, practice: null })}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {practiceDialog.practice ? '编辑最佳实践' : '添加最佳实践'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="space-y-2">
              <Label>标题 <span className="text-red-400">*</span></Label>
              <Input
                value={practiceForm.title}
                onChange={(e) => setPracticeForm({ ...practiceForm, title: e.target.value })}
                placeholder="请输入最佳实践标题"
              />
            </div>

            <div className="space-y-2">
              <Label>实践描述 <span className="text-red-400">*</span></Label>
              <Textarea
                value={practiceForm.description}
                onChange={(e) => setPracticeForm({ ...practiceForm, description: e.target.value })}
                placeholder="请详细描述最佳实践的内容"
                rows={4}
              />
            </div>

            <div className="space-y-2">
              <Label>适用场景</Label>
              <Textarea
                value={practiceForm.context}
                onChange={(e) => setPracticeForm({ ...practiceForm, context: e.target.value })}
                placeholder="描述该实践适用的场景和条件"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>实施方法</Label>
              <Textarea
                value={practiceForm.implementation}
                onChange={(e) => setPracticeForm({ ...practiceForm, implementation: e.target.value })}
                placeholder="描述具体的实施步骤和方法"
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>带来的收益</Label>
              <Textarea
                value={practiceForm.benefits}
                onChange={(e) => setPracticeForm({ ...practiceForm, benefits: e.target.value })}
                placeholder="说明该实践带来的收益和价值"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>分类</Label>
                <select
                  value={practiceForm.category}
                  onChange={(e) => setPracticeForm({ ...practiceForm, category: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="">请选择分类</option>
                  <option value="流程">流程</option>
                  <option value="工具">工具</option>
                  <option value="技术">技术</option>
                  <option value="管理">管理</option>
                  <option value="沟通">沟通</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label>验证状态</Label>
                <select
                  value={practiceForm.validation_status}
                  onChange={(e) => setPracticeForm({ ...practiceForm, validation_status: e.target.value })}
                  className="flex h-10 w-full rounded-xl bg-white/[0.03] border border-white/10 px-4 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  <option value="PENDING">待验证</option>
                  <option value="VALIDATED">已验证</option>
                  <option value="REJECTED">已拒绝</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>适用项目类型（用逗号分隔）</Label>
                <Input
                  value={practiceForm.applicable_project_types}
                  onChange={(e) => setPracticeForm({ ...practiceForm, applicable_project_types: e.target.value })}
                  placeholder="例如：ICT测试,视觉检测"
                />
              </div>
              
              <div className="space-y-2">
                <Label>适用阶段（用逗号分隔，如：S1,S2,S3）</Label>
                <Input
                  value={practiceForm.applicable_stages}
                  onChange={(e) => setPracticeForm({ ...practiceForm, applicable_stages: e.target.value })}
                  placeholder="例如：S1,S2,S3"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>标签（用逗号分隔）</Label>
                <Input
                  value={practiceForm.tags}
                  onChange={(e) => setPracticeForm({ ...practiceForm, tags: e.target.value })}
                  placeholder="例如：效率提升,质量保证"
                />
              </div>
              
              <div className="flex items-center space-x-2 pt-8">
                <Checkbox
                  id="is_reusable"
                  checked={practiceForm.is_reusable}
                  onCheckedChange={(checked) => setPracticeForm({ ...practiceForm, is_reusable: checked })}
                />
                <Label htmlFor="is_reusable" className="cursor-pointer">
                  可复用
                </Label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPracticeDialog({ open: false, practice: null })}
              disabled={saving}
            >
              取消
            </Button>
            <Button onClick={handleSavePractice} disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除经验教训确认对话框 */}
      <Dialog
        open={deleteLessonDialog.open}
        onClose={() => setDeleteLessonDialog({ open: false, lessonId: null, title: '' })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除经验教训</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">
              确定要删除经验教训 "{deleteLessonDialog.title}" 吗？此操作不可恢复。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteLessonDialog({ open: false, lessonId: null, title: '' })}
            >
              取消
            </Button>
            <Button variant="destructive" onClick={confirmDeleteLesson}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除最佳实践确认对话框 */}
      <Dialog
        open={deletePracticeDialog.open}
        onClose={() => setDeletePracticeDialog({ open: false, practiceId: null, title: '' })}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除最佳实践</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">
              确定要删除最佳实践 "{deletePracticeDialog.title}" 吗？此操作不可恢复。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeletePracticeDialog({ open: false, practiceId: null, title: '' })}
            >
              取消
            </Button>
            <Button variant="destructive" onClick={confirmDeletePractice}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

