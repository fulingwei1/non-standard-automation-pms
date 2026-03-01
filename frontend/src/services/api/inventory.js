import { api } from "./client.js";

export const inventoryApi = {
  list: (params) => api.get("/inventory-analysis", { params }),
};
