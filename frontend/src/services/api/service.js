import { api } from "./client.js";



export const serviceApi = {
  tickets: {
    list: (params) => api.get("/service-tickets", { params }),
    get: (id) => api.get(`/service-tickets/${id}`),
    create: (data) => api.post("/service-tickets", data),
    update: (id, data) => api.put(`/service-tickets/${id}`, data),
    assign: (id, data) => api.put(`/service-tickets/${id}/assign`, data),
    batchAssign: (data) => api.post("/service-tickets/batch-assign", data),
    close: (id, data) => api.put(`/service-tickets/${id}/close`, data),
    getStatistics: () => api.get("/service-tickets/statistics"),
    getProjectMembers: (params) => api.get("/service-tickets/project-members", { params }),
    getRelatedProjects: (id) => api.get(`/service-tickets/${id}/projects`),
  },
  records: {
    list: (params) => api.get("/service-records", { params }),
    get: (id) => api.get(`/service-records/${id}`),
    create: (data) => api.post("/service-records", data),
    update: (id, data) => api.put(`/service-records/${id}`, data),
    uploadPhoto: (recordId, file, description) => {
      const formData = new FormData();
      formData.append("file", file);
      if (description) formData.append("description", description);
      return api.post(`/service-records/${recordId}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    deletePhoto: (recordId, photoIndex) =>
      api.delete(`/service-records/${recordId}/photos/${photoIndex}`),
    getStatistics: () => api.get("/service-records/statistics"),
  },
  communications: {
    list: (params) => api.get("/customer-communications", { params }),
    get: (id) => api.get(`/customer-communications/${id}`),
    create: (data) => api.post("/customer-communications", data),
    update: (id, data) => api.put(`/customer-communications/${id}`, data),
  },
  satisfaction: {
    list: (params) => api.get("/customer-satisfactions", { params }),
    get: (id) => api.get(`/customer-satisfactions/${id}`),
    create: (data) => api.post("/customer-satisfactions", data),
    update: (id, data) => api.put(`/customer-satisfactions/${id}`, data),
    send: (id, data) => api.post(`/customer-satisfactions/${id}/send`, data),
    submit: (id, data) =>
      api.post(`/customer-satisfactions/${id}/submit`, data),
    statistics: () => api.get("/customer-satisfactions/statistics"),
    templates: {
      list: (params) => api.get("/satisfaction-templates", { params }),
      get: (id) => api.get(`/satisfaction-templates/${id}`),
    },
  },
  dashboardStatistics: () => api.get("/service/dashboard-statistics"),
  knowledgeBase: {
    list: (params) => api.get("/knowledge-base", { params }),
    get: (id) => api.get(`/knowledge-base/${id}`),
    create: (data) => api.post("/knowledge-base", data),
    update: (id, data) => api.put(`/knowledge-base/${id}`, data),
    delete: (id) => api.delete(`/knowledge-base/${id}`),
    publish: (id) => api.put(`/knowledge-base/${id}/publish`),
    archive: (id) => api.put(`/knowledge-base/${id}/archive`),
    statistics: () => api.get("/knowledge-base/statistics"),
    // 文件上传（最大 200MB）
    upload: (formData) => api.post("/knowledge-base/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
    // 文件下载
    downloadUrl: (id) => `${api.defaults.baseURL}/knowledge-base/${id}/download`,
    // 获取上传配额使用情况
    getQuota: () => api.get("/knowledge-base/quota"),
    // 点赞
    like: (id) => api.post(`/knowledge-base/${id}/like`),
    // 标记采用（表示文档被实际应用到工作中）
    adopt: (id) => api.post(`/knowledge-base/${id}/adopt`),
  },
};

export const installationDispatchApi = {
  orders: {
    list: (params) => api.get("/installation-dispatch/orders", { params }),
    get: (id) => api.get(`/installation-dispatch/orders/${id}`),
    create: (data) => api.post("/installation-dispatch/orders", data),
    update: (id, data) => api.put(`/installation-dispatch/orders/${id}`, data),
    assign: (id, data) =>
      api.put(`/installation-dispatch/orders/${id}/assign`, data),
    batchAssign: (data) =>
      api.post("/installation-dispatch/orders/batch-assign", data),
    start: (id, data) =>
      api.put(`/installation-dispatch/orders/${id}/start`, data),
    progress: (id, data) =>
      api.put(`/installation-dispatch/orders/${id}/progress`, data),
    complete: (id, data) =>
      api.put(`/installation-dispatch/orders/${id}/complete`, data),
    cancel: (id) => api.put(`/installation-dispatch/orders/${id}/cancel`),
  },
  statistics: () => api.get("/installation-dispatch/statistics"),
};

export const itrApi = {
  // ITR流程效率分析
  getEfficiencyAnalysis: (params) =>
    api.get("/itr/analytics/efficiency", { params }),

  // ITR满意度趋势分析
  getSatisfactionTrend: (params) =>
    api.get("/itr/analytics/satisfaction", { params }),

  // ITR流程瓶颈分析
  getBottlenecksAnalysis: (params) =>
    api.get("/itr/analytics/bottlenecks", { params }),

  // ITR SLA性能分析
  getSlaAnalysis: (params) =>
    api.get("/itr/analytics/sla", { params }),

  // ITR流程看板
  getDashboard: (params) =>
    api.get("/itr/dashboard", { params }),

  // 工单时间线
  getTicketTimeline: (ticketId) =>
    api.get(`/itr/tickets/${ticketId}/timeline`),

  // 问题关联数据
  getIssueRelated: (issueId) =>
    api.get(`/itr/issues/${issueId}/related`),
};
