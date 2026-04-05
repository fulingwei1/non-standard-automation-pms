import { MapPin, Video, Phone } from "lucide-react";

// 调研方式配置
export const surveyMethods = [
  { id: "onsite", name: "现场调研", icon: MapPin, color: "text-emerald-400" },
  { id: "remote", name: "远程调研", icon: Video, color: "text-blue-400" },
  { id: "phone", name: "电话调研", icon: Phone, color: "text-amber-400" },
];

// 调研状态配置
export const surveyStatuses = [
  { id: "all", name: "全部", color: "bg-slate-500" },
  { id: "scheduled", name: "已排期", color: "bg-blue-500" },
  { id: "in_progress", name: "进行中", color: "bg-amber-500" },
  { id: "completed", name: "已完成", color: "bg-emerald-500" },
  { id: "cancelled", name: "已取消", color: "bg-red-500" },
];
