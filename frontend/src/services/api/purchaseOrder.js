/**
 * @deprecated This file is superseded by `procurement.js`.
 *
 * All functionality here is available via `purchaseApi.orders` (and the
 * top-level convenience methods on `purchaseApi`) exported from
 * `./procurement.js`. Import from there instead:
 *
 *   import { purchaseApi } from "./procurement.js";
 *   purchaseApi.orders.list(params)
 *   purchaseApi.orders.submit(id)
 *   // etc.
 *
 * This file is kept only for backward compatibility and will be removed
 * in a future cleanup pass.
 */
import { api } from "./client.js";

export const purchaseOrderApi = {
  list: (params) => api.get("/purchase-orders", { params }),
  get: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post("/purchase-orders", data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),
  submit: (id) => api.put(`/purchase-orders/${id}/submit`),
  cancel: (id) => api.put(`/purchase-orders/${id}/cancel`),
  addItem: (id, data) => api.post(`/purchase-orders/${id}/items`, data),
  getPending: (params) => api.get("/purchase-orders/pending", { params }),
};
