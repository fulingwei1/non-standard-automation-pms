import { api } from "./client.js";

export const supplierPriceTrendApi = {
  getTrends: () => api.get("/supplier-price/trends"),
  getComparison: () => api.get("/supplier-price/comparison"),
  getVolatility: (params) => api.get("/supplier-price/volatility", { params }),
};
