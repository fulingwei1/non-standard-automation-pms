export const stageConfigs = {
    initial: { label: '初步接触', color: 'bg-slate-500', probability: 10 },
    qualified: { label: '需求确认', color: 'bg-blue-500', probability: 30 },
    proposal: { label: '方案报价', color: 'bg-cyan-500', probability: 50 },
    negotiation: { label: '商务谈判', color: 'bg-amber-500', probability: 75 },
    closed_won: { label: '赢单', color: 'bg-emerald-500', probability: 100 },
    closed_lost: { label: '丢单', color: 'bg-red-500', probability: 0 },
};

export const viewModes = [
    { id: 'kanban', label: '看板视图', icon: 'Columns' },
    { id: 'list', label: '列表视图', icon: 'List' },
    { id: 'funnel', label: '漏斗视图', icon: 'Filter' },
];

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    medium: { label: '中', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
