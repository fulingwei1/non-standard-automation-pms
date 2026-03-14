import { api } from "./client.js";

const unwrap = (response) => response?.data?.data ?? response?.data ?? response;

const normalizeOverallResult = (value) => {
  const map = {
    PASS: "PASSED",
    FAIL: "FAILED",
    CONDITIONAL: "CONDITIONAL",
    PASSED: "PASSED",
    FAILED: "FAILED",
  };
  return map[value] || value;
};

const normalizeLegacyOrder = (order = {}) => ({
  ...order,
  title: order.title || order.order_no || `验收单 #${order.id}`,
  scheduled_date: order.scheduled_date || order.planned_date || null,
  project_name: order.project_name || "",
  customer_name: order.customer_name || order.project_name || "",
  progress:
    order.progress ??
    (order.total_items
      ? Math.round(
          (((order.passed_items || 0) + (order.failed_items || 0) + (order.na_items || 0)) /
            order.total_items) *
            100,
        )
      : 0),
});

const mapTemplateFormToPayload = (data = {}) => {
  const timestamp = Date.now().toString().slice(-8);
  const templateName = (data.template_name || "未命名模板").trim();
  const categoryName = (data.category || data.equipment_type || "默认分类").trim();

  return {
    template_code:
      data.template_code ||
      `TPL_${(data.template_type || data.acceptance_type || "FAT").toUpperCase()}_${timestamp}`,
    template_name: templateName,
    acceptance_type: data.acceptance_type || data.template_type || "FAT",
    equipment_type: data.equipment_type || data.category || null,
    version: data.version || "1.0",
    description: data.description || "",
    categories: [
      {
        category_code: data.category_code || "DEFAULT",
        category_name: categoryName,
        weight: 100,
        sort_order: 1,
        is_required: true,
        description: `${templateName}默认检查分类`,
        check_items: [],
      },
    ],
  };
};

const mapIssueCreatePayload = (orderId, data = {}) => ({
  order_id: Number(orderId),
  order_item_id: data.item_id || data.order_item_id || null,
  issue_type: data.issue_type || (data.category ? "DEVIATION" : "DEFECT"),
  severity: data.severity || "MINOR",
  title:
    data.title ||
    data.item_name ||
    data.category ||
    (data.description ? data.description.slice(0, 50) : "验收问题"),
  description: data.description || data.remark || "",
  is_blocking: Boolean(data.is_blocking),
  assigned_to: data.assigned_to || null,
  due_date: data.due_date || null,
  attachments: data.photos || data.attachments || [],
});

const mapTemplateItemPayload = (item = {}) => ({
  item_code: item.item_code || `ITEM_${Date.now().toString().slice(-6)}`,
  item_name: item.item_name,
  check_method: item.check_method || item.category_name || null,
  acceptance_criteria: item.acceptance_criteria || null,
  standard_value: item.standard_value || null,
  tolerance_min: item.tolerance_min || null,
  tolerance_max: item.tolerance_max || null,
  unit: item.unit || null,
  is_required: item.is_required ?? true,
  is_key_item: item.is_key_item ?? false,
  sort_order: item.sort_order ?? 0,
});

export const acceptanceApi = {
  orders: {
    list: (params = {}) =>
      api.get("/acceptance-orders", {
        params: {
          ...params,
          keyword: params.keyword || params.search || undefined,
          acceptance_type:
            params.acceptance_type ||
            (params.template_type && params.template_type !== "all"
              ? params.template_type
              : undefined),
          project_id:
            params.project_id && params.project_id !== "all"
              ? params.project_id
              : undefined,
          status:
            params.status && params.status !== "all" ? params.status : undefined,
        },
      }),
    get: (id) => api.get(`/acceptance-orders/${id}`),
    create: (data) => api.post("/acceptance-orders", data),
    update: (id, data) => api.put(`/acceptance-orders/${id}`, data),
    start: (id, data = {}) => api.put(`/acceptance-orders/${id}/start`, data),
    complete: (id, data = {}) =>
      api.put(`/acceptance-orders/${id}/complete`, {
        ...data,
        overall_result: normalizeOverallResult(data.overall_result),
      }),
    getItems: (id) => api.get(`/acceptance-orders/${id}/items`),
    updateItem: (itemId, data) => api.put(`/acceptance-items/${itemId}`, data),
    submit: (id) => api.post(`/acceptance-orders/${id}/submit`),
  },

  issues: {
    list: (orderIdOrParams) => {
      const params =
        typeof orderIdOrParams === "object"
          ? orderIdOrParams
          : { order_id: orderIdOrParams };
      return api.get("/acceptance-issues", { params });
    },
    create: (orderId, data) =>
      api.post("/acceptance-issues", mapIssueCreatePayload(orderId, data)),
  },

  templates: {
    list: (params = {}) =>
      api.get("/acceptance-templates", {
        params: {
          ...params,
          keyword: params.keyword || params.search || undefined,
          acceptance_type:
            params.acceptance_type ||
            (params.template_type && params.template_type !== "all"
              ? params.template_type
              : undefined),
        },
      }),
    get: (id) => api.get(`/acceptance-templates/${id}`),
    create: (data) => api.post("/acceptance-templates", mapTemplateFormToPayload(data)),
    update: (id, data) => api.put(`/acceptance-templates/${id}`, data),
    getItems: (id) => api.get(`/acceptance-templates/${id}/items`),
    addItems: async (id, payload = {}) => {
      let categoryId = payload.category_id;
      if (!categoryId) {
        const detail = unwrap(await api.get(`/acceptance-templates/${id}`));
        categoryId = detail?.categories?.[0]?.id;
      }
      if (!categoryId) {
        throw new Error("模板缺少可用分类，无法新增检查项");
      }
      return api.post(
        `/acceptance-templates/${id}/items`,
        (payload.items || []).map(mapTemplateItemPayload),
        {
          params: { category_id: categoryId },
        },
      );
    },
  },

  // 兼容旧页面
  list: async (params = {}) => {
    const response = await acceptanceApi.orders.list(params);
    const data = unwrap(response);
    const items = data?.items || [];
    return {
      ...response,
      data: {
        ...data,
        items: items.map(normalizeLegacyOrder),
      },
    };
  },
  detail: async (id) => {
    const response = await acceptanceApi.orders.get(id);
    const data = unwrap(response);
    return { ...response, data: normalizeLegacyOrder(data) };
  },
  create: (data) =>
    acceptanceApi.orders.create({
      project_id: data.project_id,
      machine_id: data.machine_id || null,
      acceptance_type: data.acceptance_type || data.type || "FAT",
      template_id: data.template_id || null,
      planned_date: data.planned_date || data.scheduled_date || null,
      location: data.location || null,
    }),
  update: (id, data) =>
    acceptanceApi.orders.update(id, {
      planned_date: data.planned_date || data.scheduled_date || null,
      location: data.location || null,
      conclusion: data.conclusion,
      conditions: data.conditions,
    }),
  addChecklist: (id, data) => acceptanceApi.templates.addItems(id, data),
  signOff: (id, data) =>
    api.post(`/acceptance-orders/${id}/customer-sign`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : undefined,
    }),
};
