import { api } from "./client.js";

export const paymentApprovalApi = {
  list: (params) => api.get("/sales/payments/approvals", { params }),
  approve: (id, data) => api.post(`/sales/payments/approvals/${id}/approve`, data),
  reject: (id, data) => api.post(`/sales/payments/approvals/${id}/reject`, data),
};
