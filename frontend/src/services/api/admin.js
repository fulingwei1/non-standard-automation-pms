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
  // 行政审批（兼容统一审批中心 /approvals/*）
  approvals: {
    list: (params = {}) => {
      const status = (params.status || "pending").toLowerCase();
      if (status === "pending") {
        return api.get("/approvals/pending/mine", { params }).then((res) => ({
          ...res,
          data: {
            ...res.data,
            items: (res.data?.items || []).map((item) => ({
              ...item,
              title: item.instance_title || item.instance_no || `审批任务 #${item.id}`,
              applicant: item.assignee_name || "",
              type: "other",
              priority:
                item.instance_urgency === "CRITICAL" || item.instance_urgency === "URGENT"
                  ? "high"
                  : "normal",
              submitTime: item.created_at || "",
            })),
          },
        }));
      }

      const action = status === "approved" ? "APPROVE" : "REJECT";
      return api.get("/approvals/pending/processed", {
        params: { ...params, action },
      }).then((res) => ({
        ...res,
        data: {
          ...res.data,
          items: (res.data?.items || []).map((item) => ({
            ...item,
            title: item.instance_title || item.instance_no || `审批任务 #${item.id}`,
            applicant: item.assignee_name || "",
            type: "other",
            priority:
              item.instance_urgency === "CRITICAL" || item.instance_urgency === "URGENT"
                ? "high"
                : "normal",
            submitTime: item.created_at || "",
            approver: item.assignee_name || "",
            approvedTime: item.completed_at || "",
            rejectedTime: item.completed_at || "",
            status,
          })),
        },
      }));
    },
    get: (id) => api.get(`/approvals/tasks/${id}`),
    approve: (id, data) => api.post(`/approvals/tasks/${id}/approve`, {
      comment: data?.comment || "同意",
    }),
    reject: (id, data) => api.post(`/approvals/tasks/${id}/reject`, {
      comment: data?.reason || data?.comment || "不符合要求",
      reject_to: "START",
    }),
    getStatistics: () => api.get("/approvals/pending/counts"),
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
    list: (params) => api.get("/management-rhythm/meetings/strategic-meetings", { params }),
    get: (id) => api.get(`/management-rhythm/meetings/strategic-meetings/${id}`),
    create: (data) => api.post("/management-rhythm/meetings/strategic-meetings", data),
    update: (id, data) => api.put(`/management-rhythm/meetings/strategic-meetings/${id}`, data),
    updateMinutes: (id, data) =>
      api.put(`/management-rhythm/meetings/strategic-meetings/${id}/minutes`, data),
  },

  // 会议行动项
  actionItems: {
    list: (meetingId, params) =>
      api.get(`/management-rhythm/action-items/strategic-meetings/${meetingId}/action-items`, { params }),
    create: (meetingId, data) =>
      api.post(`/management-rhythm/action-items/strategic-meetings/${meetingId}/action-items`, data),
    update: (meetingId, itemId, data) =>
      api.put(`/management-rhythm/action-items/strategic-meetings/${meetingId}/action-items/${itemId}`, data),
  },

  // 节律仪表盘
  dashboard: {
    get: () => api.get("/management-rhythm/dashboard/"),
  },

  // 会议地图
  meetingMap: {
    get: (params) => api.get("/management-rhythm/meeting-map/", { params }),
    calendar: (params) =>
      api.get("/management-rhythm/meeting-map/calendar", { params }),
    statistics: (params) =>
      api.get("/management-rhythm/meeting-map/statistics", { params }),
  },

  // 战略结构模板
  getStrategicStructureTemplate: () =>
    api.get("/management-rhythm/strategic-structure-template"),

  // 会议报告
  reports: {
    list: (params) => api.get("/management-rhythm/meeting-reports", { params }),
    get: (id) => api.get(`/management-rhythm/meeting-reports/${id}`),
    generate: (data) =>
      api.post("/management-rhythm/meeting-reports/generate", data),
    exportDocx: (id) =>
      api.get(`/management-rhythm/meeting-reports/${id}/export-docx`, {
        responseType: "blob",
      }),
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
    review: (id, data) => api.post(`/culture-wall/contents/${id}/review`, data),
    delete: (id) => api.delete(`/culture-wall/contents/${id}`),
  },

  // 个人目标
  goals: {
    list: (params) => api.get("/culture-wall/personal-goals", { params }),
    create: (data) => api.post("/culture-wall/personal-goals", data),
    update: (id, data) => api.put(`/culture-wall/personal-goals/${id}`, data),
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
  create: (data) => api.post("/my/work-logs", data),
  update: (id, data) => api.put(`/my/work-logs/${id}`, data),
  fieldServiceContext: (params) =>
    api.get("/my/work-logs/field-service-context", { params }),
  createFromDispatch: (data) => api.post("/my/work-logs/from-dispatch", data),
};

export const auditApi = {
  list: (params) => api.get("/audits/", { params }),
  get: (id) => api.get(`/audits/${id}`),
};

const DATA_IMPORT_EXPORT_BASE = "/data-import-export";

export const dataImportExportApi = {
  // 导入相关
  getTemplateTypes: () => api.get(`${DATA_IMPORT_EXPORT_BASE}/templates`),
  downloadTemplate: (templateType) =>
    api.get(`${DATA_IMPORT_EXPORT_BASE}/templates/${templateType}`, { responseType: "blob" }),
  previewImport: (file, templateType) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`${DATA_IMPORT_EXPORT_BASE}/preview`, formData, {
      params: { template_type: templateType },
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  validateImport: (data) => api.post(`${DATA_IMPORT_EXPORT_BASE}/validate`, data),
  uploadImport: (file, templateType, updateExisting = false) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`${DATA_IMPORT_EXPORT_BASE}/upload`, formData, {
      params: { template_type: templateType, update_existing: updateExisting },
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  // 导出相关
  exportProjectList: (data) =>
    api.post(`${DATA_IMPORT_EXPORT_BASE}/export/project_list`, data, { responseType: "blob" }),
  exportProjectDetail: (data) =>
    api.post(`${DATA_IMPORT_EXPORT_BASE}/export/project_detail`, data, { responseType: "blob" }),
  exportTaskList: (data) =>
    api.post(`${DATA_IMPORT_EXPORT_BASE}/export/task_list`, data, { responseType: "blob" }),
  exportTimesheet: (data) =>
    api.post(`${DATA_IMPORT_EXPORT_BASE}/export/timesheet`, data, { responseType: "blob" }),
  exportWorkload: (data) =>
    api.post(`${DATA_IMPORT_EXPORT_BASE}/export/workload`, data, { responseType: "blob" }),
};

export const reportCenterApi = {
  // 报表配置
  getRoles: () => api.get("/report-center/configs/roles"),
  getTypes: () => api.get("/report-center/configs/types"),
  getRoleReportMatrix: () => api.get("/report-center/configs/role-report-matrix"),
  // 报表生成
  generate: (data) => api.post("/reports/generate", data),
  preview: (reportType, params) =>
    api.get(`/reports/${reportType}/preview`, { params }),
  previewByTemplate: (params) => api.get(`/reports/${params.report_code}/preview`, { params }),
  compareRoles: (data) => api.post("/reports/compare-roles", data),
  // 报表导出
  exportReport: (data) => api.post("/reports/export", data),
  exportDirect: (params) =>
    api.post("/reports/export-direct", null, { params }),
  download: (reportId) =>
    api.get(`/reports/download/${reportId}`, { responseType: "blob" }),
  // 报表模板
  getTemplates: (params) => api.get("/report-center/templates", { params }),
  createTemplate: (data) => api.post("/report-center/templates", data),
  toggleTemplate: (id) => api.post(`/report-center/templates/${id}/toggle`),
  deleteTemplate: (id) => api.delete(`/report-center/templates/${id}`),
  applyTemplate: (data) => api.post("/report-center/templates/apply", data),
  // 报表归档
  getArchives: (params) => api.get("/report/archives", { params }),
  downloadArchive: (id) =>
    api.get(`/report/archives/${id}/download`, { responseType: "blob" }),
  // BI 报表
  getDeliveryRate: (params) => api.get("/report-center/bi/delivery-rate", { params }),
  getHealthDistribution: () => api.get("/report-center/bi/health-distribution"),
  getUtilization: (params) => api.get("/report-center/bi/utilization", { params }),
  getSupplierPerformance: (params) =>
    api.get("/report-center/bi/supplier-performance", { params }),
  getExecutiveDashboard: () => api.get("/report-center/bi/dashboard/executive"),
  // 研发费用报表
  getRdAuxiliaryLedger: (params) =>
    api.get("/report-center/rd-expense/rd-auxiliary-ledger", { params }),
  getRdDeductionDetail: (params) =>
    api.get("/report-center/rd-expense/rd-deduction-detail", { params }),
  getRdHighTech: (params) => api.get("/report-center/rd-expense/rd-high-tech", { params }),
  getRdIntensity: (params) => api.get("/report-center/rd-expense/rd-intensity", { params }),
  getRdPersonnel: (params) => api.get("/report-center/rd-expense/rd-personnel", { params }),
  exportRdReport: (params) =>
    api.get("/report-center/rd-expense/rd-export", { params, responseType: "blob" }),
};
