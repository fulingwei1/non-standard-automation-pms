/**
 * 任务中心 - 配置
 */

import {
  Circle,
  PlayCircle,
  PauseCircle,
  CheckCircle2
} from "lucide-react";

// 状态配置
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
    label: "阻塞",
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

// 优先级配置
export const priorityConfigs = {
  low: { label: "低", color: "text-slate-400", flagColor: "text-slate-400" },
  medium: { label: "中", color: "text-blue-400", flagColor: "text-blue-400" },
  high: { label: "高", color: "text-amber-400", flagColor: "text-amber-400" },
  critical: { label: "紧急", color: "text-red-400", flagColor: "text-red-400" }
};
