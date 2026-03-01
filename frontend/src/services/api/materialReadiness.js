import { api } from "./client.js";

export const materialReadinessApi = {
  list: (params) => api.get("/assembly/material-readiness", { params }),
};
