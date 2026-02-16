/**
 * 智能缺料预警系统 - 常量定义
 */

// 预警级别颜色
export const ALERT_COLORS = {
  URGENT: '#DC2626',    // 红色
  CRITICAL: '#EA580C',  // 橙色
  WARNING: '#CA8A04',   // 黄色
  INFO: '#2563EB'       // 蓝色
};

// 预警级别配置
export const ALERT_LEVELS = {
  URGENT: {
    label: '紧急',
    color: ALERT_COLORS.URGENT,
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
    icon: '🔴',
    description: '已断料或当天需要',
    responseTime: '立即',
  },
  CRITICAL: {
    label: '严重',
    color: ALERT_COLORS.CRITICAL,
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-700',
    borderColor: 'border-orange-200',
    icon: '🟠',
    description: '3-7天内断料',
    responseTime: '2小时',
  },
  WARNING: {
    label: '警告',
    color: ALERT_COLORS.WARNING,
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-700',
    borderColor: 'border-yellow-200',
    icon: '🟡',
    description: '7-14天内断料',
    responseTime: '8小时',
  },
  INFO: {
    label: '提示',
    color: ALERT_COLORS.INFO,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
    icon: '🔵',
    description: '14天以上断料',
    responseTime: '24小时',
  },
};

// 预警状态
export const ALERT_STATUS = {
  PENDING: { label: '待处理', color: 'text-gray-600' },
  PROCESSING: { label: '处理中', color: 'text-blue-600' },
  RESOLVED: { label: '已解决', color: 'text-green-600' },
  CLOSED: { label: '已关闭', color: 'text-gray-400' },
};

// 方案类型
export const SOLUTION_TYPES = {
  URGENT_PURCHASE: {
    label: '紧急采购',
    icon: '⚡',
    description: '从供应商加急采购',
    color: 'text-red-600',
  },
  SUBSTITUTE: {
    label: '替代料',
    icon: '🔄',
    description: '使用替代物料',
    color: 'text-blue-600',
  },
  TRANSFER: {
    label: '项目间调拨',
    icon: '🔀',
    description: '从其他项目借用',
    color: 'text-purple-600',
  },
  PARTIAL_DELIVERY: {
    label: '分批交付',
    icon: '📦',
    description: '先使用现有库存',
    color: 'text-green-600',
  },
  RESCHEDULE: {
    label: '生产重排期',
    icon: '📅',
    description: '调整生产计划',
    color: 'text-orange-600',
  },
};

// 预测算法
export const FORECAST_ALGORITHMS = {
  MOVING_AVERAGE: {
    label: '移动平均',
    value: 'MOVING_AVERAGE',
    description: '适用于需求较稳定的物料',
    icon: '📊',
  },
  EXP_SMOOTHING: {
    label: '指数平滑',
    value: 'EXP_SMOOTHING',
    description: '适用于有趋势变化的物料 (推荐)',
    icon: '📈',
    recommended: true,
  },
  LINEAR_REGRESSION: {
    label: '线性回归',
    value: 'LINEAR_REGRESSION',
    description: '适用于有明显增长/下降趋势',
    icon: '📉',
  },
};

// 根因类型
export const ROOT_CAUSE_TYPES = {
  FORECAST_ERROR: { label: '需求预测不准', color: '#DC2626' },
  SUPPLIER_DELAY: { label: '供应商延期', color: '#EA580C' },
  QUALITY_ISSUE: { label: '质量问题退货', color: '#CA8A04' },
  URGENT_ORDER: { label: '紧急插单', color: '#2563EB' },
  OTHER: { label: '其他', color: '#6B7280' },
};

// 评分颜色映射
export const getScoreColor = (score) => {
  if (score >= 80) return '#22C55E'; // 绿色
  if (score >= 60) return '#3B82F6'; // 蓝色
  if (score >= 40) return '#F59E0B'; // 橙色
  return '#EF4444'; // 红色
};

// 风险评分颜色映射
export const getRiskScoreColor = (score) => {
  if (score >= 75) return ALERT_COLORS.URGENT;
  if (score >= 50) return ALERT_COLORS.CRITICAL;
  if (score >= 25) return ALERT_COLORS.WARNING;
  return ALERT_COLORS.INFO;
};
