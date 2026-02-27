import { api } from "./client.js";



export const presaleApi = {
  tickets: {
    list: (params) => api.get("/presale/tickets", { params }),
    get: (id) => api.get(`/presale/tickets/${id}`),
    create: (data) => api.post("/presale/tickets", data),
    update: (id, data) => api.put(`/presale/tickets/${id}`, data),
    accept: (id, data) => api.put(`/presale/tickets/${id}/accept`, data),
    updateProgress: (id, data) =>
      api.put(`/presale/tickets/${id}/progress`, data),
    complete: (id, data) => api.put(`/presale/tickets/${id}/complete`, data),
    rate: (id, data) => api.put(`/presale/tickets/${id}/rating`, data),
    getBoard: (params) => api.get("/presale/tickets/board", { params }),
  },
  solutions: {
    list: (params) => api.get("/presale/proposals/solutions", { params }),
    get: (id) => api.get(`/presale/proposals/solutions/${id}`),
    create: (data) => api.post("/presale/proposals/solutions", data),
    update: (id, data) => api.put(`/presale/proposals/solutions/${id}`, data),
    review: (id, data) => api.put(`/presale/proposals/solutions/${id}/review`, data),
    getVersions: (id) => api.get(`/presale/proposals/solutions/${id}/versions`),
    getCost: (id) => api.get(`/presale/proposals/solutions/${id}/cost`),
  },
  templates: {
    list: (params) => api.get("/presale/templates", { params }),
    get: (id) => api.get(`/presale/templates/${id}`),
    create: (data) => api.post("/presale/templates", data),
    update: (id, data) => api.put(`/presale/templates/${id}`, data),
  },
  tenders: {
    list: (params) => api.get("/presale/tenders", { params }),
    get: (id) => api.get(`/presale/tenders/${id}`),
    create: (data) => api.post("/presale/tenders", data),
    update: (id, data) => api.put(`/presale/tenders/${id}`, data),
    updateResult: (id, data) => api.put(`/presale/tenders/${id}/result`, data),
  },
  statistics: {
    workload: (params) => api.get("/presale/statistics/stats/workload", { params }),
    responseTime: (params) =>
      api.get("/presale/statistics/stats/response-time", { params }),
    conversion: (params) => api.get("/presale/statistics/stats/conversion", { params }),
    performance: (params) => api.get("/presale/statistics/stats/performance", { params }),
  },
};

export const presalesIntegrationApi = {
  // 线索转项目
  createProjectFromLead: (data) => api.post("/presales/from-lead", data),

  // 中标率预测
  predictWinRate: (data) => api.post("/presales/predict-win-rate", data),

  // 资源投入分析
  getLeadResourceInvestment: (leadId) =>
    api.get(`/presales/lead/${leadId}/resource-investment`),

  // 资源浪费分析
  getResourceWasteAnalysis: (period) =>
    api.get("/presales/resource-waste-analysis", { params: { period } }),

  // 销售人员绩效
  getSalespersonPerformance: (salespersonId, period) =>
    api.get(`/presales/salesperson/${salespersonId}/performance`, {
      params: { period },
    }),
  getSalespersonRanking: (rankingType, period, limit) =>
    api.get("/presales/salesperson-ranking", {
      params: { ranking_type: rankingType, period, limit },
    }),

  // 仪表板
  getDashboard: () => api.get("/presales/dashboard"),
};

export const advantageProductApi = {
  // 类别
  getCategories: (includeInactive = false) =>
    api.get("/advantage-products/categories", {
      params: { include_inactive: includeInactive },
    }),
  createCategory: (data) => api.post("/advantage-products/categories", data),
  updateCategory: (id, data) =>
    api.put(`/advantage-products/categories/${id}`, data),

  // 产品列表
  getProducts: (params) => api.get("/advantage-products", { params }),
  getProductsGrouped: (includeInactive = false) =>
    api.get("/advantage-products/grouped", {
      params: { include_inactive: includeInactive },
    }),
  getProductsSimple: (categoryId) =>
    api.get("/advantage-products/simple", {
      params: { category_id: categoryId },
    }),

  // 产品 CRUD
  createProduct: (data) => api.post("/advantage-products", data),
  updateProduct: (id, data) => api.put(`/advantage-products/${id}`, data),
  deleteProduct: (id) => api.delete(`/advantage-products/${id}`),

  // Excel 导入
  importFromExcel: (file, clearExisting = true) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/advantage-products/import", formData, {
      params: { clear_existing: clearExisting },
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 产品匹配检查
  checkMatch: (productName) =>
    api.post("/advantage-products/check-match", { product_name: productName }),
};
