import { api } from "./client.js";

export const ganttDependencyApi = {
  getGantt: (projectId) => api.get(`/gantt/${projectId}`),
  createDependency: (projectId, data) =>
    api.post(`/gantt/${projectId}/dependency`, data),
  deleteDependency: (dependencyId) =>
    api.delete(`/gantt/dependency/${dependencyId}`),
  getCriticalPath: (projectId) => api.get(`/gantt/${projectId}/critical-path`),
};
