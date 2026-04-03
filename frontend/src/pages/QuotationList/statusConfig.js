/**
 * Status configuration with colors and labels for quotation display
 */
export const statusConfig = {
  draft: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-400" },
  pending_approval: {
    label: "待审批",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  approved: {
    label: "已审批",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  sent: {
    label: "已发送",
    color: "bg-purple-500",
    textColor: "text-purple-400",
  },
  accepted: {
    label: "已接受",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  rejected: {
    label: "已拒绝",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
  expired: {
    label: "已过期",
    color: "bg-slate-600",
    textColor: "text-slate-500",
  },
};
