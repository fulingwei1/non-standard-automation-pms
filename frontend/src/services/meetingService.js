// Meeting Management API Service
import { apiClient } from './apiClient';

/**
 * 获取会议列表
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 会议列表
 */
export const getMeetings = async (params = {}) => {
  const response = await apiClient.get('/meetings', { params });
  return response.data;
};

export default {
  getMeetings,
};
