import { api } from "./client.js";

export const aiSalesApi = {
  // 话术推荐
  recommendScripts: (customerId, stage, scenario) => 
    api.get("/ai-sales/scripts", { params: { customerId, stage, scenario } }),
  
  // 方案生成
  generateProposal: (opportunityId, proposalType) =>
    api.post("/ai-sales/proposal", { opportunityId, proposalType }),
  
  // 竞品分析
  analyzeCompetitor: (competitorName) =>
    api.get("/ai-sales/competitor-analysis", { params: { competitorName } }),
  
  // 流失风险
  getChurnRiskList: () =>
    api.get("/ai-sales/churn-risk"),
};
