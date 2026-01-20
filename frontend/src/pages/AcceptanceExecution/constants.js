export const executionStatusConfigs = {
    pending: { label: '待执行', color: 'bg-slate-500' },
    in_progress: { label: '执行中', color: 'bg-blue-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    failed: { label: '未通过', color: 'bg-red-500' },
};

export const acceptanceTypeConfigs = {
    fat: { label: 'FAT', description: '出厂验收' },
    sat: { label: 'SAT', description: '现场验收' },
    final: { label: '终验', description: '最终验收' },
};

export const resultOptions = [
    { value: 'pass', label: '通过', color: 'bg-emerald-500' },
    { value: 'conditional', label: '有条件通过', color: 'bg-amber-500' },
    { value: 'fail', label: '不通过', color: 'bg-red-500' },
];
