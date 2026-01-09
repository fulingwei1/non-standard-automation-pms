/**
 * 跨部门进度可视化组件
 * 用于展示项目的跨部门进度数据
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, Progress, Badge } from '../ui'
import { Users, TrendingUp, AlertTriangle, CheckCircle2, Clock, Target } from 'lucide-react'
import { engineersApi } from '../../services/api'
import { cn } from '../../lib/utils'

export function CrossDepartmentProgress({ projectId }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await engineersApi.getProgressVisibility(projectId)
        setData(response.data)
        setError(null)
      } catch (err) {
        setError(err.response?.data?.detail || err.message || '加载失败')
      } finally {
        setLoading(false)
      }
    }

    if (projectId) {
      fetchData()
    }
  }, [projectId])

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-white/10 rounded w-1/4" />
            <div className="h-20 bg-white/10 rounded" />
            <div className="h-20 bg-white/10 rounded" />
            <div className="h-20 bg-white/10 rounded" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
            <div className="text-red-400 text-sm">{error}</div>
            <p className="text-xs text-slate-500 mt-2">
              请确保后端服务正在运行，并且项目ID正确
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-slate-400 py-8">
            暂无数据
          </div>
        </CardContent>
      </Card>
    )
  }

  const {
    project_name,
    overall_progress,
    project_health,
    total_tasks,
    completed_tasks,
    in_progress_tasks,
    pending_tasks,
    department_progress,
    active_delays
  } = data

  // 健康度颜色和标签
  const healthConfig = {
    H1: { label: '正常', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/30' },
    H2: { label: '有风险', color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/30' },
    H3: { label: '阻塞', color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' },
    H4: { label: '已完结', color: 'text-slate-400', bgColor: 'bg-slate-500/10', borderColor: 'border-slate-500/30' },
  }

  const health = healthConfig[project_health] || healthConfig.H1

  return (
    <div className="space-y-6">
      {/* 项目整体进度 */}
      <Card className={cn('border-2', health.borderColor)}>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">{project_name || '项目进度'}</h3>
              <p className="text-xs text-slate-400 mt-1">项目整体进度概览</p>
            </div>
            <Badge className={cn('px-3 py-1 text-sm font-medium', health.color, health.bgColor, health.borderColor)}>
              {health.label}
            </Badge>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="p-3 rounded-lg bg-surface-1/50 border border-border">
              <div className="text-xs text-slate-400 mb-1">总任务数</div>
              <div className="text-2xl font-bold text-white">{total_tasks}</div>
            </div>
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <div className="text-xs text-emerald-400 mb-1">已完成</div>
              <div className="text-2xl font-bold text-emerald-400">{completed_tasks}</div>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20">
              <div className="text-xs text-blue-400 mb-1">进行中</div>
              <div className="text-2xl font-bold text-blue-400">{in_progress_tasks}</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-500/10 border border-slate-500/20">
              <div className="text-xs text-slate-400 mb-1">待开始</div>
              <div className="text-2xl font-bold text-slate-400">{pending_tasks}</div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">整体进度</span>
              <span className="text-white font-medium text-lg">{overall_progress?.toFixed(1) || 0}%</span>
            </div>
            <Progress value={overall_progress || 0} className="h-4" />
          </div>
        </CardContent>
      </Card>

      {/* 各部门进度统计 */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2 mb-6">
            <Users className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">各部门进度</h3>
            <span className="text-xs text-slate-400 ml-auto">
              共 {department_progress?.length || 0} 个部门
            </span>
          </div>

          <div className="space-y-4">
            {department_progress && department_progress.length > 0 ? (
              department_progress.map((dept, index) => (
                <motion.div
                  key={dept.department}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 rounded-lg bg-surface-1/50 border border-border hover:border-border/80 transition-colors"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="text-white font-medium flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400" />
                        {dept.department}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1">
                        {dept.completed_tasks}/{dept.total_tasks} 任务已完成 ·
                        完成率 {dept.completion_rate?.toFixed(0) || 0}%
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-white">
                        {dept.average_progress?.toFixed(1) || 0}%
                      </div>
                      <div className="text-xs text-slate-400">
                        {dept.in_progress_tasks || 0} 进行中
                      </div>
                    </div>
                  </div>

                  <Progress value={dept.average_progress || 0} className="h-2 mb-3" />

                  {/* 部门成员明细 */}
                  {dept.members && Object.keys(dept.members).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                      <p className="text-xs text-slate-400 mb-2">成员进度:</p>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {Object.entries(dept.members).map(([name, member]) => (
                          <div key={name} className="flex items-center justify-between text-xs p-2 rounded bg-surface-2/50">
                            <span className="text-slate-300 truncate flex-1">{member.real_name}</span>
                            <span className="text-white font-medium ml-2">{member.average_progress?.toFixed(0) || 0}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400">
                暂无部门数据
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 延期任务预警 */}
      {active_delays && active_delays.length > 0 && (
        <Card className="border-2 border-red-500/30">
          <CardContent className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <h3 className="text-lg font-semibold text-white">延期任务</h3>
              <Badge className="bg-red-500/10 text-red-400 border border-red-500/20">
                {active_delays.length} 个
              </Badge>
            </div>

            <div className="space-y-3">
              {active_delays.map((task) => (
                <motion.div
                  key={task.task_id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 hover:border-red-500/30 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-white font-medium text-sm mb-1 truncate">
                        {task.task_name}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {task.assignee} · {task.department}
                        </span>
                        <span className="flex items-center gap-1 text-red-400">
                          <Clock className="w-3 h-3" />
                          延期 {task.delay_days} 天
                        </span>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-sm text-white font-medium">{task.progress}%</div>
                      <div className="text-xs text-slate-400">进度</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 如果没有延期任务，显示正常状态 */}
      {(!active_delays || active_delays.length === 0) && (
        <Card className="border-2 border-emerald-500/30">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-medium">所有任务进度正常，无延期情况</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
