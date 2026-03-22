/**
 * Alert Statistics Configuration Constants - 告警统计配置常量
 * 包含告警类型、级别、状态、时间维度等统计配置
 *
 * 拆分自原 alertStatsConstants.js，按职责分为：
 * - statTypes.js: 告警统计类型、级别、状态、类型配置
 * - chartAndFilterConfigs.js: 图表、过滤器、颜色、指标配置
 * - alertCenterConfigs.js: 预警中心级别、状态、类型、规则、通知、优先级配置
 * - defaults.js: 预警操作、指标、时间、权限、默认值配置
 * - utils.js: 统计计算、格式化、验证等工具函数
 */

// 统计类型配置
export {
 ALERT_STAT_TYPES,
 ALERT_LEVEL_STATS,
 ALERT_STATUS_STATS,
 ALERT_TYPE_STATS
} from './statTypes';

// 图表与过滤器配置
export {
 TIME_DIMENSIONS,
 CHART_TYPES,
 STAT_METRICS,
 FILTER_CONFIGS,
 CHART_COLORS,
 STATISTICS_METRICS,
 TABLE_CONFIG
} from './chartAndFilterConfigs';

// 预警中心配置
export {
 ALERT_LEVELS,
 ALERT_STATUS,
 ALERT_TYPES,
 ALERT_RULES,
 NOTIFICATION_CHANNELS,
 ALERT_PRIORITY
} from './alertCenterConfigs';

// 预警处理与默认配置
export {
 ALERT_ACTIONS,
 ALERT_METRICS,
 ALERT_TIME_CONFIG,
 ALERT_STATUS_FLOW,
 ALERT_PERMISSIONS,
 DEFAULT_STAT_CONFIG,
 DEFAULT_CHART_CONFIG,
 DEFAULT_ALERT_CONFIG,
 DEFAULT_RULE_CONFIG,
 TIME_PERIODS,
 EXPORT_FORMATS,
 FILTER_CATEGORIES,
 DEFAULT_FILTERS,
 DASHBOARD_LAYOUTS
} from './defaults';

// 工具函数
export {
 getAlertLevelConfig,
 getAlertStatusConfig,
 getAlertTypeConfig,
 calculateSLACompliance,
 calculateAverageResponseTime,
 calculateResponseTime,
 formatStatValue,
 getTrendDirection,
 getTrendColor,
 getTrendIcon,
 generateTimeSeries,
 getAlertCenterLevelConfig,
 getAlertCenterStatusConfig,
 getAlertCenterTypeConfig,
 getAlertRuleConfig,
 getNotificationChannelConfig,
 calculateCenterResponseTime,
 calculateResolutionTime,
 checkResponseTimeSLA,
 checkResolutionTimeSLA,
 getAvailableActions,
 validateAlertRule,
 generateAlertNumber,
 getAlertSummary,
 requiresEscalation,
 getAlertSeverityScore,
 isBusinessHour,
 formatAlertTime
} from './utils';

// ==================== 默认导出（向后兼容） ====================
import { ALERT_STAT_TYPES, ALERT_LEVEL_STATS, ALERT_STATUS_STATS, ALERT_TYPE_STATS } from './statTypes';
import { TIME_DIMENSIONS, CHART_TYPES, STAT_METRICS, FILTER_CONFIGS, CHART_COLORS, STATISTICS_METRICS, TABLE_CONFIG } from './chartAndFilterConfigs';
import { ALERT_LEVELS, ALERT_STATUS, ALERT_TYPES, ALERT_RULES, NOTIFICATION_CHANNELS, ALERT_PRIORITY } from './alertCenterConfigs';
import { ALERT_ACTIONS, ALERT_METRICS, ALERT_TIME_CONFIG, ALERT_STATUS_FLOW, ALERT_PERMISSIONS, DEFAULT_STAT_CONFIG, DEFAULT_CHART_CONFIG, DEFAULT_ALERT_CONFIG, DEFAULT_RULE_CONFIG, TIME_PERIODS, EXPORT_FORMATS, FILTER_CATEGORIES, DEFAULT_FILTERS, DASHBOARD_LAYOUTS } from './defaults';
import { getAlertLevelConfig, getAlertStatusConfig, getAlertTypeConfig, calculateSLACompliance, calculateAverageResponseTime, calculateResponseTime, formatStatValue, getTrendDirection, getTrendColor, getTrendIcon, generateTimeSeries, getAlertCenterLevelConfig, getAlertCenterStatusConfig, getAlertCenterTypeConfig, getAlertRuleConfig, getNotificationChannelConfig, calculateCenterResponseTime, calculateResolutionTime, checkResponseTimeSLA, checkResolutionTimeSLA, getAvailableActions, validateAlertRule, generateAlertNumber, getAlertSummary, requiresEscalation, getAlertSeverityScore, isBusinessHour, formatAlertTime } from './utils';

export default {
 ALERT_STAT_TYPES,
 ALERT_LEVEL_STATS,
 ALERT_STATUS_STATS,
 ALERT_TYPE_STATS,
 TIME_DIMENSIONS,
 CHART_TYPES,
 STAT_METRICS,
  FILTER_CONFIGS,
 CHART_COLORS,
 STATISTICS_METRICS,
  TABLE_CONFIG,
 ALERT_LEVELS,
 ALERT_STATUS,
 ALERT_TYPES,
 ALERT_RULES,
 NOTIFICATION_CHANNELS,
 ALERT_PRIORITY,
 ALERT_ACTIONS,
 ALERT_METRICS,
 ALERT_TIME_CONFIG,
 ALERT_STATUS_FLOW,
  ALERT_PERMISSIONS,
 DEFAULT_STAT_CONFIG,
 DEFAULT_CHART_CONFIG,
 DEFAULT_ALERT_CONFIG,
 DEFAULT_RULE_CONFIG,
 TIME_PERIODS,
  EXPORT_FORMATS,
 FILTER_CATEGORIES,
 DEFAULT_FILTERS,
 DASHBOARD_LAYOUTS,
 getAlertLevelConfig,
 getAlertStatusConfig,
 getAlertTypeConfig,
 calculateSLACompliance,
 calculateAverageResponseTime,
 calculateResponseTime,
 formatStatValue,
 getTrendDirection,
 getTrendColor,
 getTrendIcon,
 generateTimeSeries,
 getAlertCenterLevelConfig,
 getAlertCenterStatusConfig,
 getAlertCenterTypeConfig,
  getAlertRuleConfig,
  getNotificationChannelConfig,
  calculateCenterResponseTime,
 calculateResolutionTime,
 checkResponseTimeSLA,
 checkResolutionTimeSLA,
 getAvailableActions,
 validateAlertRule,
 generateAlertNumber,
 getAlertSummary,
 requiresEscalation,
 getAlertSeverityScore,
 isBusinessHour,
 formatAlertTime
};
