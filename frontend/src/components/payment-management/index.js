/**
 * 💰 支付管理组件库
 * 统一导出所有支付管理相关组件和工具
 */

// 核心组件
export { default as PaymentStatsOverview } from './PaymentStatsOverview';
export { default as PaymentCard } from './PaymentCard';
export { default as PaymentTable } from './PaymentTable';
export { default as PaymentGrid } from './PaymentGrid';
export { default as PaymentFilters } from './PaymentFilters';
export { default as PaymentReminders } from './PaymentReminders';
export { default as AgingAnalysis } from './AgingAnalysis';

// 配置常量和工具
export {
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
  generateCollectionReport
} from '@/lib/constants/finance';

// 默认导出
export * as paymentManagementConstants from '@/lib/constants/finance';