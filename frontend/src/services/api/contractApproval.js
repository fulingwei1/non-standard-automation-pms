import { api } from "./client.js";

export const contractApprovalApi = {
  list: (params) => api.get("/sales/contracts/approvals", { params }),
  approve: (id, data) => api.post(`/sales/contracts/approvals/${id}/approve`, data),
  reject: (id, data) => api.post(`/sales/contracts/approvals/${id}/reject`, data),
};
