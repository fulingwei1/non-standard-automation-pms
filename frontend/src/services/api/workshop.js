import { api } from "./client.js";

export const workshopApi = {
  list: (params) => api.get("/production/workshops", { params }),
  create: (data) => api.post("/production/workshops", data),
};
