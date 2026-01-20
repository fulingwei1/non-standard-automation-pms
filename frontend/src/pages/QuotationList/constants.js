export const quotationStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已审批', color: 'bg-blue-500' },
    sent: { label: '已发送', color: 'bg-purple-500' },
    accepted: { label: '已接受', color: 'bg-emerald-500' },
    rejected: { label: '已拒绝', color: 'bg-red-500' },
    expired: { label: '已过期', color: 'bg-slate-400' },
};

export const validityPeriods = [
    { value: 7, label: '7天' },
    { value: 15, label: '15天' },
    { value: 30, label: '30天' },
    { value: 60, label: '60天' },
    { value: 90, label: '90天' },
];
