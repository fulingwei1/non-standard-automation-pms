import { api } from "./client.js";

// AI销售助手API
export const aiSalesApi = {
  recommendScripts: (customerId, opportunityId, scenario) =>
    api.get(`/sales/ai/customers/${customerId}/recommend-scripts`, {
      params: { opportunity_id: opportunityId, scenario_type: scenario },
    }),
  generateProposal: (opportunityId, type) =>
    api.post(`/sales/ai/opportunities/${opportunityId}/generate-proposal`, null, {
      params: { proposal_type: type },
    }),
  analyzeCompetitor: (name, category) =>
    api.get("/sales/ai/competitor-analysis", {
      params: { competitor_name: name, product_category: category },
    }),
  getChurnRiskList: () => api.get("/sales/ai/churn-risk-list"),
};

// 智能报价API
export const intelligentQuoteApi = {
  getHistoricalPrices: (category, amount, industry) =>
    api.get("/sales/quotes/historical-prices", {
      params: { product_category: category, estimated_amount: amount, industry },
    }),
  getCompetitorComparison: (category, ourPrice) =>
    api.get("/sales/competitor-prices/comparison", {
      params: { product_category: category, our_price: ourPrice },
    }),
  getOptimalPrice: (quoteId, targetMargin) =>
    api.post(`/sales/quotes/${quoteId}/optimal-price`, null, {
      params: { target_margin: targetMargin },
    }),
  predictWinRate: (opportunityId) =>
    api.get(`/sales/opportunities/${opportunityId}/win-rate-prediction`),
  batchPredictWinRate: (ids) =>
    api.post("/sales/batch-win-rate-prediction", { opportunity_ids: ids }),
};

// 销售自动化API
export const salesAutomationApi = {
  getFollowUpReminders: (days = 3) =>
    api.get("/sales/follow-up-reminders", { params: { days } }),
  getEmailSequences: (type) =>
    api.get("/sales/email-sequences", { params: { sequence_type: type } }),
  getTaskTriggers: () => api.get("/sales/auto-tasks/triggers"),
  generateReport: (type, startDate, endDate) =>
    api.post("/sales/reports/generate", null, {
      params: { report_type: type, start_date: startDate, end_date: endDate },
    }),
  getReportSchedules: () => api.get("/sales/reports/schedules"),
};

// 需求提取与工程师推荐 API
export const requirementExtractionApi = {
  extractRequirements: (projectId) =>
    api.get(`/projects/${projectId}/requirements`),
  recommendEngineers: (requirementId, limit = 5) =>
    api.post(`/requirements/${requirementId}/recommend`, null, {
      params: { limit },
    }),
};
