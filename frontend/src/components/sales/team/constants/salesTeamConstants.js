/**
 * Sales Team Constants - 销售团队管理常量配置
 * 包含：日期工具、格式化函数、排名指标配置、状态配置等
 */

import {
  DEFAULT_SALES_TEAM_STATS,
  QUICK_DATE_RANGE_PRESETS,
  getDefaultDateRange as getDefaultDateRangeShared,
  getWeekDateRange as getWeekDateRangeShared,
  formatAutoRefreshTime as formatAutoRefreshTimeShared,
} from "../../salesConstants";

export {
  DEFAULT_RANKING_METRICS,
  FALLBACK_RANKING_FIELDS,
  isAmountMetric,
  isPercentageMetric,
  buildMetricDetailMap,
  formatMetricValueDisplay,
  formatMetricScoreDisplay,
} from "../../salesConstants";

// ==================== 日期工具函数 ====================

export const getDefaultDateRange = getDefaultDateRangeShared;
export const getWeekDateRange = getWeekDateRangeShared;

/**
 * 快捷时间段预设
 */
export const QUICK_RANGE_PRESETS = [
  ...QUICK_DATE_RANGE_PRESETS
    .filter((preset) => ["day", "week", "month"].includes(preset.key))
    .map((preset) => ({
      key: preset.key,
      label: preset.label,
      getRange: preset.range,
    })),
];

// ==================== 格式化函数 ====================

// Re-export formatCurrency from unified formatters for backward compatibility
export { formatCurrencyCompact as formatCurrency } from "../../../../lib/formatters";

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
export const formatAutoRefreshTime = formatAutoRefreshTimeShared;

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
  ...DEFAULT_SALES_TEAM_STATS,
};
