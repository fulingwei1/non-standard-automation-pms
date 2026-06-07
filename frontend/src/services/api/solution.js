import { presaleSolutionApi } from "./presaleSolution.js";

export const solutionApi = {
  list: (params) => presaleSolutionApi.list(params),
};
