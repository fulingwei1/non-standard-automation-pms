import {
  Clock,
  CheckCircle2,
  Users,
  Briefcase
} from 'lucide-react'

/**
 * 获取状态标签配置
 */
export const getStatusBadge = (status) => {
  const badges = {
    PENDING: { label: '待评价', color: 'bg-amber-500/20 text-amber-400', icon: Clock },
    COMPLETED: { label: '已完成', color: 'bg-emerald-500/20 text-emerald-400', icon: CheckCircle2 }
  }
  return badges[status] || badges.PENDING
}

/**
 * 获取类型标签配置
 */
export const getTypeBadge = (type, projectName) => {
  if (type === 'dept' || type === 'DEPT_MANAGER') {
    return { label: '部门评价', color: 'bg-blue-500/20 text-blue-400', icon: Users }
  }
  return { label: `项目评价: ${projectName || '未知项目'}`, color: 'bg-purple-500/20 text-purple-400', icon: Briefcase }
}

/**
 * 获取紧急程度颜色
 */
export const getUrgencyColor = (daysLeft) => {
  if (daysLeft < 0) return 'text-slate-500' // 已过期
  if (daysLeft <= 2) return 'text-red-400' // 紧急
  if (daysLeft <= 5) return 'text-amber-400' // 警告
  return 'text-emerald-400' // 正常
}

/**
 * 计算任务统计信息
 */
export const calculateTaskStatistics = (tasks) => {
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
}

/**
 * 过滤任务列表
 */
export const filterTasks = (tasks, searchTerm, typeFilter) => {
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
}
