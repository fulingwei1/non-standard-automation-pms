import { api } from "./client.js";
export const quoteCompareApi = {
  list: () => api.get("/quote-compare/list"),
  detail: (projectId) => api.get(`/quote-compare/${projectId}`),
};
