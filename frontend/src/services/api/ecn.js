import { api } from "./client.js";



export const ecnApi = {
  list: (params) => api.get("/ecns", { params }),
  get: (id) => api.get(`/ecns/${id}`),
  create: (data) => api.post("/ecns", data),
  update: (id, data) => api.put(`/ecns/${id}`, data),
  submit: (id, data) => api.put(`/ecns/${id}/submit`, data || {}),
  cancel: (id) => api.put(`/ecns/${id}/cancel`),
  // Evaluations
  getEvaluations: (id) => api.get(`/ecns/${id}/evaluations`),
  createEvaluation: (id, data) => api.post(`/ecns/${id}/evaluations`, data),
  getEvaluation: (evalId) => api.get(`/ecn-evaluations/${evalId}`),
  submitEvaluation: (evalId) => api.put(`/ecn-evaluations/${evalId}/submit`),
  getEvaluationSummary: (id) => api.get(`/ecns/${id}/evaluation-summary`),
  // Approvals - using unified approval engine
  getApprovals: (id) => api.get(`/ecns/approval/status/${id}`),
  submitApproval: (data) => api.post("/ecns/approval/submit", data),
  getPendingApprovals: () => api.get("/ecns/approval/pending"),
  performApprovalAction: (data) => api.post("/ecns/approval/action", data),
  batchApprovalAction: (data) => api.post("/ecns/approval/batch-action", data),
  withdrawApproval: (data) => api.post("/ecns/approval/withdraw", data),
  getApprovalHistory: () => api.get("/ecns/approval/history"),
  // Tasks
  getTasks: (id) => api.get(`/ecns/${id}/tasks`),
  createTask: (id, data) => api.post(`/ecns/${id}/tasks`, data),
  getTask: (taskId) => api.get(`/ecn-tasks/${taskId}`),
  updateTaskProgress: (taskId, progress) =>
    api.put(`/ecn-tasks/${taskId}/progress`, null, { params: { progress } }),
  completeTask: (taskId) => api.put(`/ecn-tasks/${taskId}/complete`),
  // Affected materials
  getAffectedMaterials: (id) => api.get(`/ecns/${id}/affected-materials`),
  createAffectedMaterial: (id, data) =>
    api.post(`/ecns/${id}/affected-materials`, data),
  updateAffectedMaterial: (id, materialId, data) =>
    api.put(`/ecns/${id}/affected-materials/${materialId}`, data),
  deleteAffectedMaterial: (id, materialId) =>
    api.delete(`/ecns/${id}/affected-materials/${materialId}`),
  // Affected orders
  getAffectedOrders: (id) => api.get(`/ecns/${id}/affected-orders`),
  createAffectedOrder: (id, data) =>
    api.post(`/ecns/${id}/affected-orders`, data),
  updateAffectedOrder: (id, orderId, data) =>
    api.put(`/ecns/${id}/affected-orders/${orderId}`, data),
  deleteAffectedOrder: (id, orderId) =>
    api.delete(`/ecns/${id}/affected-orders/${orderId}`),
  // Execution
  startExecution: (id, data) =>
    api.put(`/ecns/${id}/start-execution`, data || {}),
  verify: (id, data) => api.put(`/ecns/${id}/verify`, data),
  close: (id, data) => api.put(`/ecns/${id}/close`, data || {}),
  // BOM Analysis
  analyzeBomImpact: (id, params) =>
    api.post(`/ecns/${id}/analyze-bom-impact`, null, { params }),
  getBomImpactSummary: (id) => api.get(`/ecns/${id}/bom-impact-summary`),
  checkObsoleteRisk: (id) => api.post(`/ecns/${id}/check-obsolete-risk`),
  getObsoleteAlerts: (id) => api.get(`/ecns/${id}/obsolete-material-alerts`),
  // Responsibility Allocation
  createResponsibilityAnalysis: (id, data) =>
    api.post(`/ecns/${id}/responsibility-analysis`, data),
  getResponsibilitySummary: (id) =>
    api.get(`/ecns/${id}/responsibility-summary`),
  // RCA Analysis
  updateRcaAnalysis: (id, data) => api.put(`/ecns/${id}/rca-analysis`, data),
  getRcaAnalysis: (id) => api.get(`/ecns/${id}/rca-analysis`),
  // Knowledge Base
  extractSolution: (id, autoExtract = true) =>
    api.post(`/ecns/${id}/extract-solution`, { auto_extract: autoExtract }),
  getSimilarEcns: (id, params) =>
    api.get(`/ecns/${id}/similar-ecns`, { params }),
  recommendSolutions: (id, params) =>
    api.get(`/ecns/${id}/recommend-solutions`, { params }),
  createSolutionTemplate: (id, data) =>
    api.post(`/ecns/${id}/create-solution-template`, data),
  applySolutionTemplate: (id, templateId) =>
    api.post(`/ecns/${id}/apply-solution-template`, {
      template_id: templateId,
    }),
  listSolutionTemplates: (params) =>
    api.get("/ecn-solution-templates", { params }),
  getSolutionTemplate: (templateId) =>
    api.get(`/ecn-solution-templates/${templateId}`),
  // ECN Types
  getEcnTypes: (params) => api.get("/ecn-types", { params }),
  getEcnType: (typeId) => api.get(`/ecn-types/${typeId}`),
  createEcnType: (data) => api.post("/ecn-types", data),
  updateEcnType: (typeId, data) => api.put(`/ecn-types/${typeId}`, data),
  deleteEcnType: (typeId) => api.delete(`/ecn-types/${typeId}`),
  // Overdue alerts
  getOverdueAlerts: () => api.get("/ecns/overdue-alerts"),
  batchProcessOverdueAlerts: (alerts) =>
    api.post("/ecns/batch-process-overdue-alerts", alerts),
  // Module integration
  syncToBom: (id) => api.post(`/ecns/${id}/sync-to-bom`),
  syncToProject: (id) => api.post(`/ecns/${id}/sync-to-project`),
  syncToPurchase: (id) => api.post(`/ecns/${id}/sync-to-purchase`),
  // Logs
  getLogs: (id) => api.get(`/ecns/${id}/logs`),
  // Statistics
  getStatistics: (params) => api.get("/ecns/statistics", { params }),
  // Batch operations
  batchSyncToBom: (ecnIds) => api.post("/ecns/batch-sync-to-bom", ecnIds),
  batchSyncToProject: (ecnIds) =>
    api.post("/ecns/batch-sync-to-project", ecnIds),
  batchSyncToPurchase: (ecnIds) =>
    api.post("/ecns/batch-sync-to-purchase", ecnIds),
  batchCreateTasks: (ecnId, tasks) =>
    api.post(`/ecns/${ecnId}/batch-create-tasks`, tasks),
};
