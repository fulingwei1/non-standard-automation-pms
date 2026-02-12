/**
 * Customer Communication Configuration Constants
 * 客户沟通配置常量
 * 客户沟通跟踪配置常量
 */

import { cn, formatDate, formatDateTime } from "../utils";

export { cn, formatDate, formatDateTime };

// 沟通状态配置
export const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-50" },
  PENDING_REVIEW: { label: "待审核", color: "bg-amber-500", textColor: "text-amber-50" },
  PENDING_APPROVAL: { label: "待审批", color: "bg-yellow-500", textColor: "text-yellow-50" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500", textColor: "text-blue-50" },
  COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
  CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50" },
  ON_HOLD: { label: "暂停", color: "bg-orange-500", textColor: "text-orange-50" },
  CLOSED: { label: "已关闭", color: "bg-slate-600", textColor: "text-slate-50" },
  OVERDUE: { label: "已逾期", color: "bg-red-500", textColor: "text-red-50" },
};

// 沟通类型配置
export const typeConfigs = {
  // 客户需求类
  REQUIREMENT_CLARIFICATION: { label: "需求澄清", color: "bg-blue-500", textColor: "text-blue-50", icon: "❓" },
  REQUIREMENT_CHANGE: { label: "需求变更", color: "bg-blue-600", textColor: "text-blue-50", icon: "🔄" },
  REQUIREMENT_CONFIRMATION: { label: "需求确认", color: "bg-blue-400", textColor: "text-blue-50", icon: "✅" },
  REQUIREMENT_REVIEW: { label: "需求评审", color: "bg-blue-700", textColor: "text-blue-50", icon: "👁️" },

  // 技术交流类
  TECHNICAL_DISCUSSION: { label: "技术讨论", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "💬" },
  TECHNICAL_PRESENTATION: { label: "技术演示", color: "bg-cyan-600", textColor: "text-cyan-50", icon: "🎯" },
  TECHNICAL_CONFIRMATION: { label: "技术确认", color: "bg-cyan-400", textColor: "text-cyan-50", icon: "📋" },

  // 项目进展类
  PROGRESS_UPDATE: { label: "进展更新", color: "bg-emerald-500", textColor: "text-emerald-50", icon: "📈" },
  MILESTONE_REVIEW: { label: "里程碑评审", color: "bg-emerald-600", textColor: "text-emerald-50", icon: "🚩" },
  PHASE_COMPLETION: { label: "阶段完成", color: "bg-emerald-400", textColor: "text-emerald-50", icon: "✨" },

  // 问题处理类
  ISSUE_NOTIFICATION: { label: "问题通知", color: "bg-red-500", textColor: "text-red-50", icon: "🚨" },
  ISSUE_STATUS_UPDATE: { label: "问题状态更新", color: "bg-red-600", textColor: "text-red-50", icon: "🔍" },
  ISSUE_RESOLUTION: { label: "问题解决", color: "bg-red-400", textColor: "text-red-50", icon: "🎉" },

  // 客户服务类
  SERVICE_REQUEST: { label: "服务请求", color: "bg-purple-500", textColor: "text-purple-50", icon: "🔧" },
  COMPLAINT_HANDLING: { label: "投诉处理", color: "bg-purple-600", textColor: "text-purple-50", icon: "😞" },
  FEEDBACK_COLLECTION: { label: "反馈收集", color: "bg-purple-400", textColor: "text-purple-50", icon: "📝" },
  SATISFACTION_SURVEY: { label: "满意度调查", color: "bg-purple-700", textColor: "text-purple-50", icon: "📊" },

  // 商务洽谈类
  QUOTE_DISCUSSION: { label: "报价洽谈", color: "bg-amber-500", textColor: "text-amber-50", icon: "💰" },
  CONTRACT_NEGOTIATION: { label: "合同洽谈", color: "bg-amber-600", textColor: "text-amber-50", icon: "📄" },
  PAYMENT_DISCUSSION: { label: "付款讨论", color: "bg-amber-400", textColor: "text-amber-50", icon: "💳" },

  // 售后支持类
  AFTER_SALES_SUPPORT: { label: "售后支持", color: "bg-green-500", textColor: "text-green-50", icon: "🛟" },
  MAINTENANCE_NOTIFICATION: { label: "维保通知", color: "bg-green-600", textColor: "text-green-50", icon: "🔧" },
  WARRANTY_CLAIM: { label: "保修申请", color: "bg-green-400", textColor: "text-green-50", icon: "🛡️" },

  // 会议相关
  MEETING_INVITATION: { label: "会议邀请", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "📅" },
  MEETING_SUMMARY: { label: "会议纪要", color: "bg-indigo-600", textColor: "text-indigo-50", icon: "📝" },
  ACTION_ITEM_TRACKING: { label: "行动计划跟踪", color: "bg-indigo-400", textColor: "text-indigo-50", icon: "📋" },

  // 其他
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌" },
};

// 优先级配置
export const priorityConfigs = {
  LOW: { label: "低", color: "bg-slate-500", textColor: "text-slate-50", value: 1, icon: "🟢" },
  MEDIUM: { label: "中", color: "bg-blue-500", textColor: "text-blue-50", value: 2, icon: "🔵" },
  HIGH: { label: "高", color: "bg-orange-500", textColor: "text-orange-50", value: 3, icon: "🟠" },
  URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", value: 4, icon: "🔴" },
  CRITICAL: { label: "关键", color: "bg-purple-500", textColor: "text-purple-50", value: 5, icon: "⚡" },
};

// 沟通渠道配置
export const channelConfigs = {
  EMAIL: { label: "邮件", color: "bg-blue-500", textColor: "text-blue-50", icon: "✉️" },
  PHONE: { label: "电话", color: "bg-green-500", textColor: "text-green-50", icon: "📞" },
  WECHAT: { label: "微信", color: "bg-green-600", textColor: "text-green-50", icon: "💬" },
  MEETING: { label: "会议", color: "bg-purple-500", textColor: "text-purple-50", icon: "👥" },
  VISIT: { label: "拜访", color: "bg-amber-500", textColor: "text-amber-50", icon: "🏢" },
  VIDEO_CALL: { label: "视频会议", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "🎥" },
  SYSTEM: { label: "系统消息", color: "bg-slate-500", textColor: "text-slate-50", icon: "💻" },
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌" },
};

// 响应时间配置
export const responseTimeConfigs = {
  IMMEDIATE: { label: "即时", color: "bg-red-500", textColor: "text-red-50", hours: 0 },
  WITHIN_1_HOUR: { label: "1小时内", color: "bg-orange-500", textColor: "text-orange-50", hours: 1 },
  WITHIN_4_HOURS: { label: "4小时内", color: "bg-amber-500", textColor: "text-amber-50", hours: 4 },
  WITHIN_24_HOURS: { label: "24小时内", color: "bg-blue-500", textColor: "text-blue-50", hours: 24 },
  WITHIN_48_HOURS: { label: "48小时内", color: "bg-green-500", textColor: "text-green-50", hours: 48 },
  WITHIN_1_WEEK: { label: "1周内", color: "bg-slate-500", textColor: "text-slate-50", hours: 168 },
};

// 消息类型配置
export const messageTypeConfigs = {
  TEXT: { label: "文本", color: "bg-slate-500", textColor: "text-slate-50" },
  DOCUMENT: { label: "文档", color: "bg-blue-500", textColor: "text-blue-50", icon: "📄" },
  IMAGE: { label: "图片", color: "bg-green-500", textColor: "text-green-50", icon: "🖼️" },
  ATTACHMENT: { label: "附件", color: "bg-purple-500", textColor: "text-purple-50", icon: "📎" },
  LINK: { label: "链接", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "🔗" },
  TEMPLATE: { label: "模板", color: "bg-amber-500", textColor: "text-amber-50", icon: "📋" },
};

// 消息状态配置
export const messageStatusConfigs = {
  SENDING: { label: "发送中", color: "bg-blue-500", textColor: "text-blue-50" },
  SENT: { label: "已发送", color: "bg-green-500", textColor: "text-green-50" },
  DELIVERED: { label: "已送达", color: "bg-emerald-500", textColor: "text-emerald-50" },
  READ: { label: "已读", color: "bg-purple-500", textColor: "text-purple-50" },
  FAILED: { label: "发送失败", color: "bg-red-500", textColor: "text-red-50" },
  PENDING: { label: "待发送", color: "bg-amber-500", textColor: "text-amber-50" },
};

// 工具函数
export const getStatusConfig = (status) => {
  return statusConfigs[status] || statusConfigs.DRAFT;
};

export const getTypeConfig = (type) => {
  return typeConfigs[type] || typeConfigs.OTHER;
};

export const getPriorityConfig = (priority) => {
  if (priorityConfigs[priority]) {return priorityConfigs[priority];}
  if (priorityConfig?.[priority]) {return priorityConfig[priority];}
  const normalized = typeof priority === "string" ? priority.toLowerCase() : priority;
  if (normalized && priorityConfig?.[normalized]) {return priorityConfig[normalized];}
  return priorityConfigs.MEDIUM || priorityConfig?.medium;
};

export const getChannelConfig = (channel) => {
  return channelConfigs[channel] || channelConfigs.OTHER;
};

export const getResponseTimeConfig = (responseTime) => {
  return responseTimeConfigs[responseTime] || responseTimeConfigs.WITHIN_24_HOURS;
};

export const getMessageTypeConfig = (messageType) => {
  return messageTypeConfigs[messageType] || messageTypeConfigs.TEXT;
};

export const getMessageStatusConfig = (messageStatus) => {
  return messageStatusConfigs[messageStatus] || messageStatusConfigs.PENDING;
};

// 格式化函数
export const formatStatus = (status) => {
  return getStatusConfig(status).label;
};

export const formatType = (type) => {
  return getTypeConfig(type).label;
};

export const formatPriority = (priority) => {
  return getPriorityConfig(priority).label;
};

export const formatChannel = (channel) => {
  return getChannelConfig(channel).label;
};

export const formatResponseTime = (responseTime) => {
  return getResponseTimeConfig(responseTime).label;
};

export const formatMessageType = (messageType) => {
  return getMessageTypeConfig(messageType).label;
};

export const formatMessageStatus = (messageStatus) => {
  return getMessageStatusConfig(messageStatus).label;
};

// 排序函数
export const sortByPriority = (a, b) => {
  return getPriorityConfig(b.priority).value - getPriorityConfig(a.priority).value;
};

export const sortByCreatedTime = (a, b) => {
  const aDate = new Date(a.created_at || a.createdAt);
  const bDate = new Date(b.created_at || b.createdAt);
  return bDate.getTime() - aDate.getTime();
};

export const sortByStatus = (a, b) => {
  const statusOrder = ['DRAFT', 'PENDING_REVIEW', 'PENDING_APPROVAL', 'IN_PROGRESS', 'COMPLETED', 'CLOSED'];
  const aIndex = statusOrder.indexOf(a.status);
  const bIndex = statusOrder.indexOf(b.status);
  return aIndex - bIndex;
};

// 验证函数
export const isValidStatus = (status) => {
  return Object.keys(statusConfigs).includes(status);
};

export const isValidType = (type) => {
  return Object.keys(typeConfigs).includes(type);
};

export const isValidPriority = (priority) => {
  if (Object.keys(priorityConfigs).includes(priority)) {return true;}
  if (!priority) {return false;}
  const normalized = typeof priority === "string" ? priority.toLowerCase() : priority;
  return Object.keys(priorityConfig).includes(normalized);
};

export const isValidChannel = (channel) => {
  return Object.keys(channelConfigs).includes(channel);
};

export const isValidResponseTime = (responseTime) => {
  return Object.keys(responseTimeConfigs).includes(responseTime);
};

// 过滤函数
export const filterByStatus = (items, status) => {
  return items.filter(item => item.status === status);
};

export const filterByType = (items, type) => {
  return items.filter(item => item.communication_type === type);
};

export const filterByPriority = (items, priority) => {
  return items.filter(item => item.priority === priority);
};

export const filterByChannel = (items, channel) => {
  return items.filter(item => item.channel === channel);
};

export const filterByCustomer = (items, customerId) => {
  return items.filter(item => item.customer_id === customerId);
};

export default {
  statusConfigs,
  typeConfigs,
  priorityConfigs,
  channelConfigs,
  responseTimeConfigs,
  messageTypeConfigs,
  messageStatusConfigs,
  getStatusConfig,
  getTypeConfig,
  getPriorityConfig,
  getChannelConfig,
  getResponseTimeConfig,
  getMessageTypeConfig,
  getMessageStatusConfig,
  formatStatus,
  formatType,
  formatPriority,
  formatChannel,
  formatResponseTime,
  formatMessageType,
  formatMessageStatus,
  sortByPriority,
  sortByCreatedTime,
  sortByStatus,
  isValidStatus,
  isValidType,
  isValidPriority,
  isValidChannel,
  isValidResponseTime,
  filterByStatus,
  filterByType,
  filterByPriority,
  filterByChannel,
  filterByCustomer,
  // 兼容导出（来自 customerCommunicationConstants.js）
  COMMUNICATION_TYPE,
  COMMUNICATION_PRIORITY,
  COMMUNICATION_STATUS,
  COMMUNICATION_TOPIC,
  CUSTOMER_SATISFACTION,
  FOLLOW_UP_PRIORITY,
  COMMUNICATION_TYPE_LABELS,
  COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_STATUS_LABELS,
  COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION_LABELS,
  FOLLOW_UP_PRIORITY_LABELS,
  COMMUNICATION_TYPE_ICONS,
  COMMUNICATION_STATUS_COLORS,
  PRIORITY_COLORS,
  TOPIC_COLORS,
  SATISFACTION_COLORS,
  COMMUNICATION_STATS_CONFIG,
  COMMUNICATION_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  TOPIC_FILTER_OPTIONS,
  DEFAULT_COMMUNICATION_CONFIG,
  DEFAULT_FOLLOW_UP_CONFIG,
};

// ==================== 兼容导出（来自 customerCommunicationConstants.js）====================

// 简单枚举定义
export const COMMUNICATION_TYPE = {
  PHONE: 'phone',
  EMAIL: 'email',
  ON_SITE: 'on_site',
  WECHAT: 'wechat',
  MEETING: 'meeting',
  VIDEO_CALL: 'video_call'
};

export const COMMUNICATION_PRIORITY = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
};

export const COMMUNICATION_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FOLLOW_UP: 'follow_up'
};

export const COMMUNICATION_TOPIC = {
  SALES: 'sales',
  SUPPORT: 'support',
  COMPLAINT: 'complaint',
  CONSULTATION: 'consultation',
  FEEDBACK: 'feedback',
  TRAINING: 'training',
  MAINTENANCE: 'maintenance',
  OTHER: 'other'
};

export const CUSTOMER_SATISFACTION = {
  VERY_SATISFIED: 5,
  SATISFIED: 4,
  NEUTRAL: 3,
  DISSATISFIED: 2,
  VERY_DISSATISFIED: 1
};

export const FOLLOW_UP_PRIORITY = {
  URGENT: 'urgent',
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
};

// 标签映射
export const COMMUNICATION_TYPE_LABELS = {
  [COMMUNICATION_TYPE.PHONE]: '电话',
  [COMMUNICATION_TYPE.EMAIL]: '邮件',
  [COMMUNICATION_TYPE.ON_SITE]: '现场',
  [COMMUNICATION_TYPE.WECHAT]: '微信',
  [COMMUNICATION_TYPE.MEETING]: '会议',
  [COMMUNICATION_TYPE.VIDEO_CALL]: '视频通话'
};

export const COMMUNICATION_PRIORITY_LABELS = {
  [COMMUNICATION_PRIORITY.HIGH]: '高优先级',
  [COMMUNICATION_PRIORITY.MEDIUM]: '中优先级',
  [COMMUNICATION_PRIORITY.LOW]: '低优先级'
};

export const COMMUNICATION_STATUS_LABELS = {
  [COMMUNICATION_STATUS.PENDING]: '待处理',
  [COMMUNICATION_STATUS.IN_PROGRESS]: '进行中',
  [COMMUNICATION_STATUS.COMPLETED]: '已完成',
  [COMMUNICATION_STATUS.FOLLOW_UP]: '需要跟进'
};

export const COMMUNICATION_TOPIC_LABELS = {
  [COMMUNICATION_TOPIC.SALES]: '销售',
  [COMMUNICATION_TOPIC.SUPPORT]: '技术支持',
  [COMMUNICATION_TOPIC.COMPLAINT]: '投诉',
  [COMMUNICATION_TOPIC.CONSULTATION]: '咨询',
  [COMMUNICATION_TOPIC.FEEDBACK]: '反馈',
  [COMMUNICATION_TOPIC.TRAINING]: '培训',
  [COMMUNICATION_TOPIC.MAINTENANCE]: '维护',
  [COMMUNICATION_TOPIC.OTHER]: '其他'
};

export const CUSTOMER_SATISFACTION_LABELS = {
  [CUSTOMER_SATISFACTION.VERY_SATISFIED]: '非常满意',
  [CUSTOMER_SATISFACTION.SATISFIED]: '满意',
  [CUSTOMER_SATISFACTION.NEUTRAL]: '一般',
  [CUSTOMER_SATISFACTION.DISSATISFIED]: '不满意',
  [CUSTOMER_SATISFACTION.VERY_DISSATISFIED]: '非常不满意'
};

export const FOLLOW_UP_PRIORITY_LABELS = {
  [FOLLOW_UP_PRIORITY.URGENT]: '紧急',
  [FOLLOW_UP_PRIORITY.HIGH]: '高',
  [FOLLOW_UP_PRIORITY.MEDIUM]: '中',
  [FOLLOW_UP_PRIORITY.LOW]: '低'
};

// 图标配置
export const COMMUNICATION_TYPE_ICONS = {
  [COMMUNICATION_TYPE.PHONE]: '📞',
  [COMMUNICATION_TYPE.EMAIL]: '📧',
  [COMMUNICATION_TYPE.ON_SITE]: '🏢',
  [COMMUNICATION_TYPE.WECHAT]: '💬',
  [COMMUNICATION_TYPE.MEETING]: '👥',
  [COMMUNICATION_TYPE.VIDEO_CALL]: '📹'
};

// 颜色配置
export const COMMUNICATION_STATUS_COLORS = {
  [COMMUNICATION_STATUS.PENDING]: '#8B5CF6',
  [COMMUNICATION_STATUS.IN_PROGRESS]: '#F59E0B',
  [COMMUNICATION_STATUS.COMPLETED]: '#10B981',
  [COMMUNICATION_STATUS.FOLLOW_UP]: '#3B82F6'
};

export const PRIORITY_COLORS = {
  [COMMUNICATION_PRIORITY.HIGH]: '#EF4444',
  [COMMUNICATION_PRIORITY.MEDIUM]: '#F59E0B',
  [COMMUNICATION_PRIORITY.LOW]: '#10B981'
};

export const TOPIC_COLORS = {
  [COMMUNICATION_TOPIC.SALES]: '#3B82F6',
  [COMMUNICATION_TOPIC.SUPPORT]: '#10B981',
  [COMMUNICATION_TOPIC.COMPLAINT]: '#EF4444',
  [COMMUNICATION_TOPIC.CONSULTATION]: '#8B5CF6',
  [COMMUNICATION_TOPIC.FEEDBACK]: '#F59E0B',
  [COMMUNICATION_TOPIC.TRAINING]: '#06B6D4',
  [COMMUNICATION_TOPIC.MAINTENANCE]: '#6B7280',
  [COMMUNICATION_TOPIC.OTHER]: '#EC4899'
};

export const SATISFACTION_COLORS = {
  [CUSTOMER_SATISFACTION.VERY_SATISFIED]: '#10B981',
  [CUSTOMER_SATISFACTION.SATISFIED]: '#22C55E',
  [CUSTOMER_SATISFACTION.NEUTRAL]: '#F59E0B',
  [CUSTOMER_SATISFACTION.DISSATISFIED]: '#F97316',
  [CUSTOMER_SATISFACTION.VERY_DISSATISFIED]: '#EF4444'
};

// 统计配置
export const COMMUNICATION_STATS_CONFIG = {
  TOTAL_COMMUNICATIONS: 'total_communications',
  PENDING_COMMUNICATIONS: 'pending_communications',
  IN_PROGRESS_COMMUNICATIONS: 'in_progress_communications',
  COMPLETED_COMMUNICATIONS: 'completed_communications',
  FOLLOW_UP_COMMUNICATIONS: 'follow_up_communications',
  AVERAGE_SATISFACTION: 'average_satisfaction',
  RESPONSE_RATE: 'response_rate'
};

// 工具函数（兼容版本）
export const getCommunicationTypeLabel = (type) => {
  return COMMUNICATION_TYPE_LABELS[type] || type;
};

export const getCommunicationPriorityLabel = (priority) => {
  return COMMUNICATION_PRIORITY_LABELS[priority] || priority;
};

export const getCommunicationStatusLabel = (status) => {
  return COMMUNICATION_STATUS_LABELS[status] || status;
};

export const getCommunicationTopicLabel = (topic) => {
  return COMMUNICATION_TOPIC_LABELS[topic] || topic;
};

export const getCustomerSatisfactionLabel = (rating) => {
  return CUSTOMER_SATISFACTION_LABELS[rating] || rating;
};

export const getFollowUpPriorityLabel = (priority) => {
  return FOLLOW_UP_PRIORITY_LABELS[priority] || priority;
};

export const getCommunicationStatusColor = (status) => {
  return COMMUNICATION_STATUS_COLORS[status] || '#6B7280';
};

export const getPriorityColor = (priority) => {
  return PRIORITY_COLORS[priority] || '#6B7280';
};

export const getTopicColor = (topic) => {
  return TOPIC_COLORS[topic] || '#6B7280';
};

export const getSatisfactionColor = (value) => {
  if (value === null || value === undefined) {return '#6B7280';}
  const numeric = typeof value === "number" ? value : Number.parseFloat(value);
  if (!Number.isNaN(numeric)) {
    return getSatisfactionScoreConfig(numeric).color;
  }
  if (SATISFACTION_COLORS[value]) {return SATISFACTION_COLORS[value];}
  const normalized = typeof value === "string" ? value.toLowerCase() : value;
  return SATISFACTION_COLORS[normalized] || '#6B7280';
};

export const getCommunicationTypeIcon = (type) => {
  return COMMUNICATION_TYPE_ICONS[type] || '📋';
};

// 统计函数
export const calculateAverageSatisfaction = (communications) => {
  if (!communications || communications.length === 0) {return 0;}
  const validRatings = communications
    .filter(comm => comm.satisfaction_rating)
    .map(comm => comm.satisfaction_rating);
  if (validRatings.length === 0) {return 0;}
  const sum = validRatings.reduce((total, rating) => total + rating, 0);
  return (sum / validRatings.length).toFixed(1);
};

export const calculateResponseRate = (communications) => {
  if (!communications || communications.length === 0) {return 0;}
  const respondedCommunications = communications.filter(comm =>
    comm.status === COMMUNICATION_STATUS.COMPLETED ||
    comm.status === COMMUNICATION_STATUS.FOLLOW_UP
  );
  return ((respondedCommunications.length / communications.length) * 100).toFixed(1);
};

export const getCommunicationStatusStats = (communications) => {
  const stats = {
    total: communications.length,
    pending: 0,
    inProgress: 0,
    completed: 0,
    followUp: 0
  };
  communications.forEach(comm => {
    switch (comm.status) {
      case COMMUNICATION_STATUS.PENDING:
        stats.pending++;
        break;
      case COMMUNICATION_STATUS.IN_PROGRESS:
        stats.inProgress++;
        break;
      case COMMUNICATION_STATUS.COMPLETED:
        stats.completed++;
        break;
      case COMMUNICATION_STATUS.FOLLOW_UP:
        stats.followUp++;
        break;
    }
  });
  return stats;
};

export const getCommunicationTypeStats = (communications) => {
  const stats = {};
  Object.values(COMMUNICATION_TYPE).forEach(type => {
    stats[type] = 0;
  });
  communications.forEach(comm => {
    if (comm.communication_type) {
      stats[comm.communication_type] = (stats[comm.communication_type] || 0) + 1;
    }
  });
  return stats;
};

export const getTopicDistributionStats = (communications) => {
  const stats = {};
  Object.values(COMMUNICATION_TOPIC).forEach(topic => {
    stats[topic] = 0;
  });
  communications.forEach(comm => {
    if (comm.topic) {
      stats[comm.topic] = (stats[comm.topic] || 0) + 1;
    }
  });
  return stats;
};

export const validateCommunicationData = (communicationData) => {
  const errors = [];
  if (!communicationData.customer_id) {
    errors.push('客户ID不能为空');
  }
  if (!communicationData.communication_type) {
    errors.push('沟通方式不能为空');
  }
  if (!communicationData.topic) {
    errors.push('沟通主题不能为空');
  }
  if (!communicationData.subject) {
    errors.push('沟通标题不能为空');
  }
  if (!communicationData.communication_date) {
    errors.push('沟通日期不能为空');
  }
  return {
    isValid: errors.length === 0,
    errors
  };
};

// 过滤选项
export const COMMUNICATION_FILTER_OPTIONS = [
  { value: 'all', label: '全部状态' },
  { value: COMMUNICATION_STATUS.PENDING, label: '待处理' },
  { value: COMMUNICATION_STATUS.IN_PROGRESS, label: '进行中' },
  { value: COMMUNICATION_STATUS.COMPLETED, label: '已完成' },
  { value: COMMUNICATION_STATUS.FOLLOW_UP, label: '需要跟进' }
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
  { value: COMMUNICATION_PRIORITY.HIGH, label: '高优先级' },
  { value: COMMUNICATION_PRIORITY.MEDIUM, label: '中优先级' },
  { value: COMMUNICATION_PRIORITY.LOW, label: '低优先级' }
];

export const TYPE_FILTER_OPTIONS = [
  { value: 'all', label: '全部方式' },
  { value: COMMUNICATION_TYPE.PHONE, label: '电话' },
  { value: COMMUNICATION_TYPE.EMAIL, label: '邮件' },
  { value: COMMUNICATION_TYPE.ON_SITE, label: '现场' },
  { value: COMMUNICATION_TYPE.WECHAT, label: '微信' },
  { value: COMMUNICATION_TYPE.MEETING, label: '会议' },
  { value: COMMUNICATION_TYPE.VIDEO_CALL, label: '视频通话' }
];

export const TOPIC_FILTER_OPTIONS = [
  { value: 'all', label: '全部主题' },
  { value: COMMUNICATION_TOPIC.SALES, label: '销售' },
  { value: COMMUNICATION_TOPIC.SUPPORT, label: '技术支持' },
  { value: COMMUNICATION_TOPIC.COMPLAINT, label: '投诉' },
  { value: COMMUNICATION_TOPIC.CONSULTATION, label: '咨询' },
  { value: COMMUNICATION_TOPIC.FEEDBACK, label: '反馈' },
  { value: COMMUNICATION_TOPIC.TRAINING, label: '培训' },
  { value: COMMUNICATION_TOPIC.MAINTENANCE, label: '维护' },
  { value: COMMUNICATION_TOPIC.OTHER, label: '其他' }
];

// 默认配置
export const DEFAULT_COMMUNICATION_CONFIG = {
  status: COMMUNICATION_STATUS.PENDING,
  priority: COMMUNICATION_PRIORITY.MEDIUM,
  communication_type: COMMUNICATION_TYPE.PHONE,
  topic: COMMUNICATION_TOPIC.SUPPORT,
  satisfaction_rating: null,
  follow_up_priority: FOLLOW_UP_PRIORITY.MEDIUM
};

export const DEFAULT_FOLLOW_UP_CONFIG = {
  priority: FOLLOW_UP_PRIORITY.MEDIUM,
  due_date: null,
  assigned_to: null,
  notes: ''
};

// === Migrated from components/customer-satisfaction/satisfactionConstants.js ===
/**
 * Customer Satisfaction Management Constants
 * 客户满意度管理系统常量配置
 * 包含满意度评分、反馈类型、分析维度等配置
 */

// ==================== 满意度评分等级配置 ====================
export const satisfactionScoreConfig = {
  excellent: {
    label: "非常满意",
    value: 5,
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    progress: "bg-emerald-500",
    description: "超出预期，体验极佳"
  },
  good: {
    label: "满意",
    value: 4,
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    progress: "bg-blue-500",
    description: "符合预期，体验良好"
  },
  average: {
    label: "一般",
    value: 3,
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    progress: "bg-amber-500",
    description: "基本符合预期，有改进空间"
  },
  poor: {
    label: "不满意",
    value: 2,
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    progress: "bg-orange-500",
    description: "未达预期，需要改进"
  },
  terrible: {
    label: "非常不满意",
    value: 1,
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    progress: "bg-red-500",
    description: "远低于预期，急需改进"
  }
};

// ==================== 反馈类型配置 ====================
export const feedbackTypeConfig = {
  product_quality: {
    label: "产品质量",
    value: "product_quality",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Package"
  },
  service_support: {
    label: "服务支持",
    value: "service_support",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "Headphones"
  },
  delivery_speed: {
    label: "交付速度",
    value: "delivery_speed",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "Truck"
  },
  technical_solution: {
    label: "技术方案",
    value: "technical_solution",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Cpu"
  },
  communication: {
    label: "沟通协调",
    value: "communication",
    color: "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
    icon: "MessageCircle"
  },
  price_value: {
    label: "价格价值",
    value: "price_value",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "DollarSign"
  },
  after_sales: {
    label: "售后服务",
    value: "after_sales",
    color: "text-pink-400 bg-pink-400/10 border-pink-400/30",
    icon: "Wrench"
  }
};

// ==================== 反馈状态配置 ====================
export const feedbackStatusConfig = {
  pending: {
    label: "待处理",
    value: "pending",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Clock"
  },
  in_progress: {
    label: "处理中",
    value: "in_progress",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "RefreshCw"
  },
  resolved: {
    label: "已解决",
    value: "resolved",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "CheckCircle2"
  },
  closed: {
    label: "已关闭",
    value: "closed",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    icon: "XCircle"
  }
};

// ==================== 优先级配置 ====================
export const priorityConfig = {
  critical: {
    label: "紧急",
    value: "critical",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "AlertTriangle",
    responseTime: "2小时内"
  },
  high: {
    label: "高",
    value: "high",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "AlertCircle",
    responseTime: "24小时内"
  },
  medium: {
    label: "中",
    value: "medium",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "AlertSquare",
    responseTime: "3天内"
  },
  low: {
    label: "低",
    value: "low",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Info",
    responseTime: "1周内"
  }
};

// ==================== 分析维度配置 ====================
export const analysisDimensionConfig = {
  overall_satisfaction: {
    label: "总体满意度",
    key: "overall_satisfaction",
    description: "客户对产品/服务的整体评价",
    weight: 0.25
  },
  product_performance: {
    label: "产品性能",
    key: "product_performance",
    description: "产品质量、稳定性、功能满足度",
    weight: 0.2
  },
  service_quality: {
    label: "服务质量",
    key: "service_quality",
    description: "响应速度、解决问题能力、服务态度",
    weight: 0.2
  },
  delivery_experience: {
    label: "交付体验",
    key: "delivery_experience",
    description: "交付准时性、包装质量、文档完整性",
    weight: 0.15
  },
  technical_support: {
    label: "技术支持",
    key: "technical_support",
    description: "技术方案、培训、售后服务",
    weight: 0.2
  }
};

// ==================== 默认数据配置 ====================
export const DEFAULT_SATISFACTION_STATS = {
  totalResponses: 0,
  averageScore: 0,
  responseRate: 0,
  positiveRate: 0,
  resolvedRate: 0,
  pendingFeedback: 0,
  totalCustomers: 0,
  satisfiedCustomers: 0
};

export const DEFAULT_FEEDBACK_DATA = {
  id: "",
  customerId: "",
  customerName: "",
  customerLevel: "regular",
  rating: 0,
  feedbackType: "product_quality",
  content: "",
  status: "pending",
  priority: "medium",
  createdAt: "",
  resolvedAt: "",
  assignedTo: "",
  resolution: ""
};

// ==================== 快速筛选配置 ====================
export const QUICK_FILTER_OPTIONS = [
  {
    key: "all",
    label: "全部反馈",
    filter: () => true
  },
  {
    key: "pending",
    label: "待处理",
    filter: (item) => item.status === "pending"
  },
  {
    key: "in_progress",
    label: "处理中",
    filter: (item) => item.status === "in_progress"
  },
  {
    key: "resolved",
    label: "已解决",
    filter: (item) => item.status === "resolved"
  },
  {
    key: "high_priority",
    label: "高优先级",
    filter: (item) => ["critical", "high"].includes(item.priority)
  },
  {
    key: "positive",
    label: "正面反馈",
    filter: (item) => item.rating >= 4
  },
  {
    key: "negative",
    label: "负面反馈",
    filter: (item) => item.rating <= 2
  }
];

// ==================== 图表类型配置 ====================
export const CHART_TYPE_CONFIG = {
  trend: {
    label: "满意度趋势",
    value: "trend",
    description: "展示满意度随时间的变化趋势"
  },
  distribution: {
    label: "评分分布",
    value: "distribution",
    description: "展示各评分等级的分布情况"
  },
  type_analysis: {
    label: "类型分析",
    value: "type_analysis",
    description: "按反馈类型分析满意度情况"
  },
  department: {
    label: "部门对比",
    value: "department",
    description: "不同部门的满意度对比"
  },
  customer_segment: {
    label: "客户分层",
    value: "customer_segment",
    description: "不同客户等级的满意度对比"
  }
};

// ==================== 工具函数 ====================

// 获取满意度评分配置
export const getSatisfactionScoreConfig = (score) => {
  if (score >= 5) {return satisfactionScoreConfig.excellent;}
  if (score >= 4) {return satisfactionScoreConfig.good;}
  if (score >= 3) {return satisfactionScoreConfig.average;}
  if (score >= 2) {return satisfactionScoreConfig.poor;}
  return satisfactionScoreConfig.terrible;
};

// 获取反馈类型配置
export const getFeedbackTypeConfig = (type) => {
  return feedbackTypeConfig[type] || feedbackTypeConfig.product_quality;
};

// 获取反馈状态配置
export const getFeedbackStatusConfig = (status) => {
  return feedbackStatusConfig[status] || feedbackStatusConfig.pending;
};

// 格式化满意度评分
export const formatSatisfactionScore = (score) => {
  if (!score) {return "-";}
  return `${score.toFixed(1)}分`;
};

// 计算满意度等级
export const getSatisfactionLevel = (score) => {
  if (score >= 4.5) {return "excellent";}
  if (score >= 3.5) {return "good";}
  if (score >= 2.5) {return "average";}
  if (score >= 1.5) {return "poor";}
  return "terrible";
};

// 计算正面反馈比例
export const calculatePositiveRate = (feedbacks) => {
  if (!feedbacks || feedbacks.length === 0) {return 0;}
  const positiveCount = feedbacks.filter(f => f.rating >= 4).length;
  return ((positiveCount / feedbacks.length) * 100).toFixed(1);
};

// 计算解决率
export const calculateResolutionRate = (feedbacks) => {
  if (!feedbacks || feedbacks.length === 0) {return 0;}
  const resolvedCount = feedbacks.filter(f => ["resolved", "closed"].includes(f.status)).length;
  return ((resolvedCount / feedbacks.length) * 100).toFixed(1);
};

// ==================== 兼容导出（来自 customerSatisfactionConstants.js）====================

// 满意度等级配置（简化版，用于向后兼容）
export const SATISFACTION_LEVELS = {
  VERY_SATISFIED: { value: 5, label: '非常满意', color: '#52c41a', icon: '😊' },
  SATISFIED: { value: 4, label: '满意', color: '#1890ff', icon: '🙂' },
  NEUTRAL: { value: 3, label: '一般', color: '#faad14', icon: '😐' },
  DISSATISFIED: { value: 2, label: '不满意', color: '#ff7a45', icon: '😕' },
  VERY_DISSATISFIED: { value: 1, label: '非常不满意', color: '#ff4d4f', icon: '😞' }
};

// 调研状态配置
export const SURVEY_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  ACTIVE: { value: 'active', label: '进行中', color: '#52c41a' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#1890ff' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

// 调研类型配置
export const SURVEY_TYPES = {
  SERVICE: { value: 'service', label: '服务满意度' },
  PRODUCT: { value: 'product', label: '产品满意度' },
  SUPPORT: { value: 'support', label: '技术支持满意度' },
  OVERALL: { value: 'overall', label: '综合满意度' }
};

// 问题类型配置
export const QUESTION_TYPES = {
  RATING: { value: 'rating', label: '评分题' },
  TEXT: { value: 'text', label: '文本题' },
  CHOICE: { value: 'choice', label: '选择题' },
  MULTIPLE_CHOICE: { value: 'multiple_choice', label: '多选题' }
};

// 分析周期配置
export const ANALYSIS_PERIODS = {
  WEEK: { value: 'week', label: '最近一周' },
  MONTH: { value: 'month', label: '最近一月' },
  QUARTER: { value: 'quarter', label: '最近一季' },
  YEAR: { value: 'year', label: '最近一年' }
};

// 反馈分类配置
export const FEEDBACK_CATEGORIES = {
  QUALITY: { value: 'quality', label: '质量问题' },
  SERVICE: { value: 'service', label: '服务问题' },
  DELIVERY: { value: 'delivery', label: '交付问题' },
  COMMUNICATION: { value: 'communication', label: '沟通问题' },
  PRICING: { value: 'pricing', label: '价格问题' },
  OTHER: { value: 'other', label: '其他问题' }
};

// 图表颜色配置
export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  NEUTRAL: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

// 导出格式配置
export const EXPORT_FORMATS = {
  EXCEL: { value: 'excel', label: 'Excel表格' },
  PDF: { value: 'pdf', label: 'PDF报告' },
  CSV: { value: 'csv', label: 'CSV数据' },
  JSON: { value: 'json', label: 'JSON数据' }
};

// 默认筛选配置
export const DEFAULT_FILTERS = {
  dateRange: null,
  surveyType: null,
  status: null,
  satisfactionLevel: null,
  category: null
};

// 表格配置
export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1200, y: 400 },
  size: 'middle'
};

// 导出配置对象
export const satisfactionConstants = {
  satisfactionScoreConfig,
  feedbackTypeConfig,
  feedbackStatusConfig,
  priorityConfig,
  analysisDimensionConfig,
  DEFAULT_SATISFACTION_STATS,
  DEFAULT_FEEDBACK_DATA,
  QUICK_FILTER_OPTIONS,
  CHART_TYPE_CONFIG,
  // 兼容导出
  SATISFACTION_LEVELS,
  SURVEY_STATUS,
  SURVEY_TYPES,
  QUESTION_TYPES,
  ANALYSIS_PERIODS,
  FEEDBACK_CATEGORIES,
  CHART_COLORS,
  EXPORT_FORMATS,
  DEFAULT_FILTERS,
  TABLE_CONFIG,
};
