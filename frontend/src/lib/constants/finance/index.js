/**
 * Finance Constants - 财务模块常量配置（单一数据源）
 * 包含发票、付款等财务相关常量
 *
 * ARCHITECTURE NOTE:
 * This is the SINGLE SOURCE OF TRUTH for all invoice/finance constants.
 * Both pages/invoice/constants.js and components/invoice-management/constants.js
 * re-export from this file. Do NOT duplicate these values elsewhere.
 *
 * 本文件从拆分后的子模块重新导出所有常量，保持向后兼容。
 * 现有的 import { X } from '../lib/constants/finance' 无需修改。
 */

// === Invoice 发票相关 ===
export {
  statusMap,
  paymentStatusMap,
  statusConfig,
  paymentStatusConfig,
  defaultFormData,
  defaultIssueData,
  defaultPaymentData,
} from './invoice.js';

// === Dashboard 仪表板相关 ===
export {
  metricTypes,
  timePeriods,
  healthLevels,
  budgetStatuses,
  revenueTypes,
  costTypes,
  cashFlowTypes,
  chartTypes,
  metricCalculations,
  alertRules,
  tabConfigs,
  defaultFinanceData,
  formatCurrency,
  formatPercentage,
  getHealthLevel,
  getBudgetStatus,
  calculateTrend,
  validateFinanceData,
  filterDataByPeriod,
} from './dashboard.js';

// === Business 财务业务管理 ===
export {
  FINANCE_STATUS,
  FINANCE_TYPE,
  PAYMENT_METHOD,
  BUDGET_TYPE,
  EXPENSE_CATEGORY,
  INCOME_CATEGORY,
  PRIORITY_LEVEL,
  FINANCE_STATUS_LABELS,
  FINANCE_TYPE_LABELS,
  PAYMENT_METHOD_LABELS,
  BUDGET_TYPE_LABELS,
  EXPENSE_CATEGORY_LABELS,
  INCOME_CATEGORY_LABELS,
  PRIORITY_LEVEL_LABELS,
  FINANCE_STATUS_COLORS,
  FINANCE_TYPE_COLORS,
  PRIORITY_COLORS,
  FINANCE_STATS_CONFIG,
  getFinanceStatusLabel,
  getFinanceTypeLabel,
  getPaymentMethodLabel,
  getBudgetTypeLabel,
  getExpenseCategoryLabel,
  getIncomeCategoryLabel,
  getPriorityLevelLabel,
  getFinanceStatusColor,
  getFinanceTypeColor,
  getPriorityColor,
  calculateNetProfit,
  calculateBudgetUtilization,
  getFinanceStatusStats,
  getIncomeExpenseStats,
  getOverduePayments,
  getPendingApprovals,
  validateFinanceFormData,
  STATUS_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  DEFAULT_FINANCE_CONFIG,
  FINANCE_DASHBOARD_DEFAULT,
} from './business.js';

// === Payment 支付管理 ===
export {
  PAYMENT_TYPES,
  PAYMENT_TYPE_OPTIONS,
  PAYMENT_STATUS,
  PAYMENT_STATUS_OPTIONS,
  INVOICE_STATUS,
  INVOICE_STATUS_OPTIONS,
  AGING_PERIODS,
  AGING_PERIOD_OPTIONS,
  COLLECTION_LEVELS,
  COLLECTION_LEVEL_OPTIONS,
  COLLECTION_METHODS,
  COLLECTION_METHOD_OPTIONS,
  PAYMENT_METHODS,
  PAYMENT_METHOD_OPTIONS,
  CREDIT_RATINGS,
  CREDIT_RATING_OPTIONS,
  PAYMENT_METRICS,
  PAYMENT_METRIC_OPTIONS,
  REMINDER_TYPES,
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
  generateCollectionReport,
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
  PAYMENT_MANAGEMENT_DEFAULT,
} from './payment.js';
