/**
 * @deprecated This file is superseded by `procurement.js`.
 *
 * All functionality here is available via `purchaseApi.requests` exported
 * from `./procurement.js`. Import from there instead:
 *
 *   import { purchaseApi } from "./procurement.js";
 *   purchaseApi.requests.list(params)
 *   purchaseApi.requests.create(data)
 *   purchaseApi.requests.submit(id)
 *   // etc.
 *
 * Note: `getMaterials` (GET /purchase-orders/requests/materials) is not
 * currently present in `procurement.js`; add it there if needed.
 *
 * This file is kept only for backward compatibility and will be removed
 * in a future cleanup pass.
 */
import { api } from "./client.js";

export const purchaseRequestApi = {
  getMaterials: (projectId) =>
    api.get("/purchase-orders/requests/materials", { params: { project_id: projectId } }),
  create: (data) => api.post("/purchase-orders/requests", data),
  get: (id) => api.get(`/purchase-orders/requests/${id}`),
  update: (id, data) => api.put(`/purchase-orders/requests/${id}`, data),
  submit: (id) => api.put(`/purchase-orders/requests/${id}/submit`),
};
