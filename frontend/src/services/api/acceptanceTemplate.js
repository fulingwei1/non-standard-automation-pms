import { api } from "./client.js";

export const acceptanceTemplateApi = {
  list: (params) => api.get("/acceptance/templates", { params }),
  create: (data) => api.post("/acceptance/templates", data),
};
