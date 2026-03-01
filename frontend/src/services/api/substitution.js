import { api } from "./client.js";

export const substitutionApi = {
  get: (id) => api.get(`/shortage/handling/substitutions/${id}`),
  approve: (id, data = {}) =>
    api.put(`/shortage/handling/substitutions/${id}/prod-approve`, {
      approved: true,
      ...data,
    }),
};
