import { api } from "./client.js";



export const workloadApi = {
  user: (userId, params) => api.get(`/workload/user/${userId}`, { params }),
  team: (params) => api.get("/workload/team", { params }),
  dashboard: (params) => api.get("/workload/dashboard", { params }),
  heatmap: (params) => api.get("/workload/heatmap", { params }),
  availableResources: (params) =>
    api.get("/workload/available-resources", { params }),
  gantt: (params) => api.get("/workload/gantt", { params }),
};
