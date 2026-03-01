import { api } from "./client.js";

export const schedulerConfigApi = {
  list: (params) => api.get("/scheduler-config", { params }),
  update: (id, data) => api.put(`/scheduler-config/${id}`, data),
  toggle: (id, data) => api.post(`/scheduler-config/${id}/toggle`, data),
};
