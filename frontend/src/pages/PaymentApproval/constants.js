export const approvalStatusConfigs = {
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
};

export const paymentTypeConfigs = {
    advance: { label: '预付款' },
    progress: { label: '进度款' },
    final: { label: '尾款' },
    warranty: { label: '质保金' },
};

// Payment type display config used by the approval page
// Icons are imported here so consumers only need to import from this file
import { ShoppingCart, Receipt, FileText, Users } from "lucide-react";

export const typeConfig = {
  purchase: {
    label: "采购付款",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: ShoppingCart,
  },
  outsourcing: {
    label: "外协付款",
    color: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    icon: Receipt,
  },
  expense: {
    label: "费用报销",
    color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    icon: FileText,
  },
  salary: {
    label: "工资发放",
    color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    icon: Users,
  },
};

export const PRIORITY_OPTIONS = [
  { value: "all", label: "全部优先级" },
  { value: "urgent", label: "紧急" },
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
  { value: "low", label: "低" },
];
