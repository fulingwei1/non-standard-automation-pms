import { api } from "./client.js";

export const customerServiceApi = {
  getDashboard: (params) => api.get("/service/dashboard-statistics", { params }),
};
