/**
 * Payment Management Constants
 * 支付管理相关常量配置
 */

import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  DollarSign,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

// ==================== 支付类型配置 ====================
export const PAYMENT_TYPES = {
  deposit: {
    label: "签约款",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    ratio: "30%",
    icon: DollarSign,
  },
  progress: {
    label: "进度款",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    ratio: "40%",
    icon: TrendingUp,
  },
  delivery: {
    label: "发货款",
    color: "bg-purple-500",
    textColor: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/30",
    ratio: "20%",
    icon: FileText,
  },
  acceptance: {
    label: "验收款",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    ratio: "5%",
    icon: CheckCircle2,
  },
  warranty: {
    label: "质保金",
    color: "bg-slate-500",
    textColor: "text-slate-400",
    bgColor: "bg-slate-500/10",
    borderColor: "border-slate-500/30",
    ratio: "5%",
    icon: Clock,
  },
};

// ==================== 支付状态配置 ====================
export const PAYMENT_STATUS = {
  paid: {
    label: "已到账",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    icon: CheckCircle2,
    value: "PAID",
  },
  pending: {
    label: "待收款",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    icon: Clock,
    value: "PENDING",
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500",
    textColor: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    icon: AlertTriangle,
    value: "OVERDUE",
  },
  invoiced: {
    label: "已开票",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    icon: FileText,
    value: "INVOICED",
  },
};

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

// ==================== 筛选选项 ====================
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

// ==================== 工具函数 ====================
export const getPaymentType = (type) => {
  return PAYMENT_TYPES[type] || PAYMENT_TYPES.deposit;
};

export const getPaymentStatus = (status) => {
  const statusKey = status?.toLowerCase();
  return PAYMENT_STATUS[statusKey] || PAYMENT_STATUS.pending;
};

export const getAgingBucket = (daysOverdue) => {
  return AGING_BUCKETS.find(
    (bucket) => daysOverdue <= bucket.days
  ) || AGING_BUCKETS[AGING_BUCKETS.length - 1];
};

export const formatPaymentAmount = (amount) => {
  if (amount >= 10000) {
    return `¥${(amount / 10000).toFixed(1)}万`;
  }
  return `¥${amount.toLocaleString('zh-CN')}`;
};

export const formatPaymentDate = (dateStr) => {
  if (!dateStr) {return "--";}
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN");
};

export const formatPaymentDateTime = (dateStr) => {
  if (!dateStr) {return "--";}
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN");
};

export const calculateOverdueDays = (dueDate) => {
  if (!dueDate) {return 0;}
  const due = new Date(dueDate);
  const now = new Date();
  const diffTime = now - due;
  return Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
};

export const getPaymentTypeLabel = (type) => {
  return getPaymentType(type).label;
};

export const getPaymentStatusLabel = (status) => {
  return getPaymentStatus(status).label;
};
