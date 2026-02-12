/**
 * Finance Constants - 财务模块常量配置（单一数据源）
 * 包含发票、付款等财务相关常量
 *
 * ARCHITECTURE NOTE:
 * This is the SINGLE SOURCE OF TRUTH for all invoice/finance constants.
 * Both pages/invoice/constants.js and components/invoice-management/constants.js
 * re-export from this file. Do NOT duplicate these values elsewhere.
 */
import { FileText, Clock, Check, X, AlertTriangle, TrendingUp } from "lucide-react";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";

// Invoice status mapping (API -> UI)
export const statusMap = {
  DRAFT: "draft",
  APPLIED: "applied",
  APPROVED: "approved",
  ISSUED: "issued",
  VOID: "void"
};

// Payment status mapping (API -> UI)
export const paymentStatusMap = {
  PENDING: "pending",
  PARTIAL: "partial",
  PAID: "paid",
  OVERDUE: "overdue"
};

// Invoice status configuration
export const statusConfig = {
  draft: {
    label: "草稿",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText
  },
  applied: {
    label: "申请中",
    color: "bg-blue-500/20 text-blue-400",
    icon: Clock
  },
  approved: {
    label: "已批准",
    color: "bg-purple-500/20 text-purple-400",
    icon: Check
  },
  issued: {
    label: "已开票",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  void: { 
    label: "作废", 
    color: "bg-red-500/20 text-red-400", 
    icon: X 
  }
};

// Payment status configuration
export const paymentStatusConfig = {
  pending: {
    label: "未收款",
    color: "bg-slate-500/20 text-slate-400",
    icon: Clock
  },
  partial: {
    label: "部分收款",
    color: "bg-amber-500/20 text-amber-400",
    icon: TrendingUp
  },
  paid: {
    label: "已收款",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle
  }
};

// Default form data
export const defaultFormData = {
  contract_id: "",
  invoice_type: "SPECIAL",
  amount: "",
  tax_rate: "13",
  issue_date: "",
  due_date: "",
  remark: ""
};

// Default issue data
export const defaultIssueData = {
  invoice_no: "",
  issue_date: new Date().toISOString().split("T")[0],
  remark: ""
};

// Default payment data
export const defaultPaymentData = {
  paid_amount: "",
  paid_date: new Date().toISOString().split("T")[0],
  remark: ""
};

// === Migrated from components/finance-dashboard/financeDashboardConstants.js ===
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
export { formatCurrency };

export const formatPercentage = (value, decimals = 1) => {
 if (value === null || value === undefined) {return '-';}
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

// === Migrated from components/payment-management/paymentManagementConstants.js ===
/**
 * 💰 支付管理系统 - 配置常量
 * 支付类型、状态、账龄分析、催收等核心配置
 */

// ==================== 支付类型配置 ====================

export const PAYMENT_TYPES = {
  DEPOSIT: {
    key: 'deposit',
    label: '签约款',
    description: '合同签订时的首付款',
    ratio: '30%',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'DollarSign',
    priority: 1,
    dueDays: 7,
    taxable: true
  },
  PROGRESS: {
    key: 'progress',
    label: '进度款',
    description: '按项目进度支付的款项',
    ratio: '40%',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'TrendingUp',
    priority: 2,
    dueDays: 15,
    taxable: true
  },
  DELIVERY: {
    key: 'delivery',
    label: '发货款',
    description: '产品发货后的付款',
    ratio: '20%',
    color: 'bg-purple-500',
    textColor: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    icon: 'Truck',
    priority: 3,
    dueDays: 10,
    taxable: true
  },
  ACCEPTANCE: {
    key: 'acceptance',
    label: '验收款',
    description: '项目验收合格后的付款',
    ratio: '5%',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: 'CheckCircle2',
    priority: 4,
    dueDays: 7,
    taxable: true
  },
  WARRANTY: {
    key: 'warranty',
    label: '质保金',
    description: '质量保证金，质保期满后退还',
    ratio: '5%',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: 'Shield',
    priority: 5,
    dueDays: 30,
    taxable: false
  }
};

export const PAYMENT_TYPE_OPTIONS = Object.values(PAYMENT_TYPES);

// ==================== 支付状态配置 ====================

export const PAYMENT_STATUS = {
  PAID: {
    key: 'paid',
    label: '已到账',
    description: '款项已收到',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: 'CheckCircle2',
    canEdit: false,
    canCancel: false,
    nextActions: []
  },
  PENDING: {
    key: 'pending',
    label: '待收款',
    description: '等待客户付款',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'Clock',
    canEdit: true,
    canCancel: true,
    nextActions: ['send_reminder', 'apply_invoice', 'mark_paid']
  },
  OVERDUE: {
    key: 'overdue',
    label: '已逾期',
    description: '付款已超过截止日期',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    icon: 'AlertTriangle',
    canEdit: true,
    canCancel: false,
    nextActions: ['send_urgent_reminder', 'escalate', 'legal_action']
  },
  INVOICED: {
    key: 'invoiced',
    label: '已开票',
    description: '发票已开出，等待付款',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'FileText',
    canEdit: true,
    canCancel: true,
    nextActions: ['send_invoice', 'follow_up', 'mark_paid']
  },
  CANCELLED: {
    key: 'cancelled',
    label: '已取消',
    description: '支付已取消',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: 'X',
    canEdit: false,
    canCancel: false,
    nextActions: []
  }
};

export const PAYMENT_STATUS_OPTIONS = Object.values(PAYMENT_STATUS);

// ==================== 发票状态配置 ====================

export const INVOICE_STATUS = {
  DRAFT: {
    key: 'draft',
    label: '草稿',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    icon: 'FileText'
  },
  ISSUED: {
    key: 'issued',
    label: '已开具',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    icon: 'Send'
  },
  SENT: {
    key: 'sent',
    label: '已发送',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    icon: 'Mail'
  },
  PAID: {
    key: 'paid',
    label: '已付款',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    icon: 'CheckCircle2'
  },
  CANCELLED: {
    key: 'cancelled',
    label: '已作废',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    icon: 'X'
  }
};

export const INVOICE_STATUS_OPTIONS = Object.values(INVOICE_STATUS);

// ==================== 账龄分析配置 ====================

export const AGING_PERIODS = {
  CURRENT: {
    key: 'current',
    label: '当前',
    minDays: 0,
    maxDays: 0,
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    riskLevel: 'low'
  },
  DAYS_1_30: {
    key: 'days_1_30',
    label: '1-30天',
    minDays: 1,
    maxDays: 30,
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    riskLevel: 'low'
  },
  DAYS_31_60: {
    key: 'days_31_60',
    label: '31-60天',
    minDays: 31,
    maxDays: 60,
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    riskLevel: 'medium'
  },
  DAYS_61_90: {
    key: 'days_61_90',
    label: '61-90天',
    minDays: 61,
    maxDays: 90,
    color: 'bg-orange-500',
    textColor: 'text-orange-400',
    riskLevel: 'high'
  },
  DAYS_OVER_90: {
    key: 'days_over_90',
    label: '90天以上',
    minDays: 91,
    maxDays: 999,
    color: 'bg-red-500',
    textColor: 'text-red-400',
    riskLevel: 'critical'
  }
};

export const AGING_PERIOD_OPTIONS = Object.values(AGING_PERIODS);

// ==================== 催收级别配置 ====================

export const COLLECTION_LEVELS = {
  NORMAL: {
    key: 'normal',
    label: '正常',
    description: '按正常流程催收',
    interval: 7, // 天
    methods: ['email', 'phone'],
    template: 'normal_reminder',
    priority: 'low'
  },
  WARNING: {
    key: 'warning',
    label: '预警',
    description: '需要重点关注',
    interval: 3,
    methods: ['email', 'phone', 'sms'],
    template: 'warning_reminder',
    priority: 'medium'
  },
  URGENT: {
    key: 'urgent',
    label: '紧急',
    description: '需要立即处理',
    interval: 1,
    methods: ['phone', 'sms', 'visit'],
    template: 'urgent_reminder',
    priority: 'high'
  },
  CRITICAL: {
    key: 'critical',
    label: '严重',
    description: '需要升级处理',
    interval: 0,
    methods: ['legal', 'management'],
    template: 'critical_reminder',
    priority: 'critical'
  }
};

export const COLLECTION_LEVEL_OPTIONS = Object.values(COLLECTION_LEVELS);

// ==================== 催收方式配置 ====================

export const COLLECTION_METHODS = {
  EMAIL: {
    key: 'email',
    label: '邮件',
    icon: 'Mail',
    cost: 0.1,
    effectiveness: 0.6,
    description: '发送催收邮件'
  },
  PHONE: {
    key: 'phone',
    label: '电话',
    icon: 'Phone',
    cost: 2.0,
    effectiveness: 0.8,
    description: '电话催收'
  },
  SMS: {
    key: 'sms',
    label: '短信',
    icon: 'MessageSquare',
    cost: 0.5,
    effectiveness: 0.7,
    description: '发送催收短信'
  },
  LETTER: {
    key: 'letter',
    label: '信函',
    icon: 'FileText',
    cost: 5.0,
    effectiveness: 0.9,
    description: '发送催收函'
  },
  VISIT: {
    key: 'visit',
    label: '上门',
    icon: 'Users',
    cost: 50.0,
    effectiveness: 0.95,
    description: '上门催收'
  },
  LEGAL: {
    key: 'legal',
    label: '法律',
    icon: 'Scale',
    cost: 1000.0,
    effectiveness: 0.98,
    description: '法律途径催收'
  }
};

export const COLLECTION_METHOD_OPTIONS = Object.values(COLLECTION_METHODS);

// ==================== 支付方式配置 ====================

export const PAYMENT_METHODS = {
  CASH: {
    key: 'cash',
    label: '现金',
    icon: 'Banknote',
    fee: 0,
    description: '现金支付',
    receiptRequired: true
  },
  BANK_TRANSFER: {
    key: 'bank_transfer',
    label: '银行转账',
    icon: 'Building2',
    fee: 0.005,
    description: '银行转账',
    receiptRequired: true
  },
  CHECK: {
    key: 'check',
    label: '支票',
    icon: 'FileText',
    fee: 0.001,
    description: '支票支付',
    receiptRequired: true
  },
  CREDIT_CARD: {
    key: 'credit_card',
    label: '信用卡',
    icon: 'CreditCard',
    fee: 0.025,
    description: '信用卡支付',
    receiptRequired: false
  },
  ALIPAY: {
    key: 'alipay',
    label: '支付宝',
    icon: 'Smartphone',
    fee: 0.006,
    description: '支付宝支付',
    receiptRequired: false
  },
  WECHAT: {
    key: 'wechat',
    label: '微信',
    icon: 'MessageSquare',
    fee: 0.006,
    description: '微信支付',
    receiptRequired: false
  },
  OTHER: {
    key: 'other',
    label: '其他',
    icon: 'MoreHorizontal',
    fee: 0,
    description: '其他支付方式',
    receiptRequired: true
  }
};

export const PAYMENT_METHOD_OPTIONS = Object.values(PAYMENT_METHODS);

// ==================== 客户信用等级配置 ====================

export const CREDIT_RATINGS = {
  AAA: {
    key: 'AAA',
    label: 'AAA级',
    description: '信用极佳',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    creditLimit: 1000000,
    paymentTerms: 30,
    riskLevel: 'very_low'
  },
  AA: {
    key: 'AA',
    label: 'AA级',
    description: '信用优秀',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    creditLimit: 500000,
    paymentTerms: 30,
    riskLevel: 'low'
  },
  A: {
    key: 'A',
    label: 'A级',
    description: '信用良好',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    creditLimit: 200000,
    paymentTerms: 30,
    riskLevel: 'medium'
  },
  BBB: {
    key: 'BBB',
    label: 'BBB级',
    description: '信用一般',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    creditLimit: 100000,
    paymentTerms: 15,
    riskLevel: 'medium_high'
  },
  BB: {
    key: 'BB',
    label: 'BB级',
    description: '信用较差',
    color: 'bg-orange-500',
    textColor: 'text-orange-400',
    creditLimit: 50000,
    paymentTerms: 7,
    riskLevel: 'high'
  },
  B: {
    key: 'B',
    label: 'B级',
    description: '信用差',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    creditLimit: 10000,
    paymentTerms: 0,
    riskLevel: 'very_high'
  }
};

export const CREDIT_RATING_OPTIONS = Object.values(CREDIT_RATINGS);

// ==================== 统计指标配置 ====================

export const PAYMENT_METRICS = {
  TOTAL_RECEIVABLES: {
    key: 'total_receivables',
    label: '应收账款总额',
    unit: '¥',
    format: 'currency',
    description: '所有未收款项的总和'
  },
  OVERDUE_AMOUNT: {
    key: 'overdue_amount',
    label: '逾期金额',
    unit: '¥',
    format: 'currency',
    description: '已逾期的款项金额'
  },
  COLLECTION_RATE: {
    key: 'collection_rate',
    label: '回款率',
    unit: '%',
    format: 'percentage',
    description: '本期回款金额占总应收的比例'
  },
  DSO: {
    key: 'dso',
    label: 'DSO天数',
    unit: '天',
    format: 'number',
    description: '应收账款周转天数'
  },
  AGING_DAYS: {
    key: 'aging_days',
    label: '平均账龄',
    unit: '天',
    format: 'number',
    description: '应收账款的平均账龄'
  },
  INVOICE_COUNT: {
    key: 'invoice_count',
    label: '开票数量',
    unit: '张',
    format: 'number',
    description: '本期开具的发票数量'
  },
  COLLECTION_COUNT: {
    key: 'collection_count',
    label: '催收次数',
    unit: '次',
    format: 'number',
    description: '本期进行的催收操作次数'
  }
};

export const PAYMENT_METRIC_OPTIONS = Object.values(PAYMENT_METRICS);

// ==================== 提醒类型配置 ====================

export const REMINDER_TYPES = {
  DUE_DATE: {
    key: 'due_date',
    label: '到期提醒',
    description: '付款到期前提醒',
    daysBefore: [7, 3, 1],
    template: 'payment_due_reminder'
  },
  OVERDUE: {
    key: 'overdue',
    label: '逾期提醒',
    description: '付款逾期后提醒',
    daysAfter: [1, 7, 15, 30],
    template: 'payment_overdue_reminder'
  },
  INVOICE_ISSUED: {
    key: 'invoice_issued',
    label: '开票通知',
    description: '发票开具后通知',
    daysAfter: 1,
    template: 'invoice_issued_notification'
  },
  PAYMENT_RECEIVED: {
    key: 'payment_received',
    label: '收款确认',
    description: '收到付款后确认',
    daysAfter: 1,
    template: 'payment_received_confirmation'
  }
};

export const REMINDER_TYPE_OPTIONS = Object.values(REMINDER_TYPES);

// ==================== 工具函数 ====================

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

/**
 * 计算账龄
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

// ==================== 视图模式配置（来自 paymentConstants）====================

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

// ==================== 筛选选项配置（来自 paymentConstants）====================

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

// ==================== 账龄分组配置（来自 paymentConstants）====================

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

// ==================== 兼容工具函数（来自 paymentConstants）====================

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

// ==================== 默认导出 ====================

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
