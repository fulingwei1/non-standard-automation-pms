import { api } from "./client.js";

export const salesProjectApi = {
  list: (params) => api.get("/sales/projects", { params }),
  updateStage: (id, data) => api.put(`/sales/projects/${id}/stage`, data),
  addFollowUp: (id, data) => api.post(`/sales/projects/${id}/follow-ups`, data),
};
