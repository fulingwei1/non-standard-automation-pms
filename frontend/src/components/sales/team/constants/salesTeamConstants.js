/**
 * Sales Team Constants - 销售团队管理常量配置
 * 包含：日期工具、格式化函数、排名指标配置、状态配置等
 */

// ==================== 日期工具函数 ====================

/**
 * 格式化日期为 YYYY-MM-DD 格式
 */
export const formatDateInput = (value) => value.toISOString().split("T")[0];

/**
 * 获取默认月份范围（本月）
 */
export const getDefaultDateRange = () => {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), 1);
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return {
    start: formatDateInput(start),
    end: formatDateInput(end),
  };
};

/**
 * 获取本周日期范围
 */
export const getWeekDateRange = () => {
  const now = new Date();
  const day = now.getDay() || 7; // 周一=1, 周日=7
  const start = new Date(now);
  start.setDate(now.getDate() - day + 1);
  const end = new Date(start);
  end.setDate(start.getDate() + 6);
  return {
    start: formatDateInput(start),
    end: formatDateInput(end),
  };
};

/**
 * 快捷时间段预设
 */
export const QUICK_RANGE_PRESETS = [
  {
    key: "day",
    label: "本日",
    getRange: () => {
      const today = new Date();
      const formatted = formatDateInput(today);
      return { start: formatted, end: formatted };
    },
  },
  {
    key: "week",
    label: "本周",
    getRange: () => getWeekDateRange(),
  },
  {
    key: "month",
    label: "本月",
    getRange: () => getDefaultDateRange(),
  },
];

// ==================== 格式化函数 ====================

/**
 * 格式化货币显示
 */
export const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0,
  }).format(value);
};

/**
 * 格式化跟进类型
 */
export const followUpTypeLabels = {
  CALL: "电话",
  EMAIL: "邮件",
  VISIT: "拜访",
  MEETING: "会议",
  OTHER: "其他",
};

export const formatFollowUpType = (value) =>
  followUpTypeLabels[value] || value || "跟进";

/**
 * 格式化相对时间（如"3分钟前"）
 */
export const formatTimeAgo = (value) => {
  if (!value) {return "";}
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {return value;}
  const diff = Date.now() - target.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) {return "刚刚";}
  if (diff < hour) {return `${Math.max(1, Math.floor(diff / minute))}分钟前`;}
  if (diff < day) {return `${Math.floor(diff / hour)}小时前`;}
  if (diff < 30 * day) {return `${Math.floor(diff / day)}天前`;}
  return target.toLocaleDateString("zh-CN");
};

/**
 * 格式化日期时间
 */
export const formatDateTime = (value) => {
  if (!value) {return "";}
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {return value;}
  return target.toLocaleString("zh-CN", { hour12: false });
};

/**
 * 格式化自动刷新时间
 */
export const formatAutoRefreshTime = (value) => {
  if (!value) {return "";}
  return value.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

// ==================== 排名指标配置 ====================

/**
 * 默认排名指标配置
 */
export const DEFAULT_RANKING_METRICS = [
  {
    key: "contract_amount",
    label: "合同金额",
    weight: 0.4,
    data_source: "contract_amount",
    is_primary: true,
  },
  {
    key: "acceptance_amount",
    label: "验收金额",
    weight: 0.2,
    data_source: "acceptance_amount",
    is_primary: true,
  },
  {
    key: "collection_amount",
    label: "回款金额",
    weight: 0.2,
    data_source: "collection_amount",
    is_primary: true,
  },
  {
    key: "opportunity_count",
    label: "商机数量",
    weight: 0.05,
    data_source: "opportunity_count",
    is_primary: false,
  },
  {
    key: "lead_conversion_rate",
    label: "线索成功率",
    weight: 0.05,
    data_source: "lead_conversion_rate",
    is_primary: false,
  },
  {
    key: "follow_up_total",
    label: "跟进次数",
    weight: 0.05,
    data_source: "follow_up_total",
    is_primary: false,
  },
  {
    key: "avg_est_margin",
    label: "平均预估毛利率",
    weight: 0.05,
    data_source: "avg_est_margin",
    is_primary: false,
  },
];

/**
 * 备选排名字段
 */
export const FALLBACK_RANKING_FIELDS = [
  { value: "lead_count", label: "线索数量" },
  { value: "opportunity_count", label: "商机数量" },
  { value: "contract_amount", label: "合同金额" },
  { value: "collection_amount", label: "回款金额" },
];

// ==================== 状态配置 ====================

/**
 * 业绩状态配置
 */
export const statusConfig = {
  excellent: {
    label: "优秀",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  good: { label: "良好", color: "bg-blue-500", textColor: "text-blue-400" },
  warning: {
    label: "需关注",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  poor: { label: "待改进", color: "bg-red-500", textColor: "text-red-400" },
};

/**
 * 获取业绩状态
 */
export const getAchievementStatus = (rate) => {
  if (rate >= 100) {return "excellent";}
  if (rate >= 80) {return "good";}
  if (rate >= 60) {return "warning";}
  return "poor";
};

// ==================== 默认值 ====================

/**
 * 默认团队统计数据
 */
export const DEFAULT_TEAM_STATS = {
  totalMembers: 0,
  activeMembers: 0,
  totalTarget: 0,
  totalAchieved: 0,
  avgAchievementRate: 0,
  totalProjects: 0,
  totalCustomers: 0,
  newCustomersThisMonth: 0,
};

// ==================== 辅助函数 ====================

/**
 * 判断是否为金额类型指标
 */
export const isAmountMetric = (key = "") =>
  key.includes("amount") || key.includes("pipeline");

/**
 * 判断是否为百分比类型指标
 */
export const isPercentageMetric = (key = "") =>
  key.includes("rate") || key.includes("margin");

/**
 * 构建指标详情映射
 */
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

/**
 * 格式化指标值显示
 */
export const formatMetricValueDisplay = (metricDetail, metricDefinition) => {
  if (!metricDetail) {return "--";}
  const key = metricDefinition?.data_source || metricDefinition?.key || "";
  const numericValue = Number(metricDetail.value ?? 0);
  if (isAmountMetric(key)) {
    return formatCurrency(numericValue || 0);
  }
  if (isPercentageMetric(key)) {
    return `${numericValue.toFixed(1)}%`;
  }
  if (!Number.isFinite(numericValue)) {return "--";}
  return Number.isInteger(numericValue)
    ? `${numericValue}`
    : numericValue.toFixed(2);
};

/**
 * 格式化指标得分显示
 */
export const formatMetricScoreDisplay = (metricDetail) => {
  if (!metricDetail) {return "--";}
  return `${Number(metricDetail.score ?? 0).toFixed(1)} 分`;
};
