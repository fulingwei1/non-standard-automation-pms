/**
 * 售前技术任务中心 - 常量配置
 */
import {
  ListTodo,
  ClipboardList,
  MessageSquare,
  FileText,
  Eye,
  DollarSign,
  Target,
  LifeBuoy,
} from "lucide-react";

// 任务类型配置
export const taskTypes = [
  { id: "all", name: "全部", icon: ListTodo, color: "text-slate-400" },
  {
    id: "support",
    name: "售前支持",
    icon: LifeBuoy,
    color: "text-cyan-400",
  },
  {
    id: "survey",
    name: "需求调研",
    icon: ClipboardList,
    color: "text-emerald-400",
  },
  {
    id: "exchange",
    name: "技术交流",
    icon: MessageSquare,
    color: "text-blue-400",
  },
  {
    id: "solution",
    name: "方案设计",
    icon: FileText,
    color: "text-violet-400",
  },
  { id: "review", name: "方案评审", icon: Eye, color: "text-pink-400" },
  {
    id: "costing",
    name: "成本核算",
    icon: DollarSign,
    color: "text-emerald-400",
  },
  { id: "bidding", name: "投标支持", icon: Target, color: "text-amber-400" },
];

// 任务状态配置
export const taskStatuses = [
  {
    id: "pending",
    name: "待处理",
    color: "bg-slate-500",
    textColor: "text-slate-400",
  },
  {
    id: "in_progress",
    name: "进行中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  {
    id: "reviewing",
    name: "待评审",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  {
    id: "completed",
    name: "已完成",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
];

// 获取优先级样式
export const getPriorityStyle = (priority) => {
  switch (priority) {
    case "high":
      return { bg: "bg-red-500/10", text: "text-red-400", label: "紧急" };
    case "medium":
      return { bg: "bg-amber-500/10", text: "text-amber-400", label: "中等" };
    case "low":
      return { bg: "bg-slate-500/10", text: "text-slate-400", label: "普通" };
    default:
      return { bg: "bg-slate-500/10", text: "text-slate-400", label: "普通" };
  }
};
