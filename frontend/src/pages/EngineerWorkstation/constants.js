export const taskStatusConfigs = {
    pending: { label: '待处理', color: 'bg-slate-500' },
    in_progress: { label: '进行中', color: 'bg-blue-500' },
    blocked: { label: '受阻', color: 'bg-red-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
};

export const taskPriorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    medium: { label: '中', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};

export const viewModes = [
    { id: 'list', label: '列表', icon: 'List' },
    { id: 'kanban', label: '看板', icon: 'Columns' },
    { id: 'calendar', label: '日历', icon: 'Calendar' },
];
