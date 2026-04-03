import { User, Users, Building2 } from "lucide-react";

export const targetScopeOptions = [
  { value: "PERSONAL", label: "个人目标", icon: User },
  { value: "TEAM", label: "团队目标", icon: Users },
  { value: "DEPARTMENT", label: "部门目标", icon: Building2 },
];

export const targetTypeOptions = [
  { value: "LEAD_COUNT", label: "线索数量", unit: "个" },
  { value: "OPPORTUNITY_COUNT", label: "商机数量", unit: "个" },
  { value: "CONTRACT_AMOUNT", label: "合同金额", unit: "元" },
  { value: "COLLECTION_AMOUNT", label: "回款金额", unit: "元" },
];

export const targetPeriodOptions = [
  { value: "MONTHLY", label: "月度" },
  { value: "QUARTERLY", label: "季度" },
  { value: "YEARLY", label: "年度" },
];

export const statusConfigs = {
  ACTIVE: {
    label: "进行中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  CANCELLED: {
    label: "已取消",
    color: "bg-slate-500",
    textColor: "text-slate-400",
  },
};
