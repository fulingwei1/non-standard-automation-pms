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
