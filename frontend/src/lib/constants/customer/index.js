/**
 * 客户常量统一导出
 * 从子模块聚合所有导出，保持向后兼容
 */

// 基础配置
export {
  cn, formatDate, formatDateTime,
  statusConfigs, typeConfigs, priorityConfigs, channelConfigs,
  responseTimeConfigs, messageTypeConfigs, messageStatusConfigs,
} from './communication';

// 工具函数（获取配置、格式化、排序、验证、过滤）
export {
  getStatusConfig, getTypeConfig, getPriorityConfig,
  getChannelConfig, getResponseTimeConfig, getMessageTypeConfig, getMessageStatusConfig,
  formatStatus, formatType, formatPriority, formatChannel,
  formatResponseTime, formatMessageType, formatMessageStatus,
  sortByPriority, sortByCreatedTime, sortByStatus,
  isValidStatus, isValidType, isValidPriority, isValidChannel, isValidResponseTime,
  filterByStatus, filterByType, filterByPriority, filterByChannel, filterByCustomer,
} from './communicationHelpers';

// 枚举常量和兼容导出
export {
  COMMUNICATION_TYPE, COMMUNICATION_PRIORITY, COMMUNICATION_STATUS,
  COMMUNICATION_TOPIC, CUSTOMER_SATISFACTION, FOLLOW_UP_PRIORITY,
  COMMUNICATION_TYPE_LABELS, COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_STATUS_LABELS, COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION_LABELS, FOLLOW_UP_PRIORITY_LABELS,
  COMMUNICATION_TYPE_ICONS, COMMUNICATION_STATUS_COLORS,
  PRIORITY_COLORS, TOPIC_COLORS, SATISFACTION_COLORS,
  COMMUNICATION_STATS_CONFIG,
  COMMUNICATION_FILTER_OPTIONS, PRIORITY_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS, TOPIC_FILTER_OPTIONS,
  DEFAULT_COMMUNICATION_CONFIG, DEFAULT_FOLLOW_UP_CONFIG,
} from './communicationEnums';

// 统计函数与验证
export {
  getCommunicationTypeLabel, getCommunicationPriorityLabel,
  getCommunicationStatusLabel, getCommunicationTopicLabel,
  getCustomerSatisfactionLabel, getFollowUpPriorityLabel,
  getCommunicationStatusColor, getPriorityColor, getTopicColor,
  getSatisfactionColor, getCommunicationTypeIcon,
  calculateAverageSatisfaction, calculateResponseRate,
  getCommunicationStatusStats, getCommunicationTypeStats,
  getTopicDistributionStats, validateCommunicationData,
} from './communicationStats';

// 满意度相关
export {
  satisfactionScoreConfig, feedbackTypeConfig, feedbackStatusConfig,
  priorityConfig, analysisDimensionConfig,
  DEFAULT_SATISFACTION_STATS, DEFAULT_FEEDBACK_DATA,
  QUICK_FILTER_OPTIONS, CHART_TYPE_CONFIG,
  getSatisfactionScoreConfig, getFeedbackTypeConfig, getFeedbackStatusConfig,
  formatSatisfactionScore, getSatisfactionLevel,
  calculatePositiveRate, calculateResolutionRate,
  SATISFACTION_LEVELS, SURVEY_STATUS, SURVEY_TYPES,
  QUESTION_TYPES, ANALYSIS_PERIODS, FEEDBACK_CATEGORIES,
  CHART_COLORS, EXPORT_FORMATS, DEFAULT_FILTERS, TABLE_CONFIG,
  satisfactionConstants,
} from './satisfaction';

// 默认导出（兼容旧的 import customerConstants from ...）
import { statusConfigs, typeConfigs, priorityConfigs, channelConfigs, responseTimeConfigs, messageTypeConfigs, messageStatusConfigs } from './communication';
import { getStatusConfig, getTypeConfig, getPriorityConfig, getChannelConfig, getResponseTimeConfig, getMessageTypeConfig, getMessageStatusConfig, formatStatus, formatType, formatPriority, formatChannel, formatResponseTime, formatMessageType, formatMessageStatus, sortByPriority, sortByCreatedTime, sortByStatus, isValidStatus, isValidType, isValidPriority, isValidChannel, isValidResponseTime, filterByStatus, filterByType, filterByPriority, filterByChannel, filterByCustomer } from './communicationHelpers';

export default {
  statusConfigs, typeConfigs, priorityConfigs, channelConfigs,
  responseTimeConfigs, messageTypeConfigs, messageStatusConfigs,
  getStatusConfig, getTypeConfig, getPriorityConfig,
  getChannelConfig, getResponseTimeConfig, getMessageTypeConfig, getMessageStatusConfig,
  formatStatus, formatType, formatPriority, formatChannel,
  formatResponseTime, formatMessageType, formatMessageStatus,
  sortByPriority, sortByCreatedTime, sortByStatus,
  isValidStatus, isValidType, isValidPriority, isValidChannel, isValidResponseTime,
  filterByStatus, filterByType, filterByPriority, filterByChannel, filterByCustomer,
};
