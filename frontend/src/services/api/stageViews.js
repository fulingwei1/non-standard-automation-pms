/**
 * 项目阶段视图 API
 *
 * 后端路由结构：
 * - /projects/views/pipeline            (pipeline_router, 项目根级)
 * - /projects/{project_id}/stages/...   (stages_router, 项目内阶段)
 * - /stage-templates/...                (stage_templates_router, 模板管理)
 */
import { api } from "./client.js";

export const stageViewsApi = {
  // ==================== 流水线视图 ====================
  pipeline: {
    get: (params) => api.get("/projects/views/pipeline", { params }),
  },

  // ==================== 时间轴视图 ====================
  timeline: {
    get: (projectId, params) =>
      api.get(`/projects/${projectId}/stages/views/timeline`, { params }),
  },

  // ==================== 分解树视图 ====================
  tree: {
    get: (projectId, params) =>
      api.get(`/projects/${projectId}/stages/views/tree`, { params }),
  },

  // ==================== 阶段状态管理 ====================
  stages: {
    getProgress: (projectId) =>
      api.get(`/projects/${projectId}/stages/progress`),

    getDetail: (projectId, stageInstanceId) =>
      api.get(`/projects/${projectId}/stages/${stageInstanceId}`),

    updateStatus: (projectId, stageInstanceId, data) =>
      api.put(`/projects/${projectId}/stages/${stageInstanceId}`, data),

    start: (projectId, stageInstanceId, actualStartDate) =>
      api.post(`/projects/${projectId}/stages/${stageInstanceId}/start`, null, {
        params: actualStartDate ? { actual_start_date: actualStartDate } : {},
      }),

    complete: (projectId, stageInstanceId, actualEndDate, autoStartNext = true) =>
      api.post(`/projects/${projectId}/stages/${stageInstanceId}/complete`, null, {
        params: {
          actual_end_date: actualEndDate,
          auto_start_next: autoStartNext,
        },
      }),

    skip: (projectId, stageInstanceId, reason) =>
      api.post(`/projects/${projectId}/stages/${stageInstanceId}/skip`, null, {
        params: reason ? { reason } : {},
      }),

    submitReview: (projectId, stageInstanceId, data) =>
      api.post(`/projects/${projectId}/stages/${stageInstanceId}/review`, data),
  },

  // ==================== 节点管理 ====================
  nodes: {
    start: (projectId, nodeInstanceId) =>
      api.post(`/projects/${projectId}/stages/nodes/${nodeInstanceId}/start`),

    complete: (projectId, nodeInstanceId, data) =>
      api.post(`/projects/${projectId}/stages/nodes/${nodeInstanceId}/complete`, data),

    skip: (projectId, nodeInstanceId, reason) =>
      api.post(`/projects/${projectId}/stages/nodes/${nodeInstanceId}/skip`, null, {
        params: reason ? { reason } : {},
      }),

    assign: (projectId, nodeInstanceId, data) =>
      api.put(`/projects/${projectId}/stages/nodes/${nodeInstanceId}/assign`, data),

    updatePlannedDate: (projectId, nodeInstanceId, plannedDate) =>
      api.put(`/projects/${projectId}/stages/nodes/${nodeInstanceId}/planned-date`, null, {
        params: { planned_date: plannedDate },
      }),
  },

  // ==================== 模板管理 ====================
  templates: {
    list: (params) => api.get("/stage-templates", { params }),
    get: (templateId) => api.get(`/stage-templates/${templateId}`),
    initializeProject: (projectId, data) =>
      api.post(`/projects/${projectId}/stages/initialize`, data),
  },
};
