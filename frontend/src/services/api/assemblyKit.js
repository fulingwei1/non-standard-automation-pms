import api from "./client.js";

const TEMPLATE_BASE = "/assembly-kit/templates/templates";

// 装配套件 API
export const assemblyKitApi = {
  // 获取套件费率
  getKitRates: () => api.get("/assembly-kit/kit-rates"),

  // 获取时间基准套件费率看板
  getTimeBasedKitRateBoard: (projectId) =>
    api.get(`/assembly-kit/projects/${projectId}/time-based-rates`),

  // 更新套件费率
  updateKitRate: (id, data) => api.put(`/assembly-kit/kit-rates/${id}`, data),

  // 创建套件费率
  createKitRate: (data) => api.post("/assembly-kit/kit-rates", data),

  // 删除套件费率
  deleteKitRate: (id) => api.delete(`/assembly-kit/kit-rates/${id}`),

  // 装配套件模板管理
  getTemplates: (params) => api.get(TEMPLATE_BASE, { params }),

  // 创建模板
  createTemplate: (data) => api.post(TEMPLATE_BASE, data),

  // 更新模板
  updateTemplate: (id, data) => api.put(`${TEMPLATE_BASE}/${id}`, data),

  // 删除模板
  deleteTemplate: (id) => api.delete(`${TEMPLATE_BASE}/${id}`),
};
