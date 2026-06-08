import { STATUS_CONFIG } from "./constants";

export function normalizeSolutionStatus(status, reviewStatus) {
  const currentStatus = String(status || "").toUpperCase();
  const currentReviewStatus = String(reviewStatus || "").toUpperCase();

  if (
    currentStatus === "APPROVED" ||
    currentStatus === "DELIVERED" ||
    currentStatus === "WON" ||
    currentReviewStatus === "APPROVED"
  ) {
    return "APPROVED";
  }
  if (
    currentStatus === "REJECTED" ||
    currentStatus === "LOST" ||
    currentReviewStatus === "REJECTED"
  ) {
    return "REJECTED";
  }
  if (
    currentStatus === "REVIEW" ||
    currentStatus === "REVIEWING" ||
    currentReviewStatus === "REVIEW" ||
    currentReviewStatus === "PENDING" ||
    currentReviewStatus === "REVIEWING"
  ) {
    return "REVIEWING";
  }
  if (currentStatus === "IN_PROGRESS" || currentStatus === "SUBMITTED") {
    return "IN_PROGRESS";
  }
  return "DRAFT";
}

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

export function normalizeSolution(solution) {
  return {
    id: solution?.id,
    solutionNo: solution?.solution_no || `SOL-${solution?.id || "NEW"}`,
    name: solution?.name || "未命名方案",
    solutionType: solution?.solution_type || "CUSTOM",
    industry: solution?.industry || "未分类行业",
    testType: solution?.test_type || "-",
    leadId: solution?.lead_id ?? solution?.leadId,
    ticketId: solution?.ticket_id ?? solution?.ticketId,
    customerId: solution?.customer_id ?? solution?.customerId,
    opportunityId: solution?.opportunity_id ?? solution?.opportunityId,
    projectId: solution?.project_id ?? solution?.projectId,
    requirementSummary: solution?.requirement_summary || "暂无需求摘要",
    solutionOverview: solution?.solution_overview || "暂无方案概述",
    technicalSpec: solution?.technical_spec || "暂无技术规格",
    estimatedCost: Number(solution?.estimated_cost) || 0,
    suggestedPrice: Number(solution?.suggested_price) || 0,
    estimatedHours: Number(solution?.estimated_hours) || 0,
    estimatedDuration: Number(solution?.estimated_duration) || 0,
    status: normalizeSolutionStatus(solution?.status, solution?.review_status),
    version: solution?.version || "V1.0",
    reviewStatus: solution?.review_status,
    reviewComment: solution?.review_comment,
    createdAt: solution?.created_at,
    updatedAt: solution?.updated_at,
  };
}

export function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatWan(amount) {
  if (!amount) {
    return "0.0";
  }
  return (Number(amount) / 10000).toFixed(1);
}

export function getStatusConfig(status) {
  return STATUS_CONFIG[status] || {
    label: status || "未知",
    className: "bg-slate-500/20 text-slate-200 border-slate-400/30",
  };
}

export function calculateCompleteness(solution) {
  let score = 20;
  if (solution.requirementSummary && solution.requirementSummary !== "暂无需求摘要") {
    score += 25;
  }
  if (solution.solutionOverview && solution.solutionOverview !== "暂无方案概述") {
    score += 25;
  }
  if (solution.technicalSpec && solution.technicalSpec !== "暂无技术规格") {
    score += 20;
  }
  if (solution.estimatedCost > 0 || solution.suggestedPrice > 0) {
    score += 10;
  }
  return Math.min(score, 100);
}
