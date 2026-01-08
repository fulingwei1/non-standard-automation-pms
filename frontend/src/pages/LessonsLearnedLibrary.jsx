/**
 * 经验教训库页面
 * 跨项目搜索和管理经验教训
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { projectReviewApi } from '../services/api'
import { formatDate } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Button,
  Badge,
  Input,
  SkeletonCard,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui'
import {
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  RefreshCw,
  Eye,
  Edit,
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

const getLessonTypeBadge = (type) => {
  const badges = {
    SUCCESS: { label: '成功经验', variant: 'success', icon: CheckCircle2, color: 'text-emerald-400' },
    FAILURE: { label: '失败教训', variant: 'destructive', icon: AlertCircle, color: 'text-red-400' },
  }
  return badges[type] || badges.SUCCESS
}

const getStatusBadge = (status) => {
  const badges = {
    OPEN: { label: '待处理', variant: 'secondary', color: 'text-slate-400' },
    IN_PROGRESS: { label: '处理中', variant: 'info', color: 'text-blue-400' },
    RESOLVED: { label: '已解决', variant: 'success', color: 'text-emerald-400' },
    CLOSED: { label: '已关闭', variant: 'secondary', color: 'text-slate-500' },
  }
  return badges[status] || badges.OPEN
}

const getPriorityBadge = (priority) => {
  const badges = {
    LOW: { label: '低', variant: 'secondary', color: 'text-slate-400' },
    MEDIUM: { label: '中', variant: 'info', color: 'text-blue-400' },
    HIGH: { label: '高', variant: 'destructive', color: 'text-red-400' },
  }
  return badges[priority] || badges.MEDIUM
}

export default function LessonsLearnedLibrary() {
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [lessons, setLessons] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)

  // 筛选条件
  const [keyword, setKeyword] = useState('')
  const [lessonType, setLessonType] = useState(null)
  const [category, setCategory] = useState(null)
  const [status, setStatus] = useState(null)
  const [priority, setPriority] = useState(null)
  const [projectId, setProjectId] = useState(null)

  // 统计信息
  const [statistics, setStatistics] = useState(null)
  const [categories, setCategories] = useState([])
  const [activeTab, setActiveTab] = useState('list')

  useEffect(() => {
    fetchLessons()
    fetchStatistics()
    fetchCategories()
  }, [page, keyword, lessonType, category, status, priority, projectId])

  const fetchLessons = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
      }
      if (keyword) params.keyword = keyword
      if (lessonType) params.lesson_type = lessonType
      if (category) params.category = category
      if (status) params.status = status
      if (priority) params.priority = priority
      if (projectId) params.project_id = projectId

      const res = await projectReviewApi.searchLessonsLearned(params)
      const data = res.data || res
      setLessons(data.items || data || [])
      setTotal(data.total || data.length || 0)
    } catch (err) {
      console.error('Failed to fetch lessons:', err)
      setLessons([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const params = projectId ? { project_id: projectId } : {}
      const res = await projectReviewApi.getLessonsStatistics(params)
      const data = res.data || res
      setStatistics(data)
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
    }
  }

  const fetchCategories = async () => {
    try {
      const res = await projectReviewApi.getLessonCategories()
      const data = res.data || res
      setCategories(data.categories || [])
    } catch (err) {
      console.error('Failed to fetch categories:', err)
    }
  }

  const handleViewReview = (reviewId) => {
    navigate(`/projects/reviews/${reviewId}`)
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="经验教训库"
        description="跨项目搜索和管理经验教训，沉淀项目知识"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="list">经验教训列表</TabsTrigger>
          <TabsTrigger value="statistics">统计分析</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-6">
          {/* 筛选栏 */}
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                <Input
                  placeholder="搜索标题或描述..."
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  icon={Search}
                  className="md:col-span-2"
                />
                <select
                  value={lessonType || ''}
                  onChange={(e) => setLessonType(e.target.value || null)}
                  className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">全部类型</option>
                  <option value="SUCCESS">成功经验</option>
                  <option value="FAILURE">失败教训</option>
                </select>
                <select
                  value={category || ''}
                  onChange={(e) => setCategory(e.target.value || null)}
                  className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">全部分类</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
                <select
                  value={status || ''}
                  onChange={(e) => setStatus(e.target.value || null)}
                  className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">全部状态</option>
                  <option value="OPEN">待处理</option>
                  <option value="IN_PROGRESS">处理中</option>
                  <option value="RESOLVED">已解决</option>
                  <option value="CLOSED">已关闭</option>
                </select>
                <select
                  value={priority || ''}
                  onChange={(e) => setPriority(e.target.value || null)}
                  className="h-10 w-full rounded-md border border-border bg-surface-1 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">全部优先级</option>
                  <option value="LOW">低</option>
                  <option value="MEDIUM">中</option>
                  <option value="HIGH">高</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* 结果列表 */}
          {loading ? (
            <div className="space-y-4">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : lessons.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <p className="text-slate-400">暂无经验教训</p>
              </CardContent>
            </Card>
          ) : (
            <motion.div variants={staggerContainer} className="space-y-4">
              {lessons.map((lesson) => {
                const typeBadge = getLessonTypeBadge(lesson.lesson_type)
                const statusBadge = getStatusBadge(lesson.status)
                const priorityBadge = getPriorityBadge(lesson.priority)
                const TypeIcon = typeBadge.icon

                return (
                  <motion.div key={lesson.id} variants={staggerChild}>
                    <Card className="hover:border-primary/50 transition-colors">
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center gap-3">
                              <TypeIcon className={cn('h-5 w-5', typeBadge.color)} />
                              <h3 className="text-lg font-semibold text-white">{lesson.title}</h3>
                              <Badge variant={typeBadge.variant}>{typeBadge.label}</Badge>
                              <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
                              <Badge variant={priorityBadge.variant}>{priorityBadge.label}</Badge>
                            </div>
                            <p className="text-slate-300 line-clamp-2">{lesson.description}</p>
                            <div className="flex items-center gap-4 text-sm text-slate-400">
                              {lesson.project_code && (
                                <span>项目: {lesson.project_code} {lesson.project_name}</span>
                              )}
                              {lesson.category && <span>分类: {lesson.category}</span>}
                              {lesson.responsible_person && (
                                <span>责任人: {lesson.responsible_person}</span>
                              )}
                              {lesson.due_date && (
                                <span>截止: {formatDate(lesson.due_date)}</span>
                              )}
                              {lesson.resolved_date && (
                                <span className="text-emerald-400">
                                  已解决: {formatDate(lesson.resolved_date)}
                                </span>
                              )}
                            </div>
                            {lesson.root_cause && (
                              <div className="mt-3 p-3 bg-surface-2 rounded-md">
                                <p className="text-sm text-slate-300">
                                  <span className="font-medium">根本原因:</span> {lesson.root_cause}
                                </p>
                              </div>
                            )}
                            {lesson.improvement_action && (
                              <div className="mt-2 p-3 bg-surface-2 rounded-md">
                                <p className="text-sm text-slate-300">
                                  <span className="font-medium">改进措施:</span> {lesson.improvement_action}
                                </p>
                              </div>
                            )}
                          </div>
                          <div className="ml-4 flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewReview(lesson.review_id)}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              查看复盘
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </motion.div>
          )}

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-400">
                共 {total} 条记录，第 {page} 页
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page * pageSize >= total}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="statistics" className="space-y-6">
          {statistics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">总数</p>
                      <p className="text-2xl font-bold text-white mt-1">{statistics.total || 0}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">成功经验</p>
                      <p className="text-2xl font-bold text-emerald-400 mt-1">
                        {statistics.success_count || 0}
                      </p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-emerald-400" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">失败教训</p>
                      <p className="text-2xl font-bold text-red-400 mt-1">
                        {statistics.failure_count || 0}
                      </p>
                    </div>
                    <TrendingDown className="h-8 w-8 text-red-400" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">已解决</p>
                      <p className="text-2xl font-bold text-emerald-400 mt-1">
                        {statistics.resolved_count || 0}
                      </p>
                    </div>
                    <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <SkeletonCard />
          )}

          {statistics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 按分类统计 */}
              {statistics.by_category && Object.keys(statistics.by_category).length > 0 && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">按分类统计</h3>
                    <div className="space-y-2">
                      {Object.entries(statistics.by_category).map(([cat, count]) => (
                        <div key={cat} className="flex items-center justify-between">
                          <span className="text-slate-300">{cat}</span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 按状态统计 */}
              {statistics.by_status && Object.keys(statistics.by_status).length > 0 && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">按状态统计</h3>
                    <div className="space-y-2">
                      {Object.entries(statistics.by_status).map(([status, count]) => (
                        <div key={status} className="flex items-center justify-between">
                          <span className="text-slate-300">{status}</span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 按优先级统计 */}
              {statistics.by_priority && Object.keys(statistics.by_priority).length > 0 && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">按优先级统计</h3>
                    <div className="space-y-2">
                      {Object.entries(statistics.by_priority).map(([priority, count]) => (
                        <div key={priority} className="flex items-center justify-between">
                          <span className="text-slate-300">{priority}</span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}




