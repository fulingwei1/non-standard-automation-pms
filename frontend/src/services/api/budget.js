import { api } from "./client.js";

export const budgetApi = {
  list: (params) => api.get("/budgets/", { params }),
  get: (id) => api.get(`/budgets/${id}`),
  create: (data) => api.post("/budgets/", data),
  update: (id, data) => api.put(`/budgets/${id}`, data),
  delete: (id) => api.delete(`/budgets/${id}`),
  submit: (id) => api.post(`/budgets/${id}/submit`),
  approve: (id, data) => api.post(`/budgets/${id}/approve`, data),
  getByProject: (projectId, params) =>
    api.get(`/budgets/projects/${projectId}/budgets`, { params }),
};

