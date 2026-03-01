import { api } from "./client.js";

export const assessmentApi = {
  list: (params) => api.get("/sales/assessments", { params }),
  create: (data) => api.post("/sales/assessments", data),
  submit: (id, data) => api.post(`/sales/assessments/${id}/submit`, data),
};
