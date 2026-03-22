/**
 * 客服工作台 - 常量、配置、工具函数和数据归一化
 */

export const PAGE_SIZE = 500;
export const TEAM_OVERVIEW_KEY = "team";

// 角色权限集合
export const SERVICE_MANAGER_ROLES = new Set([
  "customer_service_manager",
  "admin",
  "super_admin",
  "gm",
  "chairman",
]);

// 状态分类集合
export const RESOLVED_TICKET_STATUSES = new Set(["RESOLVED", "CLOSED"]);
export const ACTIVE_TICKET_STATUSES = new Set(["PENDING", "IN_PROGRESS", "PENDING_VERIFY"]);
export const RESOLVED_ISSUE_STATUSES = new Set(["RESOLVED", "CLOSED", "VERIFIED", "DONE"]);
export const ACTIVE_RECORD_STATUSES = new Set(["SCHEDULED", "IN_PROGRESS", "ACTIVE"]);
export const ACTIVE_ORDER_STATUSES = new Set(["PENDING", "ASSIGNED", "IN_PROGRESS"]);

// ── 通用工具 ──────────────────────────────────────────────

export function unwrapResponseBody(response) {
  if (!response) {
    return null;
  }
  if (response.data?.data !== undefined) {
    return response.data.data;
  }
  if (response.data !== undefined) {
    return response.data;
  }
  return response;
}

export function unwrapItems(response) {
  const body = unwrapResponseBody(response);
  if (Array.isArray(body)) {
    return body;
  }
  return Array.isArray(body?.items) ? body.items : [];
}

export function toNumber(value, fallback = 0) {
  const normalized = Number(value);
  return Number.isFinite(normalized) ? normalized : fallback;
}

export function toTrimmedString(value) {
  return String(value || "").trim();
}

// ── 数据归一化 ──────────────────────────────────────────────

export function normalizeTicket(ticket = {}) {
  return {
    ...ticket,
    id: ticket.id,
    ticket_no: ticket.ticket_no || `T-${ticket.id}`,
    project_id: ticket.project_id,
    project_name: ticket.project_name || "未关联项目",
    problem_desc: ticket.problem_desc || ticket.title || "-",
    urgency: ticket.urgency || "-",
    status: toTrimmedString(ticket.status).toUpperCase() || "PENDING",
    reported_time: ticket.reported_time || ticket.created_at || null,
    assigned_to_id: ticket.assigned_to_id ?? null,
    assigned_to_name: ticket.assigned_to_name || ticket.assignee_name || "",
  };
}

export function normalizeRecord(record = {}) {
  return {
    ...record,
    id: record.id,
    record_no: record.record_no || `R-${record.id}`,
    project_id: record.project_id,
    project_name: record.project_name || "未关联项目",
    service_type: record.service_type || "-",
    service_date: record.service_date || record.created_at || null,
    status: toTrimmedString(record.status).toUpperCase() || "SCHEDULED",
    service_engineer_id: record.service_engineer_id ?? null,
    service_engineer_name: record.service_engineer_name || "",
    service_content: record.service_content || "-",
    issues_found: record.issues_found || "",
  };
}

export function normalizeOrder(order = {}) {
  return {
    ...order,
    id: order.id,
    order_no: order.order_no || `D-${order.id}`,
    project_id: order.project_id,
    project_name: order.project_name || "未关联项目",
    task_title: order.task_title || "-",
    task_type: order.task_type || "-",
    status: toTrimmedString(order.status).toUpperCase() || "PENDING",
    priority: order.priority || "-",
    scheduled_date: order.scheduled_date || order.created_at || null,
    assigned_to_id: order.assigned_to_id ?? null,
    assigned_to_name: order.assigned_to_name || "",
    progress: toNumber(order.progress),
  };
}

export function normalizeProject(project = {}) {
  return {
    ...project,
    id: project.id,
    project_code: project.project_code || `P-${project.id}`,
    project_name: project.project_name || "未命名项目",
    customer_name: project.customer_name || "-",
    stage: project.stage || "-",
    health: project.health || null,
    progress_pct: toNumber(project.progress_pct),
    pm_name: project.pm_name || "-",
  };
}

export function normalizeIssue(issue = {}) {
  return {
    ...issue,
    id: issue.id,
    issue_no: issue.issue_no || `I-${issue.id}`,
    title: issue.title || "-",
    project_id: issue.project_id ?? null,
    project_name: issue.project_name || "未关联项目",
    status: toTrimmedString(issue.status).toUpperCase() || "OPEN",
    severity: issue.severity || "-",
    priority: issue.priority || "-",
    assignee_id: issue.assignee_id ?? null,
    assignee_name: issue.assignee_name || "",
    responsible_engineer_id: issue.responsible_engineer_id ?? null,
    responsible_engineer_name: issue.responsible_engineer_name || "",
    solution: issue.solution || "",
    report_date: issue.report_date || issue.created_at || null,
  };
}

export function normalizeUser(user = {}) {
  return {
    ...user,
    id: user.id,
    username: user.username || "",
    real_name: user.real_name || user.username || "未命名工程师",
    department: user.department || "",
    position: user.position || "",
    roles: Array.isArray(user.roles) ? user.roles : [],
  };
}

// ── 状态判断 ──────────────────────────────────────────────

export function isTicketResolved(status) {
  return RESOLVED_TICKET_STATUSES.has(toTrimmedString(status).toUpperCase());
}

export function isTicketActive(status) {
  return ACTIVE_TICKET_STATUSES.has(toTrimmedString(status).toUpperCase());
}

export function isIssueResolved(status) {
  return RESOLVED_ISSUE_STATUSES.has(toTrimmedString(status).toUpperCase());
}

export function isRecordActive(status) {
  return ACTIVE_RECORD_STATUSES.has(toTrimmedString(status).toUpperCase());
}

export function isOrderActive(status) {
  return ACTIVE_ORDER_STATUSES.has(toTrimmedString(status).toUpperCase());
}

// ── 状态标签 ──────────────────────────────────────────────

export function getTicketStatusLabel(status) {
  return (
    {
      PENDING: "待处理",
      IN_PROGRESS: "处理中",
      PENDING_VERIFY: "待验证",
      RESOLVED: "已解决",
      CLOSED: "已关闭",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

export function getIssueStatusLabel(status) {
  return (
    {
      OPEN: "待处理",
      PROCESSING: "处理中",
      IN_PROGRESS: "处理中",
      RESOLVED: "已解决",
      VERIFIED: "已验证",
      CLOSED: "已关闭",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

export function getRecordStatusLabel(status) {
  return (
    {
      SCHEDULED: "待执行",
      IN_PROGRESS: "进行中",
      ACTIVE: "进行中",
      COMPLETED: "已完成",
      APPROVED: "已归档",
      CANCELLED: "已取消",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

export function getOrderStatusLabel(status) {
  return (
    {
      PENDING: "待派工",
      ASSIGNED: "已派工",
      IN_PROGRESS: "进行中",
      COMPLETED: "已完成",
      CANCELLED: "已取消",
    }[toTrimmedString(status).toUpperCase()] || status
  );
}

// ── 徽章样式 ──────────────────────────────────────────────

export function getStatusBadgeVariant(status) {
  const normalized = toTrimmedString(status).toUpperCase();
  if (
    ["CLOSED", "RESOLVED", "VERIFIED", "DONE", "COMPLETED", "APPROVED"].includes(
      normalized,
    )
  ) {
    return "success";
  }
  if (["PENDING_VERIFY", "ASSIGNED", "SCHEDULED"].includes(normalized)) {
    return "warning";
  }
  if (["IN_PROGRESS", "PROCESSING", "ACTIVE", "OPEN"].includes(normalized)) {
    return "info";
  }
  if (["CANCELLED", "REJECTED", "FAILED", "BLOCKED"].includes(normalized)) {
    return "danger";
  }
  return "secondary";
}

export function getUrgencyBadgeVariant(urgency) {
  const normalized = toTrimmedString(urgency).toUpperCase();
  if (["URGENT", "CRITICAL", "HIGH", "紧急", "高"].includes(normalized)) {
    return "danger";
  }
  if (["MEDIUM", "中"].includes(normalized)) {
    return "warning";
  }
  return "secondary";
}

// ── 工程师匹配 ──────────────────────────────────────────────

export function engineerMatches(engineer, userId, userName) {
  if (!engineer) {
    return false;
  }
  if (engineer.id !== null && engineer.id !== undefined && userId !== null && userId !== undefined) {
    return Number(engineer.id) === Number(userId);
  }
  const normalizedEngineerName = toTrimmedString(engineer.name);
  const normalizedUserName = toTrimmedString(userName);
  return Boolean(normalizedEngineerName && normalizedUserName && normalizedEngineerName === normalizedUserName);
}
