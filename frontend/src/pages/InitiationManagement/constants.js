export const INITIATION_STATUS_BADGES = {
    DRAFT: { label: "草稿", variant: "secondary" },
    SUBMITTED: { label: "已提交", variant: "info" },
    REVIEWING: { label: "评审中", variant: "warning" },
    APPROVED: { label: "已通过", variant: "success" },
    REJECTED: { label: "已驳回", variant: "danger" }
};

export const getStatusBadge = (status) => INITIATION_STATUS_BADGES[status] || INITIATION_STATUS_BADGES.DRAFT;
