export const STATUS_BADGES = {
    DRAFT: { label: "草稿", variant: "secondary" },
    SUBMITTED: { label: "已提交", variant: "info" },
    REVIEWED: { label: "已评审", variant: "success" }
};

export const getStatusBadge = (status) => {
    return STATUS_BADGES[status] || STATUS_BADGES.DRAFT;
};
