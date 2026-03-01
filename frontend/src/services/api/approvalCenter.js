import { api } from "./client.js";

export const approvalApi = {
  list: (params) => api.get("/approvals/pending/mine", { params }),
  approve: (taskId, data) => api.post(`/approvals/tasks/${taskId}/approve`, data),
  reject: (taskId, data) => api.post(`/approvals/tasks/${taskId}/reject`, data),
  getCounts: () => api.get("/approvals/pending/counts"),
};
