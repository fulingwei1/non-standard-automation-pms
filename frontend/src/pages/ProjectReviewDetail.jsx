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
      console.error('Failed to fetch review:', err)
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
      console.error('Failed to fetch lessons:', err)
      setLessons([])
    }
  }

  const fetchBestPractices = async () => {
    try {
      const res = await projectReviewApi.getBestPractices(reviewId, { page: 1, page_size: 100 })
      const data = res.data || res
      setBestPractices(data.items || data || [])
    } catch (err) {
      console.error('Failed to fetch best practices:', err)
      setBestPractices([])
    }
  }

  const handleDelete = async () => {
    try {
      await projectReviewApi.delete(reviewId)
      navigate('/projects/reviews')
    } catch (err) {
      console.error('Failed to delete review:', err)
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handlePublish = async () => {
    try {
      await projectReviewApi.publish(reviewId)
      fetchReview()
    } catch (err) {
      console.error('Failed to publish review:', err)
      alert('发布失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleArchive = async () => {
    try {
      await projectReviewApi.archive(reviewId)
      fetchReview()
    } catch (err) {
      console.error('Failed to archive review:', err)
      alert('归档失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeleteLesson = async (lessonId) => {
    try {
      await projectReviewApi.deleteLesson(lessonId)
      fetchLessons()
    } catch (err) {
      console.error('Failed to delete lesson:', err)
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeletePractice = async (practiceId) => {
    try {
      await projectReviewApi.deleteBestPractice(practiceId)
      fetchBestPractices()
    } catch (err) {
      console.error('Failed to delete practice:', err)
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
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
                onClick={() => setLessonDialog({ open: true, lesson: null })}
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
                    <Card>
                      <CardContent className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
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
                                onClick={() => setLessonDialog({ open: true, lesson })}
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
                        {lesson.improvement_measures && (
                          <div>
                            <span className="text-sm text-slate-400">改进措施: </span>
                            <span className="text-white text-sm">{lesson.improvement_measures}</span>
                          </div>
                        )}
                        {lesson.status && (
                          <div className="mt-3">
                            <Badge variant="outline">{lesson.status}</Badge>
                          </div>
                        )}
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
                onClick={() => setPracticeDialog({ open: true, practice: null })}
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
                          {practice.benefits && (
                            <div>
                              <span className="text-sm text-slate-400">带来的收益: </span>
                              <span className="text-white text-sm">{practice.benefits}</span>
                            </div>
                          )}
                          {practice.reuse_count > 0 && (
                            <div className="mt-2">
                              <span className="text-sm text-slate-400">复用次数: </span>
                              <span className="text-white text-sm">{practice.reuse_count} 次</span>
                            </div>
                          )}
                        </div>
                        {review.status === 'DRAFT' && (
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setPracticeDialog({ open: true, practice })}
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

      {/* 经验教训对话框（简化版，后续可完善） */}
      <Dialog
        open={lessonDialog.open}
        onClose={() => setLessonDialog({ open: false, lesson: null })}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {lessonDialog.lesson ? '编辑经验教训' : '添加经验教训'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-400">经验教训表单（待实现）</p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setLessonDialog({ open: false, lesson: null })}
            >
              取消
            </Button>
            <Button>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 最佳实践对话框（简化版，后续可完善） */}
      <Dialog
        open={practiceDialog.open}
        onClose={() => setPracticeDialog({ open: false, practice: null })}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {practiceDialog.practice ? '编辑最佳实践' : '添加最佳实践'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-400">最佳实践表单（待实现）</p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setPracticeDialog({ open: false, practice: null })}
            >
              取消
            </Button>
            <Button>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

