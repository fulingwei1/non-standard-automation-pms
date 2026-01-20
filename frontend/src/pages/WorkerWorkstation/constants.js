export const taskStatusConfigs = {
    pending: { label: '待处理', color: 'bg-slate-500' },
    in_progress: { label: '进行中', color: 'bg-blue-500' },
    paused: { label: '已暂停', color: 'bg-amber-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    blocked: { label: '受阻', color: 'bg-red-500' },
};

export const taskTypeConfigs = {
    assembly: { label: '装配', icon: 'Wrench', color: 'bg-blue-500' },
    testing: { label: '测试', icon: 'CheckCircle', color: 'bg-purple-500' },
    inspection: { label: '检验', icon: 'Eye', color: 'bg-cyan-500' },
    repair: { label: '维修', icon: 'Tool', color: 'bg-amber-500' },
};

export const issueTypeConfigs = {
    material: { label: '物料问题', icon: 'Package' },
    equipment: { label: '设备问题', icon: 'Settings' },
    quality: { label: '质量问题', icon: 'AlertTriangle' },
    other: { label: '其他', icon: 'HelpCircle' },
};
