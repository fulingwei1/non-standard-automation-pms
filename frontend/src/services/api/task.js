import { api } from "./client.js";

export const taskApi = {
  getMyTasks: (params) => api.get("/tasks/my", { params }),
  getTeamTasks: (params) => api.get("/tasks/team", { params }),
  updateStatus: (taskId, data) => api.put(`/tasks/${taskId}/status`, data),
  assign: (taskId, data) => api.put(`/tasks/${taskId}/assign`, data),
};
