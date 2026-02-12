/**
 * Production Management Constants and Configuration
 * 生产管理系统常量和配置
 */

// 生产计划状态配置
export const PRODUCTION_PLAN_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: 'bg-slate-500' },
  APPROVED: { value: 'approved', label: '已审批', color: 'bg-emerald-500' },
  PUBLISHED: { value: 'published', label: '已发布', color: 'bg-purple-500' },
  EXECUTING: { value: 'executing', label: '执行中', color: 'bg-blue-500' },
  COMPLETED: { value: 'completed', label: '已完成', color: 'bg-green-500' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: 'bg-red-500' }
};

// 工单状态配置
export const WORK_ORDER_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: 'bg-slate-500' },
  PENDING: { value: 'pending', label: '待处理', color: 'bg-gray-500' },
  ASSIGNED: { value: 'assigned', label: '已派工', color: 'bg-amber-500' },
  STARTED: { value: 'started', label: '已开工', color: 'bg-blue-500' },
  IN_PROGRESS: { value: 'in_progress', label: '进行中', color: 'bg-indigo-500' },
  COMPLETED: { value: 'completed', label: '已完工', color: 'bg-emerald-500' },
  PAUSED: { value: 'paused', label: '已暂停', color: 'bg-orange-500' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: 'bg-red-500' }
};

// 生产线状态配置
export const PRODUCTION_LINE_STATUS = {
  ACTIVE: { value: 'active', label: '运行中', color: 'bg-green-500' },
  IDLE: { value: 'idle', label: '空闲', color: 'bg-gray-500' },
  MAINTENANCE: { value: 'maintenance', label: '维护中', color: 'bg-orange-500' },
  STOPPED: { value: 'stopped', label: '已停止', color: 'bg-red-500' },
  SETUP: { value: 'setup', label: '设置中', color: 'bg-blue-500' }
};

// 生产优先级配置
export const PRODUCTION_PRIORITY = {
  URGENT: { value: 'urgent', label: '紧急', color: 'bg-red-500', weight: 4 },
  HIGH: { value: 'high', label: '高', color: 'bg-orange-500', weight: 3 },
  NORMAL: { value: 'normal', label: '正常', color: 'bg-blue-500', weight: 2 },
  LOW: { value: 'low', label: '低', color: 'bg-gray-500', weight: 1 }
};

// 质量等级配置
export const QUALITY_GRADE = {
  EXCELLENT: { value: 'excellent', label: '优秀', color: 'bg-emerald-500', minScore: 95 },
  GOOD: { value: 'good', label: '良好', color: 'bg-blue-500', minScore: 85 },
  ACCEPTABLE: { value: 'acceptable', label: '合格', color: 'bg-green-500', minScore: 70 },
  POOR: { value: 'poor', label: '不合格', color: 'bg-red-500', minScore: 0 }
};

// 设备状态配置
export const EQUIPMENT_STATUS = {
  RUNNING: { value: 'running', label: '运行中', color: 'bg-green-500' },
  IDLE: { value: 'idle', label: '空闲', color: 'bg-gray-500' },
  MAINTENANCE: { value: 'maintenance', label: '维护中', color: 'bg-orange-500' },
  BREAKDOWN: { value: 'breakdown', label: '故障', color: 'bg-red-500' },
  CALIBRATION: { value: 'calibration', label: '校准中', color: 'bg-blue-500' }
};

// 班次配置
export const WORK_SHIFT = {
  MORNING: { value: 'morning', label: '早班', time: '08:00-16:00' },
  AFTERNOON: { value: 'afternoon', label: '中班', time: '16:00-24:00' },
  NIGHT: { value: 'night', label: '夜班', time: '00:00-08:00' },
  ALL_DAY: { value: 'all_day', label: '全天', time: '00:00-24:00' }
};

// 生产类型配置
export const PRODUCTION_TYPE = {
  MASS_PRODUCTION: { value: 'mass_production', label: '大批量生产' },
  BATCH_PRODUCTION: { value: 'batch_production', label: '批次生产' },
  CUSTOM_PRODUCTION: { value: 'custom_production', label: '定制生产' },
  PROTOTYPE: { value: 'prototype', label: '原型制作' },
  TRIAL_PRODUCTION: { value: 'trial_production', label: '试生产' }
};

// 工艺类型配置
export const PROCESS_TYPE = {
  ASSEMBLY: { value: 'assembly', label: '组装' },
  MACHINING: { value: 'machining', label: '机加工' },
  WELDING: { value: 'welding', label: '焊接' },
  PAINTING: { value: 'painting', label: '喷涂' },
  TESTING: { value: 'testing', label: '测试' },
  PACKAGING: { value: 'packaging', label: '包装' },
  INSPECTION: { value: 'inspection', label: '检验' }
};

// 警告级别配置
export const ALERT_LEVEL = {
  CRITICAL: { value: 'critical', label: '严重', color: 'bg-red-500', icon: '⚠️' },
  WARNING: { value: 'warning', label: '警告', color: 'bg-amber-500', icon: '⚡' },
  INFO: { value: 'info', label: '信息', color: 'bg-blue-500', icon: 'ℹ️' }
};

// 警告状态配置
export const ALERT_STATUS = {
  PENDING: { value: 'pending', label: '待处理', className: 'bg-amber-500/20 text-amber-400' },
  PROCESSING: { value: 'processing', label: '处理中', className: 'bg-blue-500/20 text-blue-400' },
  RESOLVED: { value: 'resolved', label: '已处理', className: 'bg-emerald-500/20 text-emerald-400' },
  CLOSED: { value: 'closed', label: '已关闭', className: 'bg-slate-500/20 text-slate-400' }
};

// 排名类型配置
export const RANKING_TYPE = {
  EFFICIENCY: { value: 'efficiency', label: '效率排名', unit: '%' },
  OUTPUT: { value: 'output', label: '产量排名', unit: '件' },
  QUALITY: { value: 'quality', label: '质量排名', unit: '分' },
  ATTENDANCE: { value: 'attendance', label: '出勤排名', unit: '%' }
};

// 生产统计指标配置
export const PRODUCTION_METRICS = {
  TOTAL_OUTPUT: { key: 'totalOutput', label: '总产量', unit: '件', icon: '📦' },
  COMPLETION_RATE: { key: 'completionRate', label: '完成率', unit: '%', icon: '✅' },
  QUALITY_RATE: { key: 'qualityRate', label: '合格率', unit: '%', icon: '🎯' },
  EFFICIENCY: { key: 'efficiency', label: '生产效率', unit: '%', icon: '⚡' },
  DOWNTIME: { key: 'downtime', label: '停机时间', unit: '小时', icon: '⏰' },
  OEE: { key: 'oee', label: '设备综合效率', unit: '%', icon: '🏭' }
};

// 时间范围配置
export const TIME_RANGE_FILTERS = {
  TODAY: { value: 'today', label: '今天', days: 0 },
  YESTERDAY: { value: 'yesterday', label: '昨天', days: 1 },
  THIS_WEEK: { value: 'this_week', label: '本周', days: 7 },
  LAST_WEEK: { value: 'last_week', label: '上周', days: 14 },
  THIS_MONTH: { value: 'this_month', label: '本月', days: 30 },
  LAST_MONTH: { value: 'last_month', label: '上月', days: 60 },
  THIS_QUARTER: { value: 'this_quarter', label: '本季度', days: 90 },
  THIS_YEAR: { value: 'this_year', label: '今年', days: 365 }
};

// 工具函数：根据状态获取颜色
export const getStatusColor = (status, type = 'plan') => {
  const statusMap = {
    plan: PRODUCTION_PLAN_STATUS,
    order: WORK_ORDER_STATUS,
    line: PRODUCTION_LINE_STATUS,
    equipment: EQUIPMENT_STATUS
  };

  const config = statusMap[type];
  if (!config) {return 'bg-slate-500';}

  return config[status.toUpperCase()]?.color || 'bg-slate-500';
};

// 工具函数：根据状态获取标签
export const getStatusLabel = (status, type = 'plan') => {
  const statusMap = {
    plan: PRODUCTION_PLAN_STATUS,
    order: WORK_ORDER_STATUS,
    line: PRODUCTION_LINE_STATUS,
    equipment: EQUIPMENT_STATUS
  };

  const config = statusMap[type];
  if (!config) {return status;}

  return config[status.toUpperCase()]?.label || status;
};

// 工具函数：根据优先级获取颜色
export const getPriorityColor = (priority) => {
  return PRODUCTION_PRIORITY[priority.toUpperCase()]?.color || 'bg-slate-500';
};

// 工具函数：根据优先级获取标签
export const getPriorityLabel = (priority) => {
  return PRODUCTION_PRIORITY[priority.toUpperCase()]?.label || priority;
};

// 工具函数：根据质量分数获取等级
export const getQualityGrade = (score) => {
  for (const [_key, grade] of Object.entries(QUALITY_GRADE)) {
    if (score >= grade.minScore) {
      return grade;
    }
  }
  return QUALITY_GRADE.POOR;
};

// 工具函数：根据警告级别获取配置
export const getAlertLevelConfig = (level) => {
  return ALERT_LEVEL[level.toUpperCase()] || ALERT_LEVEL.INFO;
};

// 工具函数：根据警告状态获取配置
export const getAlertStatusConfig = (status) => {
  return ALERT_STATUS[status.toUpperCase()] || ALERT_STATUS.PENDING;
};

// 工具函数：计算完成率
export const calculateCompletionRate = (completed, total) => {
  if (total === 0) {return 0;}
  return Math.round(completed / total * 100);
};

// 工具函数：计算合格率
export const calculateQualityRate = (qualified, total) => {
  if (total === 0) {return 0;}
  return Math.round(qualified / total * 100);
};

// 工具函数：计算设备综合效率(OEE)
export const calculateOEE = (availability, performance, quality) => {
  return Math.round(availability * performance * quality * 100) / 100;
};

// 工具函数：格式化生产数据
export const formatProductionData = (data) => {
  return {
    ...data,
    completionRate: calculateCompletionRate(data.completedQty || 0, data.plannedQty || 0),
    qualityRate: calculateQualityRate(data.qualifiedQty || 0, data.completedQty || 0),
    efficiency: data.efficiency || 0,
    statusLabel: getStatusLabel(data.status),
    priorityLabel: getPriorityLabel(data.priority)
  };
};

// 工具函数：验证生产数据
export const validateProductionData = (data) => {
  const errors = [];

  if (!data.planCode) {errors.push('计划编号不能为空');}
  if (!data.projectName) {errors.push('项目名称不能为空');}
  if (!data.plannedQty || data.plannedQty <= 0) {errors.push('计划数量必须大于0');}
  if (!data.startDate) {errors.push('开始日期不能为空');}
  if (!data.endDate) {errors.push('结束日期不能为空');}
  if (new Date(data.startDate) >= new Date(data.endDate)) {
    errors.push('开始日期必须早于结束日期');
  }

  return errors;
};

// 导出所有配置对象
export {
  PRODUCTION_PLAN_STATUS as PLAN_STATUS,
  WORK_ORDER_STATUS as ORDER_STATUS,
  PRODUCTION_LINE_STATUS as LINE_STATUS,
  EQUIPMENT_STATUS as EQUIPMENT,
  WORK_SHIFT as SHIFT,
  PRODUCTION_TYPE as TYPE,
  PROCESS_TYPE as PROCESS,
  ALERT_LEVEL as ALERT,
  ALERT_STATUS as ALERT_STATE,
  RANKING_TYPE as RANKING,
  PRODUCTION_METRICS as METRICS,
  TIME_RANGE_FILTERS as TIME_RANGE };