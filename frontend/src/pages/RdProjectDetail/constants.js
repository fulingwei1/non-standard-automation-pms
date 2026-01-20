export const rdStatusConfigs = {
    planning: { label: '规划中', color: 'bg-slate-500' },
    designing: { label: '设计中', color: 'bg-blue-500' },
    developing: { label: '开发中', color: 'bg-purple-500' },
    testing: { label: '测试中', color: 'bg-amber-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

export const taskTypeConfigs = {
    design: { label: '设计', icon: 'Pencil' },
    development: { label: '开发', icon: 'Code' },
    testing: { label: '测试', icon: 'CheckCircle' },
    review: { label: '评审', icon: 'Eye' },
    documentation: { label: '文档', icon: 'FileText' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
