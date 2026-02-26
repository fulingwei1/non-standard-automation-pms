/**
 * 节点子任务 API
 * 后端路由：/node-tasks/...
 */
import { api } from "./client.js";

export const nodeTasksApi = {
  // CRUD
  create: (data) => api.post("/node-tasks/", data),
  get: (taskId) => api.get(`/node-tasks/${taskId}`),
  update: (taskId, data) => api.put(`/node-tasks/${taskId}`, data),
  delete: (taskId) => api.delete(`/node-tasks/${taskId}`),

  // 查询
  getMyTasks: (params) => api.get("/node-tasks/my-tasks", { params }),
  getUserTasks: (userId) => api.get(`/node-tasks/user/${userId}`),
  getByNode: (nodeInstanceId) => api.get(`/node-tasks/node/${nodeInstanceId}`),
  getNodeProgress: (nodeInstanceId) =>
    api.get(`/node-tasks/node/${nodeInstanceId}/progress`),

  // 批量操作
  batchCreate: (nodeInstanceId, data) =>
    api.post(`/node-tasks/node/${nodeInstanceId}/batch`, data),
  reorder: (nodeInstanceId, data) =>
    api.post(`/node-tasks/node/${nodeInstanceId}/reorder`, data),

  // 状态流转
  start: (taskId) => api.post(`/node-tasks/${taskId}/start`),
  complete: (taskId, data) => api.post(`/node-tasks/${taskId}/complete`, data),
  skip: (taskId) => api.post(`/node-tasks/${taskId}/skip`),
  assign: (taskId, data) => api.put(`/node-tasks/${taskId}/assign`, data),
  updatePriority: (taskId, data) =>
    api.put(`/node-tasks/${taskId}/priority`, data),
};
