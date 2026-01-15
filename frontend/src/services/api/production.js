import { api } from "./client.js";



export const shortageApi = {
  // 缺料上报
  reports: {
    list: (params) => api.get("/shortage/reports", { params }),
    get: (id) => api.get(`/shortage/reports/${id}`),
    create: (data) => api.post("/shortage/reports", data),
    confirm: (id) => api.put(`/shortage/reports/${id}/confirm`),
    handle: (id, data) => api.put(`/shortage/reports/${id}/handle`, data),
    resolve: (id) => api.put(`/shortage/reports/${id}/resolve`),
  },
  // 到货跟踪
  arrivals: {
    list: (params) => api.get("/shortage/arrivals", { params }),
    get: (id) => api.get(`/shortage/arrivals/${id}`),
    create: (data) => api.post("/shortage/arrivals", data),
    updateStatus: (id, status) =>
      api.put(`/shortage/arrivals/${id}/status`, { status }),
    createFollowUp: (id, data) =>
      api.post(`/shortage/arrivals/${id}/follow-up`, data),
    getFollowUps: (id, params) =>
      api.get(`/shortage/arrivals/${id}/follow-ups`, { params }),
    receive: (id, receivedQty) =>
      api.post(`/shortage/arrivals/${id}/receive`, {
        received_qty: receivedQty,
      }),
    getDelayed: (params) => api.get("/shortage/arrivals/delayed", { params }),
  },
  // 物料替代
  substitutions: {
    list: (params) => api.get("/shortage/substitutions", { params }),
    get: (id) => api.get(`/shortage/substitutions/${id}`),
    create: (data) => api.post("/shortage/substitutions", data),
    techApprove: (id, approved, note) =>
      api.put(`/shortage/substitutions/${id}/tech-approve`, {
        approved,
        approval_note: note,
      }),
    prodApprove: (id, approved, note) =>
      api.put(`/shortage/substitutions/${id}/prod-approve`, {
        approved,
        approval_note: note,
      }),
    execute: (id, note) =>
      api.put(`/shortage/substitutions/${id}/execute`, {
        execution_note: note,
      }),
  },
  // 物料调拨
  transfers: {
    list: (params) => api.get("/shortage/transfers", { params }),
    get: (id) => api.get(`/shortage/transfers/${id}`),
    create: (data) => api.post("/shortage/transfers", data),
    approve: (id, approved, note) =>
      api.put(`/shortage/transfers/${id}/approve`, {
        approved,
        approval_note: note,
      }),
    execute: (id, actualQty, note) =>
      api.put(`/shortage/transfers/${id}/execute`, {
        actual_qty: actualQty,
        execution_note: note,
      }),
  },
  // 统计分析
  statistics: {
    dashboard: () => api.get("/shortage/dashboard"),
    supplierDelivery: (params) =>
      api.get("/shortage/supplier-delivery", { params }),
    dailyReport: (date) =>
      api.get("/shortage/daily-report", { params: { report_date: date } }),
    latestDailyReport: () => api.get("/shortage/daily-report/latest"),
    dailyReportByDate: (date) =>
      api.get("/shortage/daily-report/by-date", {
        params: { report_date: date },
      }),
  },
};

export const productionApi = {
  dashboard: () => api.get("/production/dashboard"),
  dailyReports: {
    daily: (params) => api.get("/production-daily-reports", { params }),
    latestDaily: () => api.get("/production-daily-reports/latest"),
  },
  workshops: {
    list: (params) => api.get("/workshops", { params }),
    get: (id) => api.get(`/workshops/${id}`),
    create: (data) => api.post("/workshops", data),
    update: (id, data) => api.put(`/workshops/${id}`, data),
    getWorkstations: (id) =>
      api.get(`/production/workshops/${id}/workstations`),
    addWorkstation: (id, data) =>
      api.post(`/production/workshops/${id}/workstations`, data),
  },
  workstations: {
    list: (params) => api.get("/workstations", { params }),
    get: (id) => api.get(`/workstations/${id}`),
    getStatus: (id) => api.get(`/workstations/${id}/status`),
  },
  productionPlans: {
    list: (params) => api.get("/production-plans", { params }),
    get: (id) => api.get(`/production-plans/${id}`),
    create: (data) => api.post("/production-plans", data),
    update: (id, data) => api.put(`/production-plans/${id}`, data),
    submit: (id) => api.put(`/production/production-plans/${id}/submit`),
    approve: (id) => api.put(`/production/production-plans/${id}/approve`),
    publish: (id) => api.put(`/production-plans/${id}/publish`),
    calendar: (params) => api.get("/production-plans/calendar", { params }),
  },
  workOrders: {
    list: (params) => api.get("/work-orders", { params }),
    get: (id) => api.get(`/work-orders/${id}`),
    create: (data) => api.post("/work-orders", data),
    update: (id, data) => api.put(`/work-orders/${id}`, data),
    assign: (id, data) => api.put(`/work-orders/${id}/assign`, data),
    start: (id) => api.put(`/work-orders/${id}/start`),
    pause: (id) => api.put(`/work-orders/${id}/pause`),
    resume: (id) => api.put(`/work-orders/${id}/resume`),
    complete: (id, data) => api.put(`/work-orders/${id}/complete`, data),
    getProgress: (id) => api.get(`/work-orders/${id}/progress`),
    getReports: (id) =>
      api.get("/work-reports", {
        params: { work_order_id: id, page_size: 1000 },
      }),
  },
  workers: {
    list: (params) => api.get("/workers", { params }),
    get: (id) => api.get(`/workers/${id}`),
    create: (data) => api.post("/workers", data),
    update: (id, data) => api.put(`/workers/${id}`, data),
  },
  workReports: {
    list: (params) => api.get("/work-reports", { params }),
    get: (id) => api.get(`/work-reports/${id}`),
    create: (data) => api.post("/work-reports", data),
    start: (data) => api.post("/production/work-reports/start", data),
    progress: (data) => api.post("/production/work-reports/progress", data),
    complete: (data) => api.post("/production/work-reports/complete", data),
    approve: (id) => api.put(`/work-reports/${id}/approve`),
    my: (params) => api.get("/work-reports/my", { params }),
  },
  materialRequisitions: {
    list: (params) => api.get("/material-requisitions", { params }),
    get: (id) => api.get(`/material-requisitions/${id}`),
    create: (data) => api.post("/material-requisitions", data),
    approve: (id, data) =>
      api.put(`/material-requisitions/${id}/approve`, data),
    issue: (id, data) => api.put(`/material-requisitions/${id}/issue`, data),
  },
  exceptions: {
    list: (params) => api.get("/production-exceptions", { params }),
    get: (id) => api.get(`/production-exceptions/${id}`),
    create: (data) => api.post("/production-exceptions", data),
    handle: (id, data) => api.put(`/production-exceptions/${id}/handle`, data),
    close: (id) => api.put(`/production-exceptions/${id}/close`),
  },
  taskBoard: (workshopId) => api.get(`/workshops/${workshopId}/task-board`),
  reports: {
    workerPerformance: (params) =>
      api.get("/production/reports/worker-performance", { params }),
    workerRanking: (params) =>
      api.get("/production/reports/worker-ranking", { params }),
  },
};

export const materialApi = {
  list: (params) => api.get("/materials/", { params }),
  get: (id) => api.get(`/materials/${id}`),
  create: (data) => api.post("/materials/", data),
  update: (id, data) => api.put(`/materials/${id}`, data),
  search: (params) => api.get("/materials/search", { params }),
  warehouse: {
    statistics: () => api.get("/materials/warehouse/statistics"),
  },
  categories: {
    list: (params) => api.get("/materials/categories/", { params }),
  },
};

export const materialDemandApi = {
  list: (params) => api.get("/material-demands", { params }),
  getVsStock: (materialId, params) =>
    api.get(`/material-demands/vs-stock`, {
      params: { material_id: materialId, ...params },
    }),
  getSchedule: (params) => api.get("/material-demands/schedule", { params }),
  generatePR: (params) =>
    api.post("/material-demands/generate-pr", null, { params }),
};

export const shortageAlertApi = {
  list: (params) => api.get("/shortage-alerts", { params }),
  get: (id) => api.get(`/shortage-alerts/${id}`),
  acknowledge: (id) => api.put(`/shortage-alerts/${id}/acknowledge`),
  resolve: (id, data) => api.put(`/shortage-alerts/${id}/resolve`, data),
  getSummary: (params) => api.get("/shortage-alerts/summary", { params }),
};

export const bomApi = {
  getByMachine: (machineId) =>
    api.get(`/bom/machines/${machineId}/bom`).then((res) => {
      // Get the latest BOM from the list
      const bomList = res.data || res || [];
      if (bomList.length > 0) {
        // Find the latest BOM (is_latest = true or most recent)
        const latestBom = bomList.find((bom) => bom.is_latest) || bomList[0];
        return { data: latestBom };
      }
      return { data: null };
    }),
  list: (params) => api.get("/bom/", { params }),
  get: (id) => api.get(`/bom/${id}`),
  create: (machineId, data) => api.post(`/bom/machines/${machineId}/bom`, data),
  update: (id, data) => api.put(`/bom/${id}`, data),
  // BOM Items
  getItems: (bomId) => api.get(`/bom/${bomId}/items`),
  addItem: (bomId, data) => api.post(`/bom/${bomId}/items`, data),
  updateItem: (itemId, data) => api.put(`/bom/items/${itemId}`, data),
  deleteItem: (itemId) => api.delete(`/bom/items/${itemId}`),
  // BOM Versions
  getVersions: (bomId) => api.get(`/bom/${bomId}/versions`),
  compareVersions: (bomId, version1Id, version2Id) =>
    api.get(`/bom/${bomId}/versions/compare`, {
      params: { version1_id: version1Id, version2_id: version2Id },
    }),
  // BOM Operations
  release: (bomId, changeNote) =>
    api.post(`/bom/${bomId}/release`, null, {
      params: { change_note: changeNote },
    }),
  // BOM Import/Export
  import: (bomId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/bom/${bomId}/import`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  export: (bomId) => api.get(`/bom/${bomId}/export`, { responseType: "blob" }),
  // Generate Purchase Requirements
  generatePR: (bomId, params) =>
    api.post(`/bom/${bomId}/generate-pr`, null, { params }),
};

export const kitCheckApi = {
  list: (params) => api.get("/kit-checks", { params }),
  get: (id) => api.get(`/kit-checks/${id}`),
  create: (data) => api.post("/kit-checks", data),
  update: (id, data) => api.put(`/kit-checks/${id}`, data),
  delete: (id) => api.delete(`/kit-checks/${id}`),
  getStatistics: (params) => api.get("/kit-checks/statistics", { params }),
};

export const assemblyKitApi = {
  // 看板数据
  dashboard: (params) => api.get("/assembly/dashboard", { params }),

  // 装配阶段
  getStages: (params) => api.get("/assembly/stages", { params }),
  updateStage: (stageCode, data) =>
    api.put(`/assembly/stages/${stageCode}`, data),

  // 物料分类映射
  getCategoryMappings: (params) =>
    api.get("/assembly/category-mappings", { params }),
  createCategoryMapping: (data) =>
    api.post("/assembly/category-mappings", data),
  updateCategoryMapping: (id, data) =>
    api.put(`/assembly/category-mappings/${id}`, data),
  deleteCategoryMapping: (id) =>
    api.delete(`/assembly/category-mappings/${id}`),

  // BOM装配属性
  getBomAssemblyAttrs: (bomId, params) =>
    api.get(`/assembly/bom/${bomId}/assembly-attrs`, { params }),
  batchSetAssemblyAttrs: (bomId, data) =>
    api.post(`/assembly/bom/${bomId}/assembly-attrs/batch`, data),
  updateAssemblyAttr: (attrId, data) =>
    api.put(`/assembly/bom/assembly-attrs/${attrId}`, data),
  autoAssignAttrs: (bomId, data) =>
    api.post(`/assembly/bom/${bomId}/assembly-attrs/auto`, data),
  applyTemplate: (bomId, data) =>
    api.post(`/assembly/bom/${bomId}/assembly-attrs/template`, data),

  // 齐套分析
  executeAnalysis: (data) => api.post("/assembly/analysis", data),
  getAnalysisDetail: (readinessId) =>
    api.get(`/assembly/analysis/${readinessId}`),
  getProjectReadiness: (projectId, params) =>
    api.get(`/assembly/projects/${projectId}/assembly-readiness`, { params }),

  // 智能推荐
  getRecommendations: (bomId) =>
    api.get(`/assembly/bom/${bomId}/assembly-attrs/recommendations`),
  smartRecommend: (bomId, data) =>
    api.post(`/assembly/bom/${bomId}/assembly-attrs/smart-recommend`, data),

  // 排产建议
  generateSuggestions: (params) =>
    api.post("/assembly/suggestions/generate", null, { params }),

  // 优化建议
  getOptimizationSuggestions: (readinessId) =>
    api.get(`/assembly/analysis/${readinessId}/optimize`),

  // 缺料预警
  getShortageAlerts: (params) =>
    api.get("/assembly/shortage-alerts", { params }),

  // 预警规则
  getAlertRules: (params) => api.get("/assembly/alert-rules", { params }),
  createAlertRule: (data) => api.post("/assembly/alert-rules", data),
  updateAlertRule: (id, data) => api.put(`/assembly/alert-rules/${id}`, data),

  // 排产建议
  getSuggestions: (params) => api.get("/assembly/suggestions", { params }),
  acceptSuggestion: (id, data) =>
    api.post(`/assembly/suggestions/${id}/accept`, data),
  rejectSuggestion: (id, data) =>
    api.post(`/assembly/suggestions/${id}/reject`, data),

  // 装配模板
  getTemplates: (params) => api.get("/assembly/templates", { params }),
  createTemplate: (data) => api.post("/assembly/templates", data),
  updateTemplate: (id, data) => api.put(`/assembly/templates/${id}`, data),
  deleteTemplate: (id) => api.delete(`/assembly/templates/${id}`),
};
