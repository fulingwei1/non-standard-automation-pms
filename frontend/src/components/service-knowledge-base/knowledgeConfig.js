/**
 * 服务知识库 - 配置
 */

// 分类配置
export const categoryConfig = {
  故障处理: { label: "故障处理", color: "text-red-400", bg: "bg-red-500/20" },
  操作指南: { label: "操作指南", color: "text-blue-400", bg: "bg-blue-500/20" },
  技术文档: {
    label: "技术文档",
    color: "text-purple-400",
    bg: "bg-purple-500/20"
  },
  FAQ: { label: "FAQ", color: "text-green-400", bg: "bg-green-500/20" },
  其他: { label: "其他", color: "text-slate-400", bg: "bg-slate-500/20" }
};

// 状态配置
export const statusConfig = {
  草稿: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-400" },
  已发布: {
    label: "已发布",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  已归档: {
    label: "已归档",
    color: "bg-slate-600",
    textColor: "text-slate-400"
  }
};
