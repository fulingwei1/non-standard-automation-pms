import { api } from "./client.js";

export const quotationApi = {
  list: (params) => api.get("/sales/quotations", { params }),
  create: (data) => api.post("/sales/quotations", data),
  duplicate: (id) => api.post(`/sales/quotations/${id}/duplicate`),
};
