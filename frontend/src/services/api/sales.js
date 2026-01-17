import { api } from "./client.js";



export const leadApi = {
  list: (params) => api.get("/sales/leads", { params }),
  get: (id) => api.get(`/sales/leads/${id}`),
  create: (data) => api.post("/sales/leads", data),
  update: (id, data) => api.put(`/sales/leads/${id}`, data),
  getFollowUps: (id) => api.get(`/sales/leads/${id}/follow-ups`),
  createFollowUp: (id, data) => api.post(`/sales/leads/${id}/follow-ups`, data),
  convert: (id, customerId, requirementData, skipValidation) =>
    api.post(`/sales/leads/${id}/convert`, requirementData, {
      params: {
        customer_id: customerId,
        skip_validation: skipValidation || false,
      },
    }),
};

export const opportunityApi = {
  // Issue 6.3: 商机赢单概率预测
  getWinProbability: (id) =>
    api.get(`/sales/opportunities/${id}/win-probability`),
  list: (params) => api.get("/sales/opportunities", { params }),
  // Alias for backward compatibility
  getOpportunities: (params) => api.get("/sales/opportunities", { params }),
  get: (id) => api.get(`/sales/opportunities/${id}`),
  create: (data) => api.post("/sales/opportunities", data),
  update: (id, data) => api.put(`/sales/opportunities/${id}`, data),
  submitGate: (id, data, gateType) =>
    api.post(`/sales/opportunities/${id}/gate`, data, {
      params: { gate_type: gateType || "G2" },
    }),
};

export const quoteApi = {
  list: (params) => api.get("/sales/quotes", { params }),
  // Aliases for backward compatibility
  getQuotes: (params) => api.get("/sales/quotes", { params }),
  getStats: (params) => api.get("/sales/statistics/quote-stats", { params }),
  get: (id) => api.get(`/sales/quotes/${id}`),
  create: (data) => api.post("/sales/quotes", data),
  update: (id, data) => api.put(`/sales/quotes/${id}`, data),
  createVersion: (id, data) => api.post(`/sales/quotes/${id}/versions`, data),
  getVersions: (id) => api.get(`/sales/quotes/${id}/versions`),
  approve: (id, data) => api.post(`/sales/quotes/${id}/approve`, data),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post(`/sales/quotes/${id}/approval/start`),
  getApprovalStatus: (id) => api.get(`/sales/quotes/${id}/approval-status`),
  approvalAction: (id, data) =>
    api.post(`/sales/quotes/${id}/approval/action`, data),
  getApprovalHistory: (id) => api.get(`/sales/quotes/${id}/approval-history`),
  // Quote Items APIs
  getItems: (id, versionId) =>
    api.get(`/sales/quotes/${id}/items`, { params: { version_id: versionId } }),
  createItem: (id, data, versionId) =>
    api.post(`/sales/quotes/${id}/items`, data, {
      params: { version_id: versionId },
    }),
  updateItem: (id, itemId, data) =>
    api.put(`/sales/quotes/${id}/items/${itemId}`, data),
  deleteItem: (id, itemId) => api.delete(`/sales/quotes/${id}/items/${itemId}`),
  batchUpdateItems: (id, data, versionId) =>
    api.put(`/sales/quotes/${id}/items/batch`, data, {
      params: { version_id: versionId },
    }),
  // Cost Management APIs
  getCostBreakdown: (id) => api.get(`/sales/quotes/${id}/cost-breakdown`),
  applyCostTemplate: (id, templateId, versionId, adjustments) =>
    api.post(`/sales/quotes/${id}/apply-template`, adjustments || {}, {
      params: { template_id: templateId, version_id: versionId },
    }),
  calculateCost: (id, versionId) =>
    api.post(`/sales/quotes/${id}/calculate-cost`, null, {
      params: { version_id: versionId },
    }),
  checkCost: (id, versionId) =>
    api.get(`/sales/quotes/${id}/cost-check`, {
      params: { version_id: versionId },
    }),
  submitCostApproval: (id, data) =>
    api.post(`/sales/quotes/${id}/cost-approval/submit`, data),
  approveCost: (id, approvalId, data) =>
    api.post(`/sales/quotes/${id}/cost-approval/${approvalId}/approve`, data),
  rejectCost: (id, approvalId, data) =>
    api.post(`/sales/quotes/${id}/cost-approval/${approvalId}/reject`, data),
  getCostApprovalHistory: (id) =>
    api.get(`/sales/quotes/${id}/cost-approval/history`),
  compareCosts: (id, params) =>
    api.get(`/sales/quotes/${id}/cost-comparison`, { params }),
  getCostTrend: (id, params) =>
    api.get(`/sales/quotes/${id}/cost-trend`, { params }),
  getCostStructure: (id, versionId) =>
    api.get(`/sales/quotes/${id}/cost-structure`, {
      params: { version_id: versionId },
    }),
  getCostMatchSuggestions: (id, versionId) =>
    api.post(`/sales/quotes/${id}/items/auto-match-cost-suggestions`, null, {
      params: { version_id: versionId },
    }),
  applyCostSuggestions: (id, versionId, data) =>
    api.post(`/sales/quotes/${id}/items/apply-cost-suggestions`, data, {
      params: { version_id: versionId },
    }),
};

export const salesTemplateApi = {
  listQuoteTemplates: (params) => api.get("/sales/quote-templates", { params }),
  createQuoteTemplate: (data) => api.post("/sales/quote-templates", data),
  updateQuoteTemplate: (id, data) =>
    api.put(`/sales/quote-templates/${id}`, data),
  createQuoteVersion: (id, data) =>
    api.post(`/sales/quote-templates/${id}/versions`, data),
  publishQuoteVersion: (templateId, versionId) =>
    api.post(
      `/sales/quote-templates/${templateId}/versions/${versionId}/publish`,
    ),
  applyQuoteTemplate: (id, data) =>
    api.post(`/sales/quote-templates/${id}/apply`, data || {}),
  listContractTemplates: (params) =>
    api.get("/sales/contract-templates", { params }),
  createContractTemplate: (data) => api.post("/sales/contract-templates", data),
  updateContractTemplate: (id, data) =>
    api.put(`/sales/contract-templates/${id}`, data),
  createContractVersion: (id, data) =>
    api.post(`/sales/contract-templates/${id}/versions`, data),
  publishContractVersion: (templateId, versionId) =>
    api.post(
      `/sales/contract-templates/${templateId}/versions/${versionId}/publish`,
    ),
  applyContractTemplate: (id, params) =>
    api.get(`/sales/contract-templates/${id}/apply`, { params }),
  listRuleSets: (params) => api.get("/sales/cpq/rule-sets", { params }),
  createRuleSet: (data) => api.post("/sales/cpq/rule-sets", data),
  updateRuleSet: (id, data) => api.put(`/sales/cpq/rule-sets/${id}`, data),
  previewPrice: (data) => api.post("/sales/cpq/price-preview", data),
  // Cost Template APIs
  listCostTemplates: (params) => api.get("/sales/cost-templates", { params }),
  getCostTemplate: (id) => api.get(`/sales/cost-templates/${id}`),
  createCostTemplate: (data) => api.post("/sales/cost-templates", data),
  updateCostTemplate: (id, data) =>
    api.put(`/sales/cost-templates/${id}`, data),
  deleteCostTemplate: (id) => api.delete(`/sales/cost-templates/${id}`),
  // Purchase Material Cost APIs
  listPurchaseMaterialCosts: (params) =>
    api.get("/sales/purchase-material-costs", { params }),
  getPurchaseMaterialCost: (id) =>
    api.get(`/sales/purchase-material-costs/${id}`),
  createPurchaseMaterialCost: (data) =>
    api.post("/sales/purchase-material-costs", data),
  updatePurchaseMaterialCost: (id, data) =>
    api.put(`/sales/purchase-material-costs/${id}`, data),
  deletePurchaseMaterialCost: (id) =>
    api.delete(`/sales/purchase-material-costs/${id}`),
  matchMaterialCost: (data) =>
    api.post("/sales/purchase-material-costs/match", data),
  getCostUpdateReminder: () =>
    api.get("/sales/purchase-material-costs/reminder"),
  updateCostUpdateReminder: (data) =>
    api.put("/sales/purchase-material-costs/reminder", data),
  acknowledgeCostUpdateReminder: () =>
    api.post("/sales/purchase-material-costs/reminder/acknowledge"),
};

export const contractApi = {
  list: (params) => api.get("/sales/contracts", { params }),
  get: (id) => api.get(`/sales/contracts/${id}`),
  create: (data) => api.post("/sales/contracts", data),
  update: (id, data) => api.put(`/sales/contracts/${id}`, data),
  sign: (id, data) => api.post(`/sales/contracts/${id}/sign`, data),
  createProject: (id, data) => api.post(`/sales/contracts/${id}/project`, data),
  getDeliverables: (id) => api.get(`/sales/contracts/${id}/deliverables`),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post(`/sales/contracts/${id}/approval/start`),
  getApprovalStatus: (id) => api.get(`/sales/contracts/${id}/approval-status`),
  approvalAction: (id, data) =>
    api.post(`/sales/contracts/${id}/approval/action`, data),
  getApprovalHistory: (id) =>
    api.get(`/sales/contracts/${id}/approval-history`),
};

export const invoiceApi = {
  list: (params) => api.get("/sales/invoices", { params }),
  get: (id) => api.get(`/sales/invoices/${id}`),
  create: (data) => api.post("/sales/invoices", data),
  update: (id, data) => api.put(`/sales/invoices/${id}`, data),
  issue: (id, data) => api.post(`/sales/invoices/${id}/issue`, data),
  receivePayment: (id, data) =>
    api.post(`/sales/invoices/${id}/receive-payment`, null, { params: data }),
  approve: (id, params) =>
    api.put(`/sales/invoices/${id}/approve`, null, { params }),
  getApprovals: (id) => api.get(`/sales/invoices/${id}/approvals`),
  approveApproval: (approvalId, params) =>
    api.put(`/sales/invoice-approvals/${approvalId}/approve`, null, { params }),
  rejectApproval: (approvalId, params) =>
    api.put(`/sales/invoice-approvals/${approvalId}/reject`, null, { params }),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post(`/sales/invoices/${id}/approval/start`),
  getApprovalStatus: (id) => api.get(`/sales/invoices/${id}/approval-status`),
  approvalAction: (id, data) =>
    api.post(`/sales/invoices/${id}/approval/action`, data),
  getApprovalHistory: (id) => api.get(`/sales/invoices/${id}/approval-history`),
};

export const paymentApi = {
  list: (params) => api.get("/sales/payments", { params }),
  get: (id) => api.get(`/sales/payments/${id}`),
  create: (params) => api.post("/sales/payments", null, { params }),
  matchInvoice: (id, params) =>
    api.put(`/sales/payments/${id}/match-invoice`, null, { params }),
  // 新增API端点
  getReminders: (params) => api.get("/sales/payments/reminders", { params }),
  getStatistics: (params) => api.get("/sales/payments/statistics", { params }),
  exportInvoices: (params) =>
    api.get("/sales/payments/invoices/export", {
      params,
      responseType: "blob",
    }),
};

export const receivableApi = {
  list: (params) => api.get("/sales/receivables/overdue", { params }),
  getAging: (params) => api.get("/sales/receivables/aging", { params }),
  getSummary: (params) => api.get("/sales/receivables/summary", { params }),
};

export const paymentPlanApi = {
  list: (params) => api.get("/sales/payment-plans", { params }),
};

export const disputeApi = {
  list: (params) => api.get("/sales/disputes", { params }),
  get: (id) => api.get(`/sales/disputes/${id}`),
  create: (data) => api.post("/sales/disputes", data),
  update: (id, data) => api.put(`/sales/disputes/${id}`, data),
};

export const salesTeamApi = {
  // 获取销售团队列表
  getTeam: (params) => api.get("/sales/team", { params }),
  // 获取销售业绩排名
  getRanking: (params) => api.get("/sales/team/ranking", { params }),
  // 导出销售团队数据
  exportTeam: (params) =>
    api.get("/sales/team/export", { params, responseType: "blob" }),
  // 获取/更新销售排名权重配置
  getRankingConfig: () => api.get("/sales/team/ranking/config"),
  updateRankingConfig: (data) =>
    api.put("/sales/team/ranking/config", data),
};

export const salesTargetApi = {
  // 获取销售目标列表
  list: (params) => api.get("/sales/targets", { params }),
  // 获取单个销售目标
  get: (id) => api.get(`/sales/targets/${id}`),
  // 创建销售目标
  create: (data) => api.post("/sales/targets", data),
  // 更新销售目标
  update: (id, data) => api.put(`/sales/targets/${id}`, data),
  // 删除销售目标
  delete: (id) => api.delete(`/sales/targets/${id}`),
};

export const salesStatisticsApi = {
  funnel: (params) => api.get("/sales/statistics/funnel", { params }),
  opportunitiesByStage: () =>
    api.get("/sales/statistics/opportunities-by-stage"),
  revenueForecast: (params) =>
    api.get("/sales/statistics/revenue-forecast", { params }),
  summary: (params) => api.get("/sales/statistics/summary", { params }),
  // Issue 6.3: 销售预测增强
  prediction: (params) => api.get("/sales/statistics/prediction", { params }),
  predictionAccuracy: (params) =>
    api.get("/sales/statistics/prediction/accuracy", { params }),
  // 销售业绩报告
  performance: (params) => api.get("/sales/reports/sales-performance", { params }),
};

export const salesApi = {
  // 销售漏斗
  getFunnel: (params) => api.get("/sales/statistics/funnel", { params }),
  // 待审批合同（使用合同列表筛选）
  getPendingApprovals: (params) =>
    api.get("/sales/contracts", {
      params: { status: "IN_REVIEW", page_size: 10, ...params },
    }),
  // Top客户贡献
  getTopCustomers: (params) =>
    api.get("/sales/reports/customer-contribution", { params }),
  // 付款计划
  getPaymentSchedule: (params = {}) => {
    const { limit, ...rest } = params || {};
    const query = {
      status: "PENDING",
      page_size: limit || 10,
      ...rest,
    };
    return api.get("/sales/payment-plans", { params: query });
  },
};

export const salesReportApi = {
  customerContribution: (params) =>
    api.get("/sales/reports/customer-contribution", { params }),
  o2cPipeline: (params) => api.get("/sales/reports/o2c-pipeline", { params }),
};

export const lossAnalysisApi = {
  deepAnalysis: (params) => api.get("/sales/analysis/loss-deep-analysis", { params }),
  byStage: (params) => api.get("/sales/analysis/loss-by-stage", { params }),
  patterns: (params) => api.get("/sales/analysis/loss-patterns", { params }),
  byPerson: (params) => api.get("/sales/analysis/loss-by-person", { params }),
};

export const presaleExpenseApi = {
  expenseLostProjects: (data) => api.post("/sales/expenses/expense-lost-projects", data),
  getLostProjectExpenses: (params) => api.get("/sales/expenses/lost-project-expenses", { params }),
  getExpenseStatistics: (params) => api.get("/sales/expenses/expense-statistics", { params }),
};

export const priorityApi = {
  calculateLeadPriority: (leadId) => api.post(`/sales/leads/${leadId}/calculate-priority`),
  getLeadPriorityRanking: (params) => api.get("/sales/leads/priority-ranking", { params }),
  getKeyLeads: () => api.get("/sales/leads/key-leads"),
  calculateOpportunityPriority: (oppId) => api.post(`/sales/opportunities/${oppId}/calculate-priority`),
  getOpportunityPriorityRanking: (params) => api.get("/sales/opportunities/priority-ranking", { params }),
  getKeyOpportunities: () => api.get("/sales/opportunities/key-opportunities"),
};

export const pipelineAnalysisApi = {
  getPipelineBreaks: (params) =>
    api.get("/sales/analysis/pipeline-breaks", { params }),
  getBreakReasons: (params) =>
    api.get("/sales/analysis/break-reasons", { params }),
  getBreakPatterns: (params) =>
    api.get("/sales/analysis/break-patterns", { params }),
  getBreakWarnings: (params) =>
    api.get("/sales/alerts/pipeline-break-warnings", { params }),
};

export const accountabilityApi = {
  getByStage: (params) =>
    api.get("/sales/analysis/accountability/by-stage", { params }),
  getByPerson: (params) =>
    api.get("/sales/analysis/accountability/by-person", { params }),
  getByDepartment: (params) =>
    api.get("/sales/analysis/accountability/by-department", { params }),
  getCostImpact: (params) =>
    api.get("/sales/analysis/accountability/cost-impact", { params }),
};

export const healthApi = {
  getLeadHealth: (leadId) => api.get(`/sales/health/lead/${leadId}`),
  getOpportunityHealth: (oppId) =>
    api.get(`/sales/health/opportunity/${oppId}`),
  getQuoteHealth: (quoteId) => api.get(`/sales/health/quote/${quoteId}`),
  getContractHealth: (contractId) =>
    api.get(`/sales/health/contract/${contractId}`),
  getPaymentHealth: (invoiceId) =>
    api.get(`/sales/health/payment/${invoiceId}`),
  getPipelineHealth: (params) => api.get("/sales/health/pipeline", { params }),
  getHealthWarnings: () => api.get("/sales/alerts/health-warnings"),
};

export const delayAnalysisApi = {
  getRootCause: (params) =>
    api.get("/sales/analysis/delay/root-cause", { params }),
  getImpact: (params) => api.get("/sales/analysis/delay/impact", { params }),
  getTrends: (params) => api.get("/sales/analysis/delay/trends", { params }),
};

export const costOverrunApi = {
  getReasons: (params) =>
    api.get("/sales/analysis/cost-overrun/reasons", { params }),
  getAccountability: (params) =>
    api.get("/sales/analysis/cost-overrun/accountability", { params }),
  getImpact: (params) =>
    api.get("/sales/analysis/cost-overrun/impact", { params }),
};

export const informationGapApi = {
  getMissing: (params) =>
    api.get("/sales/analysis/information-gap/missing", { params }),
  getImpact: (params) =>
    api.get("/sales/analysis/information-gap/impact", { params }),
  getQualityScore: (params) =>
    api.get("/sales/analysis/information-gap/quality-score", { params }),
};

export const crossAnalysisApi = {
  getCrossDimension: (params) =>
    api.get("/sales/analysis/cross-dimension", { params }),
};
