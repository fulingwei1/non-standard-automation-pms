/**
 * 客户沟通统计与验证函数
 */

import {
  COMMUNICATION_TYPE,
  COMMUNICATION_TYPE_LABELS,
  COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_STATUS,
  COMMUNICATION_STATUS_LABELS,
  COMMUNICATION_TOPIC,
  COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION_LABELS,
  FOLLOW_UP_PRIORITY_LABELS,
  COMMUNICATION_TYPE_ICONS,
  COMMUNICATION_STATUS_COLORS,
  PRIORITY_COLORS,
  TOPIC_COLORS,
  SATISFACTION_COLORS,
} from './communicationEnums';
import { getSatisfactionScoreConfig } from './satisfaction';

// 工具函数（兼容版本）
export const getCommunicationTypeLabel = (type) => COMMUNICATION_TYPE_LABELS[type] || type;
export const getCommunicationPriorityLabel = (priority) => COMMUNICATION_PRIORITY_LABELS[priority] || priority;
export const getCommunicationStatusLabel = (status) => COMMUNICATION_STATUS_LABELS[status] || status;
export const getCommunicationTopicLabel = (topic) => COMMUNICATION_TOPIC_LABELS[topic] || topic;
export const getCustomerSatisfactionLabel = (rating) => CUSTOMER_SATISFACTION_LABELS[rating] || rating;
export const getFollowUpPriorityLabel = (priority) => FOLLOW_UP_PRIORITY_LABELS[priority] || priority;
export const getCommunicationStatusColor = (status) => COMMUNICATION_STATUS_COLORS[status] || '#6B7280';
export const getPriorityColor = (priority) => PRIORITY_COLORS[priority] || '#6B7280';
export const getTopicColor = (topic) => TOPIC_COLORS[topic] || '#6B7280';
export const getCommunicationTypeIcon = (type) => COMMUNICATION_TYPE_ICONS[type] || '📋';

export const getSatisfactionColor = (value) => {
  if (value === null || value === undefined) return '#6B7280';
  const numeric = typeof value === "number" ? value : Number.parseFloat(value);
  if (!Number.isNaN(numeric)) {
    return getSatisfactionScoreConfig(numeric).color;
  }
  if (SATISFACTION_COLORS[value]) return SATISFACTION_COLORS[value];
  const normalized = typeof value === "string" ? value.toLowerCase() : value;
  return SATISFACTION_COLORS[normalized] || '#6B7280';
};

// 统计函数
export const calculateAverageSatisfaction = (communications) => {
  if (!communications || communications.length === 0) return 0;
  const validRatings = communications
    .filter(comm => comm.satisfaction_rating)
    .map(comm => comm.satisfaction_rating);
  if (validRatings.length === 0) return 0;
  const sum = validRatings.reduce((total, rating) => total + rating, 0);
  return (sum / validRatings.length).toFixed(1);
};

export const calculateResponseRate = (communications) => {
  if (!communications || communications.length === 0) return 0;
  const respondedCommunications = communications.filter(comm =>
    comm.status === COMMUNICATION_STATUS.COMPLETED ||
    comm.status === COMMUNICATION_STATUS.FOLLOW_UP
  );
  return ((respondedCommunications.length / communications.length) * 100).toFixed(1);
};

export const getCommunicationStatusStats = (communications) => {
  const stats = { total: communications.length, pending: 0, inProgress: 0, completed: 0, followUp: 0 };
  communications.forEach(comm => {
    switch (comm.status) {
      case COMMUNICATION_STATUS.PENDING: stats.pending++; break;
      case COMMUNICATION_STATUS.IN_PROGRESS: stats.inProgress++; break;
      case COMMUNICATION_STATUS.COMPLETED: stats.completed++; break;
      case COMMUNICATION_STATUS.FOLLOW_UP: stats.followUp++; break;
    }
  });
  return stats;
};

export const getCommunicationTypeStats = (communications) => {
  const stats = {};
  Object.values(COMMUNICATION_TYPE).forEach(type => { stats[type] = 0; });
  communications.forEach(comm => {
    if (comm.communication_type) {
      stats[comm.communication_type] = (stats[comm.communication_type] || 0) + 1;
    }
  });
  return stats;
};

export const getTopicDistributionStats = (communications) => {
  const stats = {};
  Object.values(COMMUNICATION_TOPIC).forEach(topic => { stats[topic] = 0; });
  communications.forEach(comm => {
    if (comm.topic) {
      stats[comm.topic] = (stats[comm.topic] || 0) + 1;
    }
  });
  return stats;
};

export const validateCommunicationData = (communicationData) => {
  const errors = [];
  if (!communicationData.customer_id) errors.push('客户ID不能为空');
  if (!communicationData.communication_type) errors.push('沟通方式不能为空');
  if (!communicationData.topic) errors.push('沟通主题不能为空');
  if (!communicationData.subject) errors.push('沟通标题不能为空');
  if (!communicationData.communication_date) errors.push('沟通日期不能为空');
  return { isValid: errors.length === 0, errors };
};
