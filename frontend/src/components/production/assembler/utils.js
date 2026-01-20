import {
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
} from "lucide-react";

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

export const priorityConfigs = {
  low: { label: "低", color: "text-slate-400", bgColor: "bg-slate-500/10" },
  medium: { label: "中", color: "text-blue-400", bgColor: "bg-blue-500/10" },
  high: { label: "高", color: "text-amber-400", bgColor: "bg-amber-500/10" }
};
