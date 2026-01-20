// Delivery Management API Service
import { apiClient } from './apiClient';

/**
 * 获取交付列表
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 交付列表
 */
export const getDeliveries = async (params = {}) => {
  const response = await apiClient.get('/delivery', { params });
  return response.data;
};

export default {
  getDeliveries,
};
