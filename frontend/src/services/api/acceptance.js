import { api } from "./client.js";

const ACCEPTANCE_PREFIX = "/acceptance";

const unwrap = (response) => response?.data?.data ?? response?.data ?? response;

const wrapResponseData = (response, data) => ({
  ...response,
  data,
});

const normalizeOverallResult = (value) => {
  const normalized = String(value || "").toUpperCase();
  return (
    {
      PASS: "PASSED",
      PASSED: "PASSED",
      FAIL: "FAILED",
      FAILED: "FAILED",
      CONDITIONAL: "CONDITIONAL",
    }[normalized] || value
  );
};

const normalizeResultKey = (value) => {
  const normalized = String(value || "").toUpperCase();
  return (
    {
      PASS: "pass",
      PASSED: "pass",
      FAIL: "fail",
      FAILED: "fail",
      CONDITIONAL: "conditional",
    }[normalized] || null
  );
};

const normalizeOrderStatus = (order = {}) => {
  const status = String(order.status || "").toUpperCase();
  if (order.is_officially_completed || order.customer_signed_file_path) {
    return "signed";
  }
  if (status === "COMPLETED") {
    if (String(order.overall_result || "").toUpperCase() === "FAILED") {
      return "failed";
    }
    return "passed";
  }
  return (
    {
      DRAFT: "draft",
      PENDING: "pending",
      IN_PROGRESS: "in_progress",
    }[status] || String(order.status || "").toLowerCase() || "draft"
  );
};

const normalizeIssueStatus = (value) => {
  const normalized = String(value || "").toUpperCase();
  return (
    {
      OPEN: "open",
      PROCESSING: "fixing",
      IN_PROGRESS: "fixing",
      RESOLVED: "resolved",
      CLOSED: "closed",
      DEFERRED: "open",
    }[normalized] || "open"
  );
};

const normalizeIssueSeverity = (value) => {
  const normalized = String(value || "").toUpperCase();
  return (
    {
      CRITICAL: "critical",
      MAJOR: "major",
      MINOR: "minor",
    }[normalized] || String(value || "").toLowerCase() || "minor"
  );
};

const normalizeChecklistStatus = (value) => {
  const normalized = String(value || "").toUpperCase();
  return (
    {
      PASSED: "pass",
      FAILED: "fail",
      PENDING: "pending",
      NA: "na",
      CONDITIONAL: "conditional",
    }[normalized] || "pending"
  );
};

const normalizeLegacyOrder = (order = {}) => ({
  ...order,
  acceptance_code: order.acceptance_code || order.order_no || "",
  title:
    order.title ||
    order.template_name ||
    `${order.acceptance_type || "验收"} - ${order.machine_name || order.project_name || order.order_no || order.id}`,
  scheduled_date: order.scheduled_date || order.planned_date || null,
  status: normalizeOrderStatus(order),
  overall_result: normalizeResultKey(order.overall_result),
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

const normalizeChecklistItem = (item = {}) => ({
  ...item,
  item_no: item.item_no || item.item_code || "",
  check_item: item.check_item || item.item_name || "",
  status: normalizeChecklistStatus(item.status || item.result_status),
});

const normalizeIssue = (issue = {}) => ({
  ...issue,
  description: issue.description || issue.title || "",
  severity: normalizeIssueSeverity(issue.severity),
  status: normalizeIssueStatus(issue.status),
});

const buildChecklistStats = (items = []) => ({
  total: items.length,
  passed: items.filter((item) => item.status === "pass").length,
  failed: items.filter((item) => item.status === "fail").length,
  pending: items.filter((item) => item.status === "pending").length,
});

const buildIssueStats = (items = []) => ({
  total: items.length,
  open: items.filter((item) => item.status === "open").length,
  fixing: items.filter((item) => item.status === "fixing").length,
  closed: items.filter((item) => ["resolved", "closed"].includes(item.status)).length,
});

const composeOrderDetail = (order = {}, checklist = [], issues = []) => {
  const normalizedChecklist = checklist.map((item) => normalizeChecklistItem(item));
  const normalizedIssues = issues.map((item) => normalizeIssue(item));
  return {
    ...normalizeLegacyOrder(order),
    checklist: normalizedChecklist,
    checklist_stats: buildChecklistStats(normalizedChecklist),
    issues: normalizedIssues,
    issues_stats: buildIssueStats(normalizedIssues),
  };
};

const mapOrderStatusParam = (value) => {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      draft: "DRAFT",
      pending: "PENDING",
      in_progress: "IN_PROGRESS",
      passed: "COMPLETED",
      failed: "COMPLETED",
      signed: "COMPLETED",
    }[normalized] || value
  );
};

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
      api.get(`${ACCEPTANCE_PREFIX}/acceptance-orders`, {
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
            params.status && params.status !== "all"
              ? mapOrderStatusParam(params.status)
              : undefined,
        },
      }),
    get: (id) => api.get(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}`),
    create: (data) => api.post(`${ACCEPTANCE_PREFIX}/acceptance-orders`, data),
    update: (id, data) => api.put(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}`, data),
    start: (id, data = {}) => api.put(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}/start`, data),
    complete: (id, data = {}) =>
      api.put(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}/complete`, {
        ...data,
        overall_result: normalizeOverallResult(data.overall_result),
      }),
    getItems: (id) => api.get(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}/items`),
    updateItem: (itemId, data) => api.put(`${ACCEPTANCE_PREFIX}/acceptance-items/${itemId}`, data),
    submit: (id) => api.post(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}/submit`),
  },

  issues: {
    list: (orderIdOrParams) => {
      const params =
        typeof orderIdOrParams === "object"
          ? orderIdOrParams
          : { order_id: orderIdOrParams };
      return api.get(`${ACCEPTANCE_PREFIX}/acceptance-orders/${params.order_id}/issues`, {
        params: params.status ? { status: params.status } : undefined,
      });
    },
    create: (orderId, data) =>
      api.post(
        `${ACCEPTANCE_PREFIX}/acceptance-orders/${orderId}/issues`,
        mapIssueCreatePayload(orderId, data),
      ),
  },

  templates: {
    list: (params = {}) =>
      api.get(`${ACCEPTANCE_PREFIX}/acceptance-templates`, {
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
    get: (id) => api.get(`${ACCEPTANCE_PREFIX}/acceptance-templates/${id}`),
    create: (data) =>
      api.post(`${ACCEPTANCE_PREFIX}/acceptance-templates`, mapTemplateFormToPayload(data)),
    update: (id, data) => api.put(`${ACCEPTANCE_PREFIX}/acceptance-templates/${id}`, data),
    getItems: (id) => api.get(`${ACCEPTANCE_PREFIX}/acceptance-templates/${id}/items`),
    addItems: async (id, payload = {}) => {
      let categoryId = payload.category_id;
      if (!categoryId) {
        const detail = unwrap(await api.get(`${ACCEPTANCE_PREFIX}/acceptance-templates/${id}`));
        categoryId = detail?.categories?.[0]?.id;
      }
      if (!categoryId) {
        throw new Error("模板缺少可用分类，无法新增检查项");
      }
      return api.post(
        `${ACCEPTANCE_PREFIX}/acceptance-templates/${id}/items`,
        (payload.items || []).map(mapTemplateItemPayload),
        {
          params: { category_id: categoryId },
        },
      );
    },
  },

  list: async (params = {}) => {
    const response = await acceptanceApi.orders.list(params);
    const data = unwrap(response);
    return wrapResponseData(response, {
      ...data,
      items: (data?.items || []).map((item) => normalizeLegacyOrder(item)),
    });
  },
  detail: async (id) => {
    const [orderResponse, itemsResponse, issuesResponse] = await Promise.all([
      acceptanceApi.orders.get(id),
      acceptanceApi.orders.getItems(id).catch(() => ({ data: [] })),
      acceptanceApi.issues.list(id).catch(() => ({ data: [] })),
    ]);

    return wrapResponseData(
      orderResponse,
      composeOrderDetail(
        unwrap(orderResponse),
        unwrap(itemsResponse) || [],
        unwrap(issuesResponse) || [],
      ),
    );
  },
  create: (data) =>
    acceptanceApi.orders.create({
      project_id: Number(data.project_id),
      machine_id: data.machine_id ? Number(data.machine_id) : null,
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
    api.post(`${ACCEPTANCE_PREFIX}/acceptance-orders/${id}/upload-signed-document`, data, {
      headers: data instanceof FormData ? { "Content-Type": "multipart/form-data" } : undefined,
    }),
};
