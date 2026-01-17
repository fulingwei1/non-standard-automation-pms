import { api } from "./client.js";



export const customerApi = {
  list: (params) => api.get("/customers/", { params }),
  // Alias for backward compatibility
  getCustomers: (params) => api.get("/customers/", { params }),
  get: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post("/customers/", data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
  getProjects: (id, params) => api.get(`/customers/${id}/projects`, { params }),
  get360: (id) => api.get(`/customers/${id}/360`),
};

export const supplierApi = {
  list: (params = {}) =>
    api.get("/suppliers/", { params: { page: 1, ...params } }),
  get: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post("/suppliers/", data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  updateRating: (id, params) =>
    api.put(`/suppliers/${id}/rating`, null, { params }),
  getMaterials: (id, params) =>
    api.get(`/suppliers/${id}/materials`, { params }),
};
