export const alertLevelConfigs = {
    info: { label: '信息', color: 'bg-blue-500', icon: 'Info' },
    warning: { label: '警告', color: 'bg-amber-500', icon: 'AlertTriangle' },
    critical: { label: '严重', color: 'bg-red-500', icon: 'AlertCircle' },
};

export const alertTypeConfigs = {
    schedule: { label: '进度预警', icon: 'Clock' },
    cost: { label: '成本预警', icon: 'DollarSign' },
    quality: { label: '质量预警', icon: 'AlertTriangle' },
    material: { label: '物料预警', icon: 'Package' },
    resource: { label: '资源预警', icon: 'Users' },
};

export const alertStatusConfigs = {
    new: { label: '新告警', color: 'bg-red-500' },
    acknowledged: { label: '已确认', color: 'bg-amber-500' },
    in_progress: { label: '处理中', color: 'bg-blue-500' },
    resolved: { label: '已解决', color: 'bg-emerald-500' },
};
