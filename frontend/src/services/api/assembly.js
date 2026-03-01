import { api } from "./client.js";

export const assemblyApi = {
  listKits: (params) => api.get("/assembly/projects/readiness", { params }),
  analyzeKit: (machineId) =>
    api.post("/assembly/analysis", {
      machine_id: machineId,
    }),
};
