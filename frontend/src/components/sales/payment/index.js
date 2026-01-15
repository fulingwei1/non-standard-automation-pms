/**
 * Payment Management Components - 统一导出入口
 * 支付管理相关组件的集中导出
 */

// ==================== 常量配置 ====================
export {
  PAYMENT_TYPES,
  PAYMENT_STATUS,
  VIEW_MODES,
  FILTER_OPTIONS,
  AGING_BUCKETS,
  getPaymentType,
  getPaymentStatus,
  getAgingBucket,
  formatPaymentAmount,
  formatPaymentDate,
  formatPaymentDateTime,
  calculateOverdueDays,
  getPaymentTypeLabel,
  getPaymentStatusLabel,
} from "./paymentConstants";

// ==================== 组件 ====================
export { default as PaymentFilters } from "./PaymentFilters";

// ==================== 待创建的组件 ====================
// export { default as PaymentReminders } from "./PaymentReminders";
// export { default as PaymentList } from "./PaymentList";
// export { default as PaymentCard } from "./PaymentCard";
// export { default as PaymentDetailDialog } from "./PaymentDetailDialog";
// export { default as InvoiceRequestDialog } from "./InvoiceRequestDialog";
// export { default as CollectionDialog } from "./CollectionDialog";

// ==================== 待创建的 Hooks ====================
// export { usePaymentData } from "./hooks/usePaymentData";
