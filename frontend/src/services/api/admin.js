import { api } from "./client.js";



export const schedulerApi = {
  status: () => api.get("/scheduler/status"),
  jobs: () => api.get("/scheduler/jobs"),
  metrics: () => api.get("/scheduler/metrics"),
  metricsPrometheus: () =>
    api.get("/scheduler/metrics/prometheus", { responseType: "text" }),
  triggerJob: (jobId) => api.post(`/scheduler/jobs/${jobId}/trigger`),
  listServices: () => api.get("/scheduler/services/list"),
  // 配置管理
  getConfigs: (params) => api.get("/scheduler/configs", { params }),
  getConfig: (taskId) => api.get(`/scheduler/configs/${taskId}`),
  updateConfig: (taskId, data) => api.put(`/scheduler/configs/${taskId}`, data),
  syncConfigs: (force = false) =>
    api.post("/scheduler/configs/sync", { force }),
};

export const adminApi = {
  // 行政审批
  approvals: {
    list: (params) => api.get("/admin/approvals", { params }),
    get: (id) => api.get(`/admin/approvals/${id}`),
    approve: (id, data) => api.put(`/admin/approvals/${id}/approve`, data),
    reject: (id, data) => api.put(`/admin/approvals/${id}/reject`, data),
    getStatistics: (params) =>
      api.get("/admin/approvals/statistics", { params }),
  },

  // 费用报销
  expenses: {
    list: (params) => api.get("/admin/expenses", { params }),
    get: (id) => api.get(`/admin/expenses/${id}`),
    create: (data) => api.post("/admin/expenses", data),
    update: (id, data) => api.put(`/admin/expenses/${id}`, data),
    submit: (id) => api.put(`/admin/expenses/${id}/submit`),
    approve: (id, data) => api.put(`/admin/expenses/${id}/approve`, data),
    reject: (id, data) => api.put(`/admin/expenses/${id}/reject`, data),
    getStatistics: (params) =>
      api.get("/admin/expenses/statistics", { params }),
  },

  // 请假管理
  leave: {
    list: (params) => api.get("/admin/leave", { params }),
    get: (id) => api.get(`/admin/leave/${id}`),
    create: (data) => api.post("/admin/leave", data),
    update: (id, data) => api.put(`/admin/leave/${id}`, data),
    approve: (id, data) => api.put(`/admin/leave/${id}/approve`, data),
    reject: (id, data) => api.put(`/admin/leave/${id}/reject`, data),
    cancel: (id) => api.put(`/admin/leave/${id}/cancel`),
    getStatistics: (params) => api.get("/admin/leave/statistics", { params }),
    getBalance: (userId) => api.get(`/admin/leave/balance/${userId}`),
  },

  // 考勤管理
  attendance: {
    list: (params) => api.get("/admin/attendance", { params }),
    get: (id) => api.get(`/admin/attendance/${id}`),
    clockIn: (data) => api.post("/admin/attendance/clock-in", data),
    clockOut: (data) => api.post("/admin/attendance/clock-out", data),
    getMyRecords: (params) =>
      api.get("/admin/attendance/my-records", { params }),
    getStatistics: (params) =>
      api.get("/admin/attendance/statistics", { params }),
    exportReport: (params) =>
      api.get("/admin/attendance/export", { params, responseType: "blob" }),
  },

  // 办公用品
  supplies: {
    list: (params) => api.get("/admin/supplies", { params }),
    get: (id) => api.get(`/admin/supplies/${id}`),
    request: (data) => api.post("/admin/supplies/request", data),
    approve: (id, data) => api.put(`/admin/supplies/${id}/approve`, data),
    reject: (id, data) => api.put(`/admin/supplies/${id}/reject`, data),
    getInventory: () => api.get("/admin/supplies/inventory"),
  },

  // 车辆管理
  vehicles: {
    list: (params) => api.get("/admin/vehicles", { params }),
    get: (id) => api.get(`/admin/vehicles/${id}`),
    request: (data) => api.post("/admin/vehicles/request", data),
    approve: (id, data) => api.put(`/admin/vehicles/${id}/approve`, data),
    reject: (id, data) => api.put(`/admin/vehicles/${id}/reject`, data),
    getAvailable: (date) =>
      api.get("/admin/vehicles/available", { params: { date } }),
  },

  // 会议室管理
  meetingRooms: {
    list: (params) => api.get("/admin/meeting-rooms", { params }),
    get: (id) => api.get(`/admin/meeting-rooms/${id}`),
    book: (data) => api.post("/admin/meeting-rooms/book", data),
    cancel: (id) => api.put(`/admin/meeting-rooms/${id}/cancel`),
    getAvailable: (date, time) =>
      api.get("/admin/meeting-rooms/available", { params: { date, time } }),
  },

  // 固定资产管理
  assets: {
    list: (params) => api.get("/admin/assets", { params }),
    get: (id) => api.get(`/admin/assets/${id}`),
    create: (data) => api.post("/admin/assets", data),
    update: (id, data) => api.put(`/admin/assets/${id}`, data),
    delete: (id) => api.delete(`/admin/assets/${id}`),
    getStatistics: (params) => api.get("/admin/assets/statistics", { params }),
  },

  // 仪表板
  getDashboard: (params) => api.get("/admin/dashboard", { params }),
};

export const managementRhythmApi = {
  // 节律配置
  configs: {
    list: (params) => api.get("/management-rhythm/configs", { params }),
    get: (id) => api.get(`/management-rhythm/configs/${id}`),
    create: (data) => api.post("/management-rhythm/configs", data),
    update: (id, data) => api.put(`/management-rhythm/configs/${id}`, data),
  },

  // 战略会议
  meetings: {
    list: (params) => api.get("/strategic-meetings", { params }),
    get: (id) => api.get(`/strategic-meetings/${id}`),
    create: (data) => api.post("/strategic-meetings", data),
    update: (id, data) => api.put(`/strategic-meetings/${id}`, data),
    updateMinutes: (id, data) =>
      api.put(`/strategic-meetings/${id}/minutes`, data),
  },

  // 会议行动项
  actionItems: {
    list: (meetingId, params) =>
      api.get(`/strategic-meetings/${meetingId}/action-items`, { params }),
    create: (meetingId, data) =>
      api.post(`/strategic-meetings/${meetingId}/action-items`, data),
    update: (meetingId, itemId, data) =>
      api.put(`/strategic-meetings/${meetingId}/action-items/${itemId}`, data),
  },

  // 节律仪表盘
  dashboard: {
    get: () => api.get("/management-rhythm/dashboard"),
  },

  // 会议地图
  meetingMap: {
    get: (params) => api.get("/meeting-map", { params }),
    calendar: (params) => api.get("/meeting-map/calendar", { params }),
    statistics: (params) => api.get("/meeting-map/statistics", { params }),
  },

  // 战略结构模板
  getStrategicStructureTemplate: () =>
    api.get("/management-rhythm/strategic-structure-template"),

  // 会议报告
  reports: {
    list: (params) => api.get("/meeting-reports", { params }),
    get: (id) => api.get(`/meeting-reports/${id}`),
    generate: (data) => api.post("/meeting-reports/generate", data),
    exportDocx: (id) =>
      api.get(`/meeting-reports/${id}/export-docx`, { responseType: "blob" }),
  },
};

export const cultureWallApi = {
  // 文化墙汇总
  summary: {
    get: () => api.get("/culture-wall/summary"),
  },

  // 文化墙内容
  contents: {
    list: (params) => api.get("/culture-wall/contents", { params }),
    get: (id) => api.get(`/culture-wall/contents/${id}`),
    create: (data) => api.post("/culture-wall/contents", data),
    update: (id, data) => api.put(`/culture-wall/contents/${id}`, data),
  },

  // 个人目标
  goals: {
    list: (params) => api.get("/personal-goals", { params }),
    create: (data) => api.post("/personal-goals", data),
    update: (id, data) => api.put(`/personal-goals/${id}`, data),
  },
};

export const financialReportApi = {
  // 综合财务数据
  getSummary: (params) => api.get("/finance/summary", { params }),
  // 损益表
  getProfitLoss: (params) => api.get("/finance/profit-loss", { params }),
  // 现金流量表
  getCashFlow: (params) => api.get("/finance/cash-flow", { params }),
  // 预算执行
  getBudgetExecution: (params) =>
    api.get("/finance/budget-execution", { params }),
  // 成本分析
  getCostAnalysis: (params) => api.get("/finance/cost-analysis", { params }),
  // 项目盈利分析
  getProjectProfitability: (params) =>
    api.get("/finance/project-profitability", { params }),
  // 月度趋势
  getMonthlyTrend: (params) => api.get("/finance/monthly-trend", { params }),
  // 导出报表
  exportReport: (params) =>
    api.get("/finance/export", { params, responseType: "blob" }),
};

export const workLogApi = {
  list: (params) => api.get("/my/work-logs", { params }),
};

export const auditApi = {
  list: (params) => api.get("/audits", { params }),
  get: (id) => api.get(`/audits/${id}`),
};

export const dataImportExportApi = {
  // 导入相关
  getTemplateTypes: () => api.get("/import/templates"),
  downloadTemplate: (templateType) =>
    api.get(`/import/templates/${templateType}`, { responseType: "blob" }),
  previewImport: (file, templateType) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/import/preview", formData, {
      params: { template_type: templateType },
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  validateImport: (data) => api.post("/import/validate", data),
  uploadImport: (file, templateType, updateExisting = false) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/import/upload", formData, {
      params: { template_type: templateType, update_existing: updateExisting },
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  // 导出相关
  exportProjectList: (data) =>
    api.post("/import/export/project_list", data, { responseType: "blob" }),
  exportProjectDetail: (data) =>
    api.post("/import/export/project_detail", data, { responseType: "blob" }),
  exportTaskList: (data) =>
    api.post("/import/export/task_list", data, { responseType: "blob" }),
  exportTimesheet: (data) =>
    api.post("/import/export/timesheet", data, { responseType: "blob" }),
  exportWorkload: (data) =>
    api.post("/import/export/workload", data, { responseType: "blob" }),
};

export const reportCenterApi = {
  // 报表配置
  getRoles: () => api.get("/reports/roles"),
  getTypes: () => api.get("/reports/types"),
  getRoleReportMatrix: () => api.get("/reports/role-report-matrix"),
  // 报表生成
  generate: (data) => api.post("/reports/generate", data),
  preview: (reportType, params) =>
    api.get(`/reports/preview/${reportType}`, { params }),
  compareRoles: (data) => api.post("/reports/compare-roles", data),
  // 报表导出
  exportReport: (data) => api.post("/reports/export", data),
  exportDirect: (params) =>
    api.post("/reports/export-direct", null, { params }),
  download: (reportId) =>
    api.get(`/reports/download/${reportId}`, { responseType: "blob" }),
  // 报表模板
  getTemplates: (params) => api.get("/reports/templates", { params }),
  applyTemplate: (data) => api.post("/reports/templates/apply", data),
  // BI 报表
  getDeliveryRate: (params) => api.get("/reports/delivery-rate", { params }),
  getHealthDistribution: () => api.get("/reports/health-distribution"),
  getUtilization: (params) => api.get("/reports/utilization", { params }),
  getSupplierPerformance: (params) =>
    api.get("/reports/supplier-performance", { params }),
  getExecutiveDashboard: () => api.get("/reports/dashboard/executive"),
  // 研发费用报表
  getRdAuxiliaryLedger: (params) =>
    api.get("/reports/rd-auxiliary-ledger", { params }),
  getRdDeductionDetail: (params) =>
    api.get("/reports/rd-deduction-detail", { params }),
  getRdHighTech: (params) => api.get("/reports/rd-high-tech", { params }),
  getRdIntensity: (params) => api.get("/reports/rd-intensity", { params }),
  getRdPersonnel: (params) => api.get("/reports/rd-personnel", { params }),
  exportRdReport: (params) =>
    api.get("/reports/rd-export", { params, responseType: "blob" }),
};
