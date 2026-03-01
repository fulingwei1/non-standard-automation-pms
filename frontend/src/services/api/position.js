import { api } from "./client.js";

export const positionApi = {
  list: (params) => api.get("/positions", { params }),
  create: (data) => api.post("/positions", data),
  update: (id, data) => api.put(`/positions/${id}`, data),
  delete: (id) => api.delete(`/positions/${id}`),
};
