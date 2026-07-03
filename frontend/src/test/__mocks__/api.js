/**
 * Global API mocks for all services
 * This file provides comprehensive mocks for all API modules used in tests
 */

import { vi } from 'vitest';

// Payment API mock
export const paymentApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  matchInvoice: vi.fn(),
  getReminders: vi.fn(),
  getStatistics: vi.fn(),
  exportInvoices: vi.fn(),
};

// Receivable API mock
export const receivableApi = {
  list: vi.fn(),
  get: vi.fn(),
  getOverdue: vi.fn(),
  getAging: vi.fn(),
  getSummary: vi.fn(),
};

export const paymentPlanApi = {
  list: vi.fn(),
};

// PMO API mock - has nested structures
export const pmoApi = {
  dashboard: vi.fn(),
  weeklyReport: vi.fn(),
  resourceOverview: vi.fn(),
  riskWall: vi.fn(),
  initiations: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
  },
  phases: {
    list: vi.fn(),
    entryCheck: vi.fn(),
    exitCheck: vi.fn(),
    review: vi.fn(),
    advance: vi.fn(),
  },
  risks: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  milestones: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  deliverables: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  closures: {
    create: vi.fn(),
    get: vi.fn(),
    review: vi.fn(),
    updateLessons: vi.fn(),
    checkReadiness: vi.fn(),
    checkReadinessCustom: vi.fn(),
    notifyReadiness: vi.fn(),
  },
  approvals: {
    list: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
  },
  notifications: {
    list: vi.fn(),
    send: vi.fn(),
  },
};

// Project API mock
export const projectApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  query: vi.fn(),
  getByCustomer: vi.fn(),
  getSummary: vi.fn(),
  getStatistics: vi.fn(),
  export: vi.fn(),
};

// Progress API mock - has nested structures
export const progressApi = {
  reports: {
    getSummary: vi.fn(),
    getTrend: vi.fn(),
    getByProject: vi.fn(),
  },
  tasks: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    assign: vi.fn(),
  },
  milestones: {
    list: vi.fn(),
    update: vi.fn(),
  },
};

// Timesheet API mock
export const timesheetApi = {
  getWeek: vi.fn(),
  submit: vi.fn(),
  approve: vi.fn(),
  reject: vi.fn(),
  getHistory: vi.fn(),
  getStatistics: vi.fn(),
};

// HR API mock
export const hrApi = {
  getEmployees: vi.fn(),
  getEmployee: vi.fn(),
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  deleteEmployee: vi.fn(),
  getDepartments: vi.fn(),
  getPositions: vi.fn(),
  getAttendance: vi.fn(),
  getLeaveRequests: vi.fn(),
  approveLeave: vi.fn(),
  rejectLeave: vi.fn(),
};

// Auth API mock
export const authApi = {
  login: vi.fn(),
  me: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
  changePassword: vi.fn(),
  getPermissions: vi.fn(),
};

// Sales API mock
export const salesApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getStatistics: vi.fn(),
  getPipeline: vi.fn(),
  convertToProject: vi.fn(),
};

// Customer API mock
export const customerApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getContacts: vi.fn(),
  getActivities: vi.fn(),
};

// Contract API mock
export const contractApi = {
  list: vi.fn(),
  get: vi.fn(),
  getPaymentPlans: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getItems: vi.fn(),
  sign: vi.fn(),
  terminate: vi.fn(),
};

// Supplier API mock
export const supplierApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getMaterials: vi.fn(),
  evaluate: vi.fn(),
};

// Material API mock
export const materialApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getStock: vi.fn(),
  transfer: vi.fn(),
};

// Inventory API mock
export const inventoryApi = {
  list: vi.fn(),
  get: vi.fn(),
  getStockLevels: vi.fn(),
  getMovements: vi.fn(),
  adjust: vi.fn(),
  audit: vi.fn(),
};

// Production API mock
export const productionApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  start: vi.fn(),
  pause: vi.fn(),
  complete: vi.fn(),
  getProgress: vi.fn(),
};

// Quality API mock
export const qualityApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  approve: vi.fn(),
  reject: vi.fn(),
};

// Engineering API mock
export const engineeringApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getBom: vi.fn(),
  updateBom: vi.fn(),
};

// Purchase API mock
export const purchaseApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  approve: vi.fn(),
  reject: vi.fn(),
  receive: vi.fn(),
};

// Purchase Order API mock
export const purchaseOrderApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  submit: vi.fn(),
  cancel: vi.fn(),
};

// Work Order API mock
export const workOrderApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  start: vi.fn(),
  complete: vi.fn(),
  cancel: vi.fn(),
};

// Machine API mock
export const machineApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getStatus: vi.fn(),
};

// Workshop API mock
export const workshopApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getUtilization: vi.fn(),
};

// Admin API mock
export const adminApi = {
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  getStatistics: vi.fn(),
};

// Export all mocks as default
export default {
  paymentApi,
  receivableApi,
  paymentPlanApi,
  pmoApi,
  projectApi,
  progressApi,
  timesheetApi,
  hrApi,
  authApi,
  salesApi,
  customerApi,
  contractApi,
  supplierApi,
  materialApi,
  inventoryApi,
  productionApi,
  qualityApi,
  engineeringApi,
  purchaseApi,
  purchaseOrderApi,
  workOrderApi,
  machineApi,
  workshopApi,
  adminApi,
};
