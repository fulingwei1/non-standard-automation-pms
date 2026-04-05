import { api } from "./client.js";

/**
 * 技术参数模板 API
 * 用于售前技术方案的参数模板管理和成本估算
 */
export const technicalParameterApi = {
  // 模板列表
  list: (params) => api.get("/presale/technical-parameters/templates", { params }),

  // 模板详情
  get: (id) => api.get(`/presale/technical-parameters/templates/${id}`),

  // 创建模板
  create: (data) => api.post("/presale/technical-parameters/templates", data),

  // 更新模板
  update: (id, data) => api.put(`/presale/technical-parameters/templates/${id}`, data),

  // 删除模板
  delete: (id) => api.delete(`/presale/technical-parameters/templates/${id}`),

  // 根据行业和测试类型匹配模板
  match: (params) => api.get("/presale/technical-parameters/templates/match", { params }),

  // 基于模板估算成本
  estimateCost: (data) => api.post("/presale/technical-parameters/estimate-cost", data),

  // 获取统计数据
  getStatistics: () => api.get("/presale/technical-parameters/statistics"),
};
