import api from "./client.js";
const BASE = "/warehouse";
export const warehouseApi = {
  stats: () => api.get(`${BASE}/stats`),
  warehouses: () => api.get(`${BASE}/warehouses`),
  inbound: {
    list: (params) => api.get(`${BASE}/inbound`, { params }),
    get: (id) => api.get(`${BASE}/inbound/${id}`),
    create: (data) => api.post(`${BASE}/inbound`, data),
    updateStatus: (id, status) => api.put(`${BASE}/inbound/${id}/status`, null, { params: { status } }),
  },
  outbound: {
    list: (params) => api.get(`${BASE}/outbound`, { params }),
    get: (id) => api.get(`${BASE}/outbound/${id}`),
    create: (data) => api.post(`${BASE}/outbound`, data),
    updateStatus: (id, status) => api.put(`${BASE}/outbound/${id}/status`, null, { params: { status } }),
  },
  inventory: { list: (params) => api.get(`${BASE}/inventory`, { params }) },
  locations: {
    list: (params) => api.get(`${BASE}/locations`, { params }),
    create: (data) => api.post(`${BASE}/locations`, data),
    update: (id, data) => api.put(`${BASE}/locations/${id}`, data),
    delete: (id) => api.delete(`${BASE}/locations/${id}`),
  },
  alerts: {
    summary: () => api.get(`${BASE}/alerts/summary`),
    list: (params) => api.get(`${BASE}/alerts`, { params }),
  },
  stockCount: {
    list: (params) => api.get(`${BASE}/stock-count`, { params }),
    get: (id) => api.get(`${BASE}/stock-count/${id}`),
    create: (data) => api.post(`${BASE}/stock-count`, data),
    updateItem: (orderId, itemId, data) => api.put(`${BASE}/stock-count/${orderId}/items/${itemId}`, data),
    updateStatus: (id, status) => api.put(`${BASE}/stock-count/${id}/status`, null, { params: { status } }),
  },
};
