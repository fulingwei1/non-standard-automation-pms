import { api } from "./client.js";

export const communicationApi = {
  list: (params) => api.get("/customer-communications", { params }),
  create: (data) => api.post("/customer-communications", data),
};
