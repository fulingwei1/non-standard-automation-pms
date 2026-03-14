import { api } from "./client.js";

const PRODUCTION_EXCEPTION_STATUS_MAP = {
  REPORTED: "OPEN",
  IN_PROGRESS: "IN_PROGRESS",
  RESOLVED: "RESOLVED",
  CLOSED: "CLOSED",
};

const PRODUCTION_EXCEPTION_STATUS_REVERSE_MAP = {
  OPEN: "REPORTED",
  IN_PROGRESS: "IN_PROGRESS",
  RESOLVED: "RESOLVED",
  CLOSED: "CLOSED",
};

const unwrapProductionResponse = (response) => response?.data?.data ?? response?.data ?? response;

const pickLatestActionContent = (actions = [], actionType) => {
  const matched = [...actions].find((action) => action?.action_type === actionType);
  return matched?.action_content || "";
};

const normalizeProductionException = (item = {}) => ({
  ...item,
  exception_no: item.exception_no || item.event_no,
  title: item.title || item.event_title,
  description: item.description || item.event_description,
  exception_type: item.exception_type || item.event_type,
  exception_level: item.exception_level || item.severity,
  report_time: item.report_time || item.discovered_at,
  reporter_name: item.reporter_name || item.discovered_by_name,
  impact_hours: item.impact_hours ?? item.schedule_impact ?? 0,
  impact_cost: item.impact_cost ?? item.cost_impact ?? 0,
  handle_plan: item.handle_plan || item.solution || pickLatestActionContent(item.actions, "PLAN"),
  handle_result:
    item.handle_result ||
    item.resolution_note ||
    pickLatestActionContent(item.actions, "RESULT"),
  status: PRODUCTION_EXCEPTION_STATUS_REVERSE_MAP[item.status] || item.status,
});


export const shortageApi = {
  // 缺料上报 - /shortage/handling/reports
  reports: {
    list: (params) => api.get("/shortage/handling/reports", { params }),
    get: (id) => api.get(`/shortage/handling/reports/${id}`),
    create: (data) => api.post("/shortage/handling/reports", data),
    confirm: (id) => api.put(`/shortage/handling/reports/${id}/confirm`),
    handle: (id, data) => api.put(`/shortage/handling/reports/${id}/handle`, data),
    resolve: (id) => api.put(`/shortage/handling/reports/${id}/resolve`),
    reject: (id, reason) => api.put(`/shortage/handling/reports/${id}/reject`, { reason }),
  },
  // 到货跟踪 - /shortage/handling/arrivals
  arrivals: {
    list: (params) => api.get("/shortage/handling/arrivals", { params }),
    get: (id) => api.get(`/shortage/handling/arrivals/${id}`),
    create: (data) => api.post("/shortage/handling/arrivals", data),
    updateStatus: (id, status) =>
      api.put(`/shortage/handling/arrivals/${id}/status`, { status }),
    createFollowUp: (id, data) =>
      api.post(`/shortage/handling/arrivals/${id}/follow-up`, data),
    getFollowUps: (id, params) =>
      api.get(`/shortage/handling/arrivals/${id}/follow-ups`, { params }),
    receive: (id, receivedQty) =>
      api.post(`/shortage/handling/arrivals/${id}/receive`, {
        received_qty: receivedQty,
      }),
    getDelayed: (params) => api.get("/shortage/handling/arrivals/delayed", { params }),
  },
  // 物料替代 - /shortage/handling/substitutions
  substitutions: {
    list: (params) => api.get("/shortage/handling/substitutions", { params }),
    get: (id) => api.get(`/shortage/handling/substitutions/${id}`),
    create: (data) => api.post("/shortage/handling/substitutions", data),
    techApprove: (id, approved, note) =>
      api.put(`/shortage/handling/substitutions/${id}/tech-approve`, {
        approved,
        approval_note: note,
      }),
    prodApprove: (id, approved, note) =>
      api.put(`/shortage/handling/substitutions/${id}/prod-approve`, {
        approved,
        approval_note: note,
      }),
    execute: (id, note) =>
      api.put(`/shortage/handling/substitutions/${id}/execute`, {
        execution_note: note,
      }),
  },
  // 物料调拨 - /shortage/handling/transfers
  transfers: {
    list: (params) => api.get("/shortage/handling/transfers", { params }),
    get: (id) => api.get(`/shortage/handling/transfers/${id}`),
    create: (data) => api.post("/shortage/handling/transfers", data),
    approve: (id, approved, note) =>
      api.put(`/shortage/handling/transfers/${id}/approve`, {
        approved,
        approval_note: note,
      }),
    execute: (id, actualQty, note) =>
      api.put(`/shortage/handling/transfers/${id}/execute`, {
        actual_qty: actualQty,
        execution_note: note,
      }),
  },
  // 统计分析 - /shortage/analytics/...
  statistics: {
    dashboard: () => api.get("/shortage/analytics/overview"),
    causeAnalysis: (params) =>
      api.get("/shortage/analytics/cause-analysis", { params }),
    kitRate: (params) =>
      api.get("/shortage/analytics/kit-rate", { params }),
    supplierDelivery: (params) =>
      api.get("/shortage/analytics/supplier-delivery", { params }),
    dailyReport: (date) =>
      api.get("/shortage/analytics/daily-report", { params: { report_date: date } }),
    latestDailyReport: () => api.get("/shortage/analytics/daily-report/latest"),
    dailyReportByDate: (date) =>
      api.get("/shortage/analytics/daily-report/by-date", {
        params: { report_date: date },
      }),
    trends: (params) =>
      api.get("/shortage/analytics/trends", { params }),
  },
};

export const productionApi = {
  dashboard: () => api.get("/production/dashboard"),
  dailyReports: {
    daily: (params) => api.get("/production-daily-reports", { params }),
    latestDaily: () => api.get("/production-daily-reports/latest"),
  },
  workshops: {
    list: (params) => api.get("/production/workshops", { params }),
    get: (id) => api.get(`/production/workshops/${id}`),
    create: (data) => api.post("/production/workshops", data),
    update: (id, data) => api.put(`/production/workshops/${id}`, data),
    getWorkstations: (id) =>
      api.get(`/production/workshops/${id}/workstations`),
    addWorkstation: (id, data) =>
      api.post(`/production/workshops/${id}/workstations`, data),
  },
  workstations: {
    list: (params) => api.get("/production/workshops", { params }),
    get: (id) => api.get(`/production/workshops/${id}`),
    getStatus: (id) => api.get(`/production/workstations/${id}/status`),
  },
  productionPlans: {
    list: (params) => api.get("/production/production-plans", { params }),
    get: (id) => api.get(`/production/production-plans/${id}`),
    create: (data) => api.post("/production/production-plans", data),
    update: (id, data) => api.put(`/production/production-plans/${id}`, data),
    submit: (id) => api.put(`/production/production-plans/${id}/submit`),
    approve: (id) => api.put(`/production/production-plans/${id}/approve`),
    publish: (id) => api.put(`/production/production-plans/${id}/publish`),
    calendar: (params) => api.get("/production/production-plans/calendar", { params }),
  },
  workOrders: {
    list: (params) => api.get("/production/work-orders", { params }),
    get: (id) => api.get(`/production/work-orders/${id}`),
    create: (data) => api.post("/production/work-orders", data),
    update: (id, data) => api.put(`/production/work-orders/${id}`, data),
    assign: (id, data) => api.put(`/production/work-orders/${id}/assign`, data),
    start: (id) => api.put(`/production/work-orders/${id}/start`),
    pause: (id) => api.put(`/production/work-orders/${id}/pause`),
    resume: (id) => api.put(`/production/work-orders/${id}/resume`),
    complete: (id, data) => api.put(`/production/work-orders/${id}/complete`, data),
    getProgress: (id) => api.get(`/production/work-orders/${id}/progress`),
    getReports: (id) =>
      api.get("/production/work-reports", {
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
    list: (params) => api.get("/production/work-reports", { params }),
    get: (id) => api.get(`/production/work-reports/${id}`),
    create: (data) => api.post("/production/work-reports", data),
    start: (data) => api.post("/production/work-reports/start", data),
    progress: (data) => api.post("/production/work-reports/progress", data),
    complete: (data) => api.post("/production/work-reports/complete", data),
    approve: (id) => api.put(`/production/work-reports/${id}/approve`),
    my: (params) => api.get("/production/work-reports/my", { params }),
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
    async list(params = {}) {
      const response = await api.get("/exceptions", {
        params: {
          project_id:
            params.project_id && params.project_id !== "all" ? params.project_id : undefined,
          event_type:
            params.event_type ||
            (params.exception_type && params.exception_type !== "all"
              ? params.exception_type
              : undefined),
          severity:
            params.severity ||
            (params.exception_level && params.exception_level !== "all"
              ? params.exception_level
              : undefined),
          status:
            params.status && params.status !== "all"
              ? PRODUCTION_EXCEPTION_STATUS_MAP[params.status] || params.status
              : undefined,
          keyword: params.keyword || params.search || undefined,
        },
      });
      const data = unwrapProductionResponse(response);
      return {
        ...response,
        data: {
          ...data,
          items: (data?.items || []).map(normalizeProductionException),
        },
      };
    },
    async get(id) {
      const response = await api.get(`/exceptions/${id}`);
      return {
        ...response,
        data: normalizeProductionException(unwrapProductionResponse(response)),
      };
    },
    async create(data) {
      const response = await api.post("/exceptions", {
        source_type: data.source_type || "PRODUCTION",
        project_id: data.project_id || null,
        machine_id: data.equipment_id || null,
        event_type: data.exception_type || "OTHER",
        severity: data.exception_level || "MINOR",
        event_title: data.title,
        event_description: data.description || data.remark || "",
        impact_description: data.remark || null,
        schedule_impact: Math.round(Number(data.impact_hours) || 0),
        cost_impact: Number(data.impact_cost) || 0,
        attachments: [],
      });
      return {
        ...response,
        data: normalizeProductionException(unwrapProductionResponse(response)),
      };
    },
    async handle(id, data = {}) {
      if (data.handle_plan) {
        await api.post(`/exceptions/${id}/actions`, null, {
          params: {
            action_type: "PLAN",
            action_content: data.handle_plan,
          },
        });
      }
      if (data.handle_result) {
        await api.post(`/exceptions/${id}/actions`, null, {
          params: {
            action_type: "RESULT",
            action_content: data.handle_result,
          },
        });
      }
      const nextStatus = data.handle_result ? "RESOLVED" : "IN_PROGRESS";
      const response = await api.put(`/exceptions/${id}/status`, null, {
        params: { status: nextStatus },
      });
      return {
        ...response,
        data: normalizeProductionException(unwrapProductionResponse(response)),
      };
    },
    async close(id) {
      const response = await api.put(`/exceptions/${id}/status`, null, {
        params: { status: "CLOSED" },
      });
      return {
        ...response,
        data: normalizeProductionException(unwrapProductionResponse(response)),
      };
    },
    statistics: (params) => api.get("/exceptions/statistics", { params }),
  },
  capacity: {
    utilization: (params) => api.get("/production/capacity/utilization", { params }),
    bottlenecks: (params) => api.get("/production/capacity/bottlenecks", { params }),
    trend: (params) => api.get("/production/capacity/trend", { params }),
    forecast: (params) => api.get("/production/capacity/forecast", { params }),
    oee: (params) => api.get("/production/capacity/oee", { params }),
  },
  taskBoard: (workshopId) => api.get(`/production/workshops/${workshopId}/task-board`),
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
  // 缺料预警检测 - /shortage/detection/alerts
  list: (params) => api.get("/shortage/detection/alerts", { params }),
  get: (id) => api.get(`/shortage/detection/alerts/${id}`),
  acknowledge: (id) => api.put(`/shortage/detection/alerts/${id}/acknowledge`),
  update: (id, data) => api.patch(`/shortage/detection/alerts/${id}`, data),
  resolve: (id, data) => api.post(`/shortage/detection/alerts/${id}/resolve`, data),
  getFollowUps: (id) => api.get(`/shortage/detection/alerts/${id}/follow-ups`),
  addFollowUp: (id, data) => api.post(`/shortage/detection/alerts/${id}/follow-ups`, data),
  // 库存预警监控
  inventoryWarnings: (params) => api.get("/shortage/detection/inventory-warnings", { params }),
  checkInventory: (data) => api.post("/shortage/detection/inventory-warnings/check", data),
};

export const bomApi = {
  getByMachine: (machineId) =>
    api.get(`/bom/machines/${machineId}/`).then((res) => {
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
  create: (machineId, data) => api.post(`/bom/machines/${machineId}/`, data),
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
  // 基于时间的齐套率预警
  getTimeBasedKitRate: (projectId, params) => api.get(`/assembly/kit-rate/project/${projectId}/time-based-kit-rate`, { params }),
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
