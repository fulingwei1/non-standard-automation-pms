import { api } from "./client.js";

export const resourceOverviewApi = {
  list: (params) => api.get("/resource-overview/", { params }),
  departments: () => api.get("/resource-overview/departments"),
  timeline: (params) => api.get("/resource-overview/timeline", { params }),
};
