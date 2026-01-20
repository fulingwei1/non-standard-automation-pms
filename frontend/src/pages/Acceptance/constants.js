export const acceptanceStatusConfigs = {
    pending: { label: '待验收', color: 'bg-amber-500' },
    in_progress: { label: '验收中', color: 'bg-blue-500' },
    passed: { label: '通过', color: 'bg-emerald-500' },
    failed: { label: '未通过', color: 'bg-red-500' },
    conditional: { label: '有条件通过', color: 'bg-cyan-500' },
};

export const acceptanceTypeConfigs = {
    fat: { label: 'FAT验收', description: '出厂验收' },
    sat: { label: 'SAT验收', description: '现场验收' },
    final: { label: '终验', description: '最终验收' },
};
