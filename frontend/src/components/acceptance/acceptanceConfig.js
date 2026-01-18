/**
 * 验收管理 - 配置
 */

import {
  FileText,
  Clock,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ClipboardList
} from "lucide-react";

// 验收类型配置
export const typeConfigs = {
  FAT: { label: "出厂验收", color: "text-blue-400", bgColor: "bg-blue-500/10" },
  SAT: {
    label: "现场验收",
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
  },
  FINAL: {
    label: "终验收",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
};

// 状态配置
export const statusConfigs = {
  draft: { label: "草稿", color: "bg-slate-500", icon: FileText },
  ready: { label: "待验收", color: "bg-slate-500", icon: Clock },
  pending: { label: "待验收", color: "bg-slate-500", icon: Clock },
  pending_sign: { label: "待签字", color: "bg-amber-500", icon: AlertCircle },
  in_progress: { label: "验收中", color: "bg-blue-500", icon: ClipboardList },
  completed: { label: "已完成", color: "bg-emerald-500", icon: CheckCircle2 },
  cancelled: { label: "已取消", color: "bg-gray-500", icon: XCircle },
  failed: { label: "未通过", color: "bg-red-500", icon: XCircle },
};

// 严重程度配置
export const severityConfigs = {
  critical: {
    label: "严重",
    color: "bg-red-500/20 text-red-400 border-red-500/30",
  },
  major: {
    label: "主要",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  },
  minor: {
    label: "次要",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
};
