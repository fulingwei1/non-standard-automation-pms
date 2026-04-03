/**
 * @deprecated This file is superseded by `procurement.js`.
 *
 * The single method here (`create`) is available via `purchaseApi.receipts.create`
 * exported from `./procurement.js`. Import from there instead:
 *
 *   import { purchaseApi } from "./procurement.js";
 *   purchaseApi.receipts.create(data)
 *
 * `procurement.js` also provides `receipts.list`, `receipts.get`,
 * `receipts.getItems`, `receipts.receive`, and `receipts.inspectItem`.
 *
 * This file is kept only for backward compatibility and will be removed
 * in a future cleanup pass.
 */
import { api } from "./client.js";

export const goodsReceiptApi = {
  create: (data) => api.post("/purchase-orders/goods-receipts", data),
};
