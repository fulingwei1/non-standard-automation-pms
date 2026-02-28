import { api } from "./client.js";

export const laborCostApi = {
  summary: () => api.get("/labor-cost/summary"),
  byEngineer: () => api.get("/labor-cost/by-engineer"),
  detail: (projectId) => api.get(`/labor-cost/${projectId}`),
};
