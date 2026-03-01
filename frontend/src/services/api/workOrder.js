import { api } from "./client.js";

export const workOrderApi = {
  list: (params) => api.get("/production/work-orders", { params }),
  create: (data) => api.post("/production/work-orders", data),
  updateStatus: (id, data) => api.put(`/production/work-orders/${id}/status`, data),
};
