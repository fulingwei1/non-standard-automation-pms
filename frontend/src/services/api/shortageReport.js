import { api } from "./client.js";

export const shortageReportApi = {
  list: (params) => api.get("/shortage/handling/reports", { params }),
  get: (id) => api.get(`/shortage/handling/reports/${id}`),
  confirm: (id) => api.put(`/shortage/handling/reports/${id}/confirm`),
  handle: (id, data) => api.put(`/shortage/handling/reports/${id}/handle`, data),
  resolve: (id) => api.put(`/shortage/handling/reports/${id}/resolve`),
  reject: (id, reason) => api.put(`/shortage/handling/reports/${id}/reject`, { reason }),
};
