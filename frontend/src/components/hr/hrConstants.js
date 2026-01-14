/**
 * HR管理常量配置
 * 包含状态、优先级、类型等配置
 */

// 员工状态配置
export const employeeStatusConfigs = {
  active: { label: '在职', color: 'bg-emerald-500' },
  pending: { label: '待入职', color: 'bg-amber-500' },
  resigned: { label: '已离职', color: 'bg-slate-500' },
  probation: { label: '试用期', color: 'bg-blue-500' },
};

// 招聘状态配置
export const recruitmentStatusConfigs = {
  recruiting: { label: '招聘中', color: 'bg-blue-500' },
  screening: { label: '筛选中', color: 'bg-amber-500' },
  interviewing: { label: '面试中', color: 'bg-purple-500' },
  offer: { label: '发Offer', color: 'bg-emerald-500' },
  completed: { label: '已完成', color: 'bg-slate-500' },
  cancelled: { label: '已取消', color: 'bg-red-500' },
};

// 绩效等级配置
export const performanceRatingConfigs = {
  A: { label: 'A-优秀', color: 'bg-emerald-500', min: 90, max: 100 },
  B: { label: 'B-良好', color: 'bg-blue-500', min: 80, max: 89 },
  C: { label: 'C-合格', color: 'bg-amber-500', min: 70, max: 79 },
  D: { label: 'D-待改进', color: 'bg-orange-500', min: 60, max: 69 },
  E: { label: 'E-不合格', color: 'bg-red-500', min: 0, max: 59 },
};

// 审批状态配置
export const approvalStatusConfigs = {
  pending: { label: '待审批', color: 'bg-amber-500' },
  approved: { label: '已通过', color: 'bg-emerald-500' },
  rejected: { label: '已驳回', color: 'bg-red-500' },
  reviewing: { label: '评审中', color: 'bg-blue-500' },
};

// 优先级配置
export const priorityConfigs = {
  high: { label: '高', color: 'bg-red-500' },
  medium: { label: '中', color: 'bg-amber-500' },
  low: { label: '低', color: 'bg-blue-500' },
};

// 员工问题类型配置
export const issueTypeConfigs = {
  conflict: { label: '冲突', color: 'bg-red-500' },
  leave: { label: '请假', color: 'bg-amber-500' },
  complaint: { label: '投诉', color: 'bg-blue-500' },
  performance: { label: '绩效', color: 'bg-purple-500' },
  attendance: { label: '考勤', color: 'bg-orange-500' },
};

// 考勤类型配置
export const attendanceTypeConfigs = {
  normal: { label: '正常', color: 'bg-emerald-500' },
  late: { label: '迟到', color: 'bg-amber-500' },
  early_leave: { label: '早退', color: 'bg-orange-500' },
  absent: { label: '缺勤', color: 'bg-red-500' },
  leave: { label: '请假', color: 'bg-blue-500' },
};

/**
 * 获取状态颜色
 */
export const getStatusColor = (status, type = 'employee') => {
  const configMap = {
    employee: employeeStatusConfigs,
    recruitment: recruitmentStatusConfigs,
    approval: approvalStatusConfigs,
  };
  
  const configs = configMap[type] || {};
  return configs[status]?.color || 'bg-slate-500';
};

/**
 * 获取状态标签
 */
export const getStatusLabel = (status, type = 'employee') => {
  const configMap = {
    employee: employeeStatusConfigs,
    recruitment: recruitmentStatusConfigs,
    approval: approvalStatusConfigs,
  };
  
  const configs = configMap[type] || {};
  return configs[status]?.label || status;
};

/**
 * 获取优先级颜色
 */
export const getPriorityColor = (priority) => {
  return priorityConfigs[priority]?.color || 'bg-slate-500';
};

/**
 * 获取问题类型颜色
 */
export const getIssueTypeColor = (type) => {
  return issueTypeConfigs[type]?.color || 'bg-slate-500';
};

/**
 * 获取绩效等级
 */
export const getPerformanceRating = (score) => {
  for (const [key, config] of Object.entries(performanceRatingConfigs)) {
    if (score >= config.min && score <= config.max) {
      return { rating: key, ...config };
    }
  }
  return { rating: 'C', ...performanceRatingConfigs.C };
};

export default {
  employeeStatusConfigs,
  recruitmentStatusConfigs,
  performanceRatingConfigs,
  approvalStatusConfigs,
  priorityConfigs,
  issueTypeConfigs,
  attendanceTypeConfigs,
  getStatusColor,
  getStatusLabel,
  getPriorityColor,
  getIssueTypeColor,
  getPerformanceRating,
};
