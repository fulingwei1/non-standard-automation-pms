import { api } from "./client.js";

/**
 * Inventory Management API
 *
 * Covers all endpoints under /api/v1/inventory:
 *   stocks        — GET  /inventory/stocks
 *   transactions  — GET  /inventory/stocks/{materialId}/transactions
 *   operations    — POST /inventory/issue | /inventory/return | /inventory/transfer
 *   reservations  — POST /inventory/reserve
 *   analysis      — GET  /inventory/analysis/turnover | /inventory/analysis/aging
 *   stockCount    — CRUD /inventory/count/tasks | /inventory/count/details
 */
export const inventoryApi = {
  // ── Stocks ──────────────────────────────────────────────────────────────
  stocks: {
    /**
     * List all stocks.
     * @param {Object} params - Optional filters: material_id, location, status
     */
    list: (params) => api.get("/inventory/stocks", { params }),

    /**
     * Get stock records for a specific material (optionally filtered by location).
     * @param {number} materialId
     * @param {string} [location]
     */
    getByMaterial: (materialId, location) =>
      api.get("/inventory/stocks", {
        params: { material_id: materialId, ...(location ? { location } : {}) },
      }),
  },

  // ── Transactions ─────────────────────────────────────────────────────────
  transactions: {
    /**
     * List transaction history for a material.
     * @param {number} materialId
     * @param {Object} params - Optional filters: transaction_type, start_date, end_date, limit
     */
    list: (materialId, params) =>
      api.get(`/inventory/stocks/${materialId}/transactions`, { params }),
  },

  // ── Operations ───────────────────────────────────────────────────────────
  operations: {
    /**
     * Issue material out of stock (领料出库).
     * @param {Object} data - IssueMaterialRequest:
     *   material_id, quantity, location, work_order_id?, work_order_no?,
     *   project_id?, reservation_id?, cost_method?, remark?
     */
    issue: (data) => api.post("/inventory/issue", data),

    /**
     * Return material back to stock (退料入库).
     * @param {Object} data - ReturnMaterialRequest:
     *   material_id, quantity, location, batch_number?, work_order_id?, remark?
     */
    return: (data) => api.post("/inventory/return", data),

    /**
     * Transfer stock between locations (库存转移).
     * @param {Object} data - TransferStockRequest:
     *   material_id, quantity, from_location, to_location, batch_number?, remark?
     */
    transfer: (data) => api.post("/inventory/transfer", data),
  },

  // ── Reservations ─────────────────────────────────────────────────────────
  reservations: {
    /**
     * Reserve material for a project or work order (预留物料).
     * @param {Object} data - ReserveMaterialRequest:
     *   material_id, quantity, project_id?, work_order_id?,
     *   expected_use_date?, remark?
     */
    create: (data) => api.post("/inventory/reserve", data),
  },

  // ── Analysis ─────────────────────────────────────────────────────────────
  analysis: {
    /**
     * Inventory turnover rate analysis (库存周转率分析).
     * @param {Object} params - Optional: material_id, start_date, end_date
     */
    turnoverRate: (params) => api.get("/inventory/analysis/turnover", { params }),

    /**
     * Inventory aging analysis (库龄分析).
     * Buckets: 0-30d, 31-90d, 91-180d, 181-365d, >365d
     * @param {Object} params - Optional: location
     */
    aging: (params) => api.get("/inventory/analysis/aging", { params }),
  },

  // ── Stock Count ───────────────────────────────────────────────────────────
  stockCount: {
    /**
     * List stock count tasks (盘点任务列表).
     * @param {Object} params - Optional: status, start_date, end_date, limit
     */
    listTasks: (params) => api.get("/inventory/count/tasks", { params }),

    /**
     * Create a new stock count task (创建盘点任务).
     * @param {Object} data - CreateCountTaskRequest:
     *   count_type (FULL|PARTIAL|CYCLE), count_date, location?,
     *   category_id?, material_ids?, assigned_to?, remark?
     */
    createTask: (data) => api.post("/inventory/count/tasks", data),

    /**
     * Get the detail lines for a count task (盘点明细列表).
     * @param {number} taskId
     */
    getDetails: (taskId) =>
      api.get(`/inventory/count/tasks/${taskId}/details`),

    /**
     * Record actual counted quantity for a detail line (录入实盘数量).
     * @param {number} detailId
     * @param {Object} data - RecordActualQuantityRequest: actual_quantity, remark?
     */
    recordActualQuantity: (detailId, data) =>
      api.put(`/inventory/count/details/${detailId}`, data),

    /**
     * Approve a count task and optionally apply stock adjustments (批准盘点调整).
     * @param {number} taskId
     * @param {boolean} [autoAdjust=true] - Whether to automatically apply adjustments
     */
    approveTask: (taskId, autoAdjust = true) =>
      api.post(`/inventory/count/tasks/${taskId}/approve`, null, {
        params: { auto_adjust: autoAdjust },
      }),
  },
};
