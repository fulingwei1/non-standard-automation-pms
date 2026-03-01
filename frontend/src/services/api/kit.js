import { api } from "./client.js";

export const kitApi = {
  list: (params) => api.get("/kit-checks", { params }),
};
