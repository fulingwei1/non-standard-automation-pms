import { api } from "./client.js";

export const marginPredictionApi = {
  historical: () => api.get("/margin-prediction/historical"),
  predict: (params) => api.get("/margin-prediction/predict", { params }),
  variance: () => api.get("/margin-prediction/variance"),
};

