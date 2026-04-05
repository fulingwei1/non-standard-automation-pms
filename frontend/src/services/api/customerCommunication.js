import { api } from "./client.js";

const safeDelete = async (url, config = {}, fallbackData = null) => {
  try {
    return await api.delete(url, config);
  } catch (_error) {
    return { data: fallbackData };
  }
};

const wrapResponseData = (response, data) => ({
  ...response,
  data,
});

const unwrap = (response) => response?.data?.data ?? response?.data ?? response;

const TYPE_MAP = {
  phone: "PHONE",
  email: "EMAIL",
  on_site: "ON_SITE",
  wechat: "WECHAT",
  meeting: "MEETING",
  video_call: "VIDEO_CALL",
};

const PRIORITY_MAP = {
  high: "高",
  medium: "中",
  low: "低",
};

const normalizeType = (value) =>
  ({
    PHONE: "phone",
    EMAIL: "email",
    ON_SITE: "on_site",
    WECHAT: "wechat",
    MEETING: "meeting",
    VIDEO_CALL: "video_call",
    phone: "phone",
    email: "email",
    on_site: "on_site",
    wechat: "wechat",
    meeting: "meeting",
    video_call: "video_call",
  }[value] || "phone");

const normalizePriority = (value) =>
  ({
    高: "high",
    中: "medium",
    低: "low",
    HIGH: "high",
    MEDIUM: "medium",
    LOW: "low",
    high: "high",
    medium: "medium",
    low: "low",
  }[value] || "medium");

const normalizeTopic = (value) =>
  ({
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
  }[value] || "other");

const deriveStatus = (item = {}) => {
  if (item.follow_up_required && item.follow_up_status !== "已完成") {
    return "follow_up";
  }
  return "completed";
};

const normalizeCommunication = (item = {}) => ({
  ...item,
  communication_type: normalizeType(item.communication_type),
  priority: normalizePriority(item.priority || item.importance),
  topic: normalizeTopic(item.topic),
  status: deriveStatus(item),
  duration_minutes: item.duration_minutes ?? item.duration ?? "",
  next_action: item.next_action || item.follow_up_task || "",
  next_action_date: item.next_action_date || item.follow_up_due_date || "",
  notes:
    item.notes ||
    (Array.isArray(item.tags) && item.tags.length > 0 ? item.tags.join("、") : ""),
});

const normalizeListResponse = (response) => {
  const data = unwrap(response) || {};
  return wrapResponseData(response, {
    ...data,
    items: (data.items || []).map((item) => normalizeCommunication(item)),
  });
};

const mapListParams = (params = {}) => ({
  keyword: params.keyword || params.search || undefined,
  communication_type:
    params.communication_type && params.communication_type !== "all"
      ? TYPE_MAP[params.communication_type] || params.communication_type
      : undefined,
  topic:
    params.topic && params.topic !== "all"
      ? params.topic.toUpperCase()
      : undefined,
  importance:
    params.priority && params.priority !== "all"
      ? PRIORITY_MAP[params.priority] || params.priority
      : undefined,
  date_from: params.start_date || undefined,
  date_to: params.end_date || undefined,
  page_size: params.page_size || 1000,
});

const mapCreatePayload = (data = {}) => ({
  communication_type:
    TYPE_MAP[data.communication_type] || data.communication_type || "PHONE",
  customer_name: data.customer_name,
  customer_contact: data.customer_contact || null,
  customer_phone: data.customer_phone || null,
  customer_email: data.customer_email || null,
  project_code: data.project_code || null,
  project_name: data.project_name || null,
  communication_date: data.communication_date,
  communication_time: data.communication_time || null,
  duration: data.duration ?? data.duration_minutes ?? null,
  location: data.location || null,
  topic: data.topic ? data.topic.toUpperCase() : "OTHER",
  subject: data.subject,
  content: data.content,
  follow_up_required: Boolean(data.follow_up_required ?? data.next_action ?? data.next_action_date),
  follow_up_task: data.follow_up_task || data.next_action || null,
  follow_up_due_date: data.follow_up_due_date || data.next_action_date || null,
  tags: data.tags || [],
  importance: PRIORITY_MAP[data.priority] || data.importance || "中",
});

const mapUpdatePayload = (data = {}) => ({
  content: data.content,
  follow_up_task: data.follow_up_task || data.next_action || null,
  follow_up_status: data.follow_up_status || (data.next_action ? "待处理" : null),
  tags: data.tags || [],
});

export const customerCommunicationApi = {
  list: (params = {}) =>
    api.get("/communications", { params: mapListParams(params) }).then(normalizeListResponse),
  get: (id) =>
    api.get(`/communications/${id}`).then((response) =>
      wrapResponseData(response, normalizeCommunication(unwrap(response))),
    ),
  create: (data) => api.post("/communications", mapCreatePayload(data)),
  update: (id, data) => api.put(`/communications/${id}`, mapUpdatePayload(data)),
  delete: (id) => safeDelete(`/communications/${id}`),
  statistics: () => api.get("/communications/statistics"),
};
