export const assessmentStatusConfigs = {
    pending: { label: '待评估', color: 'bg-slate-500' },
    in_progress: { label: '评估中', color: 'bg-blue-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

export const assessmentTypeConfigs = {
    feasibility: { label: '可行性评估', icon: 'CheckCircle' },
    risk: { label: '风险评估', icon: 'AlertTriangle' },
    cost: { label: '成本评估', icon: 'DollarSign' },
    technical: { label: '技术评估', icon: 'Cpu' },
};

export const riskLevelConfigs = {
    low: { label: '低风险', color: 'bg-emerald-500' },
    medium: { label: '中风险', color: 'bg-amber-500' },
    high: { label: '高风险', color: 'bg-red-500' },
};

export const feasibilityOptions = [
    { value: 'feasible', label: '可行' },
    { value: 'conditional', label: '有条件可行' },
    { value: 'not_feasible', label: '不可行' },
];
