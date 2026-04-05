/**
 * BOM Assembly Attributes - Constants and configuration
 */
import {
  Wrench,
  Package,
  Zap,
  Cable,
  Bug,
  Palette,
} from "lucide-react";

// 装配阶段配置
export const stageOptions = [
  { value: "FRAME", label: "框架装配", icon: Wrench, color: "bg-slate-500" },
  { value: "MECH", label: "机械模组", icon: Package, color: "bg-blue-500" },
  { value: "ELECTRIC", label: "电气安装", icon: Zap, color: "bg-yellow-500" },
  { value: "WIRING", label: "线路整理", icon: Cable, color: "bg-green-500" },
  { value: "DEBUG", label: "调试准备", icon: Bug, color: "bg-purple-500" },
  { value: "COSMETIC", label: "外观完善", icon: Palette, color: "bg-pink-500" },
];

// 重要程度配置
export const importanceOptions = [
  { value: "CRITICAL", label: "关键", color: "bg-red-500" },
  { value: "HIGH", label: "高", color: "bg-orange-500" },
  { value: "NORMAL", label: "普通", color: "bg-blue-500" },
  { value: "LOW", label: "低", color: "bg-slate-500" },
];

export const getStageOption = (code) =>
  (stageOptions || []).find((s) => s.value === code) || stageOptions[1];
