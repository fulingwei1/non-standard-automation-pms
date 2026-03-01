import { api } from "./client.js";

export const purchaseRequestApi = {
  getMaterials: (projectId) =>
    api.get("/purchase-orders/requests/materials", { params: { project_id: projectId } }),
  create: (data) => api.post("/purchase-orders/requests", data),
  get: (id) => api.get(`/purchase-orders/requests/${id}`),
  update: (id, data) => api.put(`/purchase-orders/requests/${id}`, data),
  submit: (id) => api.put(`/purchase-orders/requests/${id}/submit`),
};
