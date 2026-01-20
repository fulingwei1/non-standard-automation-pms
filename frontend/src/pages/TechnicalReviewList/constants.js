export const REVIEW_STATUS_BADGES = {
    DRAFT: { label: "草稿", variant: "secondary", color: "text-slate-400" },
    PENDING: { label: "待评审", variant: "info", color: "text-blue-400" },
    IN_PROGRESS: { label: "评审中", variant: "warning", color: "text-amber-400" },
    COMPLETED: { label: "已完成", variant: "success", color: "text-emerald-400" },
    CANCELLED: { label: "已取消", variant: "danger", color: "text-red-400" },
};

export const REVIEW_TYPES = {
    PDR: "方案设计评审",
    DDR: "详细设计评审",
    PRR: "生产准备评审",
    FRR: "出厂评审",
    ARR: "现场评审",
};

export const REVIEW_TYPE_COLORS = {
    PDR: "bg-blue-500/20 text-blue-400",
    DDR: "bg-purple-500/20 text-purple-400",
    PRR: "bg-amber-500/20 text-amber-400",
    FRR: "bg-green-500/20 text-green-400",
    ARR: "bg-orange-500/20 text-orange-400",
};

export const REVIEW_CONCLUSION_BADGES = {
    PASS: { label: "通过", color: "bg-emerald-500/20 text-emerald-400" },
    PASS_WITH_CONDITION: { label: "有条件通过", color: "bg-amber-500/20 text-amber-400" },
    REJECT: { label: "不通过", color: "bg-red-500/20 text-red-400" },
    ABORT: { label: "中止", color: "bg-slate-500/20 text-slate-400" },
};

export const getStatusBadge = (status) => REVIEW_STATUS_BADGES[status] || REVIEW_STATUS_BADGES.DRAFT;
export const getReviewTypeLabel = (type) => REVIEW_TYPES[type] || type;
export const getReviewTypeColor = (type) => REVIEW_TYPE_COLORS[type] || "bg-slate-500/20 text-slate-400";
export const getConclusionBadge = (conclusion) => REVIEW_CONCLUSION_BADGES[conclusion] || null;
