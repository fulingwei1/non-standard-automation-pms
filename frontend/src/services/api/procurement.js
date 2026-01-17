import { api } from "./client.js";



export const purchaseApi = {
  // 顶层便捷方法
  list: (params) => api.get("/purchase-orders/", { params }),
  get: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post("/purchase-orders", data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),

  orders: {
    list: (params) => api.get("/purchase-orders/", { params }),
    get: (id) => api.get(`/purchase-orders/${id}`),
    create: (data) => api.post("/purchase-orders", data),
    update: (id, data) => api.put(`/purchase-orders/${id}`, data),
    submit: (id) => api.put(`/purchase-orders/${id}/submit`),
    approve: (id, data) => api.put(`/purchase-orders/${id}/approve`, data),
    getItems: (id) => api.get(`/purchase-orders/${id}/items`),
    createFromBOM: (params) =>
      api.post("/purchase-orders/from-bom", null, { params }),
  },

  requests: {
    list: (params) => api.get("/purchase-orders/requests", { params }),
    get: (id) => api.get(`/purchase-orders/requests/${id}`),
    create: (data) => api.post("/purchase-orders/requests", data),
    update: (id, data) => api.put(`/purchase-orders/requests/${id}`, data),
    submit: (id) => api.put(`/purchase-orders/requests/${id}/submit`),
    approve: (id, data) =>
      api.put(`/purchase-orders/requests/${id}/approve`, { params: data }),
    generateOrders: (id, params) =>
      api.post(`/purchase-orders/requests/${id}/generate-orders`, null, {
        params,
      }),
    delete: (id) => api.delete(`/purchase-orders/requests/${id}`),
  },

  receipts: {
    list: (params) => api.get("/goods-receipts", { params }),
    get: (id) => api.get(`/goods-receipts/${id}`),
    create: (data) => api.post("/goods-receipts", data),
    getItems: (id) => api.get(`/goods-receipts/${id}/items`),
    receive: (id, data) =>
      api.put(`/goods-receipts/${id}/receive`, null, { params: data }),
    updateStatus: (id, status) =>
      api.put(`/goods-receipts/${id}/receive`, null, { params: { status } }),
    inspectItem: (receiptId, itemId, data) =>
      api.put(`/goods-receipts/${receiptId}/items/${itemId}/inspect`, null, {
        params: data,
      }),
  },

  items: {
    receive: (itemId, data) =>
      api.put(`/purchase-order-items/${itemId}/receive`, data),
  },

  // Kit Rate
  kitRate: {
    getProject: (projectId, params) =>
      api.get(`/projects/${projectId}/kit-rate`, { params }),
    getMachine: (machineId, params) =>
      api.get(`/machines/${machineId}/kit-rate`, { params }),
    getMachineStatus: (machineId) =>
      api.get(`/machines/${machineId}/material-status`),
    getProjectMaterialStatus: (projectId) =>
      api.get(`/projects/${projectId}/material-status`),
    dashboard: (params) => api.get("/kit-rate/dashboard", { params }),
    trend: (params) => api.get("/kit-rate/trend", { params }),
  },
};

export const procurementApi = purchaseApi;

export const outsourcingApi = {
  vendors: {
    list: (params) => api.get("/outsourcing-vendors", { params }),
    get: (id) => api.get(`/outsourcing-vendors/${id}`),
    create: (data) => api.post("/outsourcing-vendors", data),
    update: (id, data) => api.put(`/outsourcing-vendors/${id}`, data),
    evaluate: (id, data) =>
      api.post(`/outsourcing-vendors/${id}/evaluations`, data),
  },
  orders: {
    list: (params) => api.get("/outsourcing-orders", { params }),
    get: (id) => api.get(`/outsourcing-orders/${id}`),
    create: (data) => api.post("/outsourcing-orders", data),
    update: (id, data) => api.put(`/outsourcing-orders/${id}`, data),
    submit: (id) => api.put(`/outsourcing-orders/${id}/submit`),
    approve: (id, data) => api.put(`/outsourcing-orders/${id}/approve`, data),
    getItems: (id) => api.get(`/outsourcing-orders/${id}/items`),
    addItem: (id, data) => api.post(`/outsourcing-orders/${id}/items`, data),
    updateItem: (itemId, data) =>
      api.put(`/outsourcing-order-items/${itemId}`, data),
    getDeliveries: (id) =>
      api.get("/outsourcing-deliveries", {
        params: { order_id: id, page_size: 1000 },
      }),
    getInspections: (id) =>
      api.get("/outsourcing-inspections", {
        params: { order_id: id, page_size: 1000 },
      }),
    getProgress: (id) => api.get(`/outsourcing-orders/${id}/progress-logs`),
  },
  deliveries: {
    list: (orderId) => api.get(`/outsourcing-orders/${orderId}/deliveries`),
    create: (orderId, data) =>
      api.post(`/outsourcing-orders/${orderId}/deliveries`, data),
    get: (id) => api.get(`/outsourcing-deliveries/${id}`),
  },
  inspections: {
    list: (orderId) => api.get(`/outsourcing-orders/${orderId}/inspections`),
    create: (orderId, data) =>
      api.post(`/outsourcing-orders/${orderId}/inspections`, data),
    get: (id) => api.get(`/outsourcing-inspections/${id}`),
  },
  progress: {
    list: (orderId) => api.get(`/outsourcing-orders/${orderId}/progress`),
    create: (orderId, data) =>
      api.post(`/outsourcing-orders/${orderId}/progress`, data),
  },
  payments: {
    list: (orderId) => api.get(`/outsourcing-orders/${orderId}/payments`),
    create: (orderId, data) =>
      api.post(`/outsourcing-orders/${orderId}/payments`, data),
    update: (id, data) => api.put(`/outsourcing-payments/${id}`, data),
  },
};
