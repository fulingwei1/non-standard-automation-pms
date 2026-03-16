import { api } from "./client.js";

const unwrap = (response) => response?.data?.data ?? response?.data ?? response;

const wrapResponseData = (response, data) => ({
  ...response,
  data,
});

const mapPaginatedItems = (response, normalizer) => {
  const data = unwrap(response) || {};
  return wrapResponseData(response, {
    ...data,
    items: (data.items || []).map((item) => normalizer(item)),
  });
};

const TICKET_STATUS_MAP = {
  RESOLVED: "PENDING_VERIFY",
  ASSIGNED: "IN_PROGRESS",
};

const COMMUNICATION_TYPE_MAP = {
  PHONE: "phone",
  EMAIL: "email",
  ON_SITE: "on_site",
  ONSITE: "on_site",
  WECHAT: "wechat",
  MEETING: "meeting",
  VIDEO_CALL: "video_call",
  VIDEO: "video_call",
  phone: "phone",
  email: "email",
  on_site: "on_site",
  wechat: "wechat",
  meeting: "meeting",
  video_call: "video_call",
};

const COMMUNICATION_PRIORITY_MAP = {
  HIGH: "high",
  MEDIUM: "medium",
  LOW: "low",
  "高": "high",
  "中": "medium",
  "低": "low",
  high: "high",
  medium: "medium",
  low: "low",
};

const COMMUNICATION_TOPIC_MAP = {
  SALES: "sales",
  SUPPORT: "support",
  TECHNICAL_SUPPORT: "support",
  COMPLAINT: "complaint",
  CONSULTATION: "consultation",
  FEEDBACK: "feedback",
  TRAINING: "training",
  MAINTENANCE: "maintenance",
  OTHER: "other",
  sales: "sales",
  support: "support",
  complaint: "complaint",
  consultation: "consultation",
  feedback: "feedback",
  training: "training",
  maintenance: "maintenance",
  other: "other",
};

const normalizeTicketStatus = (status) => TICKET_STATUS_MAP[status] || status || "PENDING";

const normalizeCommunicationType = (value) =>
  COMMUNICATION_TYPE_MAP[value] || COMMUNICATION_TYPE_MAP[String(value || "").toUpperCase()] || "phone";

const normalizeCommunicationPriority = (value) =>
  COMMUNICATION_PRIORITY_MAP[value] ||
  COMMUNICATION_PRIORITY_MAP[String(value || "").toUpperCase()] ||
  "medium";

const normalizeCommunicationTopic = (value) =>
  COMMUNICATION_TOPIC_MAP[value] ||
  COMMUNICATION_TOPIC_MAP[String(value || "").toUpperCase()] ||
  "other";

const normalizeSurveyStatus = (value) =>
  ({
    DRAFT: "draft",
    SENT: "sent",
    PENDING: "pending",
    COMPLETED: "completed",
    EXPIRED: "expired",
  }[value] || String(value || "").toLowerCase() || "draft");

const deriveCommunicationStatus = (item = {}) => {
  const followUpStatus = String(item.follow_up_status || "").toUpperCase();
  if (item.follow_up_required) {
    if (["COMPLETED", "DONE", "CLOSED", "已完成"].includes(followUpStatus)) {
      return "completed";
    }
    return "follow_up";
  }
  if (["COMPLETED", "DONE", "CLOSED", "已完成"].includes(followUpStatus)) {
    return "completed";
  }
  return "completed";
};

const normalizeServiceTicket = (ticket = {}) => {
  const assignedName = ticket.assigned_to_name || ticket.assignee_name || ticket.assigned_engineer || "";
  return {
    ...ticket,
    title: ticket.title || ticket.problem_desc || `服务工单 ${ticket.ticket_no || `#${ticket.id}`}`,
    created_time: ticket.created_time || ticket.created_at || ticket.reported_time || null,
    closed_time: ticket.closed_time || ticket.resolved_time || null,
    assignee_name: assignedName,
    assigned_engineer: assignedName,
    status: normalizeTicketStatus(ticket.status),
    reported_phone: ticket.reported_phone || ticket.contact_phone || "",
  };
};

const normalizeTicketStatistics = (stats = {}) => ({
  ...stats,
  total: stats.total || 0,
  pending: stats.pending || 0,
  inProgress: stats.inProgress ?? stats.in_progress ?? 0,
  pendingVerify: stats.pendingVerify ?? stats.resolved ?? 0,
  resolved: stats.resolved ?? 0,
  closed: stats.closed ?? 0,
  overdue: stats.overdue ?? 0,
  urgent: stats.urgent ?? 0,
  high: stats.high ?? 0,
  satisfactionScore: stats.satisfactionScore ?? 0,
  avgResolutionTime: stats.avgResolutionTime ?? 0,
});

const normalizeServiceRecord = (record = {}) => ({
  ...record,
  status: record.status || "SCHEDULED",
  duration: record.duration ?? record.duration_hours ?? 0,
  photos: Array.isArray(record.photos) ? record.photos : [],
});

const normalizeCommunication = (item = {}) => ({
  ...item,
  communication_type: normalizeCommunicationType(item.communication_type),
  priority: normalizeCommunicationPriority(item.priority || item.importance),
  topic: normalizeCommunicationTopic(item.topic),
  status: deriveCommunicationStatus(item),
  duration_minutes: item.duration_minutes ?? item.duration ?? "",
  next_action: item.next_action || item.follow_up_task || "",
  next_action_date: item.next_action_date || item.follow_up_due_date || "",
  satisfaction_rating: item.satisfaction_rating ?? null,
  customer_feedback: item.customer_feedback || "",
  notes:
    item.notes ||
    (Array.isArray(item.tags) && item.tags.length > 0 ? item.tags.join("、") : ""),
});

const normalizeSurvey = (item = {}) => ({
  ...item,
  status: normalizeSurveyStatus(item.status),
  title: item.title || item.survey_title || item.subject || item.survey_no || `满意度调查 #${item.id}`,
  type: item.type || item.survey_type || "service",
});

export const serviceApi = {
  tickets: {
    list: (params) =>
      api.get("/tickets", { params }).then((response) => mapPaginatedItems(response, normalizeServiceTicket)),
    get: (id) =>
      api.get(`/tickets/${id}`).then((response) => wrapResponseData(response, normalizeServiceTicket(unwrap(response)))),
    create: (data) =>
      api.post("/tickets", data).then((response) => wrapResponseData(response, normalizeServiceTicket(unwrap(response)))),
    update: (id, data) =>
      api.put(`/tickets/${id}`, data).then((response) => wrapResponseData(response, normalizeServiceTicket(unwrap(response)))),
    assign: (id, data) =>
      api.put(`/tickets/${id}/assign`, data).then((response) => wrapResponseData(response, normalizeServiceTicket(unwrap(response)))),
    batchAssign: async ({ ticket_ids = [], assignee_id, cc_user_ids = [] }) => {
      await Promise.all(
        ticket_ids.map((ticketId) =>
          api.put(`/tickets/${ticketId}/assign`, { assignee_id, cc_user_ids }),
        ),
      );
      return { data: { success: true, updated: ticket_ids.length } };
    },
    batchDelete: async () => {
      throw new Error("当前后端未提供服务工单批量删除接口");
    },
    close: (id, data) =>
      api.put(`/tickets/${id}/close`, data).then((response) => wrapResponseData(response, normalizeServiceTicket(unwrap(response)))),
    getStatistics: () =>
      api.get("/tickets/statistics").then((response) => wrapResponseData(response, normalizeTicketStatistics(unwrap(response)))),
    getProjectMembers: (params) => api.get("/tickets/project-members", { params }),
    getRelatedProjects: (id) => api.get(`/tickets/${id}/projects`),
  },
  records: {
    list: (params) =>
      api.get("/records", { params }).then((response) => mapPaginatedItems(response, normalizeServiceRecord)),
    get: (id) =>
      api.get(`/records/${id}`).then((response) => wrapResponseData(response, normalizeServiceRecord(unwrap(response)))),
    create: (data) => api.post("/records", data),
    update: (id, data) => api.put(`/records/${id}`, data),
    uploadPhoto: (recordId, file, description) => {
      const formData = new FormData();
      formData.append("file", file);
      if (description) {
        formData.append("description", description);
      }
      return api.post(`/records/${recordId}/photos`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    deletePhoto: (recordId, photoIndex) => api.delete(`/records/${recordId}/photos/${photoIndex}`),
    getStatistics: () => api.get("/records/statistics"),
  },
  communications: {
    list: (params) =>
      api.get("/communications", { params }).then((response) => mapPaginatedItems(response, normalizeCommunication)),
    get: (id) =>
      api.get(`/communications/${id}`).then((response) => wrapResponseData(response, normalizeCommunication(unwrap(response)))),
    create: (data) => api.post("/communications", data),
    update: (id, data) => api.put(`/communications/${id}`, data),
    statistics: () => api.get("/communications/statistics"),
  },
  satisfaction: {
    list: (params) =>
      api.get("/surveys", { params }).then((response) => mapPaginatedItems(response, normalizeSurvey)),
    get: (id) =>
      api.get(`/surveys/${id}`).then((response) => wrapResponseData(response, normalizeSurvey(unwrap(response)))),
    create: (data) => api.post("/surveys", data),
    update: (id, data) => api.put(`/surveys/${id}`, data),
    send: (id, data) => api.post(`/surveys/${id}/send`, data),
    submit: (id, data) => api.post(`/surveys/${id}/submit`, data),
    statistics: () => api.get("/surveys/statistics"),
    templates: {
      list: (params) => api.get("/survey-templates", { params }),
      get: (id) => api.get(`/survey-templates/${id}`),
    },
  },
  dashboardStatistics: () => api.get("/statistics/dashboard-statistics"),
  knowledgeBase: {
    list: (params) => api.get("/knowledge-base", { params }),
    get: (id) => api.get(`/knowledge-base/${id}`),
    create: (data) => api.post("/knowledge-base", data),
    update: (id, data) => api.put(`/knowledge-base/${id}`, data),
    delete: (id) => api.delete(`/knowledge-base/${id}`),
    publish: (id) => api.put(`/knowledge-base/${id}/publish`),
    archive: (id) => api.put(`/knowledge-base/${id}/archive`),
    statistics: () => api.get("/knowledge-base/statistics"),
    upload: (formData) =>
      api.post("/knowledge-base/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }),
    downloadUrl: (id) => `${api.defaults.baseURL}/knowledge-base/${id}/download`,
    getQuota: () => api.get("/knowledge-base/quota"),
    like: (id) => api.post(`/knowledge-base/${id}/like`),
    adopt: (id) => api.post(`/knowledge-base/${id}/adopt`),
  },
};

export const installationDispatchApi = {
  orders: {
    list: (params) => api.get("/installation-dispatch/orders", { params }),
    get: (id) => api.get(`/installation-dispatch/orders/${id}`),
    create: (data) => api.post("/installation-dispatch/orders", data),
    update: (id, data) => api.put(`/installation-dispatch/orders/${id}`, data),
    assign: (id, data) => api.put(`/installation-dispatch/orders/${id}/assign`, data),
    batchAssign: (data) => api.post("/installation-dispatch/orders/batch-assign", data),
    start: (id, data) => api.put(`/installation-dispatch/orders/${id}/start`, data),
    progress: (id, data) => api.put(`/installation-dispatch/orders/${id}/progress`, data),
    complete: (id, data) => api.put(`/installation-dispatch/orders/${id}/complete`, data),
    cancel: (id) => api.put(`/installation-dispatch/orders/${id}/cancel`),
  },
  statistics: () => api.get("/installation-dispatch/statistics"),
};

export const itrApi = {
  getEfficiencyAnalysis: (params) => api.get("/itr/analytics/efficiency", { params }),
  getSatisfactionTrend: (params) => api.get("/itr/analytics/satisfaction", { params }),
  getBottlenecksAnalysis: (params) => api.get("/itr/analytics/bottlenecks", { params }),
  getSlaAnalysis: (params) => api.get("/itr/analytics/sla", { params }),
  getDashboard: (params) => api.get("/itr/dashboard", { params }),
  getTicketTimeline: (ticketId) => api.get(`/itr/tickets/${ticketId}/timeline`),
  getIssueRelated: (issueId) => api.get(`/itr/issues/${issueId}/related`),
};
