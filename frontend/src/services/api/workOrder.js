import { productionApi } from "./production.js";

export const workOrderApi = {
  list: productionApi.workOrders.list,
  get: productionApi.workOrders.get,
  create: productionApi.workOrders.create,
  update: productionApi.workOrders.update,
  assign: productionApi.workOrders.assign,
  start: productionApi.workOrders.start,
  pause: productionApi.workOrders.pause,
  resume: productionApi.workOrders.resume,
  complete: productionApi.workOrders.complete,
  getProgress: productionApi.workOrders.getProgress,
  getReports: productionApi.workOrders.getReports,
};
