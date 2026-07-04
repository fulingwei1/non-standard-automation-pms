import { api } from "./client.js";

export const resourceOverviewApi = {
  list: (params) => api.get("/pmo/resource-overview", { params }),
};
