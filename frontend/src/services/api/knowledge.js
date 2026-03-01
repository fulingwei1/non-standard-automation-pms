import { api } from "./client.js";

export const knowledgeApi = {
  list: (params) => api.get("/knowledge-base", { params }),
  getCategories: () => api.get("/knowledge-base/categories"),
  create: (data) => api.post("/knowledge-base", data),
};
