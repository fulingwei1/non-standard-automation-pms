export const taskStatusConfigs = {
    pending: { label: '待处理', color: 'bg-slate-500' },
    in_progress: { label: '进行中', color: 'bg-blue-500' },
    review: { label: '待审核', color: 'bg-amber-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
};

export const taskTypeConfigs = {
    survey: { label: '需求调研', icon: 'ClipboardList', color: 'bg-blue-500' },
    solution: { label: '方案设计', icon: 'Layout', color: 'bg-purple-500' },
    quote: { label: '报价编制', icon: 'DollarSign', color: 'bg-amber-500' },
    demo: { label: '演示/POC', icon: 'Monitor', color: 'bg-cyan-500' },
    support: { label: '技术支持', icon: 'HelpCircle', color: 'bg-emerald-500' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
