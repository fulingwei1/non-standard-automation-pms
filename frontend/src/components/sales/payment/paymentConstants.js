/**
 * Payment Management Constants (legacy path)
 * 支付管理相关常量配置
 *
 * [DEPRECATED] Re-export shim for backward compatibility.
 * Canonical source: components/payment-management/paymentManagementConstants.js
 */

import {
  PAYMENT_TYPES as CANON_PAYMENT_TYPES,
  PAYMENT_STATUS as CANON_PAYMENT_STATUS,
  VIEW_MODES,
  FILTER_OPTIONS,
  AGING_BUCKETS,
  getAgingBucket,
  formatPaymentAmount,
  formatPaymentDate,
  formatPaymentDateTime,
  calculateOverdueDays,
  getPaymentTypeLabel,
  getPaymentStatusLabel,
} from "../../payment-management/paymentManagementConstants";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  DollarSign,
  TrendingUp,
} from "lucide-react";

const legacyTypeKeys = ["deposit", "progress", "delivery", "acceptance", "warranty"];
const legacyStatusKeys = ["paid", "pending", "overdue", "invoiced"];

const typeIcons = {
  deposit: DollarSign,
  progress: TrendingUp,
  delivery: FileText,
  acceptance: CheckCircle2,
  warranty: Clock,
};

const statusIcons = {
  paid: CheckCircle2,
  pending: Clock,
  overdue: AlertTriangle,
  invoiced: FileText,
};

const statusValues = {
  paid: "PAID",
  pending: "PENDING",
  overdue: "OVERDUE",
  invoiced: "INVOICED",
};

const canonicalTypesByKey = Object.values(CANON_PAYMENT_TYPES).reduce((acc, type) => {
  if (type?.key) {
    acc[type.key] = type;
  }
  return acc;
}, {});

const canonicalStatusByKey = Object.values(CANON_PAYMENT_STATUS).reduce((acc, status) => {
  if (status?.key) {
    acc[status.key] = status;
  }
  return acc;
}, {});

// ==================== 支付类型配置 ====================
export const PAYMENT_TYPES = legacyTypeKeys.reduce((acc, key) => {
  const type = canonicalTypesByKey[key];
  if (!type) {
    return acc;
  }
  acc[key] = {
    label: type.label,
    color: type.color,
    textColor: type.textColor,
    bgColor: type.bgColor,
    borderColor: type.borderColor,
    ratio: type.ratio,
    icon: typeIcons[key],
  };
  return acc;
}, {});

// ==================== 支付状态配置 ====================
export const PAYMENT_STATUS = legacyStatusKeys.reduce((acc, key) => {
  const status = canonicalStatusByKey[key];
  if (!status) {
    return acc;
  }
  acc[key] = {
    label: status.label,
    color: status.color,
    textColor: status.textColor,
    bgColor: status.bgColor,
    borderColor: status.borderColor,
    icon: statusIcons[key],
    value: statusValues[key],
  };
  return acc;
}, {});

// ==================== 视图模式配置 ====================
export { VIEW_MODES };

// ==================== 筛选选项 ====================
export { FILTER_OPTIONS };

// ==================== 账龄分组配置 ====================
export { AGING_BUCKETS };

// ==================== 工具函数 ====================
export const getPaymentType = (type) => {
  return PAYMENT_TYPES[type] || PAYMENT_TYPES.deposit;
};

export const getPaymentStatus = (status) => {
  const statusKey = status?.toLowerCase();
  return PAYMENT_STATUS[statusKey] || PAYMENT_STATUS.pending;
};

export {
  getAgingBucket,
  formatPaymentAmount,
  formatPaymentDate,
  formatPaymentDateTime,
  calculateOverdueDays,
  getPaymentTypeLabel,
  getPaymentStatusLabel,
};
