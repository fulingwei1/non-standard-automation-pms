import { api } from "./client.js";

export const reportApi = {
  listFinancial: (params) => api.get("/reports/financial", { params }),
  generateFinancial: (type, params) =>
    api.post("/reports/financial/generate", {
      report_type: type,
      ...params,
    }),
  exportFinancial: (id, format = "excel") =>
    api.get(`/reports/financial/${id}/export`, {
      params: { format },
      responseType: "blob",
    }),
};
