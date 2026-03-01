import { api } from "./client.js";

export const requirementExtractionApi = {
  // 抽取项目需求
  extractRequirements: (projectId) => api.get(`/requirement-extraction/projects/${projectId}/requirements`),
  
  // 推荐工程师
  recommendEngineers: (requirementId, limit = 5) =>
    api.post(`/requirement-extraction/requirements/${requirementId}/recommend`, null, {
      params: { limit },
    }),
  
  // 项目自动推荐
  autoRecommendForProject: (projectId, limit = 5) =>
    api.post(`/requirement-extraction/projects/${projectId}/auto-recommend`, null, {
      params: { limit },
    }),
};
