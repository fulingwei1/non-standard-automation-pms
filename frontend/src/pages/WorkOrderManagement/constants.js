export const workOrderStatusConfigs = {
    pending: { label: '待处理', color: 'bg-slate-500' },
    assigned: { label: '已分配', color: 'bg-blue-500' },
    in_progress: { label: '进行中', color: 'bg-purple-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

export const workOrderTypeConfigs = {
    production: { label: '生产工单', icon: 'Factory' },
    assembly: { label: '装配工单', icon: 'Wrench' },
    testing: { label: '测试工单', icon: 'CheckCircle' },
    repair: { label: '维修工单', icon: 'Tool' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
