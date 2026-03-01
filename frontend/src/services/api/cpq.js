import { api } from "./client.js";

export const cpqApi = {
  getRules: (params) => api.get("/sales/cpq/rule-sets", { params }),
  calculatePrice: (data) => api.post("/sales/cpq/price-preview", data),
};
