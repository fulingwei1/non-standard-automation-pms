export const trackingStatusConfigs = {
    pending: { label: '待采购', color: 'bg-slate-500' },
    ordered: { label: '已下单', color: 'bg-blue-500' },
    shipped: { label: '运输中', color: 'bg-purple-500' },
    received: { label: '已到货', color: 'bg-emerald-500' },
    inspected: { label: '已检验', color: 'bg-cyan-500' },
    stored: { label: '已入库', color: 'bg-teal-500' },
};

export const materialCategoryConfigs = {
    mechanical: { label: '机械件', icon: 'Cog' },
    electrical: { label: '电气件', icon: 'Zap' },
    standard: { label: '标准件', icon: 'Box' },
    electronic: { label: '电子件', icon: 'Cpu' },
};

export const urgencyLevelConfigs = {
    normal: { label: '普通', color: 'bg-slate-500' },
    urgent: { label: '紧急', color: 'bg-amber-500' },
    critical: { label: '特急', color: 'bg-red-500' },
};
