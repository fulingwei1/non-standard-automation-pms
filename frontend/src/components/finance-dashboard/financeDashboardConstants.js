/**
 * Finance Dashboard Configuration Constants
 * 财务仪表板配置常量
 * 财务指标和图表配置定义
 *
 * This is the main finance constants file.
 * financeManagerConstants.js re-exports from this file.
 */

// 财务指标类型配置
export const metricTypes = {
 REVENUE: {
  label: "营业收入",
  color: "text-green-400",
 bgColor: "bg-green-500/10",
 borderColor: "border-green-500/20",
 icon: "💰",
  description: "公司总收入，包含产品销售和服务收入"
 },
  PROFIT: {
 label: "净利润",
  color: "text-emerald-400",
 bgColor: "bg-emerald-500/10",
 borderColor: "border-emerald-500/20",
 icon: "📈",
 description: "扣除所有成本和费用后的纯利润"
 },
 COST: {
  label: "总成本",
 color: "text-red-400",
 bgColor: "bg-red-500/10",
 borderColor: "border-red-500/20",
 icon: "💸",
 description: "包括生产成本、运营成本、管理费用等"
  },
 MARGIN: {
 label: "毛利率",
  color: "text-blue-400",
  bgColor: "bg-blue-500/10",
 borderColor: "border-blue-500/20",
 icon: "📊",
  description: "毛利占营业收入的百分比"
 },
 CASH_FLOW: {
  label: "现金流",
 color: "text-purple-400",
 bgColor: "bg-purple-500/10",
 borderColor: "border-purple-500/20",
 icon: "💧",
 description: "经营活动产生的现金流量净额"
 },
 ASSETS: {
  label: "总资产",
 color: "text-amber-400",
 bgColor: "bg-amber-500/10",
  borderColor: "border-amber-500/20",
 icon: "🏦",
  description: "公司拥有的所有资产总额"
 },
  LIABILITIES: {
  label: "总负债",
 color: "text-orange-400",
 bgColor: "bg-orange-500/10",
  borderColor: "border-orange-500/20",
 icon: "📋",
 description: "公司需要偿还的所有债务总额"
 },
  EQUITY: {
  label: "净资产",
 color: "text-cyan-400",
  bgColor: "bg-cyan-500/10",
  borderColor: "border-cyan-500/20",
 icon: "💎",
 description: "资产减去负债后的所有者权益"
 }
};

// 时间周期配置
export const timePeriods = {
 CURRENT_MONTH: { label: "本月", value: "month", days: 30, format: "YYYY-MM-DD" },
 LAST_MONTH: { label: "上月", value: "last_month", days: 30, format: "YYYY-MM-DD" },
  CURRENT_QUARTER: { label: "本季度", value: "quarter", days: 90, format: "YYYY-MM" },
  LAST_QUARTER: { label: "上季度", value: "last_quarter", days: 90, format: "YYYY-MM" },
 CURRENT_YEAR: { label: "本年度", value: "year", days: 365, format: "YYYY" },
 LAST_YEAR: { label: "上年度", value: "last_year", days: 365, format: "YYYY" },
 CUSTOM: { label: "自定义", value: "custom", days: null, format: "YYYY-MM-DD" }
};

// 财务健康度等级
export const healthLevels = {
 EXCELLENT: { label: "优秀", color: "text-green-400", bgColor: "bg-green-500/10", borderColor: "border-green-500/20", score: 90, description: "财务状况极佳，各项指标均达到最优" },
  GOOD: { label: "良好", color: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/20", score: 75, description: "财务状况良好，大部分指标达标" },
 FAIR: { label: "一般", color: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/20", score: 60, description: "财务状况一般，部分指标需要关注" },
 POOR: { label: "较差", color: "text-orange-400", bgColor: "bg-orange-500/10", borderColor: "border-orange-500/20", score: 45, description: "财务状况较差，多个指标需要改善" },
 CRITICAL: { label: "危险", color: "text-red-400", bgColor: "bg-red-500/10", borderColor: "border-red-500/20", score: 30, description: "财务状况危险，需要立即采取行动" }
};

// 预算状态配置
export const budgetStatuses = {
 ON_TRACK: { label: "正常", color: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/20", progress: 0, description: "预算执行正常，在计划范围内" },
 WARNING: { label: "预警", color: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/20", progress: 75, description: "预算接近上限，需要关注" },
 EXCEEDED: { label: "超支", color: "text-red-400", bgColor: "bg-red-500/10", borderColor: "border-red-500/20", progress: 100, description: "预算已超支，需要审批调整" },
 UNDERSPENT: { label: "节约", color: "text-blue-400", bgColor: "bg-blue-500/10", borderColor: "border-blue-500/20", progress: 50, description: "预算执行不足，可调整使用" }
};

// 收入类型配置
export const revenueTypes = {
 PRODUCT_SALES: { label: "产品销售", color: "text-green-400", percentage: 60, description: "自动化设备销售收入" },
 SERVICE_FEES: { label: "服务收入", color: "text-blue-400", percentage: 25, description: "技术服务、维修、培训等收入" },
 CONSULTING: { label: "咨询收入", color: "text-purple-400", percentage: 10, description: "技术咨询和方案设计收入" },
 OTHER: { label: "其他收入", color: "text-gray-400", percentage: 5, description: "利息、租金等其他收入" }
};

// 成本类型配置
export const costTypes = {
  MATERIAL_COST: { label: "材料成本", color: "text-red-400", percentage: 45, description: "原材料、零部件采购成本" },
  LABOR_COST: { label: "人工成本", color: "text-orange-400", percentage: 30, description: "生产人员、管理人员工资福利" },
 OVERHEAD: { label: "制造费用", color: "text-amber-400", percentage: 15, description: "厂房租金、设备折旧、水电等" },
 MARKETING: { label: "营销费用", color: "text-cyan-400", percentage: 10, description: "市场推广、广告、差旅等费用" }
};

// 现金流类型配置
export const cashFlowTypes = {
  OPERATING: { label: "经营活动现金流", color: "text-green-400", description: "主营业务产生的现金流量" },
 INVESTING: { label: "投资活动现金流", color: "text-blue-400", description: "投资和资产处置产生的现金流量" },
 FINANCING: { label: "筹资活动现金流", color: "text-purple-400", description: "融资和还款产生的现金流量" },
 NET: { label: "现金流量净额", color: "text-emerald-400", description: "所有活动现金流量净额" }
};

// 图表类型配置
export const chartTypes = {
 LINE: { label: "折线图", component: "LineChart", description: "展示趋势变化，适合时间序列数据" },
 BAR: { label: "柱状图", component: "BarChart", description: "对比不同类别的数值大小" },
 PIE: { label: "饼图", component: "PieChart", description: "展示部分与整体的关系" },
 AREA: { label: "面积图", component: "AreaChart", description: "展示总量和趋势，适合占比分析" },
 GAUGE: { label: "仪表图", component: "GaugeChart", description: "展示单个指标的完成度" },
 DUAL_AXES: { label: "双轴图", component: "DualAxesChart", description: "展示两个不同量级的指标" }
};

// 财务指标计算规则
export const metricCalculations = {
 grossProfit: (revenue, costOfGoodsSold) => revenue - costOfGoodsSold,
 grossMargin: (revenue, costOfGoodsSold) => revenue > 0 ? (revenue - costOfGoodsSold) / revenue * 100 : 0,
 netProfit: (revenue, totalExpenses) => revenue - totalExpenses,
 netMargin: (revenue, totalExpenses) => revenue > 0 ? (revenue - totalExpenses) / revenue * 100 : 0,
 currentRatio: (currentAssets, currentLiabilities) => currentLiabilities > 0 ? currentAssets / currentLiabilities : 0,
 debtToEquity: (totalDebt, totalEquity) => totalEquity > 0 ? totalDebt / totalEquity : 0,
 assetTurnover: (revenue, totalAssets) => totalAssets > 0 ? revenue / totalAssets : 0,
  inventoryTurnover: (costOfGoodsSold, averageInventory) => averageInventory > 0 ? costOfGoodsSold / averageInventory : 0
};

// 财务预警规则
export const alertRules = {
 lowCashFlow: { threshold: -100000, message: "现金流为负，需要关注资金状况", severity: "HIGH" },
 highDebtRatio: { threshold: 0.7, message: "负债率过高，存在财务风险", severity: "MEDIUM" },
 decliningRevenue: { threshold: -0.1, message: "收入连续下降，需要分析原因", severity: "MEDIUM" },
 highOperatingCost: { threshold: 0.8, message: "运营成本占比过高", severity: "LOW" },
 budgetOverrun: { threshold: 1.1, message: "预算执行超出10%", severity: "HIGH" }
};

// Tab 配置
export const tabConfigs = [
 { value: "overview", label: "财务概览", icon: "📊" },
 { value: "revenue", label: "收入分析", icon: "💰" },
 { value: "cost", label: "成本分析", icon: "💸" },
  { value: "cashflow", label: "现金流", icon: "💧" },
 { value: "budget", label: "预算管理", icon: "📋" },
 { value: "forecast", label: "财务预测", icon: "🔮" },
 { value: "reports", label: "财务报表", icon: "📑" },
 { value: "alerts", label: "财务预警", icon: "⚠️" },
];

// 默认财务数据
export const defaultFinanceData = {
 overview: { totalRevenue: 0, totalProfit: 0, totalCost: 0, grossMargin: 0, netMargin: 0, totalAssets: 0, totalLiabilities: 0, netEquity: 0, cashFlow: 0, healthScore: 0 },
 revenue: { byMonth: [], byType: [], byCustomer: [], growth: 0, target: 0, achievement: 0 },
 cost: { byMonth: [], byType: [], byDepartment: [], trend: 0, budget: 0, actual: 0 },
 cashflow: { byMonth: [], byType: [], operating: 0, investing: 0, financing: 0, net: 0 },
  budget: { departments: [], categories: [], variances: [], overallProgress: 0 },
 forecast: { revenue: [], profit: [], cashflow: [], accuracy: 0 },
 alerts: [],
 reports: []
};

// Re-export formatCurrency from unified formatters for backward compatibility
export { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

export const formatPercentage = (value, decimals = 2) => {
 return `${value.toFixed(decimals)}%`;
};

export const getHealthLevel = (score) => {
 if (score >= 90) {return healthLevels.EXCELLENT;}
 if (score >= 75) {return healthLevels.GOOD;}
 if (score >= 60) {return healthLevels.FAIR;}
 if (score >= 45) {return healthLevels.POOR;}
 return healthLevels.CRITICAL;
};

export const getBudgetStatus = (actual, budget) => {
 const ratio = budget > 0 ? actual / budget : 0;
 if (ratio >= 1.1) {return budgetStatuses.EXCEEDED;}
 if (ratio >= 0.9) {return budgetStatuses.WARNING;}
 if (ratio < 0.7) {return budgetStatuses.UNDERSPENT;}
 return budgetStatuses.ON_TRACK;
};

export const calculateTrend = (current, previous) => {
 if (previous === 0) {return 0;}
 return (current - previous) / previous * 100;
};

export const validateFinanceData = (data) => {
 return data && typeof data === 'object' && data.overview && data.revenue && data.cost && data.cashflow;
};

export const filterDataByPeriod = (data, period) => {
 const now = new Date();
 const startDate = new Date(now);

 switch (period.value) {
  case 'month': startDate.setMonth(now.getMonth() - 1); break;
  case 'quarter': startDate.setMonth(now.getMonth() - 3); break;
  case 'year': startDate.setFullYear(now.getFullYear() - 1); break;
 case 'last_month': startDate.setMonth(now.getMonth() - 2); now.setMonth(now.getMonth() - 1); break;
 case 'last_quarter': startDate.setMonth(now.getMonth() - 6); now.setMonth(now.getMonth() - 3); break;
  case 'last_year': startDate.setFullYear(now.getFullYear() - 2); now.setFullYear(now.getFullYear() - 1); break;
 default: break;
 }

 return data;
};

// ==================== 财务业务管理配置（来自 financeManagerConstants）====================

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

// 标签配置
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

// 状态颜色配置
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

// 业务标签获取函数
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

export const calculateNetProfit = (income, expenses) => income - expenses;

export const calculateBudgetUtilization = (spent, budget) => {
 if (!budget || budget === 0) {return 0;}
 return Math.round((spent / budget) * 100);
};

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

export const getOverduePayments = (transactions) => {
 const today = new Date();
 return transactions.filter(transaction => {
 if (transaction.status === FINANCE_STATUS.PAID || transaction.status === FINANCE_STATUS.CANCELLED) { return false; }
  if (!transaction.due_date) {return false;}
 const dueDate = new Date(transaction.due_date);
  return dueDate < today;
 });
};

export const getPendingApprovals = (transactions) => {
 return transactions.filter(transaction => transaction.status === FINANCE_STATUS.PENDING);
};

export const validateFinanceFormData = (financeData) => {
 const errors = [];
  if (!financeData.amount || parseFloat(financeData.amount) <= 0) { errors.push('金额必须大于0'); }
 if (!financeData.type) { errors.push('财务类型不能为空'); }
 if (!financeData.category) { errors.push('分类不能为空'); }
 if (!financeData.date) { errors.push('日期不能为空'); }
 return { isValid: errors.length === 0, errors };
};

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

export default {
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
