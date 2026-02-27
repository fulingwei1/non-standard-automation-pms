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
  getBoard: (params) => api.get("/projects/board", { params }),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post("/projects/", data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  getMachines: (id) => api.get(`/projects/${id}/machines`),
  getInProductionSummary: (params) =>
    api.get("/projects/in-production-summary", { params }),
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
  advanceStage: (id, data) => api.post(`/projects/${id}/stage-advance`, data),
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
  getHealthDetails: (id) => api.get(`/projects/${id}/health/details`),
  // Sprint 3.2: 项目经理统计
  getStats: (params) => api.get("/projects/stats", { params }),
};

export const machineApi = {
  list: (projectId, params) =>
    api.get(`/projects/${projectId}/machines`, { params }),
  get: (projectId, machineId) =>
    api.get(`/projects/${projectId}/machines/${machineId}`),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/machines`, data),
  update: (projectId, machineId, data) =>
    api.put(`/projects/${projectId}/machines/${machineId}`, data),
  delete: (projectId, machineId) =>
    api.delete(`/projects/${projectId}/machines/${machineId}`),
  updateProgress: (projectId, machineId, progress) =>
    api.put(
      `/projects/${projectId}/machines/${machineId}/progress`,
      null,
      { params: { progress_pct: progress } },
    ),
  getBom: (projectId, machineId) =>
    api.get(`/projects/${projectId}/machines/${machineId}/bom`),
  getServiceHistory: (projectId, machineId, params) =>
    api.get(`/projects/${projectId}/machines/${machineId}/service-history`, {
      params,
    }),
  // 汇总视图
  getSummary: (projectId) =>
    api.get(`/projects/${projectId}/machines/summary`),
  recalculate: (projectId) =>
    api.post(`/projects/${projectId}/machines/recalculate`),
  // 文档管理
  uploadDocument: (projectId, machineId, formData) =>
    api.post(
      `/projects/${projectId}/machines/${machineId}/documents/upload`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    ),
  getDocuments: (projectId, machineId, params) =>
    api.get(`/projects/${projectId}/machines/${machineId}/documents`, { params }),
  downloadDocument: (projectId, machineId, docId) =>
    api.get(
      `/projects/${projectId}/machines/${machineId}/documents/${docId}/download`,
      { responseType: "blob" },
    ),
  getDocumentVersions: (projectId, machineId, docId) =>
    api.get(
      `/projects/${projectId}/machines/${machineId}/documents/${docId}/versions`,
    ),
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
  // 项目成本管理 - 使用项目中心路由
  list: (projectId, params) =>
    api.get(`/projects/${projectId}/costs`, { params }),
  get: (projectId, costId) =>
    api.get(`/projects/${projectId}/costs/${costId}`),
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/costs`, data),
  update: (projectId, costId, data) =>
    api.put(`/projects/${projectId}/costs/${costId}`, data),
  delete: (projectId, costId) =>
    api.delete(`/projects/${projectId}/costs/${costId}`),
  // 兼容旧接口（已废弃，请使用上面的接口）
  getProjectCosts: (projectId, params) =>
    api.get(`/projects/${projectId}/costs`, { params }),
  getProjectSummary: (projectId) =>
    api.get(`/projects/${projectId}/costs/summary`),
  // 成本分析
  getCostAnalysis: (projectId, compareProjectId) =>
    api.get(`/projects/${projectId}/costs/cost-analysis`, {
      params: compareProjectId ? { compare_project_id: compareProjectId } : {},
    }),
  getRevenueDetail: (projectId) =>
    api.get(`/projects/${projectId}/costs/revenue-detail`),
  getProfitAnalysis: (projectId) =>
    api.get(`/projects/${projectId}/costs/profit-analysis`),
  // 人工成本计算
  calculateLaborCost: (projectId, params) =>
    api.post(`/projects/${projectId}/costs/calculate-labor-cost`, null, {
      params,
    }),
  // 预算分析
  getBudgetExecution: (projectId) =>
    api.get(`/projects/${projectId}/costs/execution`),
  getBudgetTrend: (projectId, params) =>
    api.get(`/projects/${projectId}/costs/trend`, { params }),
  // 成本复盘
  generateCostReview: (projectId) =>
    api.post(`/projects/${projectId}/costs/generate-cost-review`),
  // 成本预警
  checkBudgetAlert: (projectId) =>
    api.post(`/projects/${projectId}/costs/check-budget-alert`),
  // 成本分摊
  allocateCost: (projectId, costId, data) =>
    api.post(`/projects/${projectId}/costs/${costId}/allocate`, data),
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
