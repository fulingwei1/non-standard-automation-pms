/**
 * Progress Board Page - 进度看板页面
 * Features: 多维度进度看板，支持筛选和统计
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
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
export default function ProgressBoard() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [boardData, setBoardData] = useState(null)
  useEffect(() => {
    if (id) {
      fetchProject()
      fetchBoardData()
    }
  }, [id])
  const fetchProject = async () => {
    try {
      const res = await projectApi.get(id)
      setProject(res.data || res)
    } catch (error) {
      console.error('Failed to fetch project:', error)
    }
  }
  const fetchBoardData = async () => {
    try {
      setLoading(true)
      const res = await progressApi.reports.getBoard(id)
      const data = res.data || res || {}
      setBoardData(data)
    } catch (error) {
      console.error('Failed to fetch board data:', error)
    } finally {
      setLoading(false)
    }
  }
  const statusColumns = [
    { key: 'TODO', label: '待办', color: 'bg-slate-200' },
    { key: 'IN_PROGRESS', label: '进行中', color: 'bg-blue-200' },
    { key: 'BLOCKED', label: '阻塞', color: 'bg-red-200' },
    { key: 'DONE', label: '已完成', color: 'bg-emerald-200' },
    { key: 'CANCELLED', label: '已取消', color: 'bg-gray-200' },
  ]
  const getStatusColor = (status) => {
    const column = statusColumns.find(col => col.key === status)
    return column?.color || 'bg-slate-200'
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
            title={`${project?.project_name || '项目'} - 进度看板`}
            description="多维度进度看板，支持按阶段、状态筛选"
          />
        </div>
        <Button variant="outline" onClick={fetchBoardData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Statistics */}
      {boardData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总任务数</div>
                  <div className="text-2xl font-bold">{boardData.summary.total || 0}</div>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">待办</div>
                  <div className="text-2xl font-bold text-slate-600">
                    {boardData.summary.todo || 0}
                  </div>
                </div>
                <Clock className="w-8 h-8 text-slate-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">进行中</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {boardData.summary.in_progress || 0}
                  </div>
                </div>
                <Clock className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">阻塞</div>
                  <div className="text-2xl font-bold text-red-600">
                    {boardData.summary.blocked || 0}
                  </div>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">已完成</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {boardData.summary.done || 0}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Kanban Board */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {boardData?.columns?.map((column) => {
          const tasks = column.tasks || []
          const columnConfig = statusColumns.find(col => col.key === column.status) || { label: column.status_name, color: 'bg-slate-200' }
          return (
            <Card key={column.status}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{column.status_name}</span>
                  <Badge className={columnConfig.color}>{tasks.length}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {tasks.map((task) => (
                    <div
                      key={task.id}
                      className="border rounded-lg p-3 hover:bg-slate-50 transition-colors cursor-pointer"
                      onClick={() => navigate(`/projects/${id}/tasks/${task.id}`)}
                    >
                      <div className="font-medium text-sm mb-2">{task.task_name}</div>
                      {task.stage && (
                        <Badge variant="outline" className="text-xs mb-2">
                          {task.stage}
                        </Badge>
                      )}
                      {task.progress !== undefined && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs text-slate-500">
                            <span>进度</span>
                            <span>{task.progress}%</span>
                          </div>
                          <Progress value={task.progress} className="h-1.5" />
                        </div>
                      )}
                      {task.owner_name && (
                        <div className="text-xs text-slate-500 mt-2">
                          负责人: {task.owner_name}
                        </div>
                      )}
                      {task.plan_end && (
                        <div className="text-xs text-slate-500 mt-1">
                          截止: {formatDate(task.plan_end)}
                        </div>
                      )}
                    </div>
                  ))}
                  {tasks.length === 0 && (
                    <div className="text-center py-8 text-slate-400 text-sm">
                      暂无任务
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
