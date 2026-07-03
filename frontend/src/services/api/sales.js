import { api } from "./client.js";

const toFiniteNumber = (value) => {
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : 0;
};

const unwrapData = (response) => response?.data?.data ?? response?.data ?? {};

const withData = (response, data) => ({
  ...response,
  data,
});



export const leadApi = {
  list: (params) => api.get("/sales/leads", { params }),
  get: (id) => api.get(`/sales/leads/${id}`),
  create: (data) => api.post("/sales/leads", data),
  update: (id, data) => api.put(`/sales/leads/${id}`, data),
  getFollowUps: (id) => api.get(`/sales/leads/${id}/follow-ups`),
  createFollowUp: (id, data) => api.post(`/sales/leads/${id}/follow-ups`, data),
  createQuickFollowUp: (id, data) => api.post(`/sales/leads/${id}/follow-ups/quick`, data),
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
  delete: (id) => api.delete(`/sales/opportunities/${id}`),
  // 商机阶段快速更新（用于看板拖拽/列表快捷切换）
  updateStage: (id, stage) =>
    api.put(`/sales/opportunities/${id}/stage`, null, {
      params: { stage },
    }),
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
  compareVersions: (id, versionId1, versionId2) =>
    api.get(`/sales/quotes/${id}/versions/compare`, {
      params: {
        version_id_1: versionId1,
        version_id_2: versionId2,
      },
    }),
  approve: (id, data) => api.post(`/sales/quotes/${id}/approve`, data),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post("/sales/quotes/approval/submit", { quote_ids: [id] }),
  getApprovalStatus: (id) => api.get(`/sales/quotes/approval/status/${id}`),
  approvalAction: (id, data) =>
    api.post("/sales/quotes/approval/action", { ...data, quote_id: id }),
  getApprovalHistory: (id) => api.get("/sales/quotes/approval/history", { params: { quote_id: id } }),
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
  recalculateCost: (id, params) =>
    api.post(`/sales/quotes/${id}/recalculate`, null, { params }),
  applyCostTemplate: (templateId, data) =>
    api.post(`/sales/quote-templates/${templateId}/apply`, data || {}),
  calculateCost: (id, versionId) =>
    api.post(`/sales/quotes/${id}/recalculate`, null, {
      params: { version_id: versionId },
    }),
  checkCost: (id) =>
    api.get(`/sales/quotes/${id}/cost-analysis`),
  submitCostApproval: (id, data) =>
    api.post(`/sales/quotes/approval/submit`, { quote_ids: [id], ...data }),
  approveCost: (id, data) =>
    api.post("/sales/quotes/approval/action", { ...data, quote_id: id }),
  rejectCost: (id, data) =>
    api.post("/sales/quotes/approval/action", { ...data, quote_id: id, action: "reject" }),
  getCostApprovalHistory: (id) =>
    api.get("/sales/quotes/approval/history", { params: { quote_id: id } }),
  compareCosts: (id) =>
    api.get(`/sales/quotes/${id}/cost-analysis`),
  getCostTrend: (id, params) =>
    api.get(`/sales/quotes/${id}/cost-analysis`, { params }),
  getCostStructure: (id) =>
    api.get(`/sales/quotes/${id}/cost-breakdown`),
  getCostMatchSuggestions: (id, versionId) =>
    api.post(`/sales/quotes/${id}/cost-match-suggestions`, null, {
      params: { version_id: versionId },
    }),
  applyCostSuggestions: (id, versionId, data) =>
    api.post(`/sales/quotes/${id}/cost-match-suggestions/apply`, data, {
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
  getPaymentPlans: (id) => api.get(`/sales/contracts/${id}/payment-plans`),
  create: (data) => api.post("/sales/contracts", data),
  // SALES-12：报价一键转合同（后端自动带出客户/商机/金额/版本，走 G3 验证）
  fromQuote: (data) => api.post("/sales/contracts/from-quote", data),
  update: (id, data) => api.put(`/sales/contracts/${id}`, data),
  sign: (id, data) => api.post(`/sales/contracts/${id}/sign`, data),
  createProject: (id, data) => api.post(`/sales/contracts/${id}/project`, data),
  getDeliverables: (id) => api.get(`/sales/contracts/${id}/deliverables`),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post("/sales/contracts/approval/submit", { contract_ids: [id] }),
  getApprovalStatus: (id) => api.get(`/sales/contracts/approval/status/${id}`),
  approvalAction: (id, data) =>
    api.post("/sales/contracts/approval/action", { ...data, contract_id: id }),
  getApprovalHistory: (id) =>
    api.get("/sales/contracts/approval/history", { params: { contract_id: id } }),
};

const normalizeInvoiceApprovalPayload = (data = {}) => {
  const { approved, remark, comments, ...rest } = data || {};
  const explicitAction = rest.action;
  const action =
    explicitAction ||
    (approved === false ? "REJECT" : "APPROVE");
  return {
    ...rest,
    action: typeof action === "string" ? action.toUpperCase() : action,
    comment: rest.comment ?? remark ?? comments,
  };
};

export const invoiceApi = {
  list: (params) => api.get("/sales/invoices", { params }),
  get: (id) => api.get(`/sales/invoices/${id}`),
  create: (data) => api.post("/sales/invoices", data),
  update: (id, data) => api.put(`/sales/invoices/${id}`, data),
  delete: (id) => api.delete(`/sales/invoices/${id}`),
  issue: (id, data) => api.post(`/sales/invoices/${id}/issue`, data),
  receivePayment: (id, data) =>
    api.post(`/sales/invoices/${id}/receive-payment`, null, { params: data }),
  approve: (id, data) =>
    api.post(`/sales/invoices/${id}/approval/action`, {
      ...normalizeInvoiceApprovalPayload(data),
      invoice_id: id,
    }),
  getApprovals: (id) => api.get(`/sales/invoices/${id}/approval-history`),
  approveApproval: (invoiceId, data) =>
    api.post(`/sales/invoices/${invoiceId}/approval/action`, {
      ...normalizeInvoiceApprovalPayload(data),
      action: "APPROVE",
    }),
  rejectApproval: (invoiceId, data) =>
    api.post(`/sales/invoices/${invoiceId}/approval/action`, {
      ...normalizeInvoiceApprovalPayload(data),
      action: "REJECT",
    }),
  // Approval Workflow APIs (Sprint 2)
  startApproval: (id) => api.post(`/sales/invoices/${id}/approval/start`),
  getApprovalStatus: (id) => api.get(`/sales/invoices/${id}/approval-status`),
  approvalAction: (id, data) =>
    api.post(`/sales/invoices/${id}/approval/action`, normalizeInvoiceApprovalPayload(data)),
  getApprovalHistory: (id) => api.get(`/sales/invoices/${id}/approval-history`),
};

export const paymentApi = {
  list: (params) => api.get("/sales/payments/records", { params }),
  get: (id) => api.get(`/sales/payments/records/${id}`),
  create: (params) => api.post("/sales/payments/records", null, { params }),
  matchInvoice: (id, params) =>
    api.put(`/sales/payments/records/${id}/match-invoice`, null, { params }),
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
  list: (params) => api.get("/sales/receivables", { params }),
  getOverdue: (params) => api.get("/sales/receivables/overdue", { params }),
  getAging: (params) => api.get("/sales/receivables/aging", { params }),
  getSummary: (params) => api.get("/sales/receivables/summary", { params }),
};

export const paymentPlanApi = {
  list: (params) => api.get("/sales/payments/plans", { params }),
};

export const disputeApi = {
  list: (params) => api.get("/sales/disputes", { params }),
  // Note: get/update not available - backend only supports list and create
  create: (data) => api.post("/sales/disputes", data),
};

export const salesTeamApi = {
  // 获取销售团队成员统计视图
  getTeam: (params) => api.get("/sales/team", { params }),
  // 获取销售团队组织架构树
  getOrg: (params) => api.get("/sales/team/org", { params }),
  // 获取销售团队实体列表
  listTeams: (params) => api.get("/sales/sales-teams", { params }),
  // 创建销售团队实体
  createTeam: (data) => api.post("/sales/sales-teams", data),
  // 添加团队成员
  addTeamMember: (teamId, data) =>
    api.post(`/sales/sales-teams/${teamId}/members`, data),
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
  // 销售仪表盘
  getDashboard: (params) => api.get("/sales/dashboard", { params }),
  getPipelineStats: async (params) => {
    const response = await api.get("/sales/statistics/funnel", { params });
    return withData(response, unwrapData(response));
  },
  getMonthlyTrend: async (params = {}) => {
    const response = await api.get("/sales/statistics/overview", {
      params: { ...params, period: "year" },
    });
    const data = unwrapData(response);
    let previousAchieved = 0;
    const monthly = (data.time_series || []).map((item) => {
      const achieved = toFiniteNumber(item.won_amount ?? item.total_amount);
      const target = Math.max(toFiniteNumber(item.target), achieved * 1.1, 1);
      const growth =
        previousAchieved > 0
          ? Math.round(((achieved - previousAchieved) / previousAchieved) * 100)
          : 0;
      previousAchieved = achieved;
      return {
        month: item.label,
        target,
        achieved,
        growth,
      };
    });
    return withData(response, monthly);
  },
  getByCustomer: async (params = {}) => {
    const { limit, ...rest } = params;
    const response = await api.get("/sales/reports/customer-contribution", {
      params: { ...rest, top_n: limit || 10 },
    });
    const data = unwrapData(response);
    const customers = (data.customers || []).map((item) => ({
      name: item.customer_name || "未命名客户",
      projects: toFiniteNumber(item.contract_count),
      amount: toFiniteNumber(item.total_amount),
      growth: 0,
    }));
    return withData(response, customers);
  },
  getByProduct: async (params = {}) => {
    const response = await api.get("/sales/statistics/overview", {
      params: { ...params, period: "year" },
    });
    const data = unwrapData(response);
    const totalAmount = (data.by_product || []).reduce(
      (sum, item) => sum + toFiniteNumber(item.amount),
      0
    );
    const products = (data.by_product || []).map((item) => {
      const amount = toFiniteNumber(item.amount);
      const count = toFiniteNumber(item.count);
      return {
        name: item.product_type || "未分类",
        count,
        amount,
        avgPrice: count > 0 ? amount / count : 0,
        ratio: totalAmount > 0 ? Math.round((amount / totalAmount) * 100) : 0,
      };
    });
    return withData(response, products);
  },
  getByRegion: async (params = {}) => {
    const response = await api.get("/sales/statistics/overview", {
      params: { ...params, period: "year" },
    });
    const data = unwrapData(response);
    const regions = (data.by_customer_type || []).map((item) => ({
      region: item.customer_type || "未分类",
      customers: toFiniteNumber(item.count),
      amount: toFiniteNumber(item.amount),
      growth: 0,
    }));
    return withData(response, regions);
  },
};

export const salesApi = {
  // 销售漏斗（综合版）
  getFunnel: (params) => api.get("/sales/funnel", { params }),
  // 销售漏斗（旧版统计）
  getFunnelLegacy: (params) => api.get("/sales/statistics/funnel", { params }),
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
    return api.get("/sales/payments/plans", { params: query });
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

export const quoteDeliveryApi = {
  get: (quoteId) => api.get(`/sales/quotes/${quoteId}/delivery`),
  update: (quoteId, data) => api.put(`/sales/quotes/${quoteId}/delivery`, data),
  upcoming: (params) => api.get("/sales/quotes/delivery/upcoming", { params }),
  overdue: () => api.get("/sales/quotes/delivery/overdue"),
  calendar: (params) => api.get("/sales/quotes/delivery/calendar", { params }),
};

// ========== P0/P1 新功能 API ==========

// 智能跟进提醒 API
export const followUpReminderApi = {
  // 获取跟进提醒列表
  list: (params) => api.get("/sales/follow-up/reminders", { params }),
  // 获取汇总统计
  getSummary: () => api.get("/sales/follow-up/reminders/summary"),
  // 获取紧急提醒
  getUrgent: () => api.get("/sales/follow-up/reminders/urgent"),
  // 获取行动看板
  getActionBoard: (params) =>
    api.get("/sales/follow-up/reminders/action-board", { params }),
};

// 催款优先级排序 API
export const collectionPriorityApi = {
  // 获取催款优先级列表
  list: (params) => api.get("/sales/collection/priority", { params }),
  // 获取汇总统计
  getSummary: () => api.get("/sales/collection/priority/summary"),
  // 获取紧急催款项
  getCritical: () => api.get("/sales/collection/priority/critical"),
};

// 一键成本推荐 API
export const quickCostApi = {
  // 商机成本推荐
  getForOpportunity: (oppId) =>
    api.get(`/sales/quick-cost/opportunities/${oppId}/quick-cost`),
  // 报价成本推荐
  getForQuote: (quoteId) =>
    api.get(`/sales/quick-cost/quotes/${quoteId}/quick-cost`),
};

// 商机健康度评分 API
export const opportunityHealthApi = {
  // 获取单个商机健康度
  get: (oppId) => api.get(`/sales/opportunities/${oppId}/health`),
  // 获取用户所有商机健康度
  list: (params) => api.get("/sales/opportunities/health", { params }),
  // 获取健康度汇总
  getSummary: () => api.get("/sales/opportunities/health/summary"),
  // 获取问题商机
  getCritical: () => api.get("/sales/opportunities/health/critical"),
};

// 报价对比分析 API
export const quoteComparisonApi = {
  // 对比多版本（支持2-4个版本）
  compareVersions: (quoteId, versionIds) =>
    api.get(`/sales/quotes/${quoteId}/versions/compare`, {
      params: { version_ids: versionIds },
    }),
  // 对比同商机多报价
  compareByOpportunity: (oppId) =>
    api.get(`/sales/quotes/opportunity/${oppId}/compare`),
  // 与竞品对比
  compareWithCompetitor: (quoteId, competitorPrice, competitorName) =>
    api.post("/sales/quotes/competitor-compare", null, {
      params: {
        quote_id: quoteId,
        competitor_price: competitorPrice,
        competitor_name: competitorName,
      },
    }),
};

// 合同里程碑提醒 API
export const contractMilestoneApi = {
  // 获取里程碑列表
  list: (params) => api.get("/sales/contracts/milestones", { params }),
  // 获取汇总统计
  getSummary: () => api.get("/sales/contracts/milestones/summary"),
  // 获取过期里程碑
  getOverdue: () => api.get("/sales/contracts/milestones/overdue"),
  // 获取付款节点
  getPayments: (params) =>
    api.get("/sales/contracts/milestones/payments", { params }),
};

// 销售漏斗优化 API（Issue 6.x）
export const funnelOptimizationApi = {
  // 获取转化率分析数据
  getConversionRates: (params) =>
    api.get("/sales/funnel/conversion-rates", { params }),
  // 获取瓶颈识别数据
  getBottlenecks: (params) =>
    api.get("/sales/funnel/bottlenecks", { params }),
  // 获取预测准确性数据
  getPredictionAccuracy: (params) =>
    api.get("/sales/funnel/prediction-accuracy", { params }),
  // 获取健康度仪表盘
  getHealthDashboard: (params) =>
    api.get("/sales/funnel/health-dashboard", { params }),
  // 获取趋势数据
  getTrends: (params) =>
    api.get("/sales/funnel/trends", { params }),
};
