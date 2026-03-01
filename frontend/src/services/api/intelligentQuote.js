import { api } from "./client.js";

export const intelligentQuoteApi = {
  // 获取历史价格
  getHistoricalPrices: (productCategory) =>
    api.get("/intelligent-quote/historical-prices", { params: { productCategory } }),
};
