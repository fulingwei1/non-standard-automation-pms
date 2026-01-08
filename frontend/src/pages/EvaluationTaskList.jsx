import React, { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  ClipboardList,
  Search,
  Filter,
  Users,
  Briefcase,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  Target,
  Award
} from 'lucide-react'
import { cn } from '../lib/utils'
import { performanceApi } from '../services/api'

const EvaluationTaskList = () => {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all') // all, pending, completed
  const [typeFilter, setTypeFilter] = useState('all') // all, dept, project
  const [periodFilter, setPeriodFilter] = useState('2025-01') // 当前周期
  const [isLoading, setIsLoading] = useState(false)
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState(null)

  // 获取当前用户信息
  const currentUser = useMemo(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        return JSON.parse(userStr)
      } catch (e) {
        console.error('解析用户信息失败:', e)
      }
    }
    return {
      id: 1,
      name: '李经理',
      role: 'dept_manager',
      department: '技术开发部',
      projects: ['项目A', '项目B']
    }
  }, [])

  // 加载评价任务列表
  const loadTasks = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await performanceApi.getEvaluationTasks({
        period: periodFilter,
        status_filter: statusFilter === 'all' ? undefined : statusFilter.toUpperCase()
      })
      setTasks(response.data.tasks || [])
    } catch (err) {
      console.error('加载评价任务失败:', err)
      setError(err.response?.data?.detail || '加载失败')
      // Fallback to mock data
      setTasks(mockEvaluationTasks)
    } finally {
      setIsLoading(false)
    }
  }

  // 监听筛选条件变化
  useEffect(() => {
    loadTasks()
  }, [periodFilter, statusFilter])

  // Mock 待评价任务列表（作为fallback）
  const mockEvaluationTasks = [
    {
      id: 1,
      employeeId: 101,
      employeeName: '张三',
      department: '技术开发部',
      position: '高级工程师',
      period: '2025-01',
      submitDate: '2025-01-28',
      evaluationType: 'dept', // dept: 部门经理评价, project: 项目经理评价
      projectName: null,
      weight: 50,
      status: 'PENDING', // PENDING, COMPLETED
      deadline: '2025-02-05',
      daysLeft: 3,
      workSummary: {
        workContent: '本月主要负责项目A的核心功能开发，完成了用户认证模块和权限管理系统...',
        selfEvaluation: '工作完成度较高，技术难点均已攻克...',
        highlights: '成功优化了系统性能，响应时间提升40%',
        problems: '在跨模块协作时遇到一些沟通问题',
        nextMonthPlan: '计划完成支付模块的开发和测试'
      },
      score: null,
      comment: null
    },
    {
      id: 2,
      employeeId: 102,
      employeeName: '王五',
      department: '技术开发部',
      position: '工程师',
      period: '2025-01',
      submitDate: '2025-01-29',
      evaluationType: 'dept',
      projectName: null,
      weight: 50,
      status: 'PENDING',
      deadline: '2025-02-05',
      daysLeft: 3,
      workSummary: {
        workContent: '参与项目B的前端开发工作...',
        selfEvaluation: '按时完成分配的任务...',
        highlights: '改进了UI交互体验',
        problems: '对新技术栈还需要更多学习',
        nextMonthPlan: '提升React开发能力'
      },
      score: null,
      comment: null
    },
    {
      id: 3,
      employeeId: 101,
      employeeName: '张三',
      department: '技术开发部',
      position: '高级工程师',
      period: '2025-01',
      submitDate: '2025-01-28',
      evaluationType: 'project',
      projectName: '项目A',
      weight: 60,
      status: 'COMPLETED',
      deadline: '2025-02-05',
      daysLeft: 3,
      workSummary: {
        workContent: '在项目A中完成了核心功能开发...',
        selfEvaluation: '项目贡献度高...',
        highlights: '技术攻关能力强',
        problems: '',
        nextMonthPlan: '继续优化系统性能'
      },
      score: 92,
      comment: '在项目中表现优异，技术能力强，按时交付高质量代码'
    },
    {
      id: 4,
      employeeId: 103,
      employeeName: '赵六',
      department: '技术开发部',
      position: '初级工程师',
      period: '2025-01',
      submitDate: '2025-01-30',
      evaluationType: 'project',
      projectName: '项目B',
      weight: 100,
      status: 'PENDING',
      deadline: '2025-02-05',
      daysLeft: 3,
      workSummary: {
        workContent: '负责项目B的测试工作...',
        selfEvaluation: '测试覆盖率达到85%...',
        highlights: '发现并修复了多个关键bug',
        problems: '自动化测试经验不足',
        nextMonthPlan: '学习自动化测试框架'
      },
      score: null,
      comment: null
    },
    {
      id: 5,
      employeeId: 104,
      employeeName: '李四',
      department: '技术开发部',
      position: '高级工程师',
      period: '2024-12',
      submitDate: '2024-12-28',
      evaluationType: 'dept',
      projectName: null,
      weight: 50,
      status: 'COMPLETED',
      deadline: '2025-01-05',
      daysLeft: -28,
      workSummary: {
        workContent: '上月工作内容...',
        selfEvaluation: '上月自评...',
        highlights: '',
        problems: '',
        nextMonthPlan: ''
      },
      score: 88,
      comment: '工作态度良好，技术能力有待提升'
    }
  ]

  // 获取可选周期列表
  const availablePeriods = useMemo(() => {
    const allTasks = [...tasks, ...mockEvaluationTasks]
    const periods = [...new Set(allTasks.map(task => task.period))]
    return periods.sort().reverse()
  }, [tasks])

  // 过滤任务列表（仅用于本地搜索和类型过滤）
  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      // 搜索过滤
      if (searchTerm && !(task.employeeName || task.employee_name || '').toLowerCase().includes(searchTerm.toLowerCase())) {
        return false
      }

      // 类型过滤
      if (typeFilter !== 'all') {
        const evaluationType = task.evaluationType || task.evaluator_type
        if (typeFilter === 'dept' && evaluationType !== 'dept' && evaluationType !== 'DEPT_MANAGER') return false
        if (typeFilter === 'project' && evaluationType !== 'project' && evaluationType !== 'PROJECT_MANAGER') return false
      }

      return true
    })
  }, [tasks, searchTerm, typeFilter])

  // 统计数据
  const statistics = useMemo(() => {
    return {
      total: tasks.length,
      pending: tasks.filter(t => (t.status || '').toUpperCase() === 'PENDING').length,
      completed: tasks.filter(t => (t.status || '').toUpperCase() === 'COMPLETED').length,
      dept: tasks.filter(t => {
        const type = t.evaluationType || t.evaluator_type
        return type === 'dept' || type === 'DEPT_MANAGER'
      }).length,
      project: tasks.filter(t => {
        const type = t.evaluationType || t.evaluator_type
        return type === 'project' || type === 'PROJECT_MANAGER'
      }).length,
      avgScore: tasks.filter(t => t.score !== null && t.score !== undefined).reduce((sum, t) => sum + t.score, 0) /
                tasks.filter(t => t.score !== null && t.score !== undefined).length || 0
    }
  }, [tasks])

  // 获取状态标签
  const getStatusBadge = (status) => {
    const badges = {
      PENDING: { label: '待评价', color: 'bg-amber-500/20 text-amber-400', icon: Clock },
      COMPLETED: { label: '已完成', color: 'bg-emerald-500/20 text-emerald-400', icon: CheckCircle2 }
    }
    return badges[status] || badges.PENDING
  }

  // 获取类型标签
  const getTypeBadge = (type, projectName) => {
    if (type === 'dept') {
      return { label: '部门评价', color: 'bg-blue-500/20 text-blue-400', icon: Users }
    }
    return { label: `项目评价: ${projectName}`, color: 'bg-purple-500/20 text-purple-400', icon: Briefcase }
  }

  // 获取紧急程度颜色
  const getUrgencyColor = (daysLeft) => {
    if (daysLeft < 0) return 'text-slate-500' // 已过期
    if (daysLeft <= 2) return 'text-red-400' // 紧急
    if (daysLeft <= 5) return 'text-amber-400' // 警告
    return 'text-emerald-400' // 正常
  }

  // 处理评价
  const handleEvaluate = (task) => {
    navigate(`/evaluation/${task.id}`, { state: { task } })
  }

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-7xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">绩效评价任务</h1>
              <p className="text-slate-400">
                {currentUser.role === 'dept_manager' ? '部门成员' : '项目成员'}绩效评价和打分
              </p>
            </div>
            <ClipboardList className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 统计卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-xl p-4 border border-blue-500/20">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <ClipboardList className="h-4 w-4" />
                <span className="text-sm">总任务</span>
              </div>
              <p className="text-3xl font-bold text-white">{statistics.total}</p>
            </div>

            <div className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 rounded-xl p-4 border border-amber-500/20">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Clock className="h-4 w-4" />
                <span className="text-sm">待评价</span>
              </div>
              <p className="text-3xl font-bold text-amber-400">{statistics.pending}</p>
            </div>

            <div className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 rounded-xl p-4 border border-emerald-500/20">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm">已完成</span>
              </div>
              <p className="text-3xl font-bold text-emerald-400">{statistics.completed}</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-xl p-4 border border-purple-500/20">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Users className="h-4 w-4" />
                <span className="text-sm">部门 / 项目</span>
              </div>
              <p className="text-3xl font-bold text-purple-400">{statistics.dept} / {statistics.project}</p>
            </div>

            <div className="bg-gradient-to-br from-pink-500/10 to-pink-500/5 rounded-xl p-4 border border-pink-500/20">
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Award className="h-4 w-4" />
                <span className="text-sm">平均分</span>
              </div>
              <p className="text-3xl font-bold text-pink-400">
                {statistics.avgScore > 0 ? statistics.avgScore.toFixed(1) : '-'}
              </p>
            </div>
          </div>
        </motion.div>

        {/* 筛选和搜索栏 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-4 border border-slate-700/50">
            <div className="flex flex-col md:flex-row gap-4">
              {/* 搜索框 */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="搜索员工姓名..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* 周期选择 */}
              <select
                value={periodFilter}
                onChange={(e) => setPeriodFilter(e.target.value)}
                className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                {availablePeriods.map(period => (
                  <option key={period} value={period}>
                    {period.split('-')[0]}年{period.split('-')[1]}月
                  </option>
                ))}
              </select>

              {/* 状态筛选 */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">全部状态</option>
                <option value="pending">待评价</option>
                <option value="completed">已完成</option>
              </select>

              {/* 类型筛选 */}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="all">全部类型</option>
                <option value="dept">部门评价</option>
                <option value="project">项目评价</option>
              </select>
            </div>
          </div>
        </motion.div>

        {/* 任务列表 */}
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
          <div className="space-y-4">
            {isLoading ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
                <div className="animate-spin h-12 w-12 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-slate-400">加载中...</p>
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
                <AlertCircle className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无评价任务</p>
              </div>
            ) : (
              filteredTasks.map((task, index) => (
                <motion.div
                  key={task.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 hover:border-slate-600 transition-all overflow-hidden"
                >
                  <div className="p-6">
                    {/* 任务头部 */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-start gap-4">
                        {/* 员工头像 */}
                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold text-lg">
                            {(task.employeeName || task.employee_name || '未知').charAt(0)}
                          </span>
                        </div>

                        {/* 员工信息 */}
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-xl font-bold text-white">{task.employeeName || task.employee_name}</h3>
                            <span className={cn(
                              'px-3 py-1 rounded-full text-sm font-medium',
                              getStatusBadge(task.status).color
                            )}>
                              {getStatusBadge(task.status).label}
                            </span>
                            <span className={cn(
                              'px-3 py-1 rounded-full text-sm font-medium',
                              getTypeBadge(task.evaluationType || task.evaluator_type, task.projectName || task.project_name).color
                            )}>
                              {getTypeBadge(task.evaluationType || task.evaluator_type, task.projectName || task.project_name).label}
                            </span>
                          </div>

                          <div className="flex items-center gap-4 text-sm text-slate-400">
                            <span>{task.department || task.employee_department || '-'}</span>
                            <span>·</span>
                            <span>{task.position || task.employee_position || '-'}</span>
                            <span>·</span>
                            <span>权重 {task.weight || task.project_weight || 50}%</span>
                          </div>
                        </div>
                      </div>

                      {/* 评分结果 */}
                      {task.status === 'COMPLETED' && task.score !== null && (
                        <div className="text-right">
                          <p className="text-sm text-slate-400 mb-1">评分</p>
                          <p className="text-3xl font-bold text-emerald-400">{task.score}</p>
                        </div>
                      )}
                    </div>

                    {/* 工作总结预览 */}
                    {(task.workSummary || task.summary) && (
                      <div className="bg-slate-900/30 rounded-lg p-4 mb-4">
                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                          <Target className="h-4 w-4" />
                          <span className="text-sm font-medium">工作总结</span>
                        </div>
                        <p className="text-slate-300 line-clamp-2 mb-2">
                          {(task.workSummary?.workContent || task.workSummary?.work_content || task.summary?.work_content || '暂无工作总结')}
                        </p>
                        {(task.workSummary?.highlights || task.summary?.highlights) && (
                          <div className="flex items-start gap-2 mt-2 p-2 bg-amber-500/10 rounded border border-amber-500/20">
                            <TrendingUp className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-amber-300 line-clamp-1">
                              {task.workSummary?.highlights || task.summary?.highlights}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* 评价内容（已完成）*/}
                    {task.status === 'COMPLETED' && task.comment && (
                      <div className="bg-emerald-500/10 rounded-lg p-4 mb-4 border border-emerald-500/20">
                        <div className="flex items-center gap-2 text-emerald-400 mb-2">
                          <CheckCircle2 className="h-4 w-4" />
                          <span className="text-sm font-medium">评价意见</span>
                        </div>
                        <p className="text-slate-300">{task.comment}</p>
                      </div>
                    )}

                    {/* 底部操作栏 */}
                    <div className="flex items-center justify-between pt-4 border-t border-slate-700/50">
                      <div className="flex items-center gap-6 text-sm">
                        <div className="flex items-center gap-2 text-slate-400">
                          <Calendar className="h-4 w-4" />
                          <span>提交: {task.submitDate || task.submit_date || '-'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className={cn('h-4 w-4', getUrgencyColor(task.daysLeft || task.days_left || 0))} />
                          <span className={getUrgencyColor(task.daysLeft || task.days_left || 0)}>
                            {(task.daysLeft || task.days_left || 0) < 0
                              ? `已过期 ${Math.abs(task.daysLeft || task.days_left || 0)} 天`
                              : (task.daysLeft || task.days_left || 0) === 0
                              ? '今天截止'
                              : `剩余 ${task.daysLeft || task.days_left || 0} 天`
                            }
                          </span>
                        </div>
                      </div>

                      {task.status === 'PENDING' && (
                        <button
                          onClick={() => handleEvaluate(task)}
                          className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg font-medium transition-all flex items-center gap-2"
                        >
                          开始评价
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      )}

                      {task.status === 'COMPLETED' && (
                        <button
                          onClick={() => handleEvaluate(task)}
                          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                        >
                          查看详情
                          <ArrowRight className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">评价说明：</p>
                <p>• 请在截止日期前完成所有待评价任务</p>
                <p>• 评分范围：60-100分，建议参考员工工作表现客观评分</p>
                <p>• 部门经理评价权重默认50%，项目经理评价权重默认50%</p>
                <p>• 员工最终得分 = 部门经理评分 × 50% + 项目经理评分 × 50%</p>
                <p>• 评价意见将反馈给员工，请认真填写建设性意见</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default EvaluationTaskList
