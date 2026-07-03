/**
 * Acceptance Management — shared constants / config maps
 */

// 状态配置
export const STATUS_CONFIG = {
  draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
  pending: { label: "待验收", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
  in_progress: { label: "进行中", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  passed: { label: "通过", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  failed: { label: "失败", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  signed: { label: "已签收", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
};

// 类型配置
export const TYPE_CONFIG = {
  FAT: { label: "FAT", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  SAT: { label: "SAT", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
};

// 结果配置
export const RESULT_CONFIG = {
  pass: { label: "通过", color: "bg-emerald-500/20 text-emerald-400" },
  fail: { label: "失败", color: "bg-red-500/20 text-red-400" },
  conditional: { label: "有条件通过", color: "bg-amber-500/20 text-amber-400" },
};
