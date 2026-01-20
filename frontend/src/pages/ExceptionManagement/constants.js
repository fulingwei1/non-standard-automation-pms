export const exceptionStatusConfigs = {
    open: { label: '待处理', color: 'bg-red-500' },
    in_progress: { label: '处理中', color: 'bg-amber-500' },
    resolved: { label: '已解决', color: 'bg-emerald-500' },
    closed: { label: '已关闭', color: 'bg-slate-500' },
};

export const exceptionTypeConfigs = {
    quality: { label: '质量异常', icon: 'AlertTriangle' },
    schedule: { label: '进度异常', icon: 'Clock' },
    material: { label: '物料异常', icon: 'Package' },
    equipment: { label: '设备异常', icon: 'Settings' },
    safety: { label: '安全异常', icon: 'Shield' },
};

export const severityConfigs = {
    low: { label: '轻微', color: 'bg-slate-500' },
    medium: { label: '一般', color: 'bg-amber-500' },
    high: { label: '严重', color: 'bg-orange-500' },
    critical: { label: '紧急', color: 'bg-red-500' },
};
