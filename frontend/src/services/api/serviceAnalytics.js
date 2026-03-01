import { api } from "./client.js";

export const serviceAnalyticsApi = {
  getData: (params) => api.get("/service/analytics", { params }),
};
