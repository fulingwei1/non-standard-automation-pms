export const orderStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已审批', color: 'bg-blue-500' },
    ordered: { label: '已下单', color: 'bg-purple-500' },
    shipped: { label: '已发货', color: 'bg-cyan-500' },
    received: { label: '已到货', color: 'bg-emerald-500' },
};

export const urgencyConfigs = {
    normal: { label: '普通', color: 'bg-slate-500' },
    urgent: { label: '紧急', color: 'bg-amber-500' },
    critical: { label: '特急', color: 'bg-red-500' },
};

export const dashboardCards = [
    { id: 'total', label: '采购单总数', icon: 'FileText' },
    { id: 'pending', label: '待处理', icon: 'Clock' },
    { id: 'ordered', label: '已下单', icon: 'ShoppingCart' },
    { id: 'delayed', label: '延迟交付', icon: 'AlertTriangle' },
];
