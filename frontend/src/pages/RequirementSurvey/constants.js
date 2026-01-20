export const surveyStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    in_progress: { label: '进行中', color: 'bg-blue-500' },
    submitted: { label: '已提交', color: 'bg-amber-500' },
    approved: { label: '已批准', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
};

export const requirementTypeConfigs = {
    functional: { label: '功能需求', icon: 'Zap' },
    performance: { label: '性能需求', icon: 'Activity' },
    interface: { label: '接口需求', icon: 'Link' },
    safety: { label: '安全需求', icon: 'Shield' },
    other: { label: '其他需求', icon: 'MoreHorizontal' },
};

export const priorityConfigs = {
    must: { label: '必须', color: 'bg-red-500' },
    should: { label: '应该', color: 'bg-amber-500' },
    could: { label: '可以', color: 'bg-blue-500' },
    wont: { label: '不需要', color: 'bg-slate-500' },
};
