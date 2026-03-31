/**
 * Engineer Workstation - Constants, configs, and status mappings
 */

import {
  Circle,
  PlayCircle,
  PauseCircle,
  CheckCircle2,
  BarChart3,
  CalendarDays,
  List,
  Briefcase,
  FileText,
  ClipboardCheck,
  Box,
  Layers,
} from "lucide-react";

// Task type configs
export const taskTypeConfigs = {
  design: {
    label: "结构设计",
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    icon: Box
  },
  drawing: {
    label: "出图",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    icon: FileText
  },
  bom: {
    label: "BOM",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    icon: Layers
  },
  review: {
    label: "评审",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    icon: ClipboardCheck
  }
};

// Status configs
export const statusConfigs = {
  pending: {
    label: "待开始",
    icon: Circle,
    color: "text-slate-400",
    bgColor: "bg-slate-500/10"
  },
  in_progress: {
    label: "进行中",
    icon: PlayCircle,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10"
  },
  blocked: {
    label: "已阻塞",
    icon: PauseCircle,
    color: "text-red-400",
    bgColor: "bg-red-500/10"
  },
  completed: {
    label: "已完成",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10"
  }
};

// Priority configs
export const priorityConfigs = {
  low: { label: "低", color: "text-slate-400", flagColor: "text-slate-400" },
  medium: { label: "中", color: "text-blue-400", flagColor: "text-blue-400" },
  high: { label: "高", color: "text-amber-400", flagColor: "text-amber-400" },
  critical: { label: "紧急", color: "text-red-400", flagColor: "text-red-400" }
};

// View modes
export const VIEW_MODES = {
  gantt: { id: "gantt", label: "甘特图", icon: BarChart3 },
  calendar: { id: "calendar", label: "日历", icon: CalendarDays },
  list: { id: "list", label: "列表", icon: List },
  project: { id: "project", label: "项目视图", icon: Briefcase }
};
