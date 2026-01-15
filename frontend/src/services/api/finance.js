import { api } from "./client.js";

const safeGet = async (url, config = {}, fallbackData = []) => {
  try {
    return await api.get(url, config);
  } catch (_error) {
    return { data: fallbackData };
  }
};

const safePut = async (url, data, config = {}, fallbackData = null) => {
  try {
    return await api.put(url, data, config);
  } catch (_error) {
    return { data: fallbackData };
  }
};

export const financeApi = {
  list: (params) => safeGet("/finance/transactions", { params }, []),
  updateStatus: (id, data) =>
    safePut(`/finance/transactions/${id}/status`, data, {}, null),
};

