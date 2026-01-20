export const supplierLevelConfigs = {
    A: { label: 'A级', color: 'bg-emerald-500', description: '战略供应商' },
    B: { label: 'B级', color: 'bg-blue-500', description: '优选供应商' },
    C: { label: 'C级', color: 'bg-amber-500', description: '合格供应商' },
    D: { label: 'D级', color: 'bg-red-500', description: '待改进供应商' },
};

export const categoryConfigs = {
    mechanical: { label: '机械加工', icon: 'Cog' },
    electrical: { label: '电气设备', icon: 'Zap' },
    electronic: { label: '电子元器件', icon: 'Cpu' },
    standard: { label: '标准件', icon: 'Box' },
    service: { label: '服务', icon: 'Wrench' },
};

export const statusConfigs = {
    active: { label: '合作中', color: 'bg-emerald-500' },
    pending: { label: '审核中', color: 'bg-amber-500' },
    blacklist: { label: '黑名单', color: 'bg-red-500' },
    inactive: { label: '已停用', color: 'bg-slate-500' },
};
