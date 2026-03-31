/**
 * Purchase Order Detail - Constants and configuration maps
 */

import {
  FileText,
  Send,
  CheckCircle2,
  Truck,
  Package,
} from "lucide-react";

export const statusConfig = {
  draft: {
    label: "\u8349\u7a3f",
    color: "bg-slate-500/20 text-slate-400",
    icon: FileText,
  },
  submitted: {
    label: "\u5df2\u63d0\u4ea4",
    color: "bg-blue-500/20 text-blue-400",
    icon: Send,
  },
  confirmed: {
    label: "\u5df2\u786e\u8ba4",
    color: "bg-purple-500/20 text-purple-400",
    icon: CheckCircle2,
  },
  shipped: {
    label: "\u5df2\u53d1\u8d27",
    color: "bg-amber-500/20 text-amber-400",
    icon: Truck,
  },
  received: {
    label: "\u5df2\u6536\u8d27",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: Package,
  },
  invoiced: {
    label: "\u5df2\u5f00\u7968",
    color: "bg-indigo-500/20 text-indigo-400",
    icon: FileText,
  },
};

export const paymentStatusConfig = {
  unpaid: { label: "\u672a\u4ed8\u6b3e", color: "bg-red-500/20 text-red-400" },
  partial: { label: "\u90e8\u5206\u4ed8\u6b3e", color: "bg-amber-500/20 text-amber-400" },
  paid: { label: "\u5df2\u4ed8\u6b3e", color: "bg-emerald-500/20 text-emerald-400" },
};

export const invoiceStatusConfig = {
  pending: { label: "\u5f85\u5f00\u7968", color: "bg-slate-500/20 text-slate-400" },
  partial: { label: "\u90e8\u5206\u5f00\u7968", color: "bg-amber-500/20 text-amber-400" },
  complete: { label: "\u5df2\u5f00\u7968", color: "bg-emerald-500/20 text-emerald-400" },
};
