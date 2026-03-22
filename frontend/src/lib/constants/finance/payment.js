/**
 * Payment Management Utilities - 支付管理系统工具函数和视图配置
 * 查询函数、计算函数、视图模式、筛选配置、催收报告生成等
 */
import { formatCurrencyCompact as formatCurrency } from "../../../lib/formatters";
import { formatPercentage } from './dashboard.js';
import {
  PAYMENT_TYPES, PAYMENT_TYPE_OPTIONS,
  PAYMENT_STATUS, PAYMENT_STATUS_OPTIONS,
  INVOICE_STATUS, INVOICE_STATUS_OPTIONS,
  AGING_PERIODS, AGING_PERIOD_OPTIONS,
  COLLECTION_LEVELS, COLLECTION_LEVEL_OPTIONS,
  COLLECTION_METHODS, COLLECTION_METHOD_OPTIONS,
  PAYMENT_METHODS, PAYMENT_METHOD_OPTIONS,
  CREDIT_RATINGS, CREDIT_RATING_OPTIONS,
  PAYMENT_METRICS, PAYMENT_METRIC_OPTIONS,
  REMINDER_TYPES, REMINDER_TYPE_OPTIONS,
} from './payment-config.js';

// 重新导出所有配置数据，保持向后兼容
export {
  PAYMENT_TYPES, PAYMENT_TYPE_OPTIONS,
  PAYMENT_STATUS, PAYMENT_STATUS_OPTIONS,
  INVOICE_STATUS, INVOICE_STATUS_OPTIONS,
  AGING_PERIODS, AGING_PERIOD_OPTIONS,
  COLLECTION_LEVELS, COLLECTION_LEVEL_OPTIONS,
  COLLECTION_METHODS, COLLECTION_METHOD_OPTIONS,
  PAYMENT_METHODS, PAYMENT_METHOD_OPTIONS,
  CREDIT_RATINGS, CREDIT_RATING_OPTIONS,
  PAYMENT_METRICS, PAYMENT_METRIC_OPTIONS,
  REMINDER_TYPES, REMINDER_TYPE_OPTIONS,
} from './payment-config.js';

// ==================== 查询工具函数 ====================

/**
 * 获取支付类型配置
 */
export function getPaymentType(type) {
  return PAYMENT_TYPES[type?.toUpperCase()] || PAYMENT_TYPES.DEPOSIT;
}

/**
 * 获取支付状态配置
 */
export function getPaymentStatus(status) {
  return PAYMENT_STATUS[status?.toUpperCase()] || PAYMENT_STATUS.PENDING;
}

/**
 * 获取发票状态配置
 */
export function getInvoiceStatus(status) {
  return INVOICE_STATUS[status?.toUpperCase()] || INVOICE_STATUS.DRAFT;
}

/**
 * 获取账龄期间配置
 */
export function getAgingPeriod(daysOverdue) {
  if (daysOverdue <= 0) {return AGING_PERIODS.CURRENT;}
  if (daysOverdue <= 30) {return AGING_PERIODS.DAYS_1_30;}
  if (daysOverdue <= 60) {return AGING_PERIODS.DAYS_31_60;}
  if (daysOverdue <= 90) {return AGING_PERIODS.DAYS_61_90;}
  return AGING_PERIODS.DAYS_OVER_90;
}

/**
 * 获取催收级别配置
 */
export function getCollectionLevel(level) {
  return COLLECTION_LEVELS[level?.toUpperCase()] || COLLECTION_LEVELS.NORMAL;
}

/**
 * 获取支付方式配置
 */
export function getPaymentMethod(method) {
  return PAYMENT_METHODS[method?.toUpperCase()] || PAYMENT_METHODS.BANK_TRANSFER;
}

/**
 * 获取客户信用等级配置
 */
export function getCreditRating(rating) {
  return CREDIT_RATINGS[rating?.toUpperCase()] || CREDIT_RATINGS.A;
}

// ==================== 计算工具函数 ====================

/**
 * 计算账龄（逾期天数）
 */
export function calculateAging(dueDate) {
  if (!dueDate) {return 0;}
  const today = new Date();
  const due = new Date(dueDate);
  const diffTime = today - due;
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * 计算DSO（应收账款周转天数）
 */
export function calculateDSO(receivables, monthlyRevenue) {
  if (!monthlyRevenue || monthlyRevenue === 0) {return 0;}
  return Math.round(receivables / monthlyRevenue * 30);
}

/**
 * 计算回款率
 */
export function calculateCollectionRate(collectedAmount, totalAmount) {
  if (!totalAmount || totalAmount === 0) {return 0;}
  return Math.round(collectedAmount / totalAmount * 100);
}

/**
 * 计算逾期利息
 */
export function calculateOverdueInterest(amount, daysOverdue, interestRate = 0.05) {
  if (daysOverdue <= 0) {return 0;}
  const dailyRate = interestRate / 365;
  return amount * daysOverdue * dailyRate;
}

/**
 * 获取催收建议
 * 根据逾期天数、金额、信用评级综合判断催收策略
 */
export function getCollectionRecommendation(overdueDays, amount, creditRating) {
  const _rating = getCreditRating(creditRating);
  const _agingPeriod = getAgingPeriod(overdueDays);

  if (overdueDays <= 0) {
    return {
      level: 'normal',
      actions: ['发送友好提醒'],
      methods: ['email'],
      frequency: 7
    };
  }

  if (overdueDays <= 30) {
    return {
      level: 'warning',
      actions: ['发送催收邮件', '电话跟进'],
      methods: ['email', 'phone'],
      frequency: 3
    };
  }

  if (overdueDays <= 90) {
    return {
      level: 'urgent',
      actions: ['电话催收', '发送催收函', '考虑法律途径'],
      methods: ['phone', 'letter'],
      frequency: 1
    };
  }

  return {
    level: 'critical',
    actions: ['立即上门催收', '启动法律程序'],
    methods: ['visit', 'legal'],
    frequency: 1
  };
}

/**
 * 生成催收报告
 * 汇总应收账款、逾期金额、回款率、账龄分布等关键指标
 */
export function generateCollectionReport(payments) {
  const totalAmount = payments.reduce((sum, p) => sum + p.amount, 0);
  const overdueAmount = payments.
  filter((p) => p.status === 'overdue').
  reduce((sum, p) => sum + p.amount, 0);
  const collectionRate = calculateCollectionRate(
    payments.filter((p) => p.status === 'paid').reduce((sum, p) => sum + p.amount, 0),
    totalAmount
  );

  const agingDistribution = {};
  Object.values(AGING_PERIODS).forEach((period) => {
    agingDistribution[period.key] = payments.
    filter((p) => {
      const daysOverdue = calculateAging(p.due_date);
      return daysOverdue >= period.minDays && daysOverdue <= period.maxDays;
    }).
    reduce((sum, p) => sum + p.amount, 0);
  });

  return {
    totalAmount,
    overdueAmount,
    collectionRate,
    overdueRate: totalAmount > 0 ? overdueAmount / totalAmount * 100 : 0,
    agingDistribution,
    totalPayments: payments.length,
    overduePayments: payments.filter((p) => p.status === 'overdue').length
  };
}

// ==================== 视图模式配置 ====================

export const VIEW_MODES = {
 list: {
  label: "列表视图",
 icon: "list",
 description: "以列表形式展示所有回款记录",
 },
 timeline: {
  label: "时间线视图",
 icon: "timeline",
  description: "按时间轴展示回款进度",
 },
 aging: {
  label: "账龄分析",
 icon: "chart",
 description: "分析回款账龄分布情况",
 },
};

// ==================== 筛选选项配置 ====================

export const FILTER_OPTIONS = {
 types: [
  { value: "all", label: "全部类型" },
 { value: "deposit", label: "签约款" },
 { value: "progress", label: "进度款" },
  { value: "delivery", label: "发货款" },
  { value: "acceptance", label: "验收款" },
 { value: "warranty", label: "质保金" },
 ],
 statuses: [
 { value: "all", label: "全部状态" },
 { value: "paid", label: "已到账" },
 { value: "pending", label: "待收款" },
   { value: "overdue", label: "已逾期" },
  { value: "invoiced", label: "已开票" },
 ],
};

// ==================== 账龄分组配置 ====================

export const AGING_BUCKETS = [
 {
  key: "current",
 label: "当前期",
  days: 0,
 color: "text-emerald-400",
  bgColor: "bg-emerald-500/10",
  },
 {
 key: "1-30",
 label: "1-30天",
 days: 30,
 color: "text-blue-400",
  bgColor: "bg-blue-500/10",
  },
 {
  key: "31-60",
  label: "31-60天",
 days: 60,
 color: "text-amber-400",
 bgColor: "bg-amber-500/10",
  },
 {
  key: "61-90",
 label: "61-90天",
  days: 90,
 color: "text-orange-400",
  bgColor: "bg-orange-500/10",
 },
 {
  key: "90+",
  label: "90天以上",
 days: Infinity,
   color: "text-red-400",
 bgColor: "bg-red-500/10",
 },
];

// ==================== 兼容工具函数 ====================

/**
 * 格式化支付金额（简化版，用于回款视图）
 */
export const formatPaymentAmount = (amount) => {
  if (amount >= 10000) {
  return `¥${(amount / 10000).toFixed(1)}万`;
 }
 return `¥${amount.toLocaleString('zh-CN')}`;
};

/**
 * 格式化支付日期
 */
export const formatPaymentDate = (dateStr) => {
 if (!dateStr) {return "--";}
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN");
};

/**
 * 格式化支付日期时间
 */
export const formatPaymentDateTime = (dateStr) => {
 if (!dateStr) {return "--";}
 const date = new Date(dateStr);
 return date.toLocaleString("zh-CN");
};

/**
 * 计算逾期天数
 */
export const calculateOverdueDays = (dueDate) => {
 if (!dueDate) {return 0;}
 const due = new Date(dueDate);
 const now = new Date();
 const diffTime = now - due;
 return Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
};

/**
 * 获取支付类型标签
 */
export const getPaymentTypeLabel = (type) => {
 return getPaymentType(type).label;
};

/**
 * 获取支付状态标签
 */
export const getPaymentStatusLabel = (status) => {
 return getPaymentStatus(status).label;
};

/**
 * 获取账龄分组
 */
export const getAgingBucket = (daysOverdue) => {
 return AGING_BUCKETS.find(
 (bucket) => daysOverdue <= bucket.days
 ) || AGING_BUCKETS[AGING_BUCKETS.length - 1];
};

// ==================== 聚合默认导出 ====================

export const PAYMENT_MANAGEMENT_DEFAULT = {
  // 配置集合
  PAYMENT_TYPES,
  PAYMENT_STATUS,
  INVOICE_STATUS,
  AGING_PERIODS,
  COLLECTION_LEVELS,
  COLLECTION_METHODS,
  PAYMENT_METHODS,
  CREDIT_RATINGS,
  PAYMENT_METRICS,
  REMINDER_TYPES,

  // 选项集合
  PAYMENT_TYPE_OPTIONS,
  PAYMENT_STATUS_OPTIONS,
  INVOICE_STATUS_OPTIONS,
  AGING_PERIOD_OPTIONS,
  COLLECTION_LEVEL_OPTIONS,
  COLLECTION_METHOD_OPTIONS,
  PAYMENT_METHOD_OPTIONS,
  CREDIT_RATING_OPTIONS,
  PAYMENT_METRIC_OPTIONS,
  REMINDER_TYPE_OPTIONS,

  // 工具函数
  getPaymentType,
  getPaymentStatus,
  getInvoiceStatus,
  getAgingPeriod,
  getCollectionLevel,
  getPaymentMethod,
  getCreditRating,
  calculateAging,
  calculateDSO,
  calculateCollectionRate,
  calculateOverdueInterest,
  getCollectionRecommendation,
  formatCurrency,
  formatPercentage,
  generateCollectionReport,

 // 来自 paymentConstants 的兼容导出
 VIEW_MODES,
 FILTER_OPTIONS,
 AGING_BUCKETS,
 formatPaymentAmount,
 formatPaymentDate,
 formatPaymentDateTime,
 calculateOverdueDays,
 getPaymentTypeLabel,
 getPaymentStatusLabel,
 getAgingBucket,
};
