import { api } from "./client.js";

export const dependencyApi = {
  list: (params) => api.get("/dependencies", { params }),
  check: (projectId) => api.get(`/dependencies/${projectId}/check`),
};
