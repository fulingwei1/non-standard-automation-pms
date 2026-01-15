import { api } from "./client.js";



export const acceptanceApi = {
  // Templates
  templates: {
    list: (params) => api.get("/acceptance-templates", { params }),
    get: (id) => api.get(`/acceptance-templates/${id}`),
    create: (data) => api.post("/acceptance-templates", data),
    getItems: (id) => api.get(`/acceptance-templates/${id}/items`),
    addItems: (id, data) => api.post(`/acceptance-templates/${id}/items`, data),
  },

  // Orders
  orders: {
    list: (params) => api.get("/acceptance-orders", { params }),
    get: (id) => api.get(`/acceptance-orders/${id}`),
    create: (data) => api.post("/acceptance-orders", data),
    start: (id, data) => api.put(`/acceptance-orders/${id}/start`, data),
    complete: (id, data) => api.put(`/acceptance-orders/${id}/complete`, data),
    getItems: (id) => api.get(`/acceptance-orders/${id}/items`),
    updateItem: (itemId, data) => api.put(`/acceptance-items/${itemId}`, data),
  },

  // Issues
  issues: {
    list: (orderId) => api.get(`/acceptance-orders/${orderId}/issues`),
    create: (orderId, data) =>
      api.post(`/acceptance-orders/${orderId}/issues`, data),
    update: (issueId, data) => api.put(`/acceptance-issues/${issueId}`, data),
    close: (issueId, data) =>
      api.put(`/acceptance-issues/${issueId}/close`, data),
    addFollowUp: (issueId, data) =>
      api.post(`/acceptance-issues/${issueId}/follow-ups`, data),
  },

  // Signatures
  signatures: {
    list: (orderId) => api.get(`/acceptance-orders/${orderId}/signatures`),
    create: (orderId, data) =>
      api.post(`/acceptance-orders/${orderId}/signatures`, data),
  },

  // Reports
  reports: {
    generate: (orderId, data) =>
      api.post(`/acceptance-orders/${orderId}/report`, data),
    download: (reportId) =>
      api.get(`/acceptance-reports/${reportId}/download`, {
        responseType: "blob",
      }),
  },
};
