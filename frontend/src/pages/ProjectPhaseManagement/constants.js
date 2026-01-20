export const phaseStatusConfigs = {
    pending: { label: '未开始', color: 'bg-slate-500' },
    active: { label: '进行中', color: 'bg-blue-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    delayed: { label: '已延期', color: 'bg-red-500' },
};

export const defaultPhases = [
    { id: 'design', label: '设计阶段', order: 1 },
    { id: 'procurement', label: '采购阶段', order: 2 },
    { id: 'production', label: '生产阶段', order: 3 },
    { id: 'assembly', label: '装配阶段', order: 4 },
    { id: 'testing', label: '调试阶段', order: 5 },
    { id: 'delivery', label: '交付阶段', order: 6 },
];
