import { api } from "./client.js";

export const solutionApi = {
  list: (params) => api.get("/presales/solutions", { params }),
};
