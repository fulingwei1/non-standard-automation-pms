import { api } from "./client.js";

export const projectSettlementApi = {
  list: (params) => api.get("/projects/settlements", { params }),
  submit: (data) => api.post("/projects/settlements", data),
};
