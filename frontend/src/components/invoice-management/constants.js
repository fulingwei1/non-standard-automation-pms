import { FileText, Clock, Check, X, TrendingUp, AlertTriangle } from "lucide-react";

export const statusMap = {
  DRAFT: "draft",
  APPLIED: "applied",
  APPROVED: "approved",
  ISSUED: "issued",
  VOID: "void"
};

export const paymentStatusMap = {
  PENDING: "pending",
  PARTIAL: "partial",
  PAID: "paid",
  OVERDUE: "overdue"
};

export const statusConfig = {
  draft: {
    label: "草稿",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText
  },
  applied: {
    label: "申请中",
    color: "bg-blue-500/20 text-blue-400",
    icon: Clock
  },
  approved: {
    label: "已批准",
    color: "bg-purple-500/20 text-purple-400",
    icon: Check
  },
  issued: {
    label: "已开票",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  void: { label: "作废", color: "bg-red-500/20 text-red-400", icon: X }
};

export const paymentStatusConfig = {
  pending: {
    label: "未收款",
    color: "bg-slate-500/20 text-slate-400",
    icon: Clock
  },
  partial: {
    label: "部分收款",
    color: "bg-amber-500/20 text-amber-400",
    icon: TrendingUp
  },
  paid: {
    label: "已收款",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Check
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle
  }
};
