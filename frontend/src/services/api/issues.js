import { api } from "./client.js";



export const issueApi = {
  list: (params) => api.get("/issues/", { params }),
  getIssues: (params) => api.get("/issues/", { params }),
  get: (id) => api.get(`/issues/${id}`),
  create: (data) => api.post("/issues", data),
  update: (id, data) => api.put(`/issues/${id}`, data),
  delete: (id) => api.delete(`/issues/${id}`),
  assign: (id, data) => api.post(`/issues/${id}/assign`, data),
  resolve: (id, data) => api.post(`/issues/${id}/resolve`, data),
  verify: (id, data) => api.post(`/issues/${id}/verify`, data),
  close: (id, data) => api.post(`/issues/${id}/close`, data),
  cancel: (id, data) => api.post(`/issues/${id}/cancel`, data),
  changeStatus: (id, data) => api.post(`/issues/${id}/status`, data),
  getStatistics: (params) => api.get("/issues/statistics/overview", { params }),
  getStats: (params) => api.get("/issues/statistics/overview", { params }),
  getTrend: (params) => api.get("/issues/statistics/trend", { params }),
  getEngineerStatistics: (params) =>
    api.get("/issues/statistics/engineer", { params }),
  getCauseAnalysis: (params) =>
    api.get("/issues/statistics/cause-analysis", { params }),
  getSnapshots: (params) => api.get("/issues/statistics/snapshots", { params }),
  getSnapshot: (id) => api.get(`/issues/statistics/snapshots/${id}`),
  getFollowUps: (id) => api.get(`/issues/${id}/follow-ups`),
  addFollowUp: (id, data) => api.post(`/issues/${id}/follow-ups`, data),
  getRelated: (id) => api.get(`/issues/${id}/related`),
  createRelated: (id, data) => api.post(`/issues/${id}/related`, data),
  batchAssign: (data) => api.post("/issues/batch-assign", data),
  batchStatus: (data) => api.post("/issues/batch-status", data),
  batchClose: (data) => api.post("/issues/batch-close", data),
  export: (params) =>
    api.get("/issues/export", { params, responseType: "blob" }),
  import: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/issues/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getBoard: (params) => api.get("/issues/board", { params }),
};

export const issueTemplateApi = {
  list: (params) => api.get("/issue-templates", { params }),
  get: (id) => api.get(`/issue-templates/${id}`),
  create: (data) => api.post("/issue-templates", data),
  update: (id, data) => api.put(`/issue-templates/${id}`, data),
  delete: (id) => api.delete(`/issue-templates/${id}`),
  createIssue: (templateId, data) =>
    api.post(`/issue-templates/${templateId}/create-issue`, data),
};
