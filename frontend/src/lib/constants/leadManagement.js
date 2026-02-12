export const statusConfig = {
  NEW: { label: "待跟进", color: "bg-blue-500", textColor: "text-blue-400" },
  CONTACTED: {
    label: "已联系",
    color: "bg-sky-500",
    textColor: "text-sky-400",
  },
  QUALIFIED: {
    label: "已合格",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  LOST: { label: "已丢失", color: "bg-red-500", textColor: "text-red-400" },
  CONVERTED: {
    label: "已转商机",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
  },
  // 兼容旧状态值
  QUALIFYING: {
    label: "已合格",
    color: "bg-amber-500",
    textColor: "text-amber-400",
  },
  INVALID: { label: "已丢失", color: "bg-red-500", textColor: "text-red-400" },
};

// 线索来源选项
export const sourceOptions = [
  { value: "exhibition", label: "展会" },
  { value: "referral", label: "转介绍" },
  { value: "website", label: "官网" },
  { value: "cold_call", label: "电销" },
  { value: "social_media", label: "社交媒体" },
  { value: "advertising", label: "广告投放" },
  { value: "partner", label: "合作伙伴" },
  { value: "other", label: "其他" },
];
