// Customer 360 API Service
import { apiClient } from './apiClient';

/**
 * 获取客户360度信息
 * @param {number} customerId - 客户ID
 * @returns {Promise<Object>} 客户完整信息
 */
export const getCustomer360 = async (customerId) => {
  const response = await apiClient.get(`/customer/${customerId}`);
  return response.data;
};

/**
 * 获取客户订单历史
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 订单列表
 */
export const getCustomerOrders = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/orders`, { params });
  return response.data;
};

/**
 * 获取客户报价历史
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 报价列表
 */
export const getCustomerQuotes = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/quotes`, { params });
  return response.data;
};

/**
 * 获取客户合同历史
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 合同列表
 */
export const getCustomerContracts = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/contracts`, { params });
  return response.data;
};

/**
 * 获取客户付款记录
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 付款记录
 */
export const getCustomerPayments = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/payments`, { params });
  return response.data;
};

/**
 * 获取客户项目交付记录
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 交付记录
 */
export const getCustomerDeliveries = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/deliveries`, { params });
  return response.data;
};

/**
 * 获取客户满意度记录
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 满意度记录
 */
export const getCustomerSatisfaction = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/satisfaction`, { params });
  return response.data;
};

/**
 * 获取客户服务记录
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 服务记录
 */
export const getCustomerServices = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/services`, { params });
  return response.data;
};

/**
 * 获取客户分析数据
 * @param {number} customerId - 客户ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 分析数据
 */
export const getCustomerAnalytics = async (customerId, params = {}) => {
  const response = await apiClient.get(`/customer/${customerId}/analytics`, { params });
  return response.data;
};

export default {
  getCustomer360,
  getCustomerOrders,
  getCustomerQuotes,
  getCustomerContracts,
  getCustomerPayments,
  getCustomerDeliveries,
  getCustomerSatisfaction,
  getCustomerServices,
  getCustomerAnalytics,
};
