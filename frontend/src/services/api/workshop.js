import { productionApi } from "./production.js";

export const workshopApi = {
  list: productionApi.workshops.list,
  get: productionApi.workshops.get,
  create: productionApi.workshops.create,
  update: productionApi.workshops.update,
  getWorkstations: productionApi.workshops.getWorkstations,
  addWorkstation: productionApi.workshops.addWorkstation,
};
