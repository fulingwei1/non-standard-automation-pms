/**
 * Utility functions for the Presales Manager Workstation
 */

export function extractItems(response) {
  const payload = response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items;
  }
  if (Array.isArray(payload?.data)) {
    return payload.data;
  }
  return [];
}

export function formatDateLabel(value) {
  if (!value) {
    return "待定";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString("zh-CN");
}

export function formatDateTimeLabel(value) {
  if (!value) {
    return "待定";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getDaysLeft(value) {
  if (!value) {
    return null;
  }

  const deadline = new Date(value);
  if (Number.isNaN(deadline.getTime())) {
    return null;
  }

  const now = new Date();
  return Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
}

export function normalizeSolutionStatus(status, reviewStatus) {
  const currentStatus = String(status || "").toUpperCase();
  const currentReviewStatus = String(reviewStatus || "").toUpperCase();

  if (currentStatus === "APPROVED" || currentStatus === "DELIVERED" || currentStatus === "WON") {
    return "APPROVED";
  }
  if (currentStatus === "REJECTED" || currentStatus === "LOST") {
    return "REJECTED";
  }
  if (
    currentStatus === "REVIEW" ||
    currentStatus === "REVIEWING" ||
    currentReviewStatus === "PENDING" ||
    currentReviewStatus === "REVIEWING"
  ) {
    return "REVIEWING";
  }
  if (currentStatus === "SUBMITTED" || currentStatus === "IN_PROGRESS") {
    return "SUBMITTED";
  }
  return "DRAFT";
}

export function mapSolutionDisplayStatus(status) {
  const statusMap = {
    DRAFT: "设计中",
    SUBMITTED: "已提交",
    REVIEWING: "评审中",
    APPROVED: "已通过",
    REJECTED: "已驳回",
  };
  return statusMap[status] || status || "待处理";
}

export function getSolutionStatusColor(status) {
  if (status === "APPROVED") {
    return "bg-emerald-500";
  }
  if (status === "REVIEWING") {
    return "bg-amber-500";
  }
  if (status === "REJECTED") {
    return "bg-red-500";
  }
  return "bg-blue-500";
}

export function getSolutionProgress(status) {
  if (status === "APPROVED") {
    return 100;
  }
  if (status === "REVIEWING") {
    return 85;
  }
  if (status === "SUBMITTED") {
    return 70;
  }
  return 55;
}

export function mapTenderStatus(result) {
  const normalizedResult = String(result || "PENDING").toUpperCase();
  const labelMap = {
    PENDING: "准备中",
    WON: "已中标",
    LOST: "未中标",
    CANCELLED: "已取消",
  };
  const colorMap = {
    PENDING: "bg-amber-500",
    WON: "bg-emerald-500",
    LOST: "bg-red-500",
    CANCELLED: "bg-slate-500",
  };

  return {
    label: labelMap[normalizedResult] || normalizedResult,
    color: colorMap[normalizedResult] || "bg-slate-500",
    progress: normalizedResult === "PENDING" ? 60 : 100,
  };
}
