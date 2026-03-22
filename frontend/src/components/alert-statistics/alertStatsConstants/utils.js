/**
 * 告警统计工具函数 - Alert Stats Utilities
 * 包含统计计算、格式化、验证等工具函数
 */

import { ALERT_LEVEL_STATS, ALERT_STATUS_STATS, ALERT_TYPE_STATS } from './statTypes';
import { TIME_DIMENSIONS, STAT_METRICS } from './chartAndFilterConfigs';
import { ALERT_LEVELS, ALERT_STATUS, ALERT_TYPES, ALERT_RULES, NOTIFICATION_CHANNELS } from './alertCenterConfigs';
import { ALERT_METRICS, ALERT_TIME_CONFIG } from './defaults';

// ==================== 工具函数（统计相关） ====================

/**
 * 获取告警级别统计配置
 */
export const getAlertLevelConfig = (level) => {
 return ALERT_LEVEL_STATS[level] || ALERT_LEVEL_STATS.INFO;
};

/**
 * 获取告警状态统计配置
 */
export const getAlertStatusConfig = (status) => {
 return ALERT_STATUS_STATS[status] || ALERT_STATUS_STATS.PENDING;
};

/**
 * 获取告警类型统计配置
 */
export const getAlertTypeConfig = (type) => {
 return ALERT_TYPE_STATS[type] || ALERT_TYPE_STATS.SYSTEM;
};

/**
 * 计算告警响应时间达标率
 */
export const calculateSLACompliance = (alerts) => {
 if (!alerts || alerts.length === 0) {return 0;}

 const compliantAlerts = alerts.filter((alert) => {
 const levelConfig = getAlertLevelConfig(alert.alert_level);
  const responseTime = calculateResponseTime(alert);
 return responseTime <= levelConfig.targetResponseTime;
  });

 return Math.round(compliantAlerts.length / alerts.length * 100);
};

/**
 * 计算平均响应时间
 */
export const calculateAverageResponseTime = (alerts) => {
 if (!alerts || alerts.length === 0) {return 0;}

 const alertsWithResponse = alerts.filter((alert) => alert.response_time);
 if (alertsWithResponse.length === 0) {return 0;}

 const totalTime = alertsWithResponse.reduce((sum, alert) =>
 sum + (alert.response_time || 0), 0
 );

 return Math.round(totalTime / alertsWithResponse.length);
};

/**
 * 计算单个告警的响应时间
 */
export const calculateResponseTime = (alert) => {
 if (!alert.created_at || !alert.first_action_time) {return 0;}

 const created = new Date(alert.created_at);
 const action = new Date(alert.first_action_time);
 const diffMs = action - created;
 return Math.round(diffMs / (1000 * 60)); // 返回分钟
};

/**
 * 格式化统计数据
 */
export const formatStatValue = (value, metric) => {
 const metricConfig = STAT_METRICS[metric];
  if (!metricConfig) {return value;}

 switch (metricConfig.format) {
  case 'percentage':
  return `${value.toFixed(metricConfig.precision)}${metricConfig.unit}`;
  case 'number':
  return value.toFixed(metricConfig.precision);
  case 'trend':
  return `${value > 0 ? '+' : ''}${value.toFixed(metricConfig.precision)}${metricConfig.unit}`;
 default:
 return value;
 }
};

/**
 * 获取趋势方向
 */
export const getTrendDirection = (current, previous) => {
 if (!previous) {return 'stable';}
 const change = (current - previous) / previous * 100;

 if (change > 5) {return 'up';}
 if (change < -5) {return 'down';}
 return 'stable';
};

/**
 * 获取趋势颜色
 */
export const getTrendColor = (direction) => {
  switch (direction) {
  case 'up':
  return 'text-red-500';
 case 'down':
   return 'text-emerald-500';
 default:
  return 'text-gray-500';
 }
};

/**
 * 获取趋势图标
 */
export const getTrendIcon = (direction) => {
 switch (direction) {
  case 'up':
  return '\u2191';
  case 'down':
 return '\u2193';
 default:
  return '\u2192';
 }
};

/**
 * 生成时间序列数据
 */
export const generateTimeSeries = (data, timeDimension) => {
 const { groupBy: _groupBy, intervals } = TIME_DIMENSIONS[timeDimension];

 // 根据实际数据格式生成时间序列
 // 返回格式: { labels: [], values: [] }
 return {
  labels: Array.from({ length: intervals }, (_, i) => `时间${i + 1}`),
 values: Array.from({ length: intervals }, () => Math.floor(Math.random() * 100))
 };
};

// ==================== 工具函数（预警中心相关） ====================

/**
 * 获取预警级别配置（预警中心版）
 */
export const getAlertCenterLevelConfig = (level) => {
 return ALERT_LEVELS[level] || ALERT_LEVELS.INFO;
};

/**
 * 获取预警状态配置（预警中心版）
 */
export const getAlertCenterStatusConfig = (status) => {
 return ALERT_STATUS[status] || ALERT_STATUS.PENDING;
};

/**
 * 获取预警类型配置（预警中心版）
 */
export const getAlertCenterTypeConfig = (type) => {
 return ALERT_TYPES[type] || ALERT_TYPES.SYSTEM;
};

/**
 * 获取预警规则配置
 */
export const getAlertRuleConfig = (ruleType) => {
 return ALERT_RULES[ruleType] || ALERT_RULES.THRESHOLD;
};

/**
 * 获取通知渠道配置
 */
export const getNotificationChannelConfig = (channel) => {
 return NOTIFICATION_CHANNELS[channel] || NOTIFICATION_CHANNELS.SYSTEM;
};

/**
 * 计算预警响应时间（预警中心版，接受两个参数）
 */
export const calculateCenterResponseTime = (createdTime, firstActionTime) => {
 if (!createdTime || !firstActionTime) {return 0;}

 const created = new Date(createdTime);
 const action = new Date(firstActionTime);
 const diffMs = action - created;
 return Math.round(diffMs / (1000 * 60)); // 返回分钟
};

/**
 * 计算预警解决时间
 */
export const calculateResolutionTime = (createdTime, resolvedTime) => {
 if (!createdTime || !resolvedTime) {return 0;}

 const created = new Date(createdTime);
 const resolved = new Date(resolvedTime);
 const diffMs = resolved - created;
 return Math.round(diffMs / (1000 * 60 * 60)); // 返回小时
};

/**
 * 检查响应时间是否达标
 */
export const checkResponseTimeSLA = (responseTime, alertLevel) => {
 const levelConfig = getAlertCenterLevelConfig(alertLevel);
 const targetTime = ALERT_TIME_CONFIG.RESPONSE_TIME_WINDOWS[levelConfig.urgency.toUpperCase()];

 return responseTime <= targetTime.max;
};

/**
 * 检查解决时间是否达标
 */
export const checkResolutionTimeSLA = (resolutionTime, alertLevel) => {
 const levelConfig = getAlertCenterLevelConfig(alertLevel);
  const targetTime = ALERT_METRICS.RESOLUTION_TIME.target[levelConfig.level];

 return resolutionTime <= targetTime;
};

/**
 * 获取预警的下一个可执行操作
 */
export const getAvailableActions = (alert) => {
 const statusConfig = getAlertCenterStatusConfig(alert.status);
  return statusConfig ? statusConfig.nextActions : [];
};

/**
 * 验证预警规则配置
 */
export const validateAlertRule = (rule) => {
 const errors = [];

 // 验证必填字段
 if (!rule.name || rule.name.trim() === '') {
  errors.push('规则名称不能为空');
 }

 if (!rule.condition || rule.condition.trim() === '') {
 errors.push('触发条件不能为空');
  }

 if (!rule.threshold && rule.rule_type !== 'TIME_BASED') {
 errors.push('阈值不能为空');
 }

 // 验证数值范围
 if (rule.threshold && (isNaN(rule.threshold) || rule.threshold <= 0)) {
 errors.push('阈值必须是正数');
 }

 // 验证通知配置
  if (rule.notification_channels && rule.notification_channels.length === 0) {
  errors.push('至少需要配置一个通知渠道');
 }

 return errors;
};

/**
 * 生成预警编号
 */
export const generateAlertNumber = (type, date = new Date()) => {
 const typeCode = type.substring(0, 3).toUpperCase();
 const year = date.getFullYear();
 const month = String(date.getMonth() + 1).padStart(2, '0');
 const day = String(date.getDate()).padStart(2, '0');
 const sequence = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

 return `ALT${typeCode}${year}${month}${day}${sequence}`;
};

/**
 * 获取预警统计摘要
 */
export const getAlertSummary = (alerts, dateRange = null) => {
 let filteredAlerts = alerts;

 if (dateRange) {
 filteredAlerts = alerts.filter(alert => {
 const alertDate = new Date(alert.created_time);
   return alertDate >= dateRange.start && alertDate <= dateRange.end;
  });
  }

 const summary = {
  total: filteredAlerts.length,
 byLevel: {},
 byStatus: {},
 byType: {},
  responseTime: 0,
 resolutionTime: 0,
  escalated: 0
 };

 filteredAlerts.forEach(alert => {
 // 按级别统计
 const level = alert.alert_level || 'INFO';
 summary.byLevel[level] = (summary.byLevel[level] || 0) + 1;

 // 按状态统计
 const status = alert.status || 'PENDING';
 summary.byStatus[status] = (summary.byStatus[status] || 0) + 1;

  // 按类型统计
  const type = alert.alert_type || 'SYSTEM';
 summary.byType[type] = (summary.byType[type] || 0) + 1;

 // 统计响应和解决时间
  if (alert.first_action_time) {
  summary.responseTime += calculateCenterResponseTime(alert.created_time, alert.first_action_time);
 }

 if (alert.resolved_time) {
 summary.resolutionTime += calculateResolutionTime(alert.created_time, alert.resolved_time);
 }

 // 统计升级数量
 if (alert.escalated) {
 summary.escalated += 1;
  }
 });

 // 计算平均时间
 const actionableAlerts = filteredAlerts.filter(a => a.first_action_time);
 summary.avgResponseTime = actionableAlerts.length > 0
  ? Math.round(summary.responseTime / actionableAlerts.length)
 : 0;

 const resolvedAlerts = filteredAlerts.filter(a => a.resolved_time);
 summary.avgResolutionTime = resolvedAlerts.length > 0
 ? Math.round(summary.resolutionTime / resolvedAlerts.length)
 : 0;

 return summary;
};

/**
 * 检查是否需要升级
 */
export const requiresEscalation = (alert, currentTime = new Date()) => {
 if (!alert.created_time) {return false;}

 const created = new Date(alert.created_time);
 const elapsed = (currentTime - created) / (1000 * 60); // 分钟

 const levelConfig = getAlertCenterLevelConfig(alert.alert_level);
 if (!levelConfig.autoEscalate) {return false;}

  const escalationWindows = ALERT_TIME_CONFIG.ESCALATION_TIME_WINDOWS[levelConfig.level];
 return escalationWindows.intervals.some(interval => elapsed > interval);
};

/**
 * 获取预警严重程度分数
 */
export const getAlertSeverityScore = (level) => {
  const levelConfig = getAlertCenterLevelConfig(level);
 return levelConfig ? levelConfig.level : 1;
};

/**
 * 检查预警是否在工作时间
 */
export const isBusinessHour = (timestamp) => {
  const time = new Date(timestamp);
 const hour = time.getHours();
  const day = time.getDay();

 const { START, END, WORK_DAYS } = ALERT_TIME_CONFIG.BUSINESS_HOURS;

 return day >= WORK_DAYS[0] && day <= WORK_DAYS[WORK_DAYS.length - 1] &&
  hour >= parseInt(START.split(':')[0]) &&
  hour <= parseInt(END.split(':')[0]);
};

/**
 * 格式化预警时间显示
 */
export const formatAlertTime = (timestamp) => {
 if (!timestamp) {return '-';}

 const date = new Date(timestamp);
 const now = new Date();
 const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

 if (diffDays === 0) {
  return `今天 ${date.toLocaleTimeString()}`;
 } else if (diffDays === 1) {
 return `昨天 ${date.toLocaleTimeString()}`;
 } else if (diffDays < 7) {
  return `${diffDays}天前 ${date.toLocaleTimeString()}`;
 } else {
 return date.toLocaleString();
 }
};
