import {
  LayoutDashboard,
  ListTodo,
  Flag,
  GitBranch,
  CreditCard,
  PieChart,
} from "lucide-react";

// Tab 配置
export const PROJECT_TABS = [
  { id: "overview", label: "概览", icon: LayoutDashboard },
  { id: "tasks", label: "任务", icon: ListTodo },
  { id: "milestones", label: "里程碑", icon: Flag },
  { id: "gantt", label: "甘特图", icon: GitBranch },
  { id: "budget", label: "预算", icon: CreditCard },
  { id: "profit", label: "利润", icon: PieChart },
];

export const STATUS_CONFIG = {
  planning: { label: "规划中", color: "bg-gray-500" },
  in_progress: { label: "进行中", color: "bg-blue-500" },
  on_hold: { label: "暂停", color: "bg-yellow-500" },
  completed: { label: "已完成", color: "bg-green-500" },
  cancelled: { label: "已取消", color: "bg-red-500" },
  archived: { label: "已归档", color: "bg-purple-500" },
};

export const PRIORITY_CONFIG = {
  low: { label: "低", color: "bg-green-500" },
  medium: { label: "中", color: "bg-yellow-500" },
  high: { label: "高", color: "bg-red-500" },
  critical: { label: "关键", color: "bg-red-600" },
};
