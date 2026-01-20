/**
 * Service Ticket Constants
 * 服务工单常量配置
 */

import { Send, CheckCircle2, Download } from "lucide-react";

// 状态配置
export const statusConfig = {
  待分配: {
    label: "待分配",
    color: "bg-slate-500",
    textColor: "text-slate-400",
    value: "PENDING",
  },
  处理中: {
    label: "处理中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    value: "IN_PROGRESS",
  },
  待验证: {
    label: "待验证",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    value: "PENDING_VERIFY",
  },
  已关闭: {
    label: "已关闭",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    value: "CLOSED",
  },
};

// 紧急程度配置
export const urgencyConfig = {
  紧急: {
    label: "紧急",
    color: "text-red-400",
    bg: "bg-red-500/20",
    value: "URGENT",
    icon: "🔥",
  },
  高: {
    label: "高",
    color: "text-orange-400",
    bg: "bg-orange-500/20",
    value: "HIGH",
    icon: "⚠️",
  },
  中: {
    label: "中",
    color: "text-yellow-400",
    bg: "bg-yellow-500/20",
    value: "MEDIUM",
    icon: "📋",
  },
  低: {
    label: "低",
    color: "text-slate-400",
    bg: "bg-slate-500/20",
    value: "LOW",
    icon: "📝",
  },
  普通: {
    label: "普通",
    color: "text-slate-400",
    bg: "bg-slate-500/20",
    value: "NORMAL",
    icon: "📄",
  },
};

// 问题类型配置
export const problemTypeConfig = {
  软件问题: {
    label: "软件问题",
    icon: "💻",
    value: "SOFTWARE",
  },
  机械问题: {
    label: "机械问题",
    icon: "⚙️",
    value: "MECHANICAL",
  },
  电气问题: {
    label: "电气问题",
    icon: "⚡",
    value: "ELECTRICAL",
  },
  操作问题: {
    label: "操作问题",
    icon: "👤",
    value: "OPERATION",
  },
  其他: {
    label: "其他",
    icon: "📋",
    value: "OTHER",
  },
};

// 筛选选项
export const filterOptions = {
  status: [
    { label: "全部状态", value: "ALL" },
    { label: "待分配", value: "待分配" },
    { label: "处理中", value: "处理中" },
    { label: "待验证", value: "待验证" },
    { label: "已关闭", value: "已关闭" },
  ],
  urgency: [
    { label: "全部紧急程度", value: "ALL" },
    { label: "紧急", value: "紧急" },
    { label: "高", value: "高" },
    { label: "中", value: "中" },
    { label: "低", value: "低" },
    { label: "普通", value: "普通" },
  ],
  problemType: [
    { label: "全部类型", value: "ALL" },
    { label: "软件问题", value: "软件问题" },
    { label: "机械问题", value: "机械问题" },
    { label: "电气问题", value: "电气问题" },
    { label: "操作问题", value: "操作问题" },
    { label: "其他", value: "其他" },
  ],
};

// 排序选项
export const sortOptions = [
  { label: "按报告时间", value: "reported_time" },
  { label: "按状态", value: "status" },
  { label: "按紧急程度", value: "urgency" },
];

// 批量操作选项
export const batchActions = [
  { label: "批量分配", value: "assign", icon: Send },
  { label: "批量关闭", value: "close", icon: CheckCircle2 },
  { label: "批量导出", value: "export", icon: Download },
];

// 表单默认值
export const defaultFormData = {
  project_code: "",
  machine_no: "",
  customer_name: "",
  problem_type: "",
  problem_desc: "",
  urgency: "普通",
  reported_by: "",
  reported_phone: "",
  assigned_to: "",
};

// 关闭工单默认值
export const defaultCloseData = {
  solution: "",
  root_cause: "",
  preventive_action: "",
  satisfaction: "",
  feedback: "",
};

// 后端状态映射到前端
export const backendToFrontendStatus = {
  PENDING: "待分配",
  ASSIGNED: "处理中",
  IN_PROGRESS: "处理中",
  PENDING_VERIFY: "待验证",
  CLOSED: "已关闭",
};

// 前端状态映射到后端
export const frontendToBackendStatus = {
  待分配: "PENDING",
  处理中: "IN_PROGRESS",
  待验证: "PENDING_VERIFY",
  已关闭: "CLOSED",
};

// 后端紧急程度映射到前端
export const backendToFrontendUrgency = {
  URGENT: "紧急",
  HIGH: "高",
  MEDIUM: "中",
  LOW: "低",
};

// 前端紧急程度映射到后端
export const frontendToBackendUrgency = {
  紧急: "URGENT",
  高: "HIGH",
  中: "MEDIUM",
  低: "LOW",
  普通: "NORMAL",
};

// 辅助函数
export const getStatusBadge = (status) => {
  const config = statusConfig[status];
  if (!config) {return status;}

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${config.color} ${config.textColor}`}
    >
      {config.label}
    </span>
  );
};

export const getUrgencyBadge = (urgency) => {
  const config = urgencyConfig[urgency];
  if (!config) {return urgency;}

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}
    >
      {config.icon} {config.label}
    </span>
  );
};

export const getProblemTypeBadge = (problemType) => {
  const config = problemTypeConfig[problemType];
  if (!config) {return problemType;}

  return (
    <span className="inline-flex items-center gap-1 text-sm text-slate-300">
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </span>
  );
};

export const mapBackendStatus = (backendStatus) => {
  return backendToFrontendStatus[backendStatus] || backendStatus;
};

export const mapBackendUrgency = (backendUrgency) => {
  return backendToFrontendUrgency[backendUrgency] || backendUrgency;
};

export const mapFrontendStatus = (frontendStatus) => {
  return frontendToBackendStatus[frontendStatus] || frontendStatus;
};

export const mapFrontendUrgency = (frontendUrgency) => {
  return frontendToBackendUrgency[frontendUrgency] || frontendUrgency;
};

// 状态排序权重（用于排序）
export const statusOrderWeight = {
  待分配: 1,
  处理中: 2,
  待验证: 3,
  已关闭: 4,
};

// 紧急程度排序权重（用于排序）
export const urgencyOrderWeight = {
  紧急: 1,
  高: 2,
  中: 3,
  低: 4,
  普通: 5,
};

// 快捷键配置
export const keyboardShortcuts = {
  closeDialog: "Escape",
  focusSearch: "CmdOrCtrl + K",
  refresh: "F5",
};

// 导出所有配置
export default {
  statusConfig,
  urgencyConfig,
  problemTypeConfig,
  filterOptions,
  sortOptions,
  batchActions,
  defaultFormData,
  defaultCloseData,
  backendToFrontendStatus,
  frontendToBackendStatus,
  backendToFrontendUrgency,
  frontendToBackendUrgency,
  getStatusBadge,
  getUrgencyBadge,
  getProblemTypeBadge,
  mapBackendStatus,
  mapBackendUrgency,
  mapFrontendStatus,
  mapFrontendUrgency,
  statusOrderWeight,
  urgencyOrderWeight,
  keyboardShortcuts,
};
