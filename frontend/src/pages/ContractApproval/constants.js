import { FileCheck, FileText, DollarSign } from "lucide-react";

// Existing approval-status configs (preserved)
export const approvalStatusConfigs = {
  pending: { label: "待审批", color: "bg-amber-500" },
  approved: { label: "已通过", color: "bg-emerald-500" },
  rejected: { label: "已驳回", color: "bg-red-500" },
};

// Existing contract-type configs (preserved)
export const contractTypeConfigs = {
  sales: { label: "销售合同" },
  purchase: { label: "采购合同" },
  service: { label: "服务合同" },
};

// Type config used by the approval cards / list
export const typeConfig = {
  contract: {
    label: "合同",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    icon: FileCheck,
  },
  quotation: {
    label: "报价",
    color: "bg-purple-500",
    textColor: "text-purple-400",
    icon: FileText,
  },
  discount: {
    label: "优惠",
    color: "bg-red-500",
    textColor: "text-red-400",
    icon: DollarSign,
  },
};

// Priority config used by the approval cards / list
export const priorityConfig = {
  high: { label: "紧急", color: "bg-red-500", textColor: "text-red-400" },
  medium: { label: "普通", color: "bg-amber-500", textColor: "text-amber-400" },
  low: { label: "低", color: "bg-slate-500", textColor: "text-slate-400" },
};
