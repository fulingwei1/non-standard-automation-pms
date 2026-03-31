/**
 * KPI 管理列表 - 常量配置
 */
import {
  CheckCircle2,
  AlertCircle,
  XCircle,
  Calendar,
} from "lucide-react";

// 健康状态配置
export const HEALTH_STATUS = {
  ON_TRACK: {
    label: "正常",
    color: "#22c55e",
    bgColor: "bg-emerald-500/20",
    borderColor: "border-emerald-500/30",
    icon: CheckCircle2,
  },
  AT_RISK: {
    label: "预警",
    color: "#f59e0b",
    bgColor: "bg-amber-500/20",
    borderColor: "border-amber-500/30",
    icon: AlertCircle,
  },
  OFF_TRACK: {
    label: "落后",
    color: "#ef4444",
    bgColor: "bg-red-500/20",
    borderColor: "border-red-500/30",
    icon: XCircle,
  },
};

// 采集频率配置
export const COLLECTION_FREQUENCY = {
  DAILY: { label: "每日", icon: Calendar },
  WEEKLY: { label: "每周", icon: Calendar },
  MONTHLY: { label: "每月", icon: Calendar },
  QUARTERLY: { label: "每季", icon: Calendar },
  YEARLY: { label: "每年", icon: Calendar },
};
