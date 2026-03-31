export const reviewStatusConfigs = {
    pending: { label: '待评审', color: 'bg-amber-500' },
    in_review: { label: '评审中', color: 'bg-blue-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
    revised: { label: '需修改', color: 'bg-purple-500' },
};

export const decisionOptions = [
    { value: 'approve', label: '通过' },
    { value: 'reject', label: '驳回' },
    { value: 'revise', label: '需修改' },
];

export const STATUS_BADGE_MAP = {
    DRAFT: { label: "草稿", color: "bg-slate-500/20 text-slate-400" },
    PENDING: { label: "待评审", color: "bg-blue-500/20 text-blue-400" },
    IN_PROGRESS: { label: "评审中", color: "bg-amber-500/20 text-amber-400" },
    COMPLETED: { label: "已完成", color: "bg-emerald-500/20 text-emerald-400" },
    CANCELLED: { label: "已取消", color: "bg-red-500/20 text-red-400" },
};

export const REVIEW_TYPE_LABELS = {
    PDR: "方案设计评审",
    DDR: "详细设计评审",
    PRR: "生产准备评审",
    FRR: "出厂评审",
    ARR: "现场评审",
};

export const ISSUE_LEVEL_COLORS = {
    A: "bg-red-500/20 text-red-400",
    B: "bg-orange-500/20 text-orange-400",
    C: "bg-amber-500/20 text-amber-400",
};

export const CHECKLIST_RESULT_COLORS = {
    PASS: "bg-emerald-500/20 text-emerald-400",
    FAIL: "bg-red-500/20 text-red-400",
    NA: "bg-slate-500/20 text-slate-400",
};

export const DEFAULT_FORM_DATA = {
    review_type: "PDR",
    review_name: "",
    project_id: "",
    equipment_id: "",
    scheduled_date: "",
    location: "",
    meeting_type: "ONSITE",
    host_id: "",
    presenter_id: "",
    recorder_id: "",
};

/**
 * Returns the badge config for a given status key.
 * Falls back to DRAFT if the status is not found.
 */
export function getStatusBadge(status) {
    return STATUS_BADGE_MAP[status] || STATUS_BADGE_MAP.DRAFT;
}

/**
 * Returns the human-readable label for a review type code.
 */
export function getReviewTypeLabel(type) {
    return REVIEW_TYPE_LABELS[type] || type;
}
