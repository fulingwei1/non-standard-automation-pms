export const exceptionStatusConfigs = {
    open: { label: '待处理', color: 'bg-red-500' },
    handling: { label: '处理中', color: 'bg-amber-500' },
    resolved: { label: '已解决', color: 'bg-emerald-500' },
};

export const exceptionTypeConfigs = {
    quality: { label: '质量问题', icon: 'AlertTriangle' },
    equipment: { label: '设备故障', icon: 'Settings' },
    material: { label: '物料问题', icon: 'Package' },
    process: { label: '工艺问题', icon: 'Workflow' },
    other: { label: '其他', icon: 'HelpCircle' },
};

export const impactLevelConfigs = {
    low: { label: '轻微影响', color: 'bg-slate-500' },
    medium: { label: '中等影响', color: 'bg-amber-500' },
    high: { label: '严重影响', color: 'bg-red-500' },
};
