import { BOARD_STATUS_ORDER, PRIORITY_CONFIG, TYPE_LABELS } from "./constants";

export function extractApiPayload(response) {
  if (response?.formatted !== undefined) {
    return response.formatted;
  }
  if (response?.data?.data !== undefined) {
    return response.data.data;
  }
  return response?.data;
}

export function normalizeStatus(status) {
  const resolved = String(status || "").toUpperCase();
  if (BOARD_STATUS_ORDER.includes(resolved)) {
    return resolved;
  }
  if (resolved === "PROCESSING") {
    return "IN_PROGRESS";
  }
  if (resolved === "CLOSED" || resolved === "CANCELLED") {
    return "COMPLETED";
  }
  return "PENDING";
}

export function normalizePriority(priority) {
  const resolved = String(priority || "").toUpperCase();
  if (PRIORITY_CONFIG[resolved]) {
    return resolved;
  }
  if (resolved === "MEDIUM") {
    return "NORMAL";
  }
  return "NORMAL";
}

export function safeDate(dateString) {
  if (!dateString) {
    return null;
  }
  const date = new Date(dateString);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDateTime(dateString) {
  const date = safeDate(dateString);
  if (!date) {
    return "-";
  }
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDate(dateString) {
  const date = safeDate(dateString);
  if (!date) {
    return "-";
  }
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function computeHoursDiff(startDateString, endDateString) {
  const start = safeDate(startDateString);
  const end = safeDate(endDateString);
  if (!start || !end) {
    return null;
  }
  return (end.getTime() - start.getTime()) / (1000 * 60 * 60);
}

export function toTicketModel(ticket, forcedStatus = null) {
  return {
    id: ticket.id,
    ticketNo: ticket.ticket_no || `PS-${String(ticket.id).padStart(6, "0")}`,
    title: ticket.title || "未命名工单",
    ticketType: ticket.ticket_type || "SOLUTION_DESIGN",
    ticketTypeLabel: TYPE_LABELS[ticket.ticket_type] || ticket.ticket_type || "售前支持",
    priority: normalizePriority(ticket.urgency),
    status: forcedStatus || normalizeStatus(ticket.status),
    customerName: ticket.customer_name || "未知客户",
    applicantName: ticket.applicant_name || "未知申请人",
    assigneeName: ticket.assignee_name || "未指派",
    applyTime: ticket.apply_time || ticket.created_at,
    acceptTime: ticket.accept_time,
    completeTime: ticket.complete_time,
    deadline: ticket.deadline,
    expectedDate: ticket.expected_date,
    description: ticket.description || "暂无工单描述",
  };
}
