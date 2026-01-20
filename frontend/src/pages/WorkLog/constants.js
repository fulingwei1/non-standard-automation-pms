export const logTypeConfigs = {
    task: { label: '任务', icon: 'CheckSquare', color: 'bg-blue-500' },
    meeting: { label: '会议', icon: 'Users', color: 'bg-purple-500' },
    review: { label: '评审', icon: 'Eye', color: 'bg-cyan-500' },
    other: { label: '其他', icon: 'FileText', color: 'bg-slate-500' },
};

export const progressOptions = [
    { value: 0, label: '未开始' },
    { value: 25, label: '25%' },
    { value: 50, label: '50%' },
    { value: 75, label: '75%' },
    { value: 100, label: '完成' },
];

export const initialLogForm = {
    date: new Date().toISOString().split('T')[0],
    project_id: '',
    task_id: '',
    type: 'task',
    content: '',
    hours: 0,
    progress: 0,
};
