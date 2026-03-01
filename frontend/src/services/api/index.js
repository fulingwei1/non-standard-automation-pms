
// AI销售助手API
export const aiSalesApi = {
  // 话术推荐
  recommendScripts: (customerId, opportunityId, scenario) =>
    api.get(`/sales/ai/customers/${customerId}/recommend-scripts`, {
      params: { opportunity_id: opportunityId, scenario_type: scenario }
    }),
  
  // 方案生成
  generateProposal: (opportunityId, type) =>
    api.post(`/sales/ai/opportunities/${opportunityId}/generate-proposal`, null, {
      params: { proposal_type: type }
    }),
  
  // 竞品分析
  analyzeCompetitor: (name, category) =>
    api.get('/sales/ai/competitor-analysis', {
      params: { competitor_name: name, product_category: category }
    }),
  
  // 流失风险
  getChurnRiskList: () =>
    api.get('/sales/ai/churn-risk-list'),
};

// 智能报价API
export const intelligentQuoteApi = {
  // 历史价格
  getHistoricalPrices: (category, amount, industry) =>
    api.get('/sales/quotes/historical-prices', {
      params: { product_category: category, estimated_amount: amount, industry }
    }),
  
  // 竞品价格对比
  getCompetitorComparison: (category, ourPrice) =>
    api.get('/sales/competitor-prices/comparison', {
      params: { product_category: category, our_price: ourPrice }
    }),
  
  // 最优价格建议
  getOptimalPrice: (quoteId, targetMargin) =>
    api.post(`/sales/quotes/${quoteId}/optimal-price`, null, {
      params: { target_margin: targetMargin }
    }),
  
  // 赢单率预测
  predictWinRate: (opportunityId) =>
    api.get(`/sales/opportunities/${opportunityId}/win-rate-prediction`),
  
  // 批量赢单率预测
  batchPredictWinRate: (ids) =>
    api.post('/sales/batch-win-rate-prediction', { opportunity_ids: ids }),
};

// 销售自动化API
export const salesAutomationApi = {
  // 跟进提醒
  getFollowUpReminders: (days = 3) =>
    api.get('/sales/follow-up-reminders', { params: { days } }),
  
  // 邮件序列
  getEmailSequences: (type) =>
    api.get('/sales/email-sequences', { params: { sequence_type: type } }),
  
  // 自动任务规则
  getTaskTriggers: () =>
    api.get('/sales/auto-tasks/triggers'),
  
  // 生成报告
  generateReport: (type, startDate, endDate) =>
    api.post('/sales/reports/generate', null, {
      params: { report_type: type, start_date: startDate, end_date: endDate }
    }),
  
  // 报告计划
  getReportSchedules: () =>
    api.get('/sales/reports/schedules'),
};
