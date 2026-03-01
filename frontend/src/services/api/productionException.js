import { api } from "./client.js";

export const productionExceptionApi = {
  list: (params) => api.get("/production-exceptions", { params }),
  create: (data) => api.post("/production-exceptions", data),
  resolve: (id, data) => api.put(`/production-exceptions/${id}/resolve`, data),
};
