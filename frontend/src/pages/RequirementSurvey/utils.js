import { surveyStatuses, surveyMethods } from "./constants";

// 获取状态样式
export const getStatusStyle = (status) => {
  const config = (surveyStatuses || []).find((s) => s.id === status);
  return config?.color || "bg-slate-500";
};

// 获取状态名称
export const getStatusName = (status) => {
  const config = (surveyStatuses || []).find((s) => s.id === status);
  return config?.name || status;
};

// 获取调研方式图标
export const getMethodIcon = (method) => {
  const config = (surveyMethods || []).find((m) => m.id === method);
  return config || surveyMethods[0];
};

// Map backend ticket type to frontend method
export const mapTicketTypeToMethod = (ticketType) => {
  const typeMap = {
    REQUIREMENT_RESEARCH: "onsite",
    TECHNICAL_EXCHANGE: "remote",
    SITE_VISIT: "onsite",
  };
  return typeMap[ticketType] || "onsite";
};

// Map backend status to frontend status
export const mapTicketStatus = (backendStatus) => {
  const statusMap = {
    PENDING: "scheduled",
    ACCEPTED: "scheduled",
    IN_PROGRESS: "in_progress",
    COMPLETED: "completed",
    CANCELLED: "cancelled",
  };
  return statusMap[backendStatus] || "scheduled";
};
