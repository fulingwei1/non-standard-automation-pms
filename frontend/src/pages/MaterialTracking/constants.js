/**
 * Material Tracking - Constants and configuration objects
 */

import { AlertTriangle, Truck, CheckCircle2, Zap } from "lucide-react";

export const statusConfig = {
  "not-arrived": {
    label: "未到货",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle,
    description: "采购订单已下达，等待物料到达"
  },
  "partial-arrived": {
    label: "部分到货",
    color: "bg-amber-500/20 text-amber-400",
    icon: Truck,
    description: "物料已部分到达，继续等待后续"
  },
  "fully-arrived": {
    label: "全部到货",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: CheckCircle2,
    description: "采购的全部物料已到达仓库"
  },
  "in-use": {
    label: "使用中",
    color: "bg-blue-500/20 text-blue-400",
    icon: Zap,
    description: "物料正在生产中使用"
  },
  completed: {
    label: "已完成",
    color: "bg-slate-500/20 text-slate-400",
    icon: CheckCircle2,
    description: "物料已全部使用或返库"
  }
};

export const qualityStatusConfig = {
  qualified: { label: "合格", color: "bg-emerald-500/20 text-emerald-400" },
  "pending-inspection": {
    label: "待检验",
    color: "bg-amber-500/20 text-amber-400"
  },
  rejected: { label: "不合格", color: "bg-red-500/20 text-red-400" }
};
