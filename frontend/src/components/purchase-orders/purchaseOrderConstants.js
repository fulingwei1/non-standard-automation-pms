/**
 * 采购订单组件配置常量
 */

// 订单状态配置
export const ORDER_STATUS = {
  draft: {
    key: 'draft',
    label: '草稿',
    color: 'bg-slate-500',
    icon: 'FileText',
    borderColor: 'border-slate-500/30',
    textColor: 'text-slate-400',
  },
  pending: {
    key: 'pending',
    label: '待收货',
    color: 'bg-blue-500',
    icon: 'Clock',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
  },
  partial_received: {
    key: 'partial_received',
    label: '部分到货',
    color: 'bg-amber-500',
    icon: 'Truck',
    borderColor: 'border-amber-500/30',
    textColor: 'text-amber-400',
  },
  completed: {
    key: 'completed',
    label: '已完成',
    color: 'bg-emerald-500',
    icon: 'CheckCircle2',
    borderColor: 'border-emerald-500/30',
    textColor: 'text-emerald-400',
  },
  delayed: {
    key: 'delayed',
    label: '延期',
    color: 'bg-red-500',
    icon: 'AlertTriangle',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
  },
  cancelled: {
    key: 'cancelled',
    label: '已取消',
    color: 'bg-slate-400',
    icon: 'Trash2',
    borderColor: 'border-slate-400/30',
    textColor: 'text-slate-400',
  },
};

// 紧急程度配置
export const ORDER_URGENCY = {
  normal: {
    key: 'normal',
    label: '普通',
    color: 'text-slate-400',
    badgeColor: 'bg-slate-500/20 border-slate-500/30',
  },
  urgent: {
    key: 'urgent',
    label: '加急',
    color: 'text-amber-400',
    badgeColor: 'bg-amber-500/20 border-amber-500/30',
  },
  critical: {
    key: 'critical',
    label: '特急',
    color: 'text-red-400',
    badgeColor: 'bg-red-500/20 border-red-500/30',
  },
};

// 筛选选项
export const ORDER_STATUS_OPTIONS = [
  { value: 'all', label: '全部状态' },
  ...Object.values(ORDER_STATUS).map(s => ({ value: s.key, label: s.label })),
];

export const ORDER_URGENCY_OPTIONS = [
  { value: 'all', label: '全部紧急程度' },
  { value: 'normal', label: '普通' },
  { value: 'urgent', label: '加急' },
  { value: 'critical', label: '特急' },
];

/**
 * 获取订单状态配置
 */
export function getOrderStatus(status) {
  return ORDER_STATUS[status] || ORDER_STATUS.draft;
}

/**
 * 获取紧急程度配置
 */
export function getOrderUrgency(urgency) {
  return ORDER_URGENCY[urgency] || ORDER_URGENCY.normal;
}

/**
 * 格式化金额
 */
export function formatAmount(amount) {
  if (!amount) return '¥0';
  return `¥${parseFloat(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/**
 * 计算到货进度百分比
 */
export function calculateProgress(received, total) {
  if (!total || total === 0) return 0;
  return Math.round((received / total) * 100);
}

/**
 * 格式化日期
 */
export function formatDate(dateStr) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('zh-CN');
}
