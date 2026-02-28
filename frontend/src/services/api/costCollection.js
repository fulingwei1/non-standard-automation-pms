import { api } from "./client.js";

export const costCollectionApi = {
  collect: (params) => api.post("/cost-collection/collect", null, { params }),
  status: () => api.get("/cost-collection/status"),
  byProject: () => api.get("/cost-collection/by-project"),
};
