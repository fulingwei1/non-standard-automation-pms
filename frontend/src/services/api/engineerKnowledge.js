import { api } from "./client.js";

export const engineerKnowledgeApi = {
  list: (params) => api.get("/engineer-performance/knowledge", { params }),
};
