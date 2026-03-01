import { api } from "./client.js";

export const goodsReceiptApi = {
  create: (data) => api.post("/purchase-orders/goods-receipts", data),
};
