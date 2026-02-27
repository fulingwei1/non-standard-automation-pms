import { api } from "./client.js";



export const employeeApi = {
  list: (params) => api.get("/org/employees", { params }),
  get: (id) => api.get(`/org/employees/${id}`),
  create: (data) => api.post("/org/employees", data),
  update: (id, data) => api.put(`/org/employees/${id}`, data),
  delete: (id) => api.delete(`/org/employees/${id}`),
  getStatistics: (params) => api.get("/employees/statistics", { params }),
};

export const departmentApi = {
  list: (params) => api.get("/org/departments", { params }),
  get: (id) => api.get(`/org/departments/${id}`),
  create: (data) => api.post("/org/departments", data),
  update: (id, data) => api.put(`/org/departments/${id}`, data),
  delete: (id) => api.delete(`/org/departments/${id}`),
  getStatistics: (params) => api.get("/org/departments/statistics", { params }),
};

export const hrApi = {
  // 人事事务
  transactions: {
    list: (params) => api.get("/hr/transactions", { params }),
    get: (id) => api.get(`/hr/transactions/${id}`),
    create: (data) => api.post("/hr/transactions", data),
    approve: (id, data) => api.post(`/hr/transactions/${id}/approve`, data),
    getStatistics: (params) =>
      api.get("/hr/transactions/statistics", { params }),
  },
  // 合同管理
  contracts: {
    list: (params) => api.get("/hr/contracts", { params }),
    get: (id) => api.get(`/hr/contracts/${id}`),
    create: (data) => api.post("/hr/contracts", data),
    update: (id, data) => api.put(`/hr/contracts/${id}`, data),
    renew: (id, data) => api.post(`/hr/contracts/${id}/renew`, data),
    getExpiring: (params) => api.get("/hr/contracts/expiring", { params }),
  },
  // 合同到期提醒
  reminders: {
    list: (params) => api.get("/hr/contract-reminders", { params }),
    handle: (id, data) => api.put(`/hr/contract-reminders/${id}/handle`, data),
    generate: () => api.post("/hr/contract-reminders/generate"),
  },
  // 仪表板
  dashboard: {
    overview: () => api.get("/hr/dashboard/overview"),
    pendingConfirmations: (params) =>
      api.get("/hr/dashboard/pending-confirmations", { params }),
  },
  // 人事档案
  profiles: {
    list: (params) => api.get("/org/hr-profiles", { params }),
    get: (id) => api.get(`/org/hr-profiles/${id}`),
    create: (data) => api.post("/org/hr-profiles", data),
    update: (id, data) => api.put(`/org/hr-profiles/${id}`, data),
  },
};

export const performanceApi = {
  // ========== 员工端 API ==========

  // 月度工作总结
  createMonthlySummary: (data) =>
    api.post("/performance/new/employee/monthly-summary", data),
  saveMonthlySummaryDraft: (period, data) =>
    api.put("/performance/new/employee/monthly-summary/draft", data, {
      params: { period },
    }),
  getMonthlySummaryHistory: (params) =>
    api.get("/performance/new/employee/monthly-summary/history", { params }),

  // 我的绩效
  getMyPerformance: () => api.get("/performance/new/employee/my-performance"),

  // ========== 经理端 API ==========

  // 待评价任务
  getEvaluationTasks: (params) =>
    api.get("/performance/new/manager/evaluation-tasks", { params }),
  getEvaluationDetail: (taskId) => api.get(`/performance/new/manager/evaluation/${taskId}`),
  submitEvaluation: (taskId, data) =>
    api.post(`/performance/new/manager/evaluation/${taskId}`, data),

  // ========== HR 端 API ==========

  // 权重配置
  getWeightConfig: () => api.get("/performance/new/hr/weight-config"),
  updateWeightConfig: (data) => api.put("/performance/new/hr/weight-config", data),

  // 融合绩效
  getIntegratedPerformance: (userId, params) =>
    api.get(`/performance/integration/integrated/${userId}`, { params }),
  calculateIntegratedPerformance: (params) =>
    api.post("/performance/integration/calculate-integrated", null, { params }),
};

export const bonusApi = {
  // 我的奖金
  getMyBonus: () => api.get("/bonus/my/my"),
  getMyBonusStatistics: (params) => api.get("/bonus/statistics/statistics", { params }),

  // 奖金计算记录
  getCalculations: (params) => api.get("/bonus/sales-calc/calculations", { params }),
  getCalculation: (id) => api.get(`/bonus/sales-calc/calculations/${id}`),

  // 奖金发放记录
  getDistributions: (params) => api.get("/bonus/payment/distributions", { params }),
  getDistribution: (id) => api.get(`/bonus/payment/distributions/${id}`),

  // 计算奖金（需要权限）
  calculateSalesBonus: (data) => api.post("/bonus/sales-calc/calculate/sales", data),
  calculateSalesDirectorBonus: (data) =>
    api.post("/bonus/sales-calc/calculate/sales-director", data),
  calculatePresaleBonus: (data) => api.post("/bonus/sales-calc/calculate/presale", data),
  calculatePerformanceBonus: (data) =>
    api.post("/bonus/calculation/calculate/performance", data),
  calculateProjectBonus: (data) => api.post("/bonus/calculation/calculate/project", data),
  calculateMilestoneBonus: (data) =>
    api.post("/bonus/calculation/calculate/milestone", data),
  calculateTeamBonus: (data) => api.post("/bonus/calculation/calculate/team", data),
};

export const qualificationApi = {
  // 等级管理
  getLevels: (params) => api.get("/qualifications/levels", { params }),
  getLevel: (id) => api.get(`/qualifications/levels/${id}`),
  createLevel: (data) => api.post("/qualifications/levels", data),
  updateLevel: (id, data) => api.put(`/qualifications/levels/${id}`, data),
  deleteLevel: (id) => api.delete(`/qualifications/levels/${id}`),

  // 能力模型管理
  getModels: (params) => api.get("/qualifications/models", { params }),
  getModel: (positionType, levelId, params) =>
    api.get(`/qualifications/models/${positionType}/${levelId}`, { params }),
  getModelById: (id) => api.get(`/qualifications/models/${id}`),
  createModel: (data) => api.post("/qualifications/models", data),
  updateModel: (id, data) => api.put(`/qualifications/models/${id}`, data),

  // 员工任职资格
  getEmployeeQualification: (employeeId, params) =>
    api.get(`/qualifications/employees/${employeeId}`, { params }),
  getEmployeeQualifications: (params) =>
    api.get("/qualifications/employees", { params }),
  certifyEmployee: (employeeId, data) =>
    api.post(`/qualifications/employees/${employeeId}/certify`, data),
  promoteEmployee: (employeeId, data) =>
    api.post(`/qualifications/employees/${employeeId}/promote`, data),

  // 评估记录
  getAssessments: (employeeId, params) =>
    api.get(`/qualifications/assessments/${employeeId}`, { params }),
  createAssessment: (data) => api.post("/qualifications/assessments", data),
  submitAssessment: (assessmentId, data) =>
    api.post(`/qualifications/assessments/${assessmentId}/submit`, data),
};

export const timesheetApi = {
  // ========== 工时记录管理 ==========
  list: (params) => api.get("/timesheets", { params }),
  get: (id) => api.get(`/timesheets/${id}`),
  create: (data) => api.post("/timesheets", data),
  batchCreate: (data) => api.post("/timesheet/batch", data),
  update: (id, data) => api.put(`/timesheets/${id}`, data),
  delete: (id) => api.delete(`/timesheets/${id}`),

  // ========== 周工时表 ==========
  getWeek: (params) => api.get("/timesheet/week", { params }),
  submitWeek: (data) => api.post("/timesheet/week/submit", data),

  // ========== 提交与审批 ==========
  submit: (data) => api.post("/timesheet/submit", data),
  getPendingApproval: (params) =>
    api.get("/timesheet/pending-approval", { params }),
  approve: (id, data) => api.put(`/timesheets/${id}/approve`, data),
  batchApprove: (data) => api.post("/timesheet/approve", data),
  reject: (id, data) => api.post(`/timesheets/${id}/reject`, data),

  // ========== 统计汇总 ==========
  getStatistics: (params) => api.get("/timesheet/statistics", { params }),
  getMonthSummary: (params) => api.get("/timesheet/month-summary", { params }),
  getMySummary: (params) => api.get("/timesheet/my-summary", { params }),
  getDepartmentSummary: (deptId, params) =>
    api.get(`/timesheets/departments/${deptId}/timesheet-summary`, { params }),

  // ========== 数据汇总 ==========
  aggregate: (data) => api.post("/timesheet/aggregate", data),

  // ========== 报表导出 ==========
  getHrReport: (params) =>
    api.get("/timesheet/reports/hr", {
      params,
      responseType: params.format === "excel" ? "blob" : "json",
    }),
  getFinanceReport: (params) =>
    api.get("/timesheet/reports/finance", {
      params,
      responseType: params.format === "excel" ? "blob" : "json",
    }),
  getRdReport: (params) =>
    api.get("/timesheet/reports/rd", {
      params,
      responseType: params.format === "excel" ? "blob" : "json",
    }),
  getProjectReport: (params) =>
    api.get("/timesheet/reports/project", {
      params,
      responseType: params.format === "excel" ? "blob" : "json",
    }),

  // ========== 数据同步 ==========
  sync: (params) => api.post("/timesheet/sync", null, { params }),
  getSyncStatus: (timesheetId) =>
    api.get(`/timesheets/sync-status/${timesheetId}`),

  // ========== 绩效统计 ==========
  getPerformanceStats: (params) =>
    api.get("/timesheet/performance", { params }),
  getResourcePlanning: (params) =>
    api.get("/timesheet/resource-planning", { params }),
  getCostAnalysis: (params) => api.get("/timesheet/cost-analysis", { params }),

  // ========== 质量检查 ==========
  getQualityCheck: (params) => api.get("/timesheet/quality-check", { params }),
  detectAnomalies: (params) => api.get("/timesheet/anomalies", { params }),
};

export const staffMatchingApi = {
  // 标签管理
  getTags: (params) => api.get("/staff-matching/tags", { params }),
  getTagTree: (tagType) =>
    api.get("/staff-matching/tags/tree", { params: { tag_type: tagType } }),
  createTag: (data) => api.post("/staff-matching/tags", data),
  updateTag: (id, data) => api.put(`/staff-matching/tags/${id}`, data),
  deleteTag: (id) => api.delete(`/staff-matching/tags/${id}`),

  // 员工标签评估
  getEvaluations: (params) =>
    api.get("/staff-matching/evaluations", { params }),
  createEvaluation: (data) => api.post("/staff-matching/evaluations", data),
  batchCreateEvaluations: (data) =>
    api.post("/staff-matching/evaluations/batch", data),
  updateEvaluation: (id, data) =>
    api.put(`/staff-matching/evaluations/${id}`, data),
  deleteEvaluation: (id) => api.delete(`/staff-matching/evaluations/${id}`),

  // 员工档案
  getProfiles: (params) => api.get("/staff-matching/profiles", { params }),
  getProfile: (employeeId) => api.get(`/staff-matching/profiles/${employeeId}`),
  refreshProfile: (employeeId) =>
    api.post(`/staff-matching/profiles/${employeeId}/refresh`),

  // 项目绩效
  getPerformance: (params) =>
    api.get("/staff-matching/performance", { params }),
  createPerformance: (data) => api.post("/staff-matching/performance", data),
  getEmployeePerformanceHistory: (employeeId) =>
    api.get(`/staff-matching/performance/employee/${employeeId}`),

  // 人员需求
  getStaffingNeeds: (params) =>
    api.get("/staff-matching/staffing-needs", { params }),
  getStaffingNeed: (id) => api.get(`/staff-matching/staffing-needs/${id}`),
  createStaffingNeed: (data) =>
    api.post("/staff-matching/staffing-needs", data),
  updateStaffingNeed: (id, data) =>
    api.put(`/staff-matching/staffing-needs/${id}`, data),
  cancelStaffingNeed: (id) =>
    api.delete(`/staff-matching/staffing-needs/${id}`),

  // AI匹配
  executeMatching: (staffingNeedId, params) =>
    api.post(`/staff-matching/matching/execute/${staffingNeedId}`, null, {
      params,
    }),
  getMatchingResults: (staffingNeedId, requestId) =>
    api.get(`/staff-matching/matching/results/${staffingNeedId}`, {
      params: { request_id: requestId },
    }),
  acceptCandidate: (data) => api.post("/staff-matching/matching/accept", data),
  rejectCandidate: (data) => api.post("/staff-matching/matching/reject", data),
  getMatchingHistory: (params) =>
    api.get("/staff-matching/matching/history", { params }),

  // 仪表板
  getDashboard: () => api.get("/staff-matching/dashboard"),
};

export const hourlyRateApi = {
  list: (params) => api.get("/hourly-rates", { params }),
  create: (data) => api.post("/hourly-rates", data),
  get: (id) => api.get(`/hourly-rates/${id}`),
  update: (id, data) => api.put(`/hourly-rates/${id}`, data),
  delete: (id) => api.delete(`/hourly-rates/${id}`),
  getUserHourlyRate: (userId, workDate) =>
    api.get(`/hourly-rates/users/${userId}/hourly-rate`, {
      params: { work_date: workDate },
    }),
  getUsersHourlyRates: (userIds, workDate) =>
    api.post("/hourly-rates/users/batch-hourly-rates", null, {
      params: { user_ids: userIds, work_date: workDate },
    }),
  getHistory: (params) => api.get("/hourly-rates/history", { params }),
};

export const hrManagementApi = {
  // 人事事务
  transactions: {
    list: (params) => api.get("/hr/transactions", { params }),
    create: (data) => api.post("/hr/transactions", data),
    approve: (id, remark) =>
      api.put(`/hr/transactions/${id}/approve`, null, {
        params: { approval_remark: remark },
      }),
    getStatistics: (params) =>
      api.get("/hr/transactions/statistics", { params }),
  },
  // 合同管理
  contracts: {
    list: (params) => api.get("/hr/contracts", { params }),
    create: (data) => api.post("/hr/contracts", data),
    update: (id, data) => api.put(`/hr/contracts/${id}`, data),
    renew: (id, newEndDate, durationMonths) =>
      api.post(`/hr/contracts/${id}/renew`, null, {
        params: { new_end_date: newEndDate, duration_months: durationMonths },
      }),
    getExpiring: (days) =>
      api.get("/hr/contracts/expiring", { params: { days } }),
  },
  // 合同提醒
  contractReminders: {
    list: (params) => api.get("/hr/contract-reminders", { params }),
    handle: (id, action, remark) =>
      api.put(`/hr/contract-reminders/${id}/handle`, null, {
        params: { action, remark },
      }),
    generate: () => api.post("/hr/contract-reminders/generate"),
  },
  // 仪表板
  dashboard: {
    getOverview: () => api.get("/hr/dashboard/overview"),
    getPendingConfirmations: () =>
      api.get("/hr/dashboard/pending-confirmations"),
  },
};
