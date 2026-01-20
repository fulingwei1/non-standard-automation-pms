export const approvalStatusConfigs = {
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
    cancelled: { label: '已撤销', color: 'bg-slate-500' },
};

export const approvalTypeConfigs = {
    purchase: { label: '采购审批', icon: 'ShoppingCart' },
    expense: { label: '费用审批', icon: 'DollarSign' },
    leave: { label: '请假审批', icon: 'Calendar' },
    contract: { label: '合同审批', icon: 'FileText' },
    project: { label: '项目审批', icon: 'Briefcase' },
};

export const tabConfigs = [
    { id: 'pending', label: '待我审批' },
    { id: 'processed', label: '我已审批' },
    { id: 'initiated', label: '我发起的' },
];
