/**
 * Page-level constants for SupplierManagement view
 * (Separate from the shared constants.js which is preserved as-is)
 */

export const levelConfig = {
  A级: {
    label: "A级",
    color: "bg-emerald-500/20 text-emerald-400",
    description: "优秀供应商",
  },
  B级: {
    label: "B级",
    color: "bg-amber-500/20 text-amber-400",
    description: "合格供应商",
  },
  C级: {
    label: "C级",
    color: "bg-orange-500/20 text-orange-400",
    description: "待改进",
  },
  D级: {
    label: "D级",
    color: "bg-red-500/20 text-red-400",
    description: "需淘汰",
  },
};

export const statusConfig = {
  active: { label: "活跃", color: "bg-blue-500/20 text-blue-400" },
  inactive: { label: "停用", color: "bg-slate-500/20 text-slate-400" },
  review: { label: "评审中", color: "bg-amber-500/20 text-amber-400" },
};
