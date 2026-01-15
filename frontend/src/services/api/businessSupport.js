import { api } from "./client.js";



export const businessSupportApi = {
  dashboard: () => api.get("/business-support/dashboard"),
  getActiveContracts: (params) =>
    api.get("/business-support/dashboard/active-contracts", { params }),
  getActiveBidding: (params) =>
    api.get("/business-support/dashboard/active-bidding", { params }),
  getTodos: (params) =>
    api.get("/business-support/dashboard/todos", { params }),
  bidding: {
    list: (params) => api.get("/business-support/bidding", { params }),
    get: (id) => api.get(`/business-support/bidding/${id}`),
    create: (data) => api.post("/business-support/bidding", data),
    update: (id, data) => api.put(`/business-support/bidding/${id}`, data),
  },
  contractReview: {
    list: (params) => api.get("/business-support/contract-review", { params }),
    get: (id) => api.get(`/business-support/contract-review/${id}`),
    create: (data) => api.post("/business-support/contract-review", data),
    update: (id, data) =>
      api.put(`/business-support/contract-review/${id}`, data),
  },
  paymentReminder: {
    list: (params) => api.get("/business-support/payment-reminder", { params }),
    get: (id) => api.get(`/business-support/payment-reminder/${id}`),
    create: (data) => api.post("/business-support/payment-reminder", data),
    update: (id, data) =>
      api.put(`/business-support/payment-reminder/${id}`, data),
  },
  deliveryOrders: {
    list: (params) => api.get("/business-support/delivery-orders", { params }),
    get: (id) => api.get(`/business-support/delivery-orders/${id}`),
    create: (data) => api.post("/business-support/delivery-orders", data),
    update: (id, data) =>
      api.put(`/business-support/delivery-orders/${id}`, data),
    statistics: () => api.get("/business-support/delivery-orders/statistics"),
  },
  salesOrders: {
    list: (params) => api.get("/business-support/sales-orders", { params }),
    get: (id) => api.get(`/business-support/sales-orders/${id}`),
  },
};

export const exceptionApi = {
  list: (params) => api.get("/exceptions", { params }),
  get: (id) => api.get(`/exceptions/${id}`),
  create: (data) => api.post("/exceptions", data),
  update: (id, data) => api.put(`/exceptions/${id}`, data),
  delete: (id) => api.delete(`/exceptions/${id}`),
  getStatistics: (params) => api.get("/exceptions/statistics", { params }),
};
