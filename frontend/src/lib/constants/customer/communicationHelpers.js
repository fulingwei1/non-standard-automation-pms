/**
 * 客户沟通工具函数
 * 获取配置、格式化、排序、验证、过滤等
 */

import {
  statusConfigs,
  typeConfigs,
  priorityConfigs,
  channelConfigs,
  responseTimeConfigs,
  messageTypeConfigs,
  messageStatusConfigs,
} from './communication';
import { priorityConfig } from './satisfaction';

// 获取配置的工具函数
export const getStatusConfig = (status) => statusConfigs[status] || statusConfigs.DRAFT;
export const getTypeConfig = (type) => typeConfigs[type] || typeConfigs.OTHER;
export const getChannelConfig = (channel) => channelConfigs[channel] || channelConfigs.OTHER;
export const getResponseTimeConfig = (responseTime) => responseTimeConfigs[responseTime] || responseTimeConfigs.WITHIN_24_HOURS;
export const getMessageTypeConfig = (messageType) => messageTypeConfigs[messageType] || messageTypeConfigs.TEXT;
export const getMessageStatusConfig = (messageStatus) => messageStatusConfigs[messageStatus] || messageStatusConfigs.PENDING;

export const getPriorityConfig = (priority) => {
  if (priorityConfigs[priority]) return priorityConfigs[priority];
  if (priorityConfig?.[priority]) return priorityConfig[priority];
  const normalized = typeof priority === "string" ? priority.toLowerCase() : priority;
  if (normalized && priorityConfig?.[normalized]) return priorityConfig[normalized];
  return priorityConfigs.MEDIUM || priorityConfig?.medium;
};

// 格式化函数
export const formatStatus = (status) => getStatusConfig(status).label;
export const formatType = (type) => getTypeConfig(type).label;
export const formatPriority = (priority) => getPriorityConfig(priority).label;
export const formatChannel = (channel) => getChannelConfig(channel).label;
export const formatResponseTime = (responseTime) => getResponseTimeConfig(responseTime).label;
export const formatMessageType = (messageType) => getMessageTypeConfig(messageType).label;
export const formatMessageStatus = (messageStatus) => getMessageStatusConfig(messageStatus).label;

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
export const isValidStatus = (status) => Object.keys(statusConfigs).includes(status);
export const isValidType = (type) => Object.keys(typeConfigs).includes(type);
export const isValidChannel = (channel) => Object.keys(channelConfigs).includes(channel);
export const isValidResponseTime = (responseTime) => Object.keys(responseTimeConfigs).includes(responseTime);

export const isValidPriority = (priority) => {
  if (Object.keys(priorityConfigs).includes(priority)) return true;
  if (!priority) return false;
  const normalized = typeof priority === "string" ? priority.toLowerCase() : priority;
  return Object.keys(priorityConfig).includes(normalized);
};

// 过滤函数
export const filterByStatus = (items, status) => items.filter(item => item.status === status);
export const filterByType = (items, type) => items.filter(item => item.communication_type === type);
export const filterByPriority = (items, priority) => items.filter(item => item.priority === priority);
export const filterByChannel = (items, channel) => items.filter(item => item.channel === channel);
export const filterByCustomer = (items, customerId) => items.filter(item => item.customer_id === customerId);
