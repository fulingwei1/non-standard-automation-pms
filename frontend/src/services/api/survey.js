import { api } from "./client.js";

export const surveyApi = {
  list: (params) => api.get("/requirement-surveys", { params }),
  create: (data) => api.post("/requirement-surveys", data),
  update: (id, data) => api.put(`/requirement-surveys/${id}`, data),
  submit: (id) => api.post(`/requirement-surveys/${id}/submit`),
};
