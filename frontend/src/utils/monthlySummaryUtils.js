/**
 * 月度总结工具函数
 */

/**
 * 获取当前考核周期信息
 */
export const getCurrentPeriod = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  return {
    year,
    month,
    period: `${year}-${String(month).padStart(2, '0')}`,
    startDate: new Date(year, month - 1, 1).toISOString().split('T')[0],
    endDate: new Date(year, month, 0).toISOString().split('T')[0],
    daysLeft: new Date(year, month, 0).getDate() - now.getDate()
  }
}

/**
 * 获取状态标签配置
 */
export const getStatusBadge = (status) => {
  const badges = {
    IN_PROGRESS: { label: '进行中', color: 'bg-blue-500/20 text-blue-400' },
    SUBMITTED: { label: '已提交', color: 'bg-emerald-500/20 text-emerald-400' },
    EVALUATING: { label: '评价中', color: 'bg-amber-500/20 text-amber-400' },
    COMPLETED: { label: '已完成', color: 'bg-slate-500/20 text-slate-400' }
  }
  return badges[status] || badges.IN_PROGRESS
}

/**
 * 获取等级颜色
 */
export const getLevelColor = (level) => {
  const colors = {
    A: 'text-emerald-400',
    B: 'text-blue-400',
    C: 'text-amber-400',
    D: 'text-red-400'
  }
  return colors[level] || 'text-slate-400'
}

/**
 * 动画配置
 */
export const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 }
}
