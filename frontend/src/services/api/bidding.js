import { api } from "./client.js";

export const biddingApi = {
  list: (params) => api.get("/sales/biddings", { params }),
  get: (id) => api.get(`/sales/biddings/${id}`),
  create: (data) => api.post("/sales/biddings", data),
  submit: (id) => api.post(`/sales/biddings/${id}/submit`),
  submitBid: (id, data) => api.post(`/sales/biddings/${id}/bid`, data),
};
