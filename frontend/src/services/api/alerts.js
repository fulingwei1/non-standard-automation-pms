import { api } from "./client.js";



export const alertApi = {
  // Alert Records
  list: (params) => api.get("/alerts", { params }),
  get: (id) => api.get(`/alerts/${id}`),
  acknowledge: (id) => api.put(`/alerts/${id}/acknowledge`),
  resolve: (id, data) => api.put(`/alerts/${id}/resolve`, data),
  close: (id, data) => api.put(`/alerts/${id}/close`, data),
  ignore: (id, data) => api.put(`/alerts/${id}/ignore`, data),

  // Alert Rules
  rules: {
    list: (params) => api.get("/alert-rules", { params }),
    get: (id) => api.get(`/alert-rules/${id}`),
    create: (data) => api.post("/alert-rules", data),
    update: (id, data) => api.put(`/alert-rules/${id}`, data),
    delete: (id) => api.delete(`/alert-rules/${id}`),
    toggle: (id) => api.put(`/alert-rules/${id}/toggle`),
  },

  // Alert Rule Templates
  templates: (params) => api.get("/alert-rule-templates", { params }),

  // Alert Statistics
  statistics: (params) => api.get("/alerts/statistics", { params }),
  dashboard: () => api.get("/alerts/statistics/dashboard"),
  trends: (params) => api.get("/alerts/statistics/trends", { params }),
  responseMetrics: (params) =>
    api.get("/alerts/statistics/response-metrics", { params }),
  efficiencyMetrics: (params) =>
    api.get("/alerts/statistics/efficiency-metrics", { params }),
  exportExcel: (params) =>
    api.get("/alerts/export/excel", { params, responseType: "blob" }),
  exportPdf: (params) =>
    api.get("/alerts/export/pdf", { params, responseType: "blob" }),

  // Alert Subscriptions
  subscriptions: {
    list: (params) => api.get("/alerts/subscriptions", { params }),
    get: (id) => api.get(`/alerts/subscriptions/${id}`),
    create: (data) => api.post("/alerts/subscriptions", data),
    update: (id, data) => api.put(`/alerts/subscriptions/${id}`, data),
    delete: (id) => api.delete(`/alerts/subscriptions/${id}`),
    toggle: (id) => api.put(`/alerts/subscriptions/${id}/toggle`),
  },
};

export const notificationApi = {
  list: (params) => api.get("/notifications/", { params }), // 添加末尾斜杠避免重定向丢失 Authorization header
  get: (id) => api.get(`/notifications/${id}`),
  getUnreadCount: () => api.get("/notifications/unread-count"),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  batchRead: (data) => api.put("/notifications/batch-read", data),
  readAll: () => api.put("/notifications/read-all"),
  delete: (id) => api.delete(`/notifications/${id}`),
  getSettings: () => api.get("/notifications/settings"),
  updateSettings: (data) => api.put("/notifications/settings", data),
};
