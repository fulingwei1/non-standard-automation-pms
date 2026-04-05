// Status configuration — merged from both sources
export const statusConfig = {
  draft: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-400" },
  pending_sign: {
    label: "待签约",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  pending: {
    label: "待审批",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  active: { label: "执行中", color: "bg-blue-500", textColor: "text-blue-400" },
  completed: {
    label: "已完成",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  terminated: {
    label: "已终止",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

// Aliases kept for backwards compatibility
export const contractStatusConfigs = statusConfig;

export const contractTypeConfigs = {
  sales: { label: "销售合同" },
  purchase: { label: "采购合同" },
  service: { label: "服务合同" },
  framework: { label: "框架协议" },
};

export const paymentTypeLabels = {
  deposit: "签约款",
  progress: "进度款",
  delivery: "发货款",
  acceptance: "验收款",
  warranty: "质保金",
};
