import { api } from "./client.js";

export const knowledgeBaseApi = {
  listArticles: (params) => api.get("/knowledge-base", { params }),
  getCategories: () => api.get("/knowledge-base/categories"),
};
