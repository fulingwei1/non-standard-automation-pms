/**
 * 节点子任务 API
 *
 * 提供节点子任务的 CRUD、状态流转、进度查询等接口
 * 后端路由：/node-tasks/...
 */
import { api } from "./client.js";

export const nodeTasksApi = {
  // ==================== 任务 CRUD ====================

  /**
   * 创建子任务
   * @param {Object} data - 任务数据
   */
  create: (data) => api.post("/node-tasks/", data),

  /**
   * 获取任务详情
   * @param {number} taskId - 任务ID
   */
  get: (taskId) => api.get(`/node-tasks/${taskId}`),

  /**
   * 更新任务
   * @param {number} taskId - 任务ID
   * @param {Object} data - 更新数据
   */
  update: (taskId, data) => api.put(`/node-tasks/${taskId}`, data),

  /**
   * 删除任务
   * @param {number} taskId - 任务ID
   */
  delete: (taskId) => api.delete(`/node-tasks/${taskId}`),

  // ==================== 查询 ====================

  /**
   * 获取当前用户的任务列表
   * @param {Object} params - 查询参数
   * @param {number} params.project_id - 项目ID筛选
   * @param {string} params.status - 状态筛选
   */
  getMyTasks: (params) => api.get("/node-tasks/my-tasks", { params }),

  /**
   * 获取指定用户的任务列表
   * @param {number} userId - 用户ID
   */
  getUserTasks: (userId) => api.get(`/node-tasks/user/${userId}`),

  /**
   * 获取节点下的所有子任务
   * @param {number} nodeInstanceId - 节点实例ID
   */
  getByNode: (nodeInstanceId) => api.get(`/node-tasks/node/${nodeInstanceId}`),

  /**
   * 获取节点任务进度
   * @param {number} nodeInstanceId - 节点实例ID
   */
  getNodeProgress: (nodeInstanceId) =>
    api.get(`/node-tasks/node/${nodeInstanceId}/progress`),

  // ==================== 批量操作 ====================

  /**
   * 批量创建任务
   * @param {number} nodeInstanceId - 节点实例ID
   * @param {Object} data - 批量任务数据
   */
  batchCreate: (nodeInstanceId, data) =>
    api.post(`/node-tasks/node/${nodeInstanceId}/batch`, data),

  /**
   * 重新排序任务
   * @param {number} nodeInstanceId - 节点实例ID
   * @param {Object} data - 排序数据
   */
  reorder: (nodeInstanceId, data) =>
    api.post(`/node-tasks/node/${nodeInstanceId}/reorder`, data),

  // ==================== 状态流转 ====================

  /**
   * 开始任务
   * @param {number} taskId - 任务ID
   */
  start: (taskId) => api.post(`/node-tasks/${taskId}/start`),

  /**
   * 完成任务
   * @param {number} taskId - 任务ID
   * @param {Object} data - 完成数据
   */
  complete: (taskId, data) => api.post(`/node-tasks/${taskId}/complete`, data),

  /**
   * 跳过任务
   * @param {number} taskId - 任务ID
   */
  skip: (taskId) => api.post(`/node-tasks/${taskId}/skip`),

  /**
   * 分配任务
   * @param {number} taskId - 任务ID
   * @param {Object} data - 分配数据
   */
  assign: (taskId, data) => api.put(`/node-tasks/${taskId}/assign`, data),

  /**
   * 更新任务优先级
   * @param {number} taskId - 任务ID
   * @param {Object} data - 优先级数据
   */
  updatePriority: (taskId, data) =>
    api.put(`/node-tasks/${taskId}/priority`, data),
};
