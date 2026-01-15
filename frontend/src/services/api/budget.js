import { api } from "./client.js";

export const budgetApi = {
  list: (params) => api.get("/budgets/", { params }),
};

