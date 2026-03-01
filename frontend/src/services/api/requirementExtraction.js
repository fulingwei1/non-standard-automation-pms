import { api } from "./client.js";

export const requirementExtractionApi = {
  extractRequirements: (projectId) =>
    api.get(`/requirement-extraction/projects/${projectId}/requirements`),
  recommendEngineers: (requirementId, limit = 5) =>
    api.post(
      `/requirement-extraction/requirements/${requirementId}/recommend`,
      null,
      { params: { limit } },
    ),
  autoRecommendForProject: (projectId, limit = 5) =>
    api.post(`/requirement-extraction/projects/${projectId}/auto-recommend`, null, {
      params: { limit },
    }),
};
