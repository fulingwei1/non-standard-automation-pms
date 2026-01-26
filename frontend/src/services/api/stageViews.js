/**
 * 项目阶段视图 API
 *
 * 提供三种视图的数据获取接口：
 * - Pipeline View: 多项目阶段全景
 * - Timeline View: 单项目甘特图
 * - Tree View: 阶段/节点/任务分解
 */
import { api } from "./client.js";

export const stageViewsApi = {
  // ==================== 流水线视图 ====================
  pipeline: {
    /**
     * 获取多项目阶段全景数据
     * @param {Object} params - 查询参数
     * @param {string} params.category - 阶段分类筛选
     * @param {string} params.health_status - 健康状态筛选
     * @param {number} params.template_id - 模板ID筛选
     * @param {boolean} params.group_by_template - 是否按模板分组
     * @param {number} params.skip - 分页偏移
     * @param {number} params.limit - 分页大小
     */
    get: (params) => api.get("/projects/project-stages/views/pipeline", { params }),
  },

  // ==================== 时间轴视图 ====================
  timeline: {
    /**
     * 获取单项目时间轴数据
     * @param {number} projectId - 项目ID
     * @param {Object} params - 查询参数
     * @param {boolean} params.include_nodes - 是否包含节点详情
     */
    get: (projectId, params) =>
      api.get(`/projects/project-stages/${projectId}/views/timeline`, { params }),
  },

  // ==================== 分解树视图 ====================
  tree: {
    /**
     * 获取项目分解树数据
     * @param {number} projectId - 项目ID
     * @param {Object} params - 查询参数
     * @param {boolean} params.include_tasks - 是否包含子任务
     */
    get: (projectId, params) =>
      api.get(`/projects/project-stages/${projectId}/views/tree`, { params }),
  },

  // ==================== 阶段状态管理 ====================
  stages: {
    /**
     * 获取项目阶段进度
     */
    getProgress: (projectId) =>
      api.get(`/projects/project-stages/${projectId}/progress`),

    /**
     * 获取阶段详情
     */
    getDetail: (stageInstanceId) =>
      api.get(`/projects/project-stages/stages/${stageInstanceId}`),

    /**
     * 更新阶段状态
     * @param {number} stageInstanceId - 阶段实例ID
     * @param {Object} data - 状态数据
     * @param {string} data.status - 新状态
     * @param {string} data.remark - 备注
     */
    updateStatus: (stageInstanceId, data) =>
      api.put(`/projects/project-stages/stages/${stageInstanceId}/status`, data),

    /**
     * 开始阶段
     */
    start: (stageInstanceId, actualStartDate) =>
      api.post(`/projects/project-stages/stages/${stageInstanceId}/start`, null, {
        params: actualStartDate ? { actual_start_date: actualStartDate } : {},
      }),

    /**
     * 完成阶段
     */
    complete: (stageInstanceId, actualEndDate, autoStartNext = true) =>
      api.post(`/projects/project-stages/stages/${stageInstanceId}/complete`, null, {
        params: {
          actual_end_date: actualEndDate,
          auto_start_next: autoStartNext
        },
      }),

    /**
     * 跳过阶段
     */
    skip: (stageInstanceId, reason) =>
      api.post(`/projects/project-stages/stages/${stageInstanceId}/skip`, null, {
        params: reason ? { reason } : {},
      }),

    /**
     * 提交阶段评审
     * @param {number} stageInstanceId - 阶段实例ID
     * @param {Object} data - 评审数据
     * @param {string} data.review_result - 评审结果 (PASSED/CONDITIONAL/FAILED)
     * @param {string} data.review_notes - 评审记录
     */
    submitReview: (stageInstanceId, data) =>
      api.post(`/projects/project-stages/stages/${stageInstanceId}/review`, data),
  },

  // ==================== 节点管理 ====================
  nodes: {
    /**
     * 开始节点
     */
    start: (nodeInstanceId) =>
      api.post(`/projects/project-stages/nodes/${nodeInstanceId}/start`),

    /**
     * 完成节点
     */
    complete: (nodeInstanceId, data) =>
      api.post(`/projects/project-stages/nodes/${nodeInstanceId}/complete`, data),

    /**
     * 跳过节点
     */
    skip: (nodeInstanceId, reason) =>
      api.post(`/projects/project-stages/nodes/${nodeInstanceId}/skip`, null, {
        params: reason ? { reason } : {},
      }),

    /**
     * 分配节点负责人
     */
    assign: (nodeInstanceId, data) =>
      api.put(`/projects/project-stages/nodes/${nodeInstanceId}/assign`, data),

    /**
     * 更新节点计划日期
     */
    updatePlannedDate: (nodeInstanceId, plannedDate) =>
      api.put(`/projects/project-stages/nodes/${nodeInstanceId}/planned-date`, null, {
        params: { planned_date: plannedDate },
      }),
  },

  // ==================== 模板管理 ====================
  templates: {
    /**
     * 获取模板列表
     */
    list: (params) => api.get("/stage-templates", { params }),

    /**
     * 获取模板详情
     */
    get: (templateId) => api.get(`/stage-templates/${templateId}`),

    /**
     * 初始化项目阶段
     */
    initializeProject: (projectId, data) =>
      api.post(`/projects/project-stages/${projectId}/stages/initialize`, data),
  },
};
