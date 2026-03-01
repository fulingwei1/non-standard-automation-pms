import { api } from "./client.js";

export const leadAssessmentApi = {
  list: (params) => api.get("/sales/leads/assessments", { params }),
  submit: (id, data) => api.post(`/sales/leads/assessments/${id}/submit`, data),
};
