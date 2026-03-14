import { productionApi } from "./production.js";

export const workerApi = {
  list: productionApi.workers.list,
  get: productionApi.workers.get,
  create: productionApi.workers.create,
  update: productionApi.workers.update,
};
