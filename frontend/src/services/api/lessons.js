import { api } from "./client.js";

export const lessonsApi = {
  list: (params) => api.get("/lessons/list", { params }),
  detail: (id) => api.get(`/lessons/${id}`),
  create: (data) => api.post("/lessons/", data),
  update: (id, data) => api.put(`/lessons/${id}`, data),
  stats: () => api.get("/lessons/stats"),
  search: (q) => api.get("/lessons/search", { params: { q } }),
};
