import { api } from "./client.js";

export const arrivalApi = {
  get: (id) => api.get(`/shortage/handling/arrivals/${id}`),
  updateStatus: (id, status) =>
    api.put(`/shortage/handling/arrivals/${id}/status`,
      typeof status === "object" ? status : { status }),
};
