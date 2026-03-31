/**
 * Assembly Kit Board - Constants and Config
 */
import {
  Wrench,
  Package,
  Zap,
  Cable,
  Bug,
  Palette,
} from "lucide-react";

// 阶段图标映射
export const stageIcons = {
  FRAME: Wrench,
  MECH: Package,
  ELECTRIC: Zap,
  WIRING: Cable,
  DEBUG: Bug,
  COSMETIC: Palette,
};

// 预警级别配置
export const alertLevelConfig = {
  L1: {
    label: "停工预警",
    color: "bg-red-600",
    textColor: "text-red-600",
    bgLight: "bg-red-50 border-red-500",
  },
  L2: {
    label: "紧急预警",
    color: "bg-orange-500",
    textColor: "text-orange-600",
    bgLight: "bg-orange-50 border-orange-500",
  },
  L3: {
    label: "提前预警",
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
    bgLight: "bg-yellow-50 border-yellow-500",
  },
  L4: {
    label: "常规预警",
    color: "bg-blue-500",
    textColor: "text-blue-600",
    bgLight: "bg-blue-50 border-blue-500",
  },
};

// Utility functions
export const getKitRateColor = (rate) => {
  if (rate >= 100) return "text-emerald-600";
  if (rate >= 80) return "text-blue-600";
  if (rate >= 50) return "text-amber-600";
  return "text-red-600";
};

export const getProgressColor = (rate) => {
  if (rate >= 100) return "bg-emerald-500";
  if (rate >= 80) return "bg-blue-500";
  if (rate >= 50) return "bg-amber-500";
  return "bg-red-500";
};
