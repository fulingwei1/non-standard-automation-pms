import { api } from "./client.js";

/**
 * 毛利率预警 API
 * 用于毛利率预警配置、检查和审批流程
 */
export const marginAlertApi = {
  // ==================== 配置管理 ====================

  // 获取预警配置列表
  listConfigs: (params) => api.get("/sales/margin-alerts/configs", { params }),

  // 获取单个配置
  getConfig: (id) => api.get(`/sales/margin-alerts/configs/${id}`),

  // 创建配置
  createConfig: (data) => api.post("/sales/margin-alerts/configs", data),

  // 更新配置
  updateConfig: (id, data) => api.put(`/sales/margin-alerts/configs/${id}`, data),

  // 删除配置
  deleteConfig: (id) => api.delete(`/sales/margin-alerts/configs/${id}`),

  // ==================== 预警检查 ====================

  // 检查报价毛利率
  checkQuoteMargin: (quoteId, versionId) =>
    api.get(`/sales/margin-alerts/check/${quoteId}`, {
      params: { version_id: versionId },
    }),

  // ==================== 预警记录 ====================

  // 获取预警记录列表
  listRecords: (params) => api.get("/sales/margin-alerts/records", { params }),

  // 获取单个预警记录
  getRecord: (id) => api.get(`/sales/margin-alerts/records/${id}`),

  // 创建预警记录（申请低毛利率审批）
  createRecord: (data) => api.post("/sales/margin-alerts/records", data),

  // 获取待审批列表
  listPending: (params) => api.get("/sales/margin-alerts/pending", { params }),

  // 审批通过
  approve: (id, data) => api.post(`/sales/margin-alerts/records/${id}/approve`, data),

  // 驳回
  reject: (id, data) => api.post(`/sales/margin-alerts/records/${id}/reject`, data),

  // 获取报价的预警历史
  getQuoteHistory: (quoteId) =>
    api.get(`/sales/margin-alerts/history/${quoteId}`),

  // ==================== 统计 ====================

  // 获取预警统计
  getStatistics: (params) => api.get("/sales/margin-alerts/statistics", { params }),
};
