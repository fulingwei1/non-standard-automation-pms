import {
  ClipboardCheck,
  Package,
  Car,
  Building2,
  Calendar,
  User,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Approval type configuration
// ---------------------------------------------------------------------------
export const approvalTypeConfigs = {
  leave: { label: "请假", icon: "Calendar" },
  expense: { label: "报销", icon: "Receipt" },
  travel: { label: "出差", icon: "Plane" },
  overtime: { label: "加班", icon: "Clock" },
  other: { label: "其他", icon: "FileText" },
};

// ---------------------------------------------------------------------------
// Status badge configuration
// ---------------------------------------------------------------------------
export const statusConfigs = {
  pending: { label: "待审批", color: "bg-amber-500" },
  approved: { label: "已通过", color: "bg-emerald-500" },
  rejected: { label: "已驳回", color: "bg-red-500" },
};

// ---------------------------------------------------------------------------
// Type icon map (component references)
// ---------------------------------------------------------------------------
export const TYPE_ICON_MAP = {
  office_supplies: Package,
  vehicle: Car,
  asset: Building2,
  meeting: Calendar,
  leave: User,
};

export const DEFAULT_TYPE_ICON = ClipboardCheck;

// ---------------------------------------------------------------------------
// Type label map
// ---------------------------------------------------------------------------
export const TYPE_LABEL_MAP = {
  office_supplies: "办公用品",
  vehicle: "车辆",
  asset: "资产",
  meeting: "会议",
  leave: "请假",
};

export const DEFAULT_TYPE_LABEL = "其他";

// ---------------------------------------------------------------------------
// Type badge class map
// ---------------------------------------------------------------------------
export const TYPE_BADGE_CLASS_MAP = {
  office_supplies: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  vehicle: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  asset: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  meeting: "bg-green-500/20 text-green-400 border-green-500/30",
  leave: "bg-pink-500/20 text-pink-400 border-pink-500/30",
};

// ---------------------------------------------------------------------------
// Select filter options
// ---------------------------------------------------------------------------
export const TYPE_FILTER_OPTIONS = [
  { value: "all", label: "全部类型" },
  { value: "office_supplies", label: "办公用品" },
  { value: "vehicle", label: "车辆" },
  { value: "asset", label: "资产" },
  { value: "meeting", label: "会议" },
  { value: "leave", label: "请假" },
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: "all", label: "全部优先级" },
  { value: "high", label: "紧急" },
  { value: "medium", label: "普通" },
  { value: "low", label: "低" },
];

// ---------------------------------------------------------------------------
// Monthly trend seed data (static baseline months)
// ---------------------------------------------------------------------------
export const MONTHLY_TREND_BASELINE = [
  { month: "2024-10", amount: 18 },
  { month: "2024-11", amount: 22 },
  { month: "2024-12", amount: 20 },
];
