export const opportunityStageConfigs = {
    initial: { label: '初步接触', color: 'bg-slate-500' },
    qualified: { label: '需求确认', color: 'bg-blue-500' },
    proposal: { label: '方案报价', color: 'bg-cyan-500' },
    negotiation: { label: '商务谈判', color: 'bg-amber-500' },
    closed_won: { label: '赢单', color: 'bg-emerald-500' },
    closed_lost: { label: '丢单', color: 'bg-red-500' },
};

export const taskPriorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};

export const dashboardCards = [
    { id: 'opportunities', label: '商机总数', icon: 'Target' },
    { id: 'pendingTasks', label: '待处理任务', icon: 'Clock' },
    { id: 'teamSize', label: '团队成员', icon: 'Users' },
    { id: 'totalValue', label: '商机总额', icon: 'DollarSign' },
];
