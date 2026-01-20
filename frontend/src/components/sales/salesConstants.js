/**
 * Sales Management Constants
 * 销售管理系统常量配置
 * 包含销售状态、阶段、类型、优先级等配置
 */

import { cn, formatDate, formatDateTime, formatCurrency } from "../../lib/utils";

export { cn, formatDate, formatDateTime, formatCurrency };

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
