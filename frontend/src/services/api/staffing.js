import { api } from "./client.js";

export const staffingApi = {
  listNeeds: (params) => api.get("/staff-matching/staffing-needs", { params }),
  assign: (needId, data) => api.post(`/staff-matching/staffing-needs/${needId}/assign`, data),
};
