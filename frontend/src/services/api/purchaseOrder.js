import { api } from "./client.js";

export const purchaseOrderApi = {
  list: (params) => api.get("/purchase-orders", { params }),
  get: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post("/purchase-orders", data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),
  submit: (id) => api.put(`/purchase-orders/${id}/submit`),
  cancel: (id) => api.put(`/purchase-orders/${id}/cancel`),
  addItem: (id, data) => api.post(`/purchase-orders/${id}/items`, data),
  getPending: (params) => api.get("/purchase-orders/pending", { params }),
};
