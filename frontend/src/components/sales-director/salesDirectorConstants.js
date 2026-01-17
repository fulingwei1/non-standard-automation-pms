/**
 * Sales Director Management Constants and Configuration
 * 销售总监管理系统常量和配置
 */

// 默认统计数据配置
export const DEFAULT_STATS = {
  monthlyTarget: 5000000,
  yearTarget: 60000000
};

// 排名主要指标
export const RANKING_PRIMARY_KEYS = [
"contract_amount",
"acceptance_amount",
"collection_amount"];


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
}];


// 时间周期配置
export const TIME_PERIODS = {
  DAY: { value: 'day', label: '今日', days: 1 },
  WEEK: { value: 'week', label: '本周', days: 7 },
  MONTH: { value: 'month', label: '本月', days: 30 },
  QUARTER: { value: 'quarter', label: '本季度', days: 90 },
  YEAR: { value: 'year', label: '今年', days: 365 }
};

// 销售阶段配置
export const SALES_STAGES = [
{ value: 'lead', label: '线索', color: '#94a3b8' },
{ value: 'opportunity', label: '商机', color: '#3b82f6' },
{ value: 'proposal', label: '方案', color: '#8b5cf6' },
{ value: 'negotiation', label: '谈判', color: '#f59e0b' },
{ value: 'closed_won', label: '成交', color: '#10b981' },
{ value: 'closed_lost', label: '失败', color: '#ef4444' }];


// 客户等级配置
export const CUSTOMER_TIERS = {
  PLATINUM: {
    value: 'platinum',
    label: '白金客户',
    minRevenue: 10000000,
    color: '#64748b',
    benefits: ['专属客户经理', '优先技术支持', '定制化服务']
  },
  GOLD: {
    value: 'gold',
    label: '黄金客户',
    minRevenue: 5000000,
    color: '#f59e0b',
    benefits: ['优先支持', '定期回访', '培训服务']
  },
  SILVER: {
    value: 'silver',
    label: '白银客户',
    minRevenue: 1000000,
    color: '#94a3b8',
    benefits: ['标准支持', '在线培训']
  },
  BRONZE: {
    value: 'bronze',
    label: '青铜客户',
    minRevenue: 0,
    color: '#cd7f32',
    benefits: ['基础支持']
  }
};

// 销售区域配置
export const SALES_REGIONS = {
  NORTH: { value: 'north', label: '华北区', color: '#3b82f6' },
  SOUTH: { value: 'south', label: '华南区', color: '#10b981' },
  EAST: { value: 'east', label: '华东区', color: '#f59e0b' },
  WEST: { value: 'west', label: '华西区', color: '#8b5cf6' },
  CENTRAL: { value: 'central', label: '华中区', color: '#ef4444' }
};

// 绩效等级配置
export const PERFORMANCE_GRADES = {
  EXCELLENT: {
    value: 'excellent',
    label: '优秀',
    minScore: 90,
    color: '#10b981',
    bonus: 1.5
  },
  GOOD: {
    value: 'good',
    label: '良好',
    minScore: 80,
    color: '#3b82f6',
    bonus: 1.2
  },
  AVERAGE: {
    value: 'average',
    label: '达标',
    minScore: 70,
    color: '#f59e0b',
    bonus: 1.0
  },
  POOR: {
    value: 'poor',
    label: '待改进',
    minScore: 0,
    color: '#ef4444',
    bonus: 0.8
  }
};

// 报表类型配置
export const REPORT_TYPES = {
  SALES_PERFORMANCE: {
    value: 'sales_performance',
    label: '销售绩效报表',
    description: '团队和个人销售绩效分析',
    icon: '📊'
  },
  REVENUE_ANALYSIS: {
    value: 'revenue_analysis',
    label: '收入分析报表',
    description: '收入趋势和构成分析',
    icon: '💰'
  },
  CUSTOMER_ANALYSIS: {
    value: 'customer_analysis',
    label: '客户分析报表',
    description: '客户价值和行为分析',
    icon: '👥'
  },
  PIPELINE_ANALYSIS: {
    value: 'pipeline_analysis',
    label: '销售管道报表',
    description: '销售管道健康度分析',
    icon: '🔍'
  },
  FORECAST_REPORT: {
    value: 'forecast_report',
    label: '销售预测报表',
    description: '销售趋势预测',
    icon: '🔮'
  }
};

// 预警类型配置
export const ALERT_TYPES = {
  TARGET_NOT_MET: {
    value: 'target_not_met',
    label: '目标未达成',
    level: 'warning',
    color: '#f59e0b',
    icon: '⚠️'
  },
  PERFORMANCE_DECLINE: {
    value: 'performance_decline',
    label: '绩效下滑',
    level: 'error',
    color: '#ef4444',
    icon: '📉'
  },
  PIPELINE_RISK: {
    value: 'pipeline_risk',
    label: '管道风险',
    level: 'warning',
    color: '#f59e0b',
    icon: '⚡'
  },
  CUSTOMER_CHURN: {
    value: 'customer_churn',
    label: '客户流失',
    level: 'error',
    color: '#ef4444',
    icon: '👋'
  }
};

// 预测模型配置
export const FORECAST_MODELS = {
  LINEAR: {
    value: 'linear',
    label: '线性回归',
    description: '基于历史数据的线性趋势预测',
    accuracy: 0.75
  },
  EXPONENTIAL: {
    value: 'exponential',
    label: '指数平滑',
    description: '考虑季节性因素的指数平滑预测',
    accuracy: 0.80
  },
  ARIMA: {
    value: 'arima',
    label: 'ARIMA模型',
    description: '自回归积分滑动平均模型',
    accuracy: 0.85
  },
  MACHINE_LEARNING: {
    value: 'ml',
    label: '机器学习',
    description: '基于多种特征的机器学习预测',
    accuracy: 0.90
  }
};

// 趋势类型配置
export const TREND_TYPES = {
  UPWARD: { value: 'upward', label: '上升趋势', color: '#10b981', icon: '📈' },
  DOWNWARD: { value: 'downward', label: '下降趋势', color: '#ef4444', icon: '📉' },
  STABLE: { value: 'stable', label: '平稳趋势', color: '#6b7280', icon: '➡️' },
  VOLATILE: { value: 'volatile', label: '波动趋势', color: '#f59e0b', icon: '📊' }
};

// 工具函数：获取时间范围
export const getPeriodRange = (period) => {
  const now = new Date();
  let start, end;

  switch (period) {
    case 'day':
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
      break;
    case 'week': {
      const dayOfWeek = now.getDay();
      start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - dayOfWeek);
      end = new Date(start.getTime() + 7 * 24 * 60 * 60 * 1000);
      break;
    }
    case 'month':
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now.getFullYear(), now.getMonth() + 1, 1);
      break;
    case 'quarter': {
      const quarter = Math.floor(now.getMonth() / 3);
      start = new Date(now.getFullYear(), quarter * 3, 1);
      end = new Date(now.getFullYear(), (quarter + 1) * 3, 1);
      break;
    }
    case 'year':
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
  return date.toISOString().split('T')[0];
};

// 工具函数：计算趋势
export const calculateTrend = (current, previous) => {
  if (!previous || previous === 0) return { trend: 'stable', value: 0 };
  const change = (current - previous) / Math.abs(previous) * 100;
  const trend = change > 5 ? 'upward' : change < -5 ? 'downward' : 'stable';
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

// 工具函数：格式化金额
export const formatCurrency = (amount, currency = 'CNY') => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
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
    errors.push('至少需要3个主要指标');
  }

  const duplicateKeys = metrics.
  map((m) => m.key || m.data_source).
  filter((key, index, arr) => key && arr.indexOf(key) !== index);

  if (duplicateKeys.length > 0) {
    errors.push(`重复的指标: ${duplicateKeys.join(', ')}`);
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
    errors.push('指标关键字不能为空');
  }

  if (!metric.label) {
    errors.push('指标名称不能为空');
  }

  const weight = parseFloat(metric.weight);
  if (isNaN(weight) || weight < 0 || weight > 1) {
    errors.push('权重必须是0-1之间的数字');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// 导出所有配置对象
export {
  TIME_PERIODS as PERIODS,
  SALES_STAGES as STAGES,
  CUSTOMER_TIERS as TIERS,
  SALES_REGIONS as REGIONS,
  PERFORMANCE_GRADES as GRADES,
  REPORT_TYPES as REPORTS,
  ALERT_TYPES as ALERTS,
  FORECAST_MODELS as MODELS,
  TREND_TYPES as TRENDS };
