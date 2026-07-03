import { api } from "./client.js";



export const purchaseApi = {
  // 顶层便捷方法
  list: (params) => api.get("/purchase-orders/", { params }),
  get: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post("/purchase-orders/", data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),
  delete: (id) => api.delete(`/purchase-orders/${id}`),
  submitApproval: (id) => api.put(`/purchase-orders/${id}/submit`),
  approve: (id, data) => api.put(`/purchase-orders/${id}/approve`, null, { params: data }),
  receiveGoods: async (orderId, data = {}) => {
    const itemsResponse = await api.get(`/purchase-orders/${orderId}/items`);
    const items = itemsResponse.data?.data || itemsResponse.data?.items || itemsResponse.data || [];
    const receivableItems = (items || [])
      .map((item) => {
        const quantity = Number(item.quantity || 0);
        const receivedQty = Number(item.received_qty || 0);
        const remainingQty = Math.max(quantity - receivedQty, 0);
        return {
          order_item_id: item.id,
          delivery_qty: remainingQty,
          received_qty: remainingQty,
        };
      })
      .filter((item) => item.delivery_qty > 0);
    return api.post("/purchase-orders/goods-receipts/", {
      order_id: orderId,
      receipt_date: data.received_date || new Date().toISOString().slice(0, 10),
      receipt_type: "NORMAL",
      remark: data.notes || null,
      items: receivableItems,
    });
  },

  orders: {
    list: (params) => api.get("/purchase-orders/", { params }),
    get: (id) => api.get(`/purchase-orders/${id}`),
    create: (data) => api.post("/purchase-orders/", data),
    update: (id, data) => api.put(`/purchase-orders/${id}`, data),
    submit: (id) => api.put(`/purchase-orders/${id}/submit`),
    approve: (id, data) => api.put(`/purchase-orders/${id}/approve`, null, { params: data }),
    delete: (id) => api.delete(`/purchase-orders/${id}`),
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
      api.put(`/purchase-orders/requests/${id}/approve`, null, { params: data }),
    generateOrders: (id, params) =>
      api.post(`/purchase-orders/requests/${id}/generate-orders`, null, {
        params,
      }),
    delete: (id) => api.delete(`/purchase-orders/requests/${id}`),
  },

  receipts: {
    list: (params) => api.get("/purchase-orders/goods-receipts/", { params }),
    get: (id) => api.get(`/purchase-orders/goods-receipts/${id}`),
    create: (data) => api.post("/purchase-orders/goods-receipts/", data),
    getItems: (id) => api.get(`/purchase-orders/goods-receipts/${id}/items`),
    receive: (id, data) =>
      api.put(`/purchase-orders/goods-receipts/${id}/receive`, null, { params: data }),
    updateStatus: (id, status) =>
      api.put(`/purchase-orders/goods-receipts/${id}/receive`, null, { params: { status } }),
    inspectItem: (receiptId, itemId, data) =>
      api.put(`/purchase-orders/goods-receipts/${receiptId}/items/${itemId}/inspect`, null, {
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
    unified: (projectId, params) =>
      api.get(`/kit-rate/unified/${projectId}`, { params }),
    dashboard: (params) => api.get("/kit-rate/dashboard", { params }),
    trend: (params) => api.get("/kit-rate/trend", { params }),
  },
};

/** @deprecated Use purchaseApi instead */
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
    submit: (id) => api.post("/outsourcing-orders/workflow/submit", { order_id: id }),
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
    list: (orderId) => api.get("/outsourcing-deliveries", { params: { order_id: orderId, page_size: 1000 } }),
    create: (orderId, data) =>
      api.post("/outsourcing-deliveries", { ...data, order_id: orderId }),
    get: (id) => api.get(`/outsourcing-deliveries/${id}`),
  },
  inspections: {
    list: (orderId) => api.get("/outsourcing-inspections", { params: { order_id: orderId, page_size: 1000 } }),
    create: (orderId, data) =>
      api.post("/outsourcing-inspections", { ...data, order_id: orderId }),
    get: (id) => api.get(`/outsourcing-inspections/${id}`),
  },
  progress: {
    list: (orderId) => api.get(`/outsourcing-orders/${orderId}/progress`),
    create: (orderId, data) =>
      api.post(`/outsourcing-orders/${orderId}/progress`, data),
  },
  payments: {
    list: (orderId) => api.get("/outsourcing-payments", { params: { order_id: orderId, page_size: 1000 } }),
    create: (orderId, data) =>
      api.post("/outsourcing-payments", { ...data, order_id: orderId }),
    update: (id, data) => api.put(`/outsourcing-payments/${id}`, data),
  },
};

/**
 * 采购分析 API
 */
export const procurementAnalysisApi = {
  // 采购成本趋势
  getCostTrend: (params) => api.get("/procurement-analysis/cost-trend", { params }),

  // 物料价格波动监控
  getPriceFluctuation: (params) => api.get("/procurement-analysis/price-fluctuation", { params }),

  // 供应商交期准时率
  getDeliveryPerformance: (params) => api.get("/procurement-analysis/delivery-performance", { params }),

  // 采购申请处理时效
  getRequestEfficiency: (params) => api.get("/procurement-analysis/request-efficiency", { params }),

  // 物料质量合格率
  getQualityRate: (params) => api.get("/procurement-analysis/quality-rate", { params }),

  // 采购分析概览
  getOverview: () => api.get("/procurement-analysis/overview"),
};
