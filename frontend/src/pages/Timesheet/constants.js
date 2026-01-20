// 工时状态配置
export const statusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    submitted: { label: '已提交', color: 'bg-blue-500' },
    approved: { label: '已批准', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
};

// 工时类型配置
export const workTypeConfigs = {
    normal: { label: '正常工时', color: 'bg-blue-500' },
    overtime: { label: '加班', color: 'bg-amber-500' },
    leave: { label: '请假', color: 'bg-slate-500' },
    travel: { label: '出差', color: 'bg-purple-500' },
};

// 视图模式
export const viewModes = [
    { id: 'day', label: '日视图' },
    { id: 'week', label: '周视图' },
    { id: 'month', label: '月视图' },
];

// 初始表单
export const initialTimesheetForm = {
    date: new Date().toISOString().split('T')[0],
    project_id: '',
    task_id: '',
    hours: 8,
    work_type: 'normal',
    description: '',
};
