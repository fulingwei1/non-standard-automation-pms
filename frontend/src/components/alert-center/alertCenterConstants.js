/**
 * Alert Center Constants - 预警中心配置常量
 *
 * [DEPRECATED] This file is a re-export shim for backward compatibility.
 * All alert center constants have been consolidated into
 * ../alert-statistics/alertStatsConstants.js
 *
 * Please import from '../alert-statistics/alertStatsConstants' instead.
 *
 * Note: getAlertLevelConfig/getAlertStatusConfig/getAlertTypeConfig are
 * re-mapped here to point to ALERT_LEVELS/ALERT_STATUS/ALERT_TYPES
 * (alert center versions) rather than the statistics versions
 * (ALERT_LEVEL_STATS/ALERT_STATUS_STATS/ALERT_TYPE_STATS).
 */
export {
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
 calculateSLACompliance,
 calculateAverageResponseTime,
 calculateResponseTime,
 formatStatValue,
 getTrendDirection,
 getTrendColor,
 getTrendIcon,
 generateTimeSeries,
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
 formatAlertTime,
  // 预警中心版的函数使用 ALERT_LEVELS/ALERT_STATUS/ALERT_TYPES 数据
 getAlertCenterLevelConfig as getAlertLevelConfig,
 getAlertCenterStatusConfig as getAlertStatusConfig,
 getAlertCenterTypeConfig as getAlertTypeConfig
} from '../alert-statistics/alertStatsConstants';

export { default } from '../alert-statistics/alertStatsConstants';
