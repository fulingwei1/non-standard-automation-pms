import { api } from "./client.js";

export const qualityApi = {
  // 质检记录
  inspection: {
    list: (params) => api.get("/production/quality/inspection", { params }),
    create: (data) => api.post("/production/quality/inspection", data),
  },

  // 质量趋势
  trend: (params) => api.get("/production/quality/trend", { params }),

  // 不良品分析
  defectAnalysis: {
    create: (data) => api.post("/production/quality/defect-analysis", data),
    get: (id) => api.get(`/production/quality/defect-analysis/${id}`),
  },

  // 质量预警
  alerts: {
    list: (params) => api.get("/production/quality/alerts", { params }),
  },
  alertRules: {
    list: (params) => api.get("/production/quality/alert-rules", { params }),
    create: (data) => api.post("/production/quality/alert-rules", data),
  },

  // SPC
  spc: (params) => api.get("/production/quality/spc", { params }),

  // 返工
  rework: {
    list: (params) => api.get("/production/quality/rework", { params }),
    create: (data) => api.post("/production/quality/rework", data),
    complete: (id, data) => api.put(`/production/quality/rework/${id}/complete`, data),
  },

  // 帕累托分析
  pareto: (params) => api.get("/production/quality/pareto", { params }),

  // 统计看板
  statistics: () => api.get("/production/quality/statistics"),

  // 批次追溯
  batchTracing: (params) => api.get("/production/quality/batch-tracing", { params }),

  // 纠正措施
  correctiveAction: {
    create: (data) => api.post("/production/quality/corrective-action", data),
  },

  // 外协质检
  outsourcing: {
    list: (params) => api.get("/outsourcing-inspections", { params }),
    create: (data) => api.post("/outsourcing-inspections", data),
    update: (id, params) => api.put(`/outsourcing-inspections/${id}`, null, { params }),
  },
};
