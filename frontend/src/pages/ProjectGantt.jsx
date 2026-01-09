/**
 * Project Gantt Chart Page - 项目甘特图页面
 * Features: 项目进度可视化，支持任务依赖关系展示
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Calendar,
  Clock,
  Users,
  CheckCircle2,
  Circle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn, formatDate } from '../lib/utils'
import { progressApi, projectApi } from '../services/api'
export default function ProjectGantt() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [ganttData, setGanttData] = useState([])
  useEffect(() => {
    if (id) {
      fetchProject()
      fetchGanttData()
    }
  }, [id])
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id)
      setProject(res.data || res)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  const fetchGanttData = async () => {
    try {
      setLoading(true)
      const res = await progressApi.reports.getGantt(id)
      const data = res.data || res || []
      setGanttData(data)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }
  const calculateProgress = (task) => {
    if (task.status === 'COMPLETED') return 100
    return task.progress || 0
  }
  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-500'
      case 'IN_PROGRESS':
        return 'bg-blue-500'
      case 'BLOCKED':
        return 'bg-red-500'
      case 'PENDING':
        return 'bg-slate-300'
      default:
        return 'bg-slate-300'
    }
  }
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    )
  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${id}`)}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            返回项目
          </Button>
          <PageHeader
            title={`${project?.project_name || '项目'} - 甘特图`}
            description="项目进度可视化，展示任务时间线和依赖关系"
          />
        </div>
        <Button variant="outline" onClick={fetchGanttData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>任务时间线</CardTitle>
        </CardHeader>
        <CardContent>
          {ganttData.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无任务数据</div>
          ) : (
            <div className="space-y-4">
              {ganttData.map((task) => {
                const progress = calculateProgress(task)
                const startDate = new Date(task.start_date || task.planned_start_date)
                const endDate = new Date(task.end_date || task.planned_end_date)
                const today = new Date()
                const isOverdue = endDate < today && task.status !== 'COMPLETED'
                return (
                  <div
                    key={task.id}
                    className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getStatusColor(task.status)}>
                            {task.status === 'COMPLETED' ? '已完成' :
                             task.status === 'IN_PROGRESS' ? '进行中' :
                             task.status === 'BLOCKED' ? '阻塞' : '待开始'}
                          </Badge>
                          <h3 className="font-medium">{task.task_name}</h3>
                          {isOverdue && (
                            <Badge className="bg-red-500">
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              逾期
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(task.planned_start_date)} - {formatDate(task.planned_end_date)}
                          </div>
                          {task.assignee_name && (
                            <div className="flex items-center gap-1">
                              <Users className="w-4 h-4" />
                              {task.assignee_name}
                            </div>
                          )}
                          {task.dependencies && task.dependencies.length > 0 && (
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              依赖 {task.dependencies.length} 个任务
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-slate-700">{progress}%</div>
                        <div className="text-xs text-slate-500">完成度</div>
                      </div>
                    </div>
                    <Progress value={progress} className="h-2" />
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

