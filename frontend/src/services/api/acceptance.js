import { api } from "./client.js";

export const acceptanceApi = {
  list: (params) => api.get("/acceptance/list", { params }),
  detail: (id) => api.get(`/acceptance/${id}`),
  create: (data) => api.post("/acceptance/", data),
  update: (id, data) => api.put(`/acceptance/${id}`, data),
  addChecklist: (id, data) => api.post(`/acceptance/${id}/checklist`, data),
  signOff: (id, data) => api.put(`/acceptance/${id}/sign`, data),
};
