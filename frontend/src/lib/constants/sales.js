/**
 * Sales Management Constants
 * 销售管理系统常量配置
 * 包含销售状态、阶段、类型、优先级等配置
 */

import { cn, formatDate, formatDateTime, formatCurrency } from "../utils";
import {
  formatCurrency as formatCurrencySymbol,
  formatCurrencyCompact
} from "../formatters";

export {
  cn,
  formatDate,
  formatDateTime,
  formatCurrency,
  formatCurrencySymbol,
  formatCurrencyCompact
};

// ==================== 销售成员状态配置 ====================
export const salesMemberStatusConfig = {
  active: {
    label: "在职",
    value: "active",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "CheckCircle2"
  },
  inactive: {
    label: "离职", 
    value: "inactive",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    icon: "XCircle"
  },
  probation: {
    label: "试用",
    value: "probation", 
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Clock"
  }
};

// ==================== 销售绩效等级配置 ====================
export const salesPerformanceLevelConfig = {
  excellent: {
    label: "优秀",
    value: "excellent",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    progress: "bg-emerald-500"
  },
  good: {
    label: "良好",
    value: "good", 
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    progress: "bg-blue-500"
  },
  average: {
    label: "一般",
    value: "average",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30", 
    progress: "bg-amber-500"
  },
  poor: {
    label: "待改进",
    value: "poor",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    progress: "bg-red-500"
  }
};

// ==================== 销售排名指标配置 ====================
export const salesRankingMetricsConfig = {
  revenue: {
    label: "销售业绩",
    key: "revenue",
    weight: 0.4,
    is_primary: true,
    data_source: "合同金额",
    format: "currency"
  },
  profit_margin: {
    label: "利润率",
    key: "profit_margin", 
    weight: 0.2,
    is_primary: true,
    data_source: "财务系统",
    format: "percentage"
  },
  customer_count: {
    label: "客户数量",
    key: "customer_count",
    weight: 0.15,
    is_primary: false,
    data_source: "CRM",
    format: "number"
  },
  project_count: {
    label: "项目数量",
    key: "project_count",
    weight: 0.1,
    is_primary: false,
    data_source: "项目管理",
    format: "number"
  },
  conversion_rate: {
    label: "转化率",
    key: "conversion_rate",
    weight: 0.1,
    is_primary: false,
    data_source: "销售漏斗",
    format: "percentage"
  },
  customer_satisfaction: {
    label: "客户满意度",
    key: "customer_satisfaction",
    weight: 0.05,
    is_primary: false,
    data_source: "客服系统",
    format: "score"
  }
};

// ==================== 销售阶段配置 ====================
export const salesStageConfig = {
  lead: {
    label: "潜在客户",
    value: "lead",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    order: 1
  },
  qualified: {
    label: "资格确认",
    value: "qualified",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    order: 2
  },
  proposal: {
    label: "方案提交",
    value: "proposal",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    order: 3
  },
  negotiation: {
    label: "商务谈判",
    value: "negotiation",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    order: 4
  },
  closed_won: {
    label: "成交",
    value: "closed_won",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    order: 5
  },
  closed_lost: {
    label: "流失",
    value: "closed_lost",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    order: 6
  }
};

// ==================== 客户等级配置 ====================
export const customerLevelConfig = {
  vip: {
    label: "VIP客户",
    value: "vip",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    discount: "最高优惠"
  },
  strategic: {
    label: "战略客户",
    value: "strategic",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    discount: "高优惠"
  },
  regular: {
    label: "普通客户",
    value: "regular",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    discount: "标准优惠"
  },
  potential: {
    label: "潜在客户",
    value: "potential",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    discount: "入门优惠"
  }
};

// ==================== 商机优先级配置 ====================
export const opportunityPriorityConfig = {
  high: {
    label: "高优先级",
    value: "high",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "AlertTriangle"
  },
  medium: {
    label: "中优先级",
    value: "medium",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Clock"
  },
  low: {
    label: "低优先级",
    value: "low",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "CheckCircle2"
  }
};

// ==================== 默认数据配置 ====================
export const DEFAULT_SALES_TEAM_STATS = {
  totalMembers: 0,
  activeMembers: 0,
  totalTarget: 0,
  totalAchieved: 0,
  avgAchievementRate: 0,
  totalProjects: 0,
  totalCustomers: 0,
  newCustomersThisMonth: 0
};

// ==================== 快速时间范围配置 ====================
export const QUICK_DATE_RANGE_PRESETS = [
  {
    key: "day",
    label: "本日",
    range: () => {
      const now = new Date();
      const start = new Date(now);
      start.setHours(0, 0, 0, 0);
      const end = new Date(now);
      end.setHours(23, 59, 59, 999);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
    }
  },
  {
    key: "week", 
    label: "本周",
    range: () => {
      const now = new Date();
      const day = now.getDay() || 7;
      const start = new Date(now);
      start.setDate(now.getDate() - day + 1);
      const end = new Date(start);
      end.setDate(start.getDate() + 6);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
    }
  },
  {
    key: "month",
    label: "本月",
    range: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
    }
  },
  {
    key: "quarter",
    label: "本季度",
    range: () => {
      const now = new Date();
      const quarter = Math.floor(now.getMonth() / 3);
      const start = new Date(now.getFullYear(), quarter * 3, 1);
      const end = new Date(now.getFullYear(), quarter * 3 + 3, 0);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
    }
  },
  {
    key: "year",
    label: "本年度", 
    range: () => {
      const now = new Date();
      const start = new Date(now.getFullYear(), 0, 1);
      const end = new Date(now.getFullYear(), 11, 31);
      return { start: start.toISOString().split('T')[0], end: end.toISOString().split('T')[0] };
    }
  }
];

// ==================== 排名选项配置 ====================
export const SALES_RANKING_OPTIONS = [
  { value: "revenue", label: "销售业绩" },
  { value: "profit_margin", label: "利润率" },
  { value: "customer_count", label: "客户数量" },
  { value: "project_count", label: "项目数量" },
  { value: "conversion_rate", label: "转化率" },
  { value: "customer_satisfaction", label: "客户满意度" },
  { value: "comprehensive", label: "综合评分" }
];

// ==================== 自动刷新配置 ====================
export const AUTO_REFRESH_INTERVALS = [
  { value: 0, label: "关闭自动刷新" },
  { value: 30, label: "30秒" },
  { value: 60, label: "1分钟" },
  { value: 300, label: "5分钟" },
  { value: 600, label: "10分钟" },
  { value: 1800, label: "30分钟" }
];

// ==================== 工具函数 ====================

// 获取销售成员状态配置
export const getSalesMemberStatusConfig = (status) => {
  return salesMemberStatusConfig[status] || salesMemberStatusConfig.active;
};

// 获取绩效等级配置
export const getSalesPerformanceLevelConfig = (level) => {
  return salesPerformanceLevelConfig[level] || salesPerformanceLevelConfig.average;
};

// 获取销售阶段配置
export const getSalesStageConfig = (stage) => {
  return salesStageConfig[stage] || salesStageConfig.lead;
};

// 获取客户等级配置
export const getCustomerLevelConfig = (level) => {
  return customerLevelConfig[level] || customerLevelConfig.regular;
};

// 获取商机优先级配置
export const getOpportunityPriorityConfig = (priority) => {
  return opportunityPriorityConfig[priority] || opportunityPriorityConfig.medium;
};

// 格式化绩效指标
export const formatPerformanceMetric = (value, format) => {
  switch (format) {
    case 'currency':
      return formatCurrency(value);
    case 'percentage':
      return `${(value || 0).toFixed(1)}%`;
    case 'number':
      return (value || 0).toLocaleString();
    case 'score':
      return `${(value || 0).toFixed(1)}分`;
    default:
      return value || '-';
  }
};

// 计算销售完成率
export const calculateSalesCompletionRate = (achieved, target) => {
  if (!target || target === 0) {return 0;}
  return ((achieved || 0) / target * 100).toFixed(1);
};

// 计算综合评分
export const calculateComprehensiveScore = (metrics, weights) => {
  let totalScore = 0;
  let totalWeight = 0;

  Object.keys(metrics).forEach(key => {
    const metric = metrics[key];
    const weight = weights[key] || 0;
    
    if (weight > 0 && metric !== null && metric !== undefined) {
      totalScore += metric * weight;
      totalWeight += weight;
    }
  });

  return totalWeight > 0 ? (totalScore / totalWeight).toFixed(2) : 0;
};

// 获取绩效等级
export const getPerformanceLevel = (rate) => {
  if (rate >= 120) {return 'excellent';}
  if (rate >= 100) {return 'good';}
  if (rate >= 80) {return 'average';}
  return 'poor';
};

// 格式化自动刷新时间
export const formatAutoRefreshTime = (value) => {
  if (!value) {return "";}
  return value.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit", 
    second: "2-digit",
    hour12: false,
  });
};

// 获取默认日期范围
export const getDefaultDateRange = () => {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
};

// 获取本周日期范围
export const getWeekDateRange = () => {
  const now = new Date();
  const day = now.getDay() || 7;
  const start = new Date(now);
  start.setDate(now.getDate() - day + 1);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
};

// 验证销售数据
export const validateSalesData = (data) => {
  const errors = [];
  
  if (!data.name || data.name.trim() === '') {
    errors.push('销售成员姓名不能为空');
  }
  
  if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
    errors.push('邮箱格式不正确');
  }
  
  if (data.monthlyTarget && (isNaN(data.monthlyTarget) || data.monthlyTarget < 0)) {
    errors.push('月度目标必须为非负数');
  }
  
  return errors;
};

// ==================== 销售总监管理常量 ====================

// 默认统计数据配置
export const DEFAULT_STATS = {
  monthlyTarget: 5000000,
  yearTarget: 60000000
};

// 排名主要指标
export const RANKING_PRIMARY_KEYS = [
  "contract_amount",
  "acceptance_amount",
  "collection_amount"
];

// 排名指标库配置
export const RANKING_METRIC_LIBRARY = [
  {
    value: "contract_amount",
    label: "签单额（合同金额）",
    description: "统计周期内签订的合同金额",
    defaultWeight: 0.4,
    isPrimary: true,
    category: "revenue"
  },
  {
    value: "acceptance_amount",
    label: "验收金额",
    description: "已审批/已开票金额，代表验收进度",
    defaultWeight: 0.2,
    isPrimary: true,
    category: "revenue"
  },
  {
    value: "collection_amount",
    label: "回款金额",
    description: "周期内到账的回款金额",
    defaultWeight: 0.2,
    isPrimary: true,
    category: "revenue"
  },
  {
    value: "opportunity_count",
    label: "商机提交数",
    description: "新增并推进的商机数量",
    defaultWeight: 0.05,
    isPrimary: false,
    category: "activity"
  },
  {
    value: "lead_conversion_rate",
    label: "线索成功率",
    description: "线索转商机/签单成功率",
    defaultWeight: 0.05,
    isPrimary: false,
    category: "efficiency"
  },
  {
    value: "customer_satisfaction",
    label: "客户满意度",
    description: "客户满意度评分",
    defaultWeight: 0.05,
    isPrimary: false,
    category: "quality"
  },
  {
    value: "sales_cycle_length",
    label: "销售周期",
    description: "平均销售周期长度",
    defaultWeight: 0.05,
    isPrimary: false,
    category: "efficiency"
  },
  {
    value: "pipeline_growth",
    label: "管道增长率",
    description: "销售管道价值增长",
    defaultWeight: 0.05,
    isPrimary: false,
    category: "growth"
  }
];

// 时间周期配置
export const TIME_PERIODS = {
  DAY: { value: "day", label: "今日", days: 1 },
  WEEK: { value: "week", label: "本周", days: 7 },
  MONTH: { value: "month", label: "本月", days: 30 },
  QUARTER: { value: "quarter", label: "本季度", days: 90 },
  YEAR: { value: "year", label: "今年", days: 365 }
};

// 销售阶段配置
export const SALES_STAGES = [
  { value: "lead", label: "线索", color: "#94a3b8" },
  { value: "opportunity", label: "商机", color: "#3b82f6" },
  { value: "proposal", label: "方案", color: "#8b5cf6" },
  { value: "negotiation", label: "谈判", color: "#f59e0b" },
  { value: "closed_won", label: "成交", color: "#10b981" },
  { value: "closed_lost", label: "失败", color: "#ef4444" }
];

// 客户等级配置
export const CUSTOMER_TIERS = {
  PLATINUM: {
    value: "platinum",
    label: "白金客户",
    minRevenue: 10000000,
    color: "#64748b",
    benefits: ["专属客户经理", "优先技术支持", "定制化服务"]
  },
  GOLD: {
    value: "gold",
    label: "黄金客户",
    minRevenue: 5000000,
    color: "#f59e0b",
    benefits: ["优先支持", "定期回访", "培训服务"]
  },
  SILVER: {
    value: "silver",
    label: "白银客户",
    minRevenue: 1000000,
    color: "#94a3b8",
    benefits: ["标准支持", "在线培训"]
  },
  BRONZE: {
    value: "bronze",
    label: "青铜客户",
    minRevenue: 0,
    color: "#cd7f32",
    benefits: ["基础支持"]
  }
};

// 销售区域配置
export const SALES_REGIONS = {
  NORTH: { value: "north", label: "华北区", color: "#3b82f6" },
  SOUTH: { value: "south", label: "华南区", color: "#10b981" },
  EAST: { value: "east", label: "华东区", color: "#f59e0b" },
  WEST: { value: "west", label: "华西区", color: "#8b5cf6" },
  CENTRAL: { value: "central", label: "华中区", color: "#ef4444" }
};

// 绩效等级配置
export const PERFORMANCE_GRADES = {
  EXCELLENT: {
    value: "excellent",
    label: "优秀",
    minScore: 90,
    color: "#10b981",
    bonus: 1.5
  },
  GOOD: {
    value: "good",
    label: "良好",
    minScore: 80,
    color: "#3b82f6",
    bonus: 1.2
  },
  AVERAGE: {
    value: "average",
    label: "达标",
    minScore: 70,
    color: "#f59e0b",
    bonus: 1.0
  },
  POOR: {
    value: "poor",
    label: "待改进",
    minScore: 0,
    color: "#ef4444",
    bonus: 0.8
  }
};

// 报表类型配置
export const REPORT_TYPES = {
  SALES_PERFORMANCE: {
    value: "sales_performance",
    label: "销售绩效报表",
    description: "团队和个人销售绩效分析",
    icon: "📊"
  },
  REVENUE_ANALYSIS: {
    value: "revenue_analysis",
    label: "收入分析报表",
    description: "收入趋势和构成分析",
    icon: "💰"
  },
  CUSTOMER_ANALYSIS: {
    value: "customer_analysis",
    label: "客户分析报表",
    description: "客户价值和行为分析",
    icon: "👥"
  },
  PIPELINE_ANALYSIS: {
    value: "pipeline_analysis",
    label: "销售管道报表",
    description: "销售管道健康度分析",
    icon: "🔍"
  },
  FORECAST_REPORT: {
    value: "forecast_report",
    label: "销售预测报表",
    description: "销售趋势预测",
    icon: "🔮"
  }
};

// 预警类型配置
export const ALERT_TYPES = {
  TARGET_NOT_MET: {
    value: "target_not_met",
    label: "目标未达成",
    level: "warning",
    color: "#f59e0b",
    icon: "⚠️"
  },
  PERFORMANCE_DECLINE: {
    value: "performance_decline",
    label: "绩效下滑",
    level: "error",
    color: "#ef4444",
    icon: "📉"
  },
  PIPELINE_RISK: {
    value: "pipeline_risk",
    label: "管道风险",
    level: "warning",
    color: "#f59e0b",
    icon: "⚡"
  },
  CUSTOMER_CHURN: {
    value: "customer_churn",
    label: "客户流失",
    level: "error",
    color: "#ef4444",
    icon: "👋"
  }
};

// 预测模型配置
export const FORECAST_MODELS = {
  LINEAR: {
    value: "linear",
    label: "线性回归",
    description: "基于历史数据的线性趋势预测",
    accuracy: 0.75
  },
  EXPONENTIAL: {
    value: "exponential",
    label: "指数平滑",
    description: "考虑季节性因素的指数平滑预测",
    accuracy: 0.8
  },
  ARIMA: {
    value: "arima",
    label: "ARIMA模型",
    description: "自回归积分滑动平均模型",
    accuracy: 0.85
  },
  MACHINE_LEARNING: {
    value: "ml",
    label: "机器学习",
    description: "基于多种特征的机器学习预测",
    accuracy: 0.9
  }
};

// 趋势类型配置
export const TREND_TYPES = {
  UPWARD: { value: "upward", label: "上升趋势", color: "#10b981", icon: "📈" },
  DOWNWARD: { value: "downward", label: "下降趋势", color: "#ef4444", icon: "📉" },
  STABLE: { value: "stable", label: "平稳趋势", color: "#6b7280", icon: "➡️" },
  VOLATILE: { value: "volatile", label: "波动趋势", color: "#f59e0b", icon: "📊" }
};

// 工具函数：获取时间范围
export const getPeriodRange = (period) => {
  const now = new Date();
  let start, end;

  switch (period) {
    case "day":
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
      break;
    case "week": {
      const dayOfWeek = now.getDay();
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - dayOfWeek);
      end = new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
      break;
    }
    case "month":
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now.getFullYear(), now.getMonth() + 1, 1);
      break;
    case "quarter": {
      const quarter = Math.floor(now.getMonth() / 3);
      start = new Date(now.getFullYear(), quarter * 3, 1);
      end = new Date(now.getFullYear(), (quarter + 1) * 3, 1);
      break;
    }
    case "year":
      start = new Date(now.getFullYear(), 0, 1);
      end = new Date(now.getFullYear() + 1, 0, 1);
      break;
    default:
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  }

  return { start, end };
};

// 工具函数：格式化日期
export const toISODate = (date) => {
  return date.toISOString().split("T")[0];
};

// 工具函数：计算趋势
export const calculateTrend = (current, previous) => {
  if (!previous || previous === 0) {return { trend: "stable", value: 0 };}
  const change = (current - previous) / Math.abs(previous) * 100;
  const trend = change > 5 ? "upward" : change < -5 ? "downward" : "stable";
  return { trend, value: Math.abs(change) };
};

// 工具函数：获取绩效等级
export const getPerformanceGrade = (score) => {
  for (const [_key, grade] of Object.entries(PERFORMANCE_GRADES)) {
    if (score >= grade.minScore) {
      return grade;
    }
  }
  return PERFORMANCE_GRADES.POOR;
};

// 工具函数：获取客户等级
export const getCustomerTier = (revenue) => {
  for (const [_key, tier] of Object.entries(CUSTOMER_TIERS)) {
    if (revenue >= tier.minRevenue) {
      return tier;
    }
  }
  return CUSTOMER_TIERS.BRONZE;
};

// 工具函数：格式化百分比
export const formatPercentage = (value, decimals = 1) => {
  return `${value.toFixed(decimals)}%`;
};

// 工具函数：计算排名验证
export const calculateRankingValidation = (metrics) => {
  const totalWeight = metrics.reduce((sum, metric) => sum + (parseFloat(metric.weight) || 0), 0);
  const errors = [];

  if (Math.abs(totalWeight - 1.0) > 0.01) {
    errors.push(`权重总和应为1.0，当前为${totalWeight.toFixed(2)}`);
  }

  const primaryMetrics = metrics.filter((m) => m.isPrimary);
  if (primaryMetrics.length < 3) {
    errors.push("至少需要3个主要指标");
  }

  const duplicateKeys = metrics
    .map((m) => m.key || m.data_source)
    .filter((key, index, arr) => key && arr.indexOf(key) !== index);

  if (duplicateKeys.length > 0) {
    errors.push(`重复的指标: ${duplicateKeys.join(", ")}`);
  }

  return {
    isValid: errors.length === 0,
    errors,
    totalWeight
  };
};

// 工具函数：验证指标配置
export const validateMetricConfig = (metric) => {
  const errors = [];

  if (!metric.key && !metric.data_source) {
    errors.push("指标关键字不能为空");
  }

  if (!metric.label) {
    errors.push("指标名称不能为空");
  }

  const weight = parseFloat(metric.weight);
  if (isNaN(weight) || weight < 0 || weight > 1) {
    errors.push("权重必须是0-1之间的数字");
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// 工具函数别名
export {
  TIME_PERIODS as PERIODS,
  SALES_STAGES as STAGES,
  CUSTOMER_TIERS as TIERS,
  SALES_REGIONS as REGIONS,
  PERFORMANCE_GRADES as GRADES,
  REPORT_TYPES as REPORTS,
  ALERT_TYPES as ALERTS,
  FORECAST_MODELS as MODELS,
  TREND_TYPES as TRENDS
};

// ==================== 销售团队排名配置 ====================

// 默认排名指标配置
export const DEFAULT_RANKING_METRICS = [
  {
    key: "contract_amount",
    label: "合同金额",
    weight: 0.4,
    data_source: "contract_amount",
    is_primary: true
  },
  {
    key: "acceptance_amount",
    label: "验收金额",
    weight: 0.2,
    data_source: "acceptance_amount",
    is_primary: true
  },
  {
    key: "collection_amount",
    label: "回款金额",
    weight: 0.2,
    data_source: "collection_amount",
    is_primary: true
  },
  {
    key: "opportunity_count",
    label: "商机数量",
    weight: 0.05,
    data_source: "opportunity_count",
    is_primary: false
  },
  {
    key: "lead_conversion_rate",
    label: "线索成功率",
    weight: 0.05,
    data_source: "lead_conversion_rate",
    is_primary: false
  },
  {
    key: "follow_up_total",
    label: "跟进次数",
    weight: 0.05,
    data_source: "follow_up_total",
    is_primary: false
  },
  {
    key: "avg_est_margin",
    label: "平均预估毛利率",
    weight: 0.05,
    data_source: "avg_est_margin",
    is_primary: false
  }
];

// 备选排名字段
export const FALLBACK_RANKING_FIELDS = [
  { value: "lead_count", label: "线索数量" },
  { value: "opportunity_count", label: "商机数量" },
  { value: "contract_amount", label: "合同金额" },
  { value: "collection_amount", label: "回款金额" }
];

// ==================== 排名指标工具函数 ====================

export const isAmountMetric = (key = "") =>
  key.includes("amount") || key.includes("pipeline");

export const isPercentageMetric = (key = "") =>
  key.includes("rate") || key.includes("margin");

export const buildMetricDetailMap = (metricDetails = []) =>
  metricDetails.reduce((acc, detail) => {
    const detailKey = detail.key || detail.data_source;
    if (detailKey) {
      acc[detailKey] = detail;
    }
    if (detail.data_source) {
      acc[detail.data_source] = detail;
    }
    return acc;
  }, {});

export const formatMetricValueDisplay = (metricDetail, metricDefinition) => {
  if (!metricDetail) {return "--";}
  const key = metricDefinition?.data_source || metricDefinition?.key || "";
  const numericValue = Number(metricDetail.value ?? 0);
  if (isAmountMetric(key)) {
    return formatCurrencyCompact(numericValue || 0);
  }
  if (isPercentageMetric(key)) {
    return `${numericValue.toFixed(1)}%`;
  }
  if (!Number.isFinite(numericValue)) {return "--";}
  return Number.isInteger(numericValue)
    ? `${numericValue}`
    : numericValue.toFixed(2);
};

export const formatMetricScoreDisplay = (metricDetail) => {
  if (!metricDetail) {return "--";}
  return `${Number(metricDetail.score ?? 0).toFixed(1)} 分`;
};

// 导出配置对象
export const salesConstants = {
  salesMemberStatusConfig,
  salesPerformanceLevelConfig,
  salesRankingMetricsConfig,
  salesStageConfig,
  customerLevelConfig,
  opportunityPriorityConfig,
  DEFAULT_SALES_TEAM_STATS,
  QUICK_DATE_RANGE_PRESETS,
  SALES_RANKING_OPTIONS,
  AUTO_REFRESH_INTERVALS
};
