import { api } from "./client.js";

export const workerApi = {
  list: (params) => api.get("/workers", { params }),
};
