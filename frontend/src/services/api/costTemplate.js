import { api } from "./client.js";

export const costTemplateApi = {
  list: (params) => api.get("/sales/cost-templates", { params }),
  create: (data) => api.post("/sales/cost-templates", data),
  update: (id, data) => api.put(`/sales/cost-templates/${id}`, data),
  duplicate: (id) => api.post(`/sales/cost-templates/${id}/duplicate`),
};
