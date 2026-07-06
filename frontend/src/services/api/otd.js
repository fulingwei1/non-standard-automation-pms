import api from "./client.js";

// ============================================================
// OTD 项目交付智能体 API
// ============================================================

export const otdApi = {
  // 扫描
  scan: (params = {}) => api.get("/otd/scan", { params }),
  scanProject: (id, params = {}) => api.get(`/otd/scan/${id}`, { params }),
  scanRun: () => api.post("/otd/scan/run"),
  scanTrend: (days = 30) => api.get("/otd/scan/trend", { params: { days } }),
  scanProjectTrend: (id, days = 30) => api.get(`/otd/scan/${id}/trend`, { params: { days } }),

  // 指标
  metrics: (params = {}) => api.get("/otd/metrics", { params }),
  projectMetrics: (id) => api.get(`/otd/metrics/${id}`),

  // 阈值
  getThresholds: () => api.get("/otd/thresholds"),
  updateThresholds: (data) => api.put("/otd/thresholds", data),

  // 对比
  compareProjects: (ids) => api.get("/otd/compare", { params: { ids: ids.join(",") } }),
  compareTrend: (days = 30) => api.get("/otd/compare/trend", { params: { days } }),

  // 导出（返回 blob）
  exportScan: (detailLevel = "summary") =>
    api.get("/otd/scan/export", {
      params: { detail_level: detailLevel },
      responseType: "blob",
    }),
  exportProject: (id, includeAi = true) =>
    api.get(`/otd/scan/${id}/export`, {
      params: { include_ai: includeAi },
      responseType: "blob",
    }),
  exportMetrics: (params = {}) =>
    api.get("/otd/metrics/export", { params, responseType: "blob" }),

  // 毛利率 Dashboard
  marginDashboard: (targetMargin = 25) =>
    api.get("/pmo/margin-dashboard", { params: { target_margin: targetMargin } }),
  marginLevels: () => api.get("/pmo/margin-dashboard/levels"),
  marginTrend: (days = 30) =>
    api.get("/pmo/margin-dashboard/trend", { params: { days } }),
  marginProjectTrend: (id, days = 30) =>
    api.get(`/pmo/margin-dashboard/${id}/trend`, { params: { days } }),
  marginSnapshotRun: () => api.post("/pmo/margin-dashboard/snapshot/run"),
  exportMarginDashboard: () =>
    api.get("/pmo/margin-dashboard/export", { responseType: "blob" }),

  // PM 月检
  pmMonthlyCheck: (pmId = null) =>
    api.get("/pmo/pm-monthly-check", { params: pmId ? { pm_id: pmId } : {} }),

  // BOM 成本检查
  bomCostCheck: (projectId) =>
    api.get(`/projects/${projectId}/bom-cost-check`),
};

export default otdApi;
