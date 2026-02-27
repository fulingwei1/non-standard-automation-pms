import { api } from "./client.js";



export const projectReviewApi = {
  // 复盘报告
  list: (params) => api.get("/project-reviews", { params }),
  get: (id) => api.get(`/project-reviews/${id}`),
  create: (data) => api.post("/project-reviews", data),
  update: (id, data) => api.put(`/project-reviews/${id}`, data),
  delete: (id) => api.delete(`/project-reviews/${id}`),
  publish: (id) => api.post(`/projects/reviews/${id}/publish`),

  // 经验教训
  getLessons: (reviewId, params) =>
    api.get("/project-reviews", { params: { review_id: reviewId, ...params } }),
  createLesson: (reviewId, data) =>
    api.post("/project-reviews/extract", { review_id: reviewId, ...data }),
  getLesson: (lessonId) =>
    api.get(`/project-reviews/${lessonId}`),
  updateLesson: (lessonId, data) =>
    api.patch(`/project-reviews/${lessonId}`, data),
  deleteLesson: (lessonId) =>
    api.delete(`/project-reviews/${lessonId}`),

  // 最佳实践
  getBestPractices: (reviewId, params) =>
    api.get("/projects/best-practices", { params: { review_id: reviewId, ...params } }),
  createBestPractice: (reviewId, data) =>
    api.post("/projects/best-practices", { review_id: reviewId, ...data }),
  getBestPractice: (practiceId) =>
    api.get(`/projects/best-practices/${practiceId}`),
  updateBestPractice: (practiceId, data) =>
    api.put(`/projects/best-practices/${practiceId}`, data),
  deleteBestPractice: (practiceId) =>
    api.delete(`/projects/best-practices/${practiceId}`),

  // 最佳实践库
  searchBestPractices: (params) =>
    api.get("/projects/best-practices", { params }),

  // 项目经验教训（从结项记录提取）
  getProjectLessons: (projectId) =>
    api.get(`/projects/${projectId}/lessons`),

  // 经验教训高级管理
  searchLessonsLearned: (params) =>
    api.get("/projects/lessons/search", { params }),

  // 最佳实践高级管理
  applyBestPractice: (practiceId, targetProjectId, notes) =>
    api.post(`/project-reviews/best-practices/${practiceId}/apply`, {
      target_project_id: targetProjectId,
      notes,
    }),
  getPopularBestPractices: (params) =>
    api.get("/projects/best-practices/popular", { params }),
};

export const technicalReviewApi = {
  // 评审主表
  list: (params) => api.get("/technical-reviews", { params }),
  get: (id) => api.get(`/technical-reviews/${id}`),
  create: (data) => api.post("/technical-reviews", data),
  update: (id, data) => api.put(`/technical-reviews/${id}`, data),
  delete: (id) => api.delete(`/technical-reviews/${id}`),

  // 评审参与人
  getParticipants: (reviewId) =>
    api.get(`/technical-reviews/${reviewId}/participants`),
  addParticipant: (reviewId, data) =>
    api.post(`/technical-reviews/${reviewId}/participants`, data),
  updateParticipant: (participantId, data) =>
    api.put(`/technical-reviews/participants/${participantId}`, data),
  deleteParticipant: (participantId) =>
    api.delete(`/technical-reviews/participants/${participantId}`),

  // 评审材料
  getMaterials: (reviewId) =>
    api.get(`/technical-reviews/${reviewId}/materials`),
  addMaterial: (reviewId, data) =>
    api.post(`/technical-reviews/${reviewId}/materials`, data),
  deleteMaterial: (materialId) =>
    api.delete(`/technical-reviews/materials/${materialId}`),

  // 检查项记录
  getChecklistRecords: (reviewId) =>
    api.get(`/technical-reviews/${reviewId}/checklist-records`),
  createChecklistRecord: (reviewId, data) =>
    api.post(`/technical-reviews/${reviewId}/checklist-records`, data),
  updateChecklistRecord: (recordId, data) =>
    api.put(`/technical-reviews/checklist-records/${recordId}`, data),

  // 评审问题
  getIssues: (params) => api.get("/technical-reviews/issues", { params }),
  createIssue: (reviewId, data) =>
    api.post(`/technical-reviews/${reviewId}/issues`, data),
  updateIssue: (issueId, data) =>
    api.put(`/technical-reviews/issues/${issueId}`, data),
};

export const engineersApi = {
  // 获取项目的跨部门进度可见性视图
  getProgressVisibility: (projectId) =>
    api.get(`/engineers/projects/${projectId}/progress-visibility`),
};

export const technicalAssessmentApi = {
  // 申请技术评估
  applyForLead: (leadId, data) =>
    api.post(`/sales/leads/${leadId}/assessments/apply`, data),
  applyForOpportunity: (oppId, data) =>
    api.post(`/sales/opportunities/${oppId}/assessments/apply`, data),

  // 执行技术评估
  evaluate: (assessmentId, data) =>
    api.post(`/sales/assessments/${assessmentId}/evaluate`, data),

  // 获取评估列表
  getLeadAssessments: (leadId) => api.get(`/sales/leads/${leadId}/assessments`),
  getOpportunityAssessments: (oppId) =>
    api.get(`/sales/opportunities/${oppId}/assessments`),

  // 获取评估详情
  get: (assessmentId) => api.get(`/sales/assessments/${assessmentId}`),

  // 评分规则管理
  getScoringRules: () => api.get("/sales/scoring-rules"),
  createScoringRule: (data) => api.post("/sales/scoring-rules", data),
  activateScoringRule: (ruleId) =>
    api.put(`/sales/scoring-rules/${ruleId}/activate`),

  // 失败案例库
  getFailureCases: (params) => api.get("/sales/failure-cases", { params }),
  getFailureCase: (id) => api.get(`/sales/failure-cases/${id}`),
  createFailureCase: (data) => api.post("/sales/failure-cases", data),
  updateFailureCase: (id, data) => api.put(`/sales/failure-cases/${id}`, data),
  findSimilarCases: (params) =>
    api.get("/sales/failure-cases/similar", { params }),

  // 未决事项
  getOpenItems: (params) => api.get("/sales/open-items", { params }),
  createOpenItemForLead: (leadId, data) =>
    api.post(`/sales/leads/${leadId}/open-items`, data),
  createOpenItemForOpportunity: (oppId, data) =>
    api.post(`/sales/opportunities/${oppId}/open-items`, data),
  updateOpenItem: (itemId, data) =>
    api.put(`/sales/open-items/${itemId}`, data),
  closeOpenItem: (itemId) => api.post(`/sales/open-items/${itemId}/close`),

  // 需求详情管理
  getRequirementDetail: (leadId) =>
    api.get(`/sales/leads/${leadId}/requirement-detail`),
  createRequirementDetail: (leadId, data) =>
    api.post(`/sales/leads/${leadId}/requirement-detail`, data),
  updateRequirementDetail: (leadId, data) =>
    api.put(`/sales/leads/${leadId}/requirement-detail`, data),

  // 需求冻结管理
  getRequirementFreezes: (sourceType, sourceId) => {
    const path =
      sourceType === "lead"
        ? `/sales/leads/${sourceId}/requirement-freezes`
        : `/sales/opportunities/${sourceId}/requirement-freezes`;
    return api.get(path);
  },
  createRequirementFreeze: (sourceType, sourceId, data) => {
    const path =
      sourceType === "lead"
        ? `/sales/leads/${sourceId}/requirement-freezes`
        : `/sales/opportunities/${sourceId}/requirement-freezes`;
    return api.post(path, data);
  },

  // AI澄清管理
  getAIClarifications: (params) =>
    api.get("/sales/ai-clarifications", { params }),
  createAIClarificationForLead: (leadId, data) =>
    api.post(`/sales/leads/${leadId}/ai-clarifications`, data),
  createAIClarificationForOpportunity: (oppId, data) =>
    api.post(`/sales/opportunities/${oppId}/ai-clarifications`, data),
  updateAIClarification: (clarificationId, data) =>
    api.put(`/sales/ai-clarifications/${clarificationId}`, data),
  getAIClarification: (clarificationId) =>
    api.get(`/sales/ai-clarifications/${clarificationId}`),
};

export const rdProjectApi = {
  // 研发项目分类
  getCategories: (params) => api.get("/rd-projects/categories", { params }),

  // 研发项目管理
  list: (params) => api.get("/rd-projects", { params }),
  get: (id) => api.get(`/rd-projects/${id}`),
  create: (data) => api.post("/rd-projects", data),
  update: (id, data) => api.put(`/rd-projects/${id}`, data),
  approve: (id, data) => api.put(`/rd-projects/${id}/approve`, data),
  close: (id, data) => api.put(`/rd-projects/${id}/close`, data),
  linkProject: (id, data) => api.put(`/rd-projects/${id}/link-project`, data),

  // 研发费用类型
  getCostTypes: (params) => api.get("/rd-projects/rd-cost-types", { params }),

  // 研发费用管理
  getCosts: (params) => api.get("/rd-projects/rd-costs", { params }),
  createCost: (data) => api.post("/rd-projects/rd-costs", data),
  updateCost: (id, data) => api.put(`/rd-projects/rd-costs/${id}`, data),
  calculateLaborCost: (data) => api.post("/rd-projects/rd-costs/calc-labor", data),

  // 费用汇总
  getCostSummary: (projectId) =>
    api.get(`/rd-projects/${projectId}/cost-summary`),
  getTimesheetSummary: (projectId, params) =>
    api.get(`/rd-projects/${projectId}/timesheet-summary`, { params }),

  // 费用分摊规则
  getAllocationRules: (params) =>
    api.get("/rd-projects/rd-cost-allocation-rules", { params }),
  applyAllocation: (ruleId, data) =>
    api.post("/rd-projects/rd-costs/apply-allocation", data, {
      params: { rule_id: ruleId, ...data },
    }),

  // 研发项目工作日志
  getWorklogs: (projectId, params) =>
    api.get(`/rd-projects/${projectId}/worklogs`, { params }),
  createWorklog: (projectId, data) =>
    api.post(`/rd-projects/${projectId}/worklogs`, data),

  // 研发项目文档管理
  getDocuments: (projectId, params) =>
    api.get(`/rd-projects/${projectId}/documents`, { params }),
  createDocument: (projectId, data) =>
    api.post(`/rd-projects/${projectId}/documents`, data),
  uploadDocument: (projectId, formData) =>
    api.post(`/rd-projects/${projectId}/documents/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  downloadDocument: (projectId, docId) =>
    api.get(`/rd-projects/${projectId}/documents/${docId}/download`, {
      responseType: "blob",
    }),
};

export const rdReportApi = {
  // 研发费用辅助账
  getAuxiliaryLedger: (params) =>
    api.get("/report-center/rd-expense/rd-auxiliary-ledger", { params }),

  // 研发费用加计扣除明细
  getDeductionDetail: (params) =>
    api.get("/report-center/rd-expense/rd-deduction-detail", { params }),

  // 高新企业研发费用表
  getHighTechReport: (params) => api.get("/report-center/rd-expense/rd-high-tech", { params }),

  // 研发投入强度报表
  getIntensityReport: (params) => api.get("/report-center/rd-expense/rd-intensity", { params }),

  // 研发人员统计
  getPersonnelReport: (params) => api.get("/report-center/rd-expense/rd-personnel", { params }),

  // 导出研发费用报表
  exportReport: (params) =>
    api.get("/report-center/rd-expense/rd-export", { params, responseType: "blob" }),
};
