import {
  Activity,
  DollarSign,
  Clock,
  FileCheck,
  FolderOpen,
  BarChart3,
  FileText,
  CheckCircle2,
  XCircle,
} from "lucide-react";

// Animation variants
export const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

// Tab data
export const tabs = [
  { id: "overview", name: "概览", icon: Activity },
  { id: "costs", name: "费用归集", icon: DollarSign },
  { id: "timesheet", name: "工时汇总", icon: Clock },
  { id: "worklogs", name: "工作日志", icon: FileCheck },
  { id: "documents", name: "文档管理", icon: FolderOpen },
  { id: "reports", name: "费用报表", icon: BarChart3 },
];

// Status mapping
export const statusMap = {
  DRAFT: { label: "草稿", color: "secondary", icon: FileText },
  APPROVED: { label: "已审批", color: "success", icon: CheckCircle2 },
  IN_PROGRESS: { label: "进行中", color: "primary", icon: Clock },
  COMPLETED: { label: "已完成", color: "success", icon: CheckCircle2 },
  CANCELLED: { label: "已取消", color: "danger", icon: XCircle },
};

export const categoryTypeMap = {
  SELF: { label: "自主研发", color: "primary" },
  ENTRUST: { label: "委托研发", color: "info" },
  COOPERATION: { label: "合作研发", color: "success" },
};

// Legacy constants (used by hooks and other modules)
export const rdStatusConfigs = {
  planning: { label: "规划中", color: "bg-slate-500" },
  designing: { label: "设计中", color: "bg-blue-500" },
  developing: { label: "开发中", color: "bg-purple-500" },
  testing: { label: "测试中", color: "bg-amber-500" },
  completed: { label: "已完成", color: "bg-emerald-500" },
  cancelled: { label: "已取消", color: "bg-red-500" },
};

export const taskTypeConfigs = {
  design: { label: "设计", icon: "Pencil" },
  development: { label: "开发", icon: "Code" },
  testing: { label: "测试", icon: "CheckCircle" },
  review: { label: "评审", icon: "Eye" },
  documentation: { label: "文档", icon: "FileText" },
};

export const priorityConfigs = {
  low: { label: "低", color: "bg-slate-400" },
  normal: { label: "普通", color: "bg-blue-500" },
  high: { label: "高", color: "bg-amber-500" },
  urgent: { label: "紧急", color: "bg-red-500" },
};
