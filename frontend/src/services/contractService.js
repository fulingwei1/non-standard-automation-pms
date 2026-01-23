// Contract Management API Service
import apiClient from './apiClient';

/**
 * 获取合同列表
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 合同列表
 */
export const getContracts = async (params = {}) => {
  const response = await apiClient.get('/sales/contracts', { params });
  return response.data;
};

/**
 * 获取合同详情
 * @param {number} contractId - 合同ID
 * @returns {Promise<Object>} 合同详情
 */
export const getContractDetail = async (contractId) => {
  const response = await apiClient.get(`/sales/contracts/${contractId}`);
  return response.data;
};

/**
 * 创建合同
 * @param {Object} data - 合同数据
 * @returns {Promise<Object>} 创建的合同
 */
export const createContract = async (data) => {
  const response = await apiClient.post('/sales/contracts', data);
  return response.data;
};

/**
 * 更新合同
 * @param {number} contractId - 合同ID
 * @param {Object} data - 更新数据
 * @returns {Promise<Object>} 更新的合同
 */
export const updateContract = async (contractId, data) => {
  const response = await apiClient.put(`/sales/contracts/${contractId}`, data);
  return response.data;
};

/**
 * 删除合同
 * @param {number} contractId - 合同ID
 * @returns {Promise<Object>} 删除结果
 */
export const deleteContract = async (contractId) => {
  const response = await apiClient.delete(`/sales/contracts/${contractId}`);
  return response.data;
};

/**
 * 获取合同历史记录
 * @param {number} contractId - 合同ID
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 历史记录
 */
export const getContractHistory = async (contractId, params = {}) => {
  const response = await apiClient.get(`/sales/contracts/${contractId}/history`, { params });
  return response.data;
};

export default {
  getContracts,
  getContractDetail,
  createContract,
  updateContract,
  deleteContract,
  getContractHistory,
};
