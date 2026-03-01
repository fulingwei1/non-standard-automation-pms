import { api } from "./client.js";

export const staffApi = {
  list: (params) => api.get("/staff-matching/profiles", { params }),
  aiMatch: (data) => api.post("/staff-matching/matching/execute", data),
  assign: (projectId, data) => api.post(`/projects/${projectId}/staff-assignments`, data),
};
