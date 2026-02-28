import { api } from "./client.js";

/**
 * 现场调试移动端 API 客户端
 */
export const fieldCommissioningApi = {
  /**
   * 获取现场调试任务列表
   * @param {Object} params - 查询参数
   * @param {string} params.status - 状态筛选
   * @param {string} params.assigned_to - 负责人筛选
   */
  list: (params) => api.get("/field/tasks", { params }),

  /**
   * 获取任务详情
   * @param {number} id - 任务 ID
   */
  detail: (id) => api.get(`/field/tasks/${id}`),

  /**
   * 现场签到
   * @param {number} id - 任务 ID
   * @param {Object} data - 签到数据
   * @param {number} data.latitude - 纬度
   * @param {number} data.longitude - 经度
   * @param {string} data.user_id - 用户 ID（可选）
   */
  checkin: (id, data) => api.post(`/field/tasks/${id}/checkin`, data),

  /**
   * 更新进度
   * @param {number} id - 任务 ID
   * @param {Object} data - 进度数据
   * @param {number} data.progress - 进度百分比 (0-100)
   * @param {string} data.note - 备注（可选）
   */
  updateProgress: (id, data) => api.post(`/field/tasks/${id}/progress`, data),

  /**
   * 报告问题
   * @param {number} id - 任务 ID
   * @param {Object} data - 问题数据
   * @param {string} data.description - 问题描述
   * @param {string} data.photo_url - 照片 URL（可选）
   * @param {string} data.severity - 严重程度 (low/medium/high/critical)
   * @param {string} data.reported_by - 报告人（可选）
   */
  reportIssue: (id, data) => api.post(`/field/tasks/${id}/issue`, data),

  /**
   * 完成任务
   * @param {number} id - 任务 ID
   * @param {Object} data - 完成数据
   * @param {string} data.signature - 签名
   * @param {string} data.completion_note - 完成备注（可选）
   */
  complete: (id, data) => api.post(`/field/tasks/${id}/complete`, data),

  /**
   * 获取调试概览统计
   */
  dashboard: () => api.get("/field/dashboard"),
};
