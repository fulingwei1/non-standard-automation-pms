export const issueStatusConfigs = {
    open: { label: '待处理', color: 'bg-red-500' },
    in_progress: { label: '处理中', color: 'bg-amber-500' },
    resolved: { label: '已解决', color: 'bg-emerald-500' },
    closed: { label: '已关闭', color: 'bg-slate-500' },
};

export const issueTypeConfigs = {
    bug: { label: '缺陷', color: 'bg-red-500' },
    improvement: { label: '改进', color: 'bg-blue-500' },
    task: { label: '任务', color: 'bg-cyan-500' },
    question: { label: '问题', color: 'bg-amber-500' },
};

export const severityConfigs = {
    critical: { label: '紧急', color: 'bg-red-600' },
    major: { label: '严重', color: 'bg-orange-500' },
    minor: { label: '一般', color: 'bg-amber-500' },
    trivial: { label: '轻微', color: 'bg-slate-500' },
};
