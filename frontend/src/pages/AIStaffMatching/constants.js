// -*- coding: utf-8 -*-
import { Star, TrendingUp, Check, AlertCircle } from "lucide-react";

// 推荐类型配置
export const RECOMMENDATION_CONFIG = {
  STRONG: { color: "green", text: "强烈推荐", icon: Star },
  RECOMMENDED: { color: "blue", text: "推荐", icon: TrendingUp },
  ACCEPTABLE: { color: "yellow", text: "可接受", icon: Check },
  WEAK: { color: "red", text: "较弱匹配", icon: AlertCircle }
};

// 优先级配置
export const PRIORITY_CONFIG = {
  P1: { color: "red", text: "P1-紧急", threshold: 85 },
  P2: { color: "orange", text: "P2-高", threshold: 75 },
  P3: { color: "blue", text: "P3-中", threshold: 65 },
  P4: { color: "green", text: "P4-低", threshold: 55 },
  P5: { color: "slate", text: "P5-最低", threshold: 50 }
};

// 维度配置
export const DIMENSIONS = [
  { key: "skill", label: "技能匹配", weight: 30 },
  { key: "domain", label: "领域经验", weight: 15 },
  { key: "attitude", label: "工作态度", weight: 20 },
  { key: "quality", label: "历史质量", weight: 15 },
  { key: "workload", label: "工作负载", weight: 15 },
  { key: "special", label: "特殊能力", weight: 5 }
];

// Legacy exports for backward compatibility with hooks
export const skillConfigs = {
  mechanical: { label: '机械设计', color: 'bg-blue-500' },
  electrical: { label: '电气设计', color: 'bg-amber-500' },
  plc: { label: 'PLC编程', color: 'bg-purple-500' },
  vision: { label: '视觉检测', color: 'bg-cyan-500' },
  assembly: { label: '装配调试', color: 'bg-emerald-500' },
  pm: { label: '项目管理', color: 'bg-indigo-500' },
};

export const matchScoreConfigs = {
  excellent: { min: 90, label: '优秀匹配', color: 'text-emerald-500' },
  good: { min: 70, label: '良好匹配', color: 'text-blue-500' },
  fair: { min: 50, label: '一般匹配', color: 'text-amber-500' },
  poor: { min: 0, label: '较差匹配', color: 'text-red-500' },
};

export const roleConfigs = {
  lead: { label: '项目负责人', level: 1 },
  engineer: { label: '工程师', level: 2 },
  technician: { label: '技术员', level: 3 },
  assistant: { label: '助理', level: 4 },
};
