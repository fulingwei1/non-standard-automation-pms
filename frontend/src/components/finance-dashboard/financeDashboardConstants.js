/**
 * Finance Dashboard Configuration Constants
 * 财务仪表板配置常量
 * 财务指标和图表配置定义
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
  CURRENT_MONTH: {
    label: "本月",
    value: "month",
    days: 30,
    format: "YYYY-MM-DD"
  },
  LAST_MONTH: {
    label: "上月",
    value: "last_month",
    days: 30,
    format: "YYYY-MM-DD"
  },
  CURRENT_QUARTER: {
    label: "本季度",
    value: "quarter",
    days: 90,
    format: "YYYY-MM"
  },
  LAST_QUARTER: {
    label: "上季度",
    value: "last_quarter",
    days: 90,
    format: "YYYY-MM"
  },
  CURRENT_YEAR: {
    label: "本年度",
    value: "year",
    days: 365,
    format: "YYYY"
  },
  LAST_YEAR: {
    label: "上年度",
    value: "last_year",
    days: 365,
    format: "YYYY"
  },
  CUSTOM: {
    label: "自定义",
    value: "custom",
    days: null,
    format: "YYYY-MM-DD"
  }
};

// 财务健康度等级
export const healthLevels = {
  EXCELLENT: {
    label: "优秀",
    color: "text-green-400",
    bgColor: "bg-green-500/10",
    borderColor: "border-green-500/20",
    score: 90,
    description: "财务状况极佳，各项指标均达到最优"
  },
  GOOD: {
    label: "良好",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
    score: 75,
    description: "财务状况良好，大部分指标达标"
  },
  FAIR: {
    label: "一般",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
    score: 60,
    description: "财务状况一般，部分指标需要关注"
  },
  POOR: {
    label: "较差",
    color: "text-orange-400",
    bgColor: "bg-orange-500/10",
    borderColor: "border-orange-500/20",
    score: 45,
    description: "财务状况较差，多个指标需要改善"
  },
  CRITICAL: {
    label: "危险",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/20",
    score: 30,
    description: "财务状况危险，需要立即采取行动"
  }
};

// 预算状态配置
export const budgetStatuses = {
  ON_TRACK: {
    label: "正常",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
    progress: 0,
    description: "预算执行正常，在计划范围内"
  },
  WARNING: {
    label: "预警",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
    progress: 75,
    description: "预算接近上限，需要关注"
  },
  EXCEEDED: {
    label: "超支",
    color: "text-red-400",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/20",
    progress: 100,
    description: "预算已超支，需要审批调整"
  },
  UNDERSPENT: {
    label: "节约",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
    progress: 50,
    description: "预算执行不足，可调整使用"
  }
};

// 收入类型配置
export const revenueTypes = {
  PRODUCT_SALES: {
    label: "产品销售",
    color: "text-green-400",
    percentage: 60,
    description: "自动化设备销售收入"
  },
  SERVICE_FEES: {
    label: "服务收入",
    color: "text-blue-400",
    percentage: 25,
    description: "技术服务、维修、培训等收入"
  },
  CONSULTING: {
    label: "咨询收入",
    color: "text-purple-400",
    percentage: 10,
    description: "技术咨询和方案设计收入"
  },
  OTHER: {
    label: "其他收入",
    color: "text-gray-400",
    percentage: 5,
    description: "利息、租金等其他收入"
  }
};

// 成本类型配置
export const costTypes = {
  MATERIAL_COST: {
    label: "材料成本",
    color: "text-red-400",
    percentage: 45,
    description: "原材料、零部件采购成本"
  },
  LABOR_COST: {
    label: "人工成本",
    color: "text-orange-400",
    percentage: 30,
    description: "生产人员、管理人员工资福利"
  },
  OVERHEAD: {
    label: "制造费用",
    color: "text-amber-400",
    percentage: 15,
    description: "厂房租金、设备折旧、水电等"
  },
  MARKETING: {
    label: "营销费用",
    color: "text-cyan-400",
    percentage: 10,
    description: "市场推广、广告、差旅等费用"
  }
};

// 现金流类型配置
export const cashFlowTypes = {
  OPERATING: {
    label: "经营活动现金流",
    color: "text-green-400",
    description: "主营业务产生的现金流量"
  },
  INVESTING: {
    label: "投资活动现金流",
    color: "text-blue-400",
    description: "投资和资产处置产生的现金流量"
  },
  FINANCING: {
    label: "筹资活动现金流",
    color: "text-purple-400",
    description: "融资和还款产生的现金流量"
  },
  NET: {
    label: "现金流量净额",
    color: "text-emerald-400",
    description: "所有活动现金流量净额"
  }
};

// 图表类型配置
export const chartTypes = {
  LINE: {
    label: "折线图",
    component: "LineChart",
    description: "展示趋势变化，适合时间序列数据"
  },
  BAR: {
    label: "柱状图",
    component: "BarChart",
    description: "对比不同类别的数值大小"
  },
  PIE: {
    label: "饼图",
    component: "PieChart",
    description: "展示部分与整体的关系"
  },
  AREA: {
    label: "面积图",
    component: "AreaChart",
    description: "展示总量和趋势，适合占比分析"
  },
  GAUGE: {
    label: "仪表图",
    component: "GaugeChart",
    description: "展示单个指标的完成度"
  },
  DUAL_AXES: {
    label: "双轴图",
    component: "DualAxesChart",
    description: "展示两个不同量级的指标"
  }
};

// 财务指标计算规则
export const metricCalculations = {
  grossProfit: (revenue, costOfGoodsSold) => {
    return revenue - costOfGoodsSold;
  },
  grossMargin: (revenue, costOfGoodsSold) => {
    return revenue > 0 ? (revenue - costOfGoodsSold) / revenue * 100 : 0;
  },
  netProfit: (revenue, totalExpenses) => {
    return revenue - totalExpenses;
  },
  netMargin: (revenue, totalExpenses) => {
    return revenue > 0 ? (revenue - totalExpenses) / revenue * 100 : 0;
  },
  currentRatio: (currentAssets, currentLiabilities) => {
    return currentLiabilities > 0 ? currentAssets / currentLiabilities : 0;
  },
  debtToEquity: (totalDebt, totalEquity) => {
    return totalEquity > 0 ? totalDebt / totalEquity : 0;
  },
  assetTurnover: (revenue, totalAssets) => {
    return totalAssets > 0 ? revenue / totalAssets : 0;
  },
  inventoryTurnover: (costOfGoodsSold, averageInventory) => {
    return averageInventory > 0 ? costOfGoodsSold / averageInventory : 0;
  }
};

// 财务预警规则
export const alertRules = {
  lowCashFlow: {
    threshold: -100000,
    message: "现金流为负，需要关注资金状况",
    severity: "HIGH"
  },
  highDebtRatio: {
    threshold: 0.7,
    message: "负债率过高，存在财务风险",
    severity: "MEDIUM"
  },
  decliningRevenue: {
    threshold: -0.1,
    message: "收入连续下降，需要分析原因",
    severity: "MEDIUM"
  },
  highOperatingCost: {
    threshold: 0.8,
    message: "运营成本占比过高",
    severity: "LOW"
  },
  budgetOverrun: {
    threshold: 1.1,
    message: "预算执行超出10%",
    severity: "HIGH"
  }
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
{ value: "alerts", label: "财务预警", icon: "⚠️" }];


// 默认财务数据
export const defaultFinanceData = {
  overview: {
    totalRevenue: 0,
    totalProfit: 0,
    totalCost: 0,
    grossMargin: 0,
    netMargin: 0,
    totalAssets: 0,
    totalLiabilities: 0,
    netEquity: 0,
    cashFlow: 0,
    healthScore: 0
  },
  revenue: {
    byMonth: [],
    byType: [],
    byCustomer: [],
    growth: 0,
    target: 0,
    achievement: 0
  },
  cost: {
    byMonth: [],
    byType: [],
    byDepartment: [],
    trend: 0,
    budget: 0,
    actual: 0
  },
  cashflow: {
    byMonth: [],
    byType: [],
    operating: 0,
    investing: 0,
    financing: 0,
    net: 0
  },
  budget: {
    departments: [],
    categories: [],
    variances: [],
    overallProgress: 0
  },
  forecast: {
    revenue: [],
    profit: [],
    cashflow: [],
    accuracy: 0
  },
  alerts: [],
  reports: []
};

// 工具函数
export const formatCurrency = (value, _currency = 'CNY') => {
  if (value === 0) return '¥0';
  if (value >= 100000000) return `¥${(value / 100000000).toFixed(2)}亿`;
  if (value >= 10000) return `¥${(value / 10000).toFixed(2)}万`;
  return `¥${value.toLocaleString()}`;
};

export const formatPercentage = (value, decimals = 2) => {
  return `${value.toFixed(decimals)}%`;
};

export const getHealthLevel = (score) => {
  if (score >= 90) return healthLevels.EXCELLENT;
  if (score >= 75) return healthLevels.GOOD;
  if (score >= 60) return healthLevels.FAIR;
  if (score >= 45) return healthLevels.POOR;
  return healthLevels.CRITICAL;
};

export const getBudgetStatus = (actual, budget) => {
  const ratio = budget > 0 ? actual / budget : 0;
  if (ratio >= 1.1) return budgetStatuses.EXCEEDED;
  if (ratio >= 0.9) return budgetStatuses.WARNING;
  if (ratio < 0.7) return budgetStatuses.UNDERSPENT;
  return budgetStatuses.ON_TRACK;
};

export const calculateTrend = (current, previous) => {
  if (previous === 0) return 0;
  return (current - previous) / previous * 100;
};

export const validateFinanceData = (data) => {
  return data && typeof data === 'object' &&
  data.overview &&
  data.revenue &&
  data.cost &&
  data.cashflow;
};

export const filterDataByPeriod = (data, period) => {
  const now = new Date();
  const startDate = new Date(now);

  switch (period.value) {
    case 'month':
      startDate.setMonth(now.getMonth() - 1);
      break;
    case 'quarter':
      startDate.setMonth(now.getMonth() - 3);
      break;
    case 'year':
      startDate.setFullYear(now.getFullYear() - 1);
      break;
    case 'last_month':
      startDate.setMonth(now.getMonth() - 2);
      now.setMonth(now.getMonth() - 1);
      break;
    case 'last_quarter':
      startDate.setMonth(now.getMonth() - 6);
      now.setMonth(now.getMonth() - 3);
      break;
    case 'last_year':
      startDate.setFullYear(now.getFullYear() - 2);
      now.setFullYear(now.getFullYear() - 1);
      break;
    default:
      break;
  }

  // 这里应该根据实际数据过滤逻辑实现
  return data;
};

export default {
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
  filterDataByPeriod
};