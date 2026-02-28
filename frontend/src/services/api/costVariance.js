import { api } from "./client.js";
export const costVarianceApi = {
  summary: () => api.get("/cost-variance/summary"),
  patterns: () => api.get("/cost-variance/patterns"),
  detail: (projectId) => api.get(`/cost-variance/${projectId}`),
};
