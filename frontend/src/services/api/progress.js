import { api } from "./client.js";



export const progressApi = {
  // Tasks - Note: Tasks are project-specific, use project_id in params
  tasks: {
    list: (params) => {
      // If project_id is provided, use project-specific endpoint
      if (params?.project_id) {
        return api.get(`/projects/${params.project_id}/tasks`, {
          params: { ...params, project_id: undefined },
        });
      }
      // Otherwise, need to fetch from all projects (not directly supported)
      return Promise.reject(new Error("project_id is required"));
    },
    get: (id) => api.get(`/tasks/${id}`),
    create: (projectId, data) => api.post(`/projects/${projectId}/tasks`, data),
    update: (id, data) => api.put(`/tasks/${id}`, data),
    delete: (id) => api.delete(`/tasks/${id}`),
    updateProgress: (id, data) => api.put(`/tasks/${id}/progress`, data),
    updateAssignee: (id, data) => api.put(`/tasks/${id}/assignee`, data),
    complete: (id) => api.put(`/tasks/${id}/complete`),
  },

  // Progress Reports
  reports: {
    list: (params) => api.get("/progress-reports", { params }),
    create: (data) => api.post("/progress-reports", data),
    get: (id) => api.get(`/progress-reports/${id}`),
    getSummary: (projectId) =>
      api.get(`/projects/${projectId}/progress-summary`),
    getGantt: (projectId) => api.get(`/projects/${projectId}/gantt`),
    getBoard: (projectId) => api.get(`/projects/${projectId}/progress-board`),
    getMilestoneRate: (projectId) =>
      api.get("/reports/milestone-rate", {
        params: projectId ? { project_id: projectId } : {},
      }),
    getDelayReasons: (projectId, topN = 10) =>
      api.get("/reports/delay-reasons", {
        params: { project_id: projectId, top_n: topN },
      }),
  },
  analytics: {
    getForecast: (projectId) =>
      api.get(`/progress/projects/${projectId}/progress-forecast`),
    checkDependencies: (projectId) =>
      api.get(`/progress/projects/${projectId}/dependency-check`),
  },
  // 新增：自动化处理API
  autoProcess: {
    applyForecast: (projectId, params) =>
      api.post(`/progress/projects/${projectId}/auto-apply-forecast`, null, {
        params: {
          auto_block: params?.autoBlock,
          delay_threshold: params?.delayThreshold || 7
        }
      }),
    
    fixDependencies: (projectId, params) =>
      api.post(`/progress/projects/${projectId}/auto-fix-dependencies`, null, {
        params: {
          auto_fix_timing: params?.autoFixTiming,
          auto_fix_missing: params?.autoFixMissing !== false // 默认为true
        }
      }),
    
    runCompleteProcess: (projectId, options) =>
      api.post(`/progress/projects/${projectId}/auto-process-complete`, options),
    
    preview: (projectId, params) =>
      api.get(`/progress/projects/${projectId}/auto-preview`, {
        params: {
          auto_block: params?.autoBlock || false,
          delay_threshold: params?.delayThreshold || 7
        }
      }),
    
    batchProcess: (projectIds, options) =>
      api.post(`/progress/projects/batch/auto-process`, {
        project_ids: projectIds,
        options: options
      })
  },
  // WBS Templates
  wbsTemplates: {
    list: (params) => api.get("/wbs-templates", { params }),
    get: (id) => api.get(`/wbs-templates/${id}`),
    create: (data) => api.post("/wbs-templates", data),
    update: (id, data) => api.put(`/wbs-templates/${id}`, data),
    delete: (id) => api.delete(`/wbs-templates/${id}`),
    getTasks: (templateId) => api.get(`/wbs-templates/${templateId}/tasks`),
    addTask: (templateId, data) =>
      api.post(`/wbs-templates/${templateId}/tasks`, data),
    updateTask: (taskId, data) =>
      api.put(`/wbs-template-tasks/${taskId}`, data),
  },

  // Projects WBS Init
  projects: {
    initWBS: (projectId, data) =>
      api.post(`/projects/${projectId}/init-wbs`, data),
  },
};
