export const orderStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已审批', color: 'bg-blue-500' },
    ordered: { label: '已下单', color: 'bg-purple-500' },
    shipped: { label: '已发货', color: 'bg-cyan-500' },
    received: { label: '已到货', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

export const itemStatusConfigs = {
    pending: { label: '待采购', color: 'text-slate-500' },
    ordered: { label: '已下单', color: 'text-blue-500' },
    shipped: { label: '运输中', color: 'text-purple-500' },
    received: { label: '已到货', color: 'text-emerald-500' },
};

export const urgencyConfigs = {
    normal: { label: '普通', color: 'bg-slate-500' },
    urgent: { label: '紧急', color: 'bg-amber-500' },
    critical: { label: '特急', color: 'bg-red-500' },
};
