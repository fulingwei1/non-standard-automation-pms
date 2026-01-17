import { api } from "./client.js";



export const financialCostApi = {
  downloadTemplate: () =>
    api.get("/projects/financial-costs/template", { responseType: "blob" }),
  uploadCosts: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/projects/financial-costs/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  listCosts: (params) => api.get("/projects/financial-costs", { params }),
  deleteCost: (id) => api.delete(`/projects/financial-costs/${id}`),
};

export const projectWorkspaceApi = {
  getWorkspace: (projectId) => api.get(`/projects/${projectId}/workspace`),
  getBonuses: (projectId) => api.get(`/projects/${projectId}/bonuses`),
  getMeetings: (projectId, params) =>
    api.get(`/projects/${projectId}/meetings`, { params }),
  linkMeeting: (projectId, meetingId, isPrimary) =>
    api.post(`/projects/${projectId}/meetings/${meetingId}/link`, null, {
      params: { is_primary: isPrimary },
    }),
  getIssues: (projectId, params) =>
    api.get(`/projects/${projectId}/issues`, { params }),
  getSolutions: (projectId, params) =>
    api.get(`/projects/${projectId}/solutions`, { params }),
};

export const projectContributionApi = {
  getContributions: (projectId, params) =>
    api.get(`/projects/${projectId}/contributions`, { params }),
  rateMember: (projectId, userId, data) =>
    api.post(`/projects/${projectId}/contributions/${userId}/rate`, data),
  getReport: (projectId, params) =>
    api.get(`/projects/${projectId}/contributions/report`, { params }),
  getUserContributions: (userId, params) =>
    api.get(`/users/${userId}/project-contributions`, { params }),
  calculate: (projectId, period) =>
    api.post(`/projects/${projectId}/contributions/calculate`, null, {
      params: { period },
    }),
};

export const projectApi = {
  list: (params = {}) =>
    api.get("/projects/", { params: { page: 1, ...params } }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post("/projects/", data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  getMachines: (id) => api.get(`/projects/${id}/machines`),
  getInProductionSummary: (params) =>
    api.get("/projects/in-production/summary", { params }),
  // Sprint 3 & 4: 模板和阶段门校验相关API
  recommendTemplates: (params) =>
    api.get("/projects/templates/recommend", { params }),
  createFromTemplate: (templateId, data) =>
    api.post(`/projects/templates/${templateId}/create-project`, data),
  checkAutoTransition: (id, autoAdvance = false) =>
    api.post(`/projects/${id}/check-auto-transition`, {
      auto_advance: autoAdvance,
    }),
  getGateCheckResult: (id, targetStage) =>
    api.get(`/projects/${id}/gate-check/${targetStage}`),
  advanceStage: (id, data) => api.post(`/projects/${id}/advance-stage`, data),
  // Sprint 5.3: 缓存管理API
  getCacheStats: () => api.get("/projects/cache/stats"),
  clearCache: (pattern) =>
    api.post("/projects/cache/clear", null, {
      params: pattern ? { pattern } : {},
    }),
  resetCacheStats: () => api.post("/projects/cache/reset-stats"),
  // Sprint 3.3: 项目详情页增强
  getStatusLogs: (id, params) =>
    api.get(`/projects/${id}/status-logs`, { params }),
  getHealthDetails: (id) => api.get(`/projects/${id}/health-details`),
  // Sprint 3.2: 项目经理统计
  getStats: (params) => api.get("/projects/stats", { params }),
};

export const machineApi = {
  list: (params) => api.get("/machines/", { params }),
  get: (id) => api.get(`/machines/${id}`),
  create: (data) => api.post("/machines/", data),
  update: (id, data) => api.put(`/machines/${id}`, data),
  delete: (id) => api.delete(`/machines/${id}`),
  getBom: (id) => api.get(`/machines/${id}/bom`),
  getServiceHistory: (id, params) =>
    api.get(`/machines/${id}/service-history`, { params }),
  // 文档管理
  uploadDocument: (machineId, formData) =>
    api.post(`/machines/${machineId}/documents/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getDocuments: (machineId, params) =>
    api.get(`/machines/${machineId}/documents`, { params }),
  downloadDocument: (machineId, docId) =>
    api.get(`/machines/${machineId}/documents/${docId}/download`, {
      responseType: "blob",
    }),
  getDocumentVersions: (machineId, docId) =>
    api.get(`/machines/${machineId}/documents/${docId}/versions`),
};

export const stageApi = {
  list: (params) => {
    const projectId = params?.project_id;
    if (projectId) {
      return api.get(`/stages/projects/${projectId}/stages`);
    }
    return api.get("/stages/", { params });
  },
  get: (id) => api.get(`/stages/${id}`),
  statuses: (stageId) =>
    api.get("/stages/statuses", { params: { stage_id: stageId } }),
};

export const milestoneApi = {
  list: (params) => {
    const projectId = params?.project_id;
    if (projectId) {
      return api.get(`/milestones/projects/${projectId}/milestones`);
    }
    return api.get("/milestones/", { params });
  },
  get: (id) => api.get(`/milestones/${id}`),
  create: (data) => api.post("/milestones/", data),
  update: (id, data) => api.put(`/milestones/${id}`, data),
  complete: (id, data) => api.put(`/milestones/${id}/complete`, data || {}),
};

export const memberApi = {
  list: (params) => {
    const projectId = params?.project_id;
    if (projectId) {
      return api.get(`/members/projects/${projectId}/members`);
    }
    return api.get("/members/", { params });
  },
  add: (data) => api.post("/members/", data),
  remove: (id) => api.delete(`/members/${id}`),
  batchAdd: (projectId, data) =>
    api.post(`/projects/${projectId}/members/batch`, data),
  checkConflicts: (projectId, userId, params) =>
    api.get(`/projects/${projectId}/members/conflicts`, {
      params: { user_id: userId, ...params },
    }),
  getDeptUsers: (projectId, deptId) =>
    api.get(`/projects/${projectId}/members/from-dept/${deptId}`),
  notifyDeptManager: (projectId, memberId) =>
    api.post(`/projects/${projectId}/members/${memberId}/notify-dept-manager`),
  update: (memberId, data) => api.put(`/project-members/${memberId}`, data),
};

export const costApi = {
  list: (params) => api.get("/costs/", { params }),
  get: (id) => api.get(`/costs/${id}`),
  create: (data) => api.post("/costs/", data),
  update: (id, data) => api.put(`/costs/${id}`, data),
  delete: (id) => api.delete(`/costs/${id}`),
  getProjectCosts: (projectId, params) =>
    api.get(`/costs/projects/${projectId}/costs`, { params }),
  getProjectSummary: (projectId) =>
    api.get(`/costs/projects/${projectId}/costs/summary`),
};

export const settlementApi = {
  list: (params) => api.get("/settlements", { params }),
  get: (id) => api.get(`/settlements/${id}`),
  create: (data) => api.post("/settlements", data),
  update: (id, data) => api.put(`/settlements/${id}`, data),
  confirm: (id) => api.put(`/settlements/${id}/confirm`),
  approve: (id, data) => api.put(`/settlements/${id}/approve`, data),
  getStatistics: (params) => api.get("/settlements/statistics", { params }),
};

export const documentApi = {
  list: (params) => api.get("/documents/", { params }),
  create: (data) => api.post("/documents/", data),
};
