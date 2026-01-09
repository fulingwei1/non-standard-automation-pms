/**
 * Milestone Rate Report Page - 里程碑达成率报表页面
 * Features: 显示项目里程碑达成率统计
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  RefreshCw,
  Target,
  CheckCircle2,
  AlertTriangle,
  Clock,
  TrendingUp,
  FileText,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { cn, formatDate } from '../lib/utils'
import { progressApi, projectApi } from '../services/api'

export default function MilestoneRateReport() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const projectIdFromQuery = searchParams.get('project_id')

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState(null)
  const [reportData, setReportData] = useState(null)
  const [selectedProjectId, setSelectedProjectId] = useState(id ? parseInt(id) : (projectIdFromQuery ? parseInt(projectIdFromQuery) : null))
  const [projects, setProjects] = useState([])

  useEffect(() => {
    if (selectedProjectId) {
      fetchProject()
      fetchReportData()
    } else {
      fetchReportData()
    }
  }, [selectedProjectId])

  const fetchProject = async () => {
    if (!selectedProjectId) return
    try {
      const res = await projectApi.get(selectedProjectId)
      setProject(res.data || res)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const fetchReportData = async () => {
    try {
      setLoading(true)
      const res = await progressApi.reports.getMilestoneRate(selectedProjectId)
      const data = res.data || res || {}
      setReportData(data)
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-500'
      case 'IN_PROGRESS':
        return 'bg-blue-500'
      case 'PENDING':
        return 'bg-slate-300'
      case 'OVERDUE':
        return 'bg-red-500'
      default:
        return 'bg-slate-300'
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case 'COMPLETED':
        return '已完成'
      case 'IN_PROGRESS':
        return '进行中'
      case 'PENDING':
        return '待开始'
      case 'OVERDUE':
        return '已逾期'
      default:
        return '未知'
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
          {selectedProjectId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(`/projects/${selectedProjectId}`)}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
            </Button>
          )}
          <PageHeader
            title={selectedProjectId ? `${project?.project_name || '项目'} - 里程碑达成率` : '里程碑达成率统计'}
            description="查看项目里程碑完成情况"
          />
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={selectedProjectId?.toString() || 'all'}
            onValueChange={(value) => setSelectedProjectId(value === 'all' ? null : parseInt(value))}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {/* TODO: 添加项目列表选择 */}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchReportData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {reportData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总里程碑数</div>
                  <div className="text-2xl font-bold">{reportData.total_milestones || 0}</div>
                </div>
                <Target className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">已完成</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {reportData.completed_milestones || 0}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">达成率</div>
                  <div className="text-2xl font-bold text-violet-600">
                    {reportData.completion_rate?.toFixed(1) || 0}%
                  </div>
                </div>
                <TrendingUp className="w-8 h-8 text-violet-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">逾期/待办</div>
                  <div className="text-2xl font-bold text-red-600">
                    {reportData.overdue_milestones || 0} / {reportData.pending_milestones || 0}
                  </div>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Completion Rate Progress */}
      {reportData && (
        <Card>
          <CardHeader>
            <CardTitle>里程碑达成率</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">整体达成率</span>
                <span className="text-lg font-bold">{reportData.completion_rate?.toFixed(1) || 0}%</span>
              </div>
              <Progress value={reportData.completion_rate || 0} className="h-3" />
              <div className="grid grid-cols-3 gap-4 text-sm text-slate-600">
                <div>
                  <span className="font-medium">已完成:</span> {reportData.completed_milestones || 0}
                </div>
                <div>
                  <span className="font-medium">待办:</span> {reportData.pending_milestones || 0}
                </div>
                <div>
                  <span className="font-medium">逾期:</span> {reportData.overdue_milestones || 0}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Milestone List */}
      {reportData?.milestones && reportData.milestones.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              里程碑详情
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {reportData.milestones.map((milestone) => {
                const isOverdue = milestone.planned_date && 
                  new Date(milestone.planned_date) < new Date() && 
                  milestone.status !== 'COMPLETED'
                const status = isOverdue ? 'OVERDUE' : milestone.status
                return (
                  <div
                    key={milestone.id}
                    className="border rounded-lg p-4 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">{milestone.milestone_name}</span>
                          {milestone.is_key && (
                            <Badge variant="outline" className="text-xs">关键</Badge>
                          )}
                          <Badge className={cn('text-xs', getStatusColor(status))}>
                            {getStatusLabel(status)}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-500 space-y-1">
                          <div>编码: {milestone.milestone_code}</div>
                          {milestone.planned_date && (
                            <div>计划日期: {formatDate(milestone.planned_date)}</div>
                          )}
                          {milestone.actual_date && (
                            <div>实际日期: {formatDate(milestone.actual_date)}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {reportData?.milestones && reportData.milestones.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">
              暂无里程碑数据
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

