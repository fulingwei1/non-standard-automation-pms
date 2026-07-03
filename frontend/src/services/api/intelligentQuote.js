import { api } from "./client.js";

export const intelligentQuoteApi = {
  // 获取历史价格
  getHistoricalPrices: (productCategory) =>
    api.get("/sales/quotes/historical-prices", {
      params: { product_category: productCategory },
    }),
};
