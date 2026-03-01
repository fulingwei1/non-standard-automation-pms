import { api } from "./client.js";

export const templateConfigApi = {
  // 获取配置列表
  list: (params) => api.get("/template-configs/configs", { params }),
  
  // 获取配置详情
  get: (id) => api.get(`/template-configs/configs/${id}`),
  
  // 创建配置
  create: (data) => api.post("/template-configs/configs", data),
  
  // 更新配置
  update: (id, data) => api.put(`/template-configs/configs/${id}`, data),
  
  // 删除配置
  delete: (id) => api.delete(`/template-configs/configs/${id}`),
  
  // 应用配置创建项目
  createProject: (configId, data) =>
    api.post(`/template-configs/apply/${configId}/create-project`, data),
};
