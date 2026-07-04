import { api } from "./client.js";

const BASE = "/sales/relationship/relationship";

export const relationshipMaturityApi = {
  assessment: (customerId, params) =>
    api.get(`${BASE}/customer/${customerId}/assessment`, { params }),
  portfolio: () => api.get(`${BASE}/portfolio-analysis`),
  improvementPlan: (data) => api.post(`${BASE}/improvement-plan`, data),
  maturityModel: () => api.get(`${BASE}/maturity-model`),
};
