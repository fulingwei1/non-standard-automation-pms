import { api } from "./client.js";

export const adminApprovalApi = {
  list: (params) => api.get("/admin/approvals", { params }),
  approve: (id, data) => api.post(`/admin/approvals/${id}/approve`, data),
  reject: (id, data) => api.post(`/admin/approvals/${id}/reject`, data),
};
