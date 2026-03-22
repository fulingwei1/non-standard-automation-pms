/**
 * Finance Business Management Constants - 财务业务管理配置
 * 财务状态、类型、支付方式、预算类型、分类、标签、颜色等枚举和工具函数
 */
import {
  metricTypes, timePeriods, healthLevels, budgetStatuses, revenueTypes,
  costTypes, cashFlowTypes, chartTypes, metricCalculations, alertRules,
  tabConfigs, defaultFinanceData, formatCurrency, formatPercentage,
  getHealthLevel, getBudgetStatus, calculateTrend, validateFinanceData, filterDataByPeriod,
} from './dashboard.js';

// ==================== 枚举定义 ====================

export const FINANCE_STATUS = {
 PENDING: 'pending', APPROVED: 'approved', REJECTED: 'rejected',
 PAID: 'paid', OVERDUE: 'overdue', CANCELLED: 'cancelled'
};

export const FINANCE_TYPE = {
 INCOME: 'income', EXPENSE: 'expense', BUDGET: 'budget',
 INVOICE: 'invoice', PAYMENT: 'payment', REFUND: 'refund', TRANSFER: 'transfer'
};

export const PAYMENT_METHOD = {
 CASH: 'cash', BANK_TRANSFER: 'bank_transfer', CREDIT_CARD: 'credit_card',
 DEBIT_CARD: 'debit_card', DIGITAL_WALLET: 'digital_wallet',
 CHECK: 'check', ONLINE_PAYMENT: 'online_payment'
};

export const BUDGET_TYPE = {
 OPERATIONAL: 'operational', CAPITAL: 'capital', PROJECT: 'project',
 EMERGENCY: 'emergency', MAINTENANCE: 'maintenance', RESEARCH: 'research'
};

export const EXPENSE_CATEGORY = {
 SALARY: 'salary', RENT: 'rent', UTILITIES: 'utilities', MARKETING: 'marketing',
 EQUIPMENT: 'equipment', MATERIALS: 'materials', TRAVEL: 'travel', TRAINING: 'training',
 SOFTWARE: 'software', INSURANCE: 'insurance', TAXES: 'taxes', OTHER: 'other'
};

export const INCOME_CATEGORY = {
 SALES: 'sales', SERVICE: 'service', CONSULTING: 'consulting', RENTAL: 'rental',
 INTEREST: 'interest', DIVIDEND: 'dividend', COMMISSION: 'commission',
 ROYALTY: 'royalty', GRANT: 'grant', INVESTMENT: 'investment', OTHER: 'other'
};

export const PRIORITY_LEVEL = {
 LOW: 'low', MEDIUM: 'medium', HIGH: 'high', URGENT: 'urgent'
};

// ==================== 标签配置 ====================

export const FINANCE_STATUS_LABELS = {
 [FINANCE_STATUS.PENDING]: '待处理', [FINANCE_STATUS.APPROVED]: '已批准',
 [FINANCE_STATUS.REJECTED]: '已拒绝', [FINANCE_STATUS.PAID]: '已支付',
 [FINANCE_STATUS.OVERDUE]: '逾期', [FINANCE_STATUS.CANCELLED]: '已取消'
};

export const FINANCE_TYPE_LABELS = {
 [FINANCE_TYPE.INCOME]: '收入', [FINANCE_TYPE.EXPENSE]: '支出',
 [FINANCE_TYPE.BUDGET]: '预算', [FINANCE_TYPE.INVOICE]: '发票',
 [FINANCE_TYPE.PAYMENT]: '付款', [FINANCE_TYPE.REFUND]: '退款',
 [FINANCE_TYPE.TRANSFER]: '转账'
};

export const PAYMENT_METHOD_LABELS = {
 [PAYMENT_METHOD.CASH]: '现金', [PAYMENT_METHOD.BANK_TRANSFER]: '银行转账',
 [PAYMENT_METHOD.CREDIT_CARD]: '信用卡', [PAYMENT_METHOD.DEBIT_CARD]: '借记卡',
 [PAYMENT_METHOD.DIGITAL_WALLET]: '数字钱包', [PAYMENT_METHOD.CHECK]: '支票',
  [PAYMENT_METHOD.ONLINE_PAYMENT]: '在线支付'
};

export const BUDGET_TYPE_LABELS = {
 [BUDGET_TYPE.OPERATIONAL]: '运营预算', [BUDGET_TYPE.CAPITAL]: '资本预算',
 [BUDGET_TYPE.PROJECT]: '项目预算', [BUDGET_TYPE.EMERGENCY]: '应急预算',
 [BUDGET_TYPE.MAINTENANCE]: '维护预算', [BUDGET_TYPE.RESEARCH]: '研发预算'
};

export const EXPENSE_CATEGORY_LABELS = {
 [EXPENSE_CATEGORY.SALARY]: '工资', [EXPENSE_CATEGORY.RENT]: '租金',
 [EXPENSE_CATEGORY.UTILITIES]: '水电费', [EXPENSE_CATEGORY.MARKETING]: '营销',
 [EXPENSE_CATEGORY.EQUIPMENT]: '设备', [EXPENSE_CATEGORY.MATERIALS]: '材料',
 [EXPENSE_CATEGORY.TRAVEL]: '差旅', [EXPENSE_CATEGORY.TRAINING]: '培训',
 [EXPENSE_CATEGORY.SOFTWARE]: '软件', [EXPENSE_CATEGORY.INSURANCE]: '保险',
 [EXPENSE_CATEGORY.TAXES]: '税费', [EXPENSE_CATEGORY.OTHER]: '其他'
};

export const INCOME_CATEGORY_LABELS = {
  [INCOME_CATEGORY.SALES]: '销售收入', [INCOME_CATEGORY.SERVICE]: '服务收入',
  [INCOME_CATEGORY.CONSULTING]: '咨询收入', [INCOME_CATEGORY.RENTAL]: '租赁收入',
 [INCOME_CATEGORY.INTEREST]: '利息收入', [INCOME_CATEGORY.DIVIDEND]: '股息收入',
 [INCOME_CATEGORY.COMMISSION]: '佣金收入', [INCOME_CATEGORY.ROYALTY]: '版权收入',
  [INCOME_CATEGORY.GRANT]: '补助金', [INCOME_CATEGORY.INVESTMENT]: '投资收益',
 [INCOME_CATEGORY.OTHER]: '其他'
};

export const PRIORITY_LEVEL_LABELS = {
  [PRIORITY_LEVEL.LOW]: '低优先级', [PRIORITY_LEVEL.MEDIUM]: '中优先级',
 [PRIORITY_LEVEL.HIGH]: '高优先级', [PRIORITY_LEVEL.URGENT]: '紧急'
};

// ==================== 状态颜色配置 ====================

export const FINANCE_STATUS_COLORS = {
 [FINANCE_STATUS.PENDING]: '#F59E0B', [FINANCE_STATUS.APPROVED]: '#10B981',
 [FINANCE_STATUS.REJECTED]: '#EF4444', [FINANCE_STATUS.PAID]: '#059669',
 [FINANCE_STATUS.OVERDUE]: '#DC2626', [FINANCE_STATUS.CANCELLED]: '#6B7280'
};

export const FINANCE_TYPE_COLORS = {
 [FINANCE_TYPE.INCOME]: '#10B981', [FINANCE_TYPE.EXPENSE]: '#EF4444',
 [FINANCE_TYPE.BUDGET]: '#3B82F6', [FINANCE_TYPE.INVOICE]: '#8B5CF6',
  [FINANCE_TYPE.PAYMENT]: '#F59E0B', [FINANCE_TYPE.REFUND]: '#EC4899',
 [FINANCE_TYPE.TRANSFER]: '#6B7280'
};

export const PRIORITY_COLORS = {
 [PRIORITY_LEVEL.LOW]: '#10B981', [PRIORITY_LEVEL.MEDIUM]: '#F59E0B',
  [PRIORITY_LEVEL.HIGH]: '#EF4444', [PRIORITY_LEVEL.URGENT]: '#DC2626'
};

export const FINANCE_STATS_CONFIG = {
 TOTAL_INCOME: 'total_income', TOTAL_EXPENSE: 'total_expense',
 NET_PROFIT: 'net_profit', BUDGET_UTILIZATION: 'budget_utilization',
 PENDING_APPROVALS: 'pending_approvals', OVERDUE_PAYMENTS: 'overdue_payments'
};

// ==================== 业务标签获取函数 ====================

export const getFinanceStatusLabel = (status) => FINANCE_STATUS_LABELS[status] || status;
export const getFinanceTypeLabel = (type) => FINANCE_TYPE_LABELS[type] || type;
export const getPaymentMethodLabel = (method) => PAYMENT_METHOD_LABELS[method] || method;
export const getBudgetTypeLabel = (type) => BUDGET_TYPE_LABELS[type] || type;
export const getExpenseCategoryLabel = (category) => EXPENSE_CATEGORY_LABELS[category] || category;
export const getIncomeCategoryLabel = (category) => INCOME_CATEGORY_LABELS[category] || category;
export const getPriorityLevelLabel = (priority) => PRIORITY_LEVEL_LABELS[priority] || priority;
export const getFinanceStatusColor = (status) => FINANCE_STATUS_COLORS[status] || '#6B7280';
export const getFinanceTypeColor = (type) => FINANCE_TYPE_COLORS[type] || '#6B7280';
export const getPriorityColor = (priority) => PRIORITY_COLORS[priority] || '#6B7280';

// 计算净利润
export const calculateNetProfit = (income, expenses) => income - expenses;

// 计算预算使用率（百分比）
export const calculateBudgetUtilization = (spent, budget) => {
 if (!budget || budget === 0) {return 0;}
 return Math.round((spent / budget) * 100);
};

// 统计各状态的交易数量
export const getFinanceStatusStats = (transactions) => {
 const stats = { total: transactions.length, pending: 0, approved: 0, rejected: 0, paid: 0, overdue: 0, cancelled: 0 };
 transactions.forEach(transaction => {
  switch (transaction.status) {
  case FINANCE_STATUS.PENDING: stats.pending++; break;
  case FINANCE_STATUS.APPROVED: stats.approved++; break;
   case FINANCE_STATUS.REJECTED: stats.rejected++; break;
 case FINANCE_STATUS.PAID: stats.paid++; break;
  case FINANCE_STATUS.OVERDUE: stats.overdue++; break;
 case FINANCE_STATUS.CANCELLED: stats.cancelled++; break;
  }
 });
 return stats;
};

// 汇总收支统计
export const getIncomeExpenseStats = (transactions) => {
 let totalIncome = 0;
 let totalExpenses = 0;
 transactions.forEach(transaction => {
  const amount = parseFloat(transaction.amount) || 0;
 if (transaction.type === FINANCE_TYPE.INCOME) { totalIncome += amount; }
 else if (transaction.type === FINANCE_TYPE.EXPENSE) { totalExpenses += amount; }
 });
 return { totalIncome, totalExpenses, netProfit: calculateNetProfit(totalIncome, totalExpenses) };
};

// 获取逾期付款列表
export const getOverduePayments = (transactions) => {
 const today = new Date();
 return transactions.filter(transaction => {
 if (transaction.status === FINANCE_STATUS.PAID || transaction.status === FINANCE_STATUS.CANCELLED) { return false; }
  if (!transaction.due_date) {return false;}
 const dueDate = new Date(transaction.due_date);
  return dueDate < today;
 });
};

// 获取待审批列表
export const getPendingApprovals = (transactions) => {
 return transactions.filter(transaction => transaction.status === FINANCE_STATUS.PENDING);
};

// 验证财务表单数据
export const validateFinanceFormData = (financeData) => {
 const errors = [];
  if (!financeData.amount || parseFloat(financeData.amount) <= 0) { errors.push('金额必须大于0'); }
 if (!financeData.type) { errors.push('财务类型不能为空'); }
 if (!financeData.category) { errors.push('分类不能为空'); }
 if (!financeData.date) { errors.push('日期不能为空'); }
 return { isValid: errors.length === 0, errors };
};

// ==================== 筛选选项 ====================

export const STATUS_FILTER_OPTIONS = [
 { value: 'all', label: '全部状态' },
  { value: FINANCE_STATUS.PENDING, label: '待处理' },
 { value: FINANCE_STATUS.APPROVED, label: '已批准' },
 { value: FINANCE_STATUS.REJECTED, label: '已拒绝' },
 { value: FINANCE_STATUS.PAID, label: '已支付' },
  { value: FINANCE_STATUS.OVERDUE, label: '逾期' },
 { value: FINANCE_STATUS.CANCELLED, label: '已取消' }
];

export const TYPE_FILTER_OPTIONS = [
 { value: 'all', label: '全部类型' },
  { value: FINANCE_TYPE.INCOME, label: '收入' },
 { value: FINANCE_TYPE.EXPENSE, label: '支出' },
 { value: FINANCE_TYPE.BUDGET, label: '预算' },
 { value: FINANCE_TYPE.INVOICE, label: '发票' },
 { value: FINANCE_TYPE.PAYMENT, label: '付款' },
 { value: FINANCE_TYPE.REFUND, label: '退款' },
  { value: FINANCE_TYPE.TRANSFER, label: '转账' }
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
 { value: PRIORITY_LEVEL.LOW, label: '低优先级' },
 { value: PRIORITY_LEVEL.MEDIUM, label: '中优先级' },
 { value: PRIORITY_LEVEL.HIGH, label: '高优先级' },
 { value: PRIORITY_LEVEL.URGENT, label: '紧急' }
];

export const DEFAULT_FINANCE_CONFIG = {
 status: FINANCE_STATUS.PENDING,
 type: FINANCE_TYPE.EXPENSE,
 priority: PRIORITY_LEVEL.MEDIUM,
 paymentMethod: PAYMENT_METHOD.BANK_TRANSFER
};

// FINANCE_DASHBOARD_DEFAULT 聚合了仪表板和业务管理的所有常量，供整体导出使用
export const FINANCE_DASHBOARD_DEFAULT = {
 metricTypes, timePeriods, healthLevels, budgetStatuses, revenueTypes,
 costTypes, cashFlowTypes, chartTypes, metricCalculations, alertRules,
 tabConfigs, defaultFinanceData, formatCurrency, formatPercentage,
 getHealthLevel, getBudgetStatus, calculateTrend, validateFinanceData, filterDataByPeriod,
 FINANCE_STATUS, FINANCE_TYPE, PAYMENT_METHOD, BUDGET_TYPE,
 EXPENSE_CATEGORY, INCOME_CATEGORY, PRIORITY_LEVEL,
 FINANCE_STATUS_LABELS, FINANCE_TYPE_LABELS, PAYMENT_METHOD_LABELS,
 BUDGET_TYPE_LABELS, EXPENSE_CATEGORY_LABELS, INCOME_CATEGORY_LABELS,
 PRIORITY_LEVEL_LABELS, FINANCE_STATUS_COLORS, FINANCE_TYPE_COLORS,
 PRIORITY_COLORS, FINANCE_STATS_CONFIG,
 getFinanceStatusLabel, getFinanceTypeLabel, getPaymentMethodLabel,
 getBudgetTypeLabel, getExpenseCategoryLabel, getIncomeCategoryLabel,
 getPriorityLevelLabel, getFinanceStatusColor, getFinanceTypeColor,
 getPriorityColor, calculateNetProfit, calculateBudgetUtilization,
 getFinanceStatusStats, getIncomeExpenseStats, getOverduePayments,
 getPendingApprovals, validateFinanceFormData,
 STATUS_FILTER_OPTIONS, TYPE_FILTER_OPTIONS, PRIORITY_FILTER_OPTIONS,
 DEFAULT_FINANCE_CONFIG,
};
