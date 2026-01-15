import { api } from "./client.js";

const safeDelete = async (url, config = {}, fallbackData = null) => {
  try {
    return await api.delete(url, config);
  } catch (_error) {
    return { data: fallbackData };
  }
};

export const customerCommunicationApi = {
  list: (params) => api.get("/customer-communications", { params }),
  get: (id) => api.get(`/customer-communications/${id}`),
  create: (data) => api.post("/customer-communications", data),
  update: (id, data) => api.put(`/customer-communications/${id}`, data),
  delete: (id) => safeDelete(`/customer-communications/${id}`),
  statistics: () => api.get("/customer-communications/statistics"),
};

