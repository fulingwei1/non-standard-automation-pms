/**
 * 战略管理 API 服务
 */
import { api } from "./client.js";

// ============================================
// 战略管理
// ============================================
export const strategyApi = {
  // 战略 CRUD
  list: (params) => api.get("/strategy/strategies", { params }),
  get: (id) => api.get(`/strategy/strategies/${id}`),
  getActive: () => api.get("/strategy/strategies/active"),
  create: (data) => api.post("/strategy/strategies", data),
  update: (id, data) => api.put(`/strategy/strategies/${id}`, data),
  delete: (id) => api.delete(`/strategy/strategies/${id}`),
  publish: (id) => api.post(`/strategy/strategies/${id}/publish`, {}),
  archive: (id) => api.post(`/strategy/strategies/${id}/archive`),

  // 战略地图
  getMap: (id) => api.get(`/strategy/strategies/${id}/map`),
};

// ============================================
// CSF 管理
// ============================================
export const csfApi = {
  list: (params) => api.get("/strategy/csfs", { params }),
  get: (id) => api.get(`/strategy/csfs/${id}`),
  getByDimension: (strategyId) =>
    api.get("/strategy/csfs/by-dimension", { params: { strategy_id: strategyId } }),
  create: (data) => api.post("/strategy/csfs", data),
  batchCreate: (data) => api.post("/strategy/csfs/batch", data),
  update: (id, data) => api.put(`/strategy/csfs/${id}`, data),
  delete: (id) => api.delete(`/strategy/csfs/${id}`),
};

// ============================================
// KPI 管理
// ============================================
export const kpiApi = {
  list: (params) => api.get("/strategy/kpis", { params }),
  get: (id) => api.get(`/strategy/kpis/${id}`),
  getHistory: (id, limit = 12) =>
    api.get(`/strategy/kpis/${id}/history`, { params: { limit } }),
  getWithHistory: (id) => api.get(`/strategy/kpis/${id}/with-history`),
  create: (data) => api.post("/strategy/kpis", data),
  update: (id, data) => api.put(`/strategy/kpis/${id}`, data),
  updateValue: (id, data) => api.post(`/strategy/kpis/${id}/value`, data),
  delete: (id) => api.delete(`/strategy/kpis/${id}`),

  // 数据采集
  collect: (id) => api.post(`/strategy/kpis/${id}/collect`),
  batchCollect: (data) => api.post("/strategy/kpis/batch-collect", data),
  getCollectionStatus: (strategyId) =>
    api.get(`/strategy/kpis/collection-status/${strategyId}`),

  // 数据源
  getDataSources: (kpiId) => api.get(`/strategy/kpis/${kpiId}/data-sources`),
  createDataSource: (kpiId, data) =>
    api.post(`/strategy/kpis/${kpiId}/data-sources`, data),
};

// ============================================
// 年度重点工作
// ============================================
export const annualWorkApi = {
  list: (params) => api.get("/strategy/annual-works", { params }),
  get: (id) => api.get(`/strategy/annual-works/${id}`),
  getStats: (strategyId, year) =>
    api.get(`/strategy/annual-works/stats/${strategyId}`, { params: { year } }),
  create: (data) => api.post("/strategy/annual-works", data),
  update: (id, data) => api.put(`/strategy/annual-works/${id}`, data),
  updateProgress: (id, data) =>
    api.post(`/strategy/annual-works/${id}/progress`, data),
  delete: (id) => api.delete(`/strategy/annual-works/${id}`),

  // 项目关联
  linkProject: (workId, data) =>
    api.post(`/strategy/annual-works/${workId}/link-project`, data),
  unlinkProject: (workId, data) =>
    api.post(`/strategy/annual-works/${workId}/unlink-project`, data),
  getLinkedProjects: (workId) =>
    api.get(`/strategy/annual-works/${workId}/linked-projects`),
  syncProgress: (workId) =>
    api.post(`/strategy/annual-works/${workId}/sync-progress`),
};

// ============================================
// 目标分解
// ============================================
export const decompositionApi = {
  // 部门目标
  listDeptObjectives: (params) =>
    api.get("/strategy/decomposition/department-objectives", { params }),
  getDeptObjective: (id) =>
    api.get(`/strategy/decomposition/department-objectives/${id}`),
  createDeptObjective: (data) =>
    api.post("/strategy/decomposition/department-objectives", data),
  updateDeptObjective: (id, data) =>
    api.put(`/strategy/decomposition/department-objectives/${id}`, data),
  deleteDeptObjective: (id) =>
    api.delete(`/strategy/decomposition/department-objectives/${id}`),

  // 个人 KPI
  listPersonalKpis: (params) =>
    api.get("/strategy/decomposition/personal-kpis", { params }),
  getMyPersonalKpis: (params) =>
    api.get("/strategy/decomposition/personal-kpis/my", { params }),
  getPersonalKpi: (id) =>
    api.get(`/strategy/decomposition/personal-kpis/${id}`),
  createPersonalKpi: (data) =>
    api.post("/strategy/decomposition/personal-kpis", data),
  batchCreatePersonalKpis: (data) =>
    api.post("/strategy/decomposition/personal-kpis/batch", data),
  updatePersonalKpi: (id, data) =>
    api.put(`/strategy/decomposition/personal-kpis/${id}`, data),
  selfRating: (id, data) =>
    api.post(`/strategy/decomposition/personal-kpis/${id}/self-rating`, data),
  managerRating: (id, data) =>
    api.post(`/strategy/decomposition/personal-kpis/${id}/manager-rating`, data),
  deletePersonalKpi: (id) =>
    api.delete(`/strategy/decomposition/personal-kpis/${id}`),

  // 分解追溯
  getTree: (strategyId) =>
    api.get(`/strategy/decomposition/tree/${strategyId}`),
  trace: (personalKpiId) =>
    api.get(`/strategy/decomposition/trace/${personalKpiId}`),
  getStats: (strategyId, year) =>
    api.get(`/strategy/decomposition/stats/${strategyId}`, { params: { year } }),
};

// ============================================
// 战略审视
// ============================================
export const reviewApi = {
  // 审视记录
  listReviews: (params) => api.get("/strategy/reviews", { params }),
  getReview: (id) => api.get(`/strategy/reviews/${id}`),
  getLatestReview: (strategyId) =>
    api.get(`/strategy/reviews/latest/${strategyId}`),
  createReview: (data) => api.post("/strategy/reviews", data),
  updateReview: (id, data) => api.put(`/strategy/reviews/${id}`, data),
  deleteReview: (id) => api.delete(`/strategy/reviews/${id}`),

  // 健康度
  getHealth: (strategyId) => api.get(`/strategy/health/${strategyId}`),

  // 日历
  listEvents: (params) => api.get("/strategy/calendar/events", { params }),
  getEvent: (id) => api.get(`/strategy/calendar/events/${id}`),
  getCalendarMonth: (strategyId, year, month) =>
    api.get(`/strategy/calendar/month/${strategyId}`, { params: { year, month } }),
  getCalendarYear: (strategyId, year) =>
    api.get(`/strategy/calendar/year/${strategyId}`, { params: { year } }),
  createEvent: (data) => api.post("/strategy/calendar/events", data),
  updateEvent: (id, data) => api.put(`/strategy/calendar/events/${id}`, data),
  deleteEvent: (id) => api.delete(`/strategy/calendar/events/${id}`),

  // 例行管理
  getRoutineCycle: (strategyId) =>
    api.get(`/strategy/routine/${strategyId}`),
  generateRoutineEvents: (strategyId, year) =>
    api.post(`/strategy/routine/${strategyId}/generate-events`, null, { params: { year } }),
};

// ============================================
// 同比分析
// ============================================
export const comparisonApi = {
  list: (params) => api.get("/strategy/comparisons", { params }),
  get: (id) => api.get(`/strategy/comparisons/${id}`),
  create: (data) => api.post("/strategy/comparisons", data),
  delete: (id) => api.delete(`/strategy/comparisons/${id}`),

  // 报告
  getYoYReport: (currentYear, previousYear) =>
    api.get("/strategy/comparisons/yoy-report", {
      params: { current_year: currentYear, previous_year: previousYear }
    }),
  getMultiYearTrend: (years = 3) =>
    api.get("/strategy/comparisons/multi-year-trend", { params: { years } }),
  getKpiAchievement: (currentYear, previousYear) =>
    api.get("/strategy/comparisons/kpi-achievement", {
      params: { current_year: currentYear, previous_year: previousYear }
    }),
};

// ============================================
// 仪表板
// ============================================
export const dashboardApi = {
  getOverview: (strategyId) =>
    api.get(`/strategy/dashboard/overview/${strategyId}`),
  getMyStrategy: () => api.get("/strategy/dashboard/my-strategy"),
  getExecutionStatus: (strategyId) =>
    api.get(`/strategy/dashboard/execution-status/${strategyId}`),
  getQuickStats: () => api.get("/strategy/dashboard/quick-stats"),
};
