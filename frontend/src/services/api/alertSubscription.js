import { api } from "./client.js";

export const alertSubscriptionApi = {
  list: (params) => api.get("/alerts/subscriptions", { params }),
  update: (id, data) => api.put(`/alerts/subscriptions/${id}`, data),
};
