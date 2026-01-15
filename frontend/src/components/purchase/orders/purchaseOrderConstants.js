/**
 * Purchase Order Constants - 采购订单管理常量配置
 * 包含：订单状态、紧急程度、格式化函数等
 */

import {
  FileText,
  Clock,
  Truck,
  CheckCircle2,
  AlertTriangle,
  Trash2,
} from "lucide-react";

// ==================== 订单状态配置 ====================
export const ORDER_STATUS = {
  draft: {
    label: "草稿",
    color: "bg-slate-500",
    textColor: "text-slate-400",
    bgColor: "bg-slate-500/10",
    borderColor: "border-slate-500/30",
    icon: FileText,
    value: "DRAFT",
  },
  pending: {
    label: "待收货",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
    icon: Clock,
    value: "PENDING",
  },
  partial_received: {
    label: "部分到货",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    icon: Truck,
    value: "PARTIAL_RECEIVED",
  },
  completed: {
    label: "已完成",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
    icon: CheckCircle2,
    value: "COMPLETED",
  },
  delayed: {
    label: "延期",
    color: "bg-red-500",
    textColor: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    icon: AlertTriangle,
    value: "DELAYED",
  },
  cancelled: {
    label: "已取消",
    color: "bg-slate-400",
    textColor: "text-slate-400",
    bgColor: "bg-slate-400/10",
    borderColor: "border-slate-400/30",
    icon: Trash2,
    value: "CANCELLED",
  },
};

// ==================== 紧急程度配置 ====================
export const ORDER_URGENCY = {
  normal: {
    label: "普通",
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
    borderColor: "border-slate-500/30",
    value: "NORMAL",
  },
  urgent: {
    label: "加急",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
    value: "URGENT",
  },
  critical: {
    label: "特急",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/30",
    value: "CRITICAL",
  },
};

// ==================== 筛选选项 ====================
export const ORDER_FILTER_OPTIONS = {
  status: [
    { value: "all", label: "全部状态" },
    { value: "draft", label: "草稿" },
    { value: "pending", label: "待收货" },
    { value: "partial_received", label: "部分到货" },
    { value: "completed", label: "已完成" },
    { value: "delayed", label: "延期" },
    { value: "cancelled", label: "已取消" },
  ],
  urgency: [
    { value: "all", label: "全部紧急程度" },
    { value: "normal", label: "普通" },
    { value: "urgent", label: "加急" },
    { value: "critical", label: "特急" },
  ],
};

// ==================== 工具函数 ====================

/**
 * 获取订单状态配置
 */
export const getOrderStatus = (status) => {
  return ORDER_STATUS[status] || ORDER_STATUS.draft;
};

/**
 * 获取紧急程度配置
 */
export const getOrderUrgency = (urgency) => {
  return ORDER_URGENCY[urgency] || ORDER_URGENCY.normal;
};

/**
 * 格式化订单金额
 */
export const formatOrderAmount = (amount) => {
  if (!amount && amount !== 0) return "¥0.00";
  const numAmount = Number(amount);
  if (numAmount >= 10000) {
    return `¥${(numAmount / 10000).toFixed(2)}万`;
  }
  return `¥${numAmount.toFixed(2)}`;
};

/**
 * 格式化订单日期
 */
export const formatOrderDate = (dateStr) => {
  if (!dateStr) return "--";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN");
};

/**
 * 格式化订单日期时间
 */
export const formatOrderDateTime = (dateStr) => {
  if (!dateStr) return "--";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN");
};

/**
 * 计算到货进度百分比
 */
export const calculateProgress = (receivedCount, itemCount) => {
  if (!itemCount || itemCount === 0) return 0;
  return Math.min(100, Math.round((receivedCount / itemCount) * 100));
};

/**
 * 获取订单状态标签
 */
export const getOrderStatusLabel = (status) => {
  return getOrderStatus(status).label;
};

/**
 * 获取紧急程度标签
 */
export const getUrgencyLabel = (urgency) => {
  return getOrderUrgency(urgency).label;
};

/**
 * 判断订单是否可编辑
 */
export const canEditOrder = (status) => {
  return ["draft", "pending"].includes(status);
};

/**
 * 判断订单是否可删除
 */
export const canDeleteOrder = (status) => {
  return status === "draft";
};

/**
 * 判断订单是否可提交
 */
export const canSubmitOrder = (status) => {
  return status === "draft";
};

/**
 * 判断订单是否可审批
 */
export const canApproveOrder = (status) => {
  return status === "pending";
};

/**
 * 判断订单是否可收货
 */
export const canReceiveOrder = (status) => {
  return ["pending", "partial_received"].includes(status);
};

/**
 * 获取进度条颜色
 */
export const getProgressColor = (status, progress) => {
  if (status === "completed") return "bg-emerald-500";
  if (status === "delayed") return "bg-red-500";
  if (progress >= 80) return "bg-emerald-500";
  if (progress >= 50) return "bg-blue-500";
  return "bg-amber-500";
};

/**
 * 计算延期天数
 */
export const calculateDelayDays = (expectedDate) => {
  if (!expectedDate) return 0;
  const expected = new Date(expectedDate);
  const now = new Date();
  const diffTime = now - expected;
  return Math.max(0, Math.floor(diffTime / (1000 * 60 * 60 * 24)));
};

/**
 * 判断是否延期
 */
export const isDelayed = (expectedDate, status) => {
  if (["completed", "cancelled"].includes(status)) return false;
  if (!expectedDate) return false;
  return calculateDelayDays(expectedDate) > 0;
};
