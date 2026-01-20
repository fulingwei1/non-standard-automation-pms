export const readinessConfigs = {
    ready: { min: 100, label: '齐套', color: 'bg-emerald-500' },
    mostly: { min: 80, label: '基本齐套', color: 'bg-blue-500' },
    partial: { min: 50, label: '部分齐套', color: 'bg-amber-500' },
    shortage: { min: 0, label: '缺料', color: 'bg-red-500' },
};

export const materialStatusConfigs = {
    available: { label: '可用', color: 'text-emerald-500' },
    reserved: { label: '已预留', color: 'text-blue-500' },
    on_order: { label: '在途', color: 'text-amber-500' },
    shortage: { label: '缺料', color: 'text-red-500' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
