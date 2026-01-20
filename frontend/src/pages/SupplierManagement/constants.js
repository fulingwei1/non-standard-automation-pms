export const levelConfigs = {
    A: { label: 'A级', color: 'bg-emerald-500', desc: '战略供应商' },
    B: { label: 'B级', color: 'bg-blue-500', desc: '优选供应商' },
    C: { label: 'C级', color: 'bg-amber-500', desc: '合格供应商' },
    D: { label: 'D级', color: 'bg-red-500', desc: '待改进' },
};

export const categoryConfigs = {
    mechanical: '机械加工',
    electrical: '电气设备',
    electronic: '电子元器件',
    standard: '标准件',
    service: '服务',
};

export const statusConfigs = {
    active: { label: '合作中', color: 'bg-emerald-500' },
    pending: { label: '审核中', color: 'bg-amber-500' },
    blacklist: { label: '黑名单', color: 'bg-red-500' },
    inactive: { label: '已停用', color: 'bg-slate-500' },
};

export const evaluationCriteria = [
    { id: 'quality', label: '质量', weight: 30 },
    { id: 'delivery', label: '交期', weight: 25 },
    { id: 'price', label: '价格', weight: 20 },
    { id: 'service', label: '服务', weight: 15 },
    { id: 'response', label: '响应', weight: 10 },
];
