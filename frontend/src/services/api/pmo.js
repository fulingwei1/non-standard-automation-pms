import { api } from "./client.js";



export const pmoApi = {
  // Dashboard
  dashboard: () => api.get("/pmo/dashboard"),
  weeklyReport: (params) => api.get("/pmo/weekly-report", { params }),
  resourceOverview: () => api.get("/pmo/resource-overview"),
  riskWall: () => api.get("/pmo/risk-wall"),

  // Initiation Management
  initiations: {
    list: (params) => api.get("/pmo/initiations", { params }),
    get: (id) => api.get(`/pmo/initiations/${id}`),
    create: (data) => api.post("/pmo/initiations", data),
    update: (id, data) => api.put(`/pmo/initiations/${id}`, data),
    submit: (id) => api.put(`/pmo/initiations/${id}/submit`),
    approve: (id, data) => api.put(`/pmo/initiations/${id}/approve`, data),
    reject: (id, data) => api.put(`/pmo/initiations/${id}/reject`, data),
  },

  // Project Phases
  phases: {
    list: (projectId) => api.get(`/pmo/projects/${projectId}/phases`),
    entryCheck: (phaseId, data) =>
      api.post(`/pmo/phases/${phaseId}/entry-check`, data),
    exitCheck: (phaseId, data) =>
      api.post(`/pmo/phases/${phaseId}/exit-check`, data),
    review: (phaseId, data) => api.post(`/pmo/phases/${phaseId}/review`, data),
    advance: (phaseId, data) => api.put(`/pmo/phases/${phaseId}/advance`, data),
  },

  // Risk Management
  risks: {
    list: (projectId, params) =>
      api.get(`/pmo/projects/${projectId}/risks`, { params }),
    // Note: Backend doesn't have GET /pmo/risks/{id}, risks are only listed by project
    create: (projectId, data) =>
      api.post(`/pmo/projects/${projectId}/risks`, data),
    assess: (riskId, data) => api.put(`/pmo/risks/${riskId}/assess`, data),
    response: (riskId, data) => api.put(`/pmo/risks/${riskId}/response`, data),
    updateStatus: (riskId, data) =>
      api.put(`/pmo/risks/${riskId}/status`, data),
    close: (riskId, data) => api.put(`/pmo/risks/${riskId}/close`, data),
  },

  // Project Closure
  closures: {
    create: (projectId, data) =>
      api.post(`/pmo/projects/${projectId}/closure`, data),
    get: (projectId) => api.get(`/pmo/projects/${projectId}/closure`),
    review: (closureId, data) =>
      api.put(`/pmo/closures/${closureId}/review`, data),
    updateLessons: (closureId, data) =>
      api.put(`/pmo/closures/${closureId}/lessons`, data),
  },

  // Meeting Management
  meetings: {
    list: (params) => api.get("/pmo/meetings", { params }),
    get: (id) => api.get(`/pmo/meetings/${id}`),
    create: (data) => api.post("/pmo/meetings", data),
    update: (id, data) => api.put(`/pmo/meetings/${id}`, data),
    updateMinutes: (id, data) => api.put(`/pmo/meetings/${id}/minutes`, data),
    getActions: (id) => api.get(`/pmo/meetings/${id}/actions`),
  },
};
