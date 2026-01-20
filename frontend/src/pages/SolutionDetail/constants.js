// 状态配置
export const statusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending_review: { label: '待审核', color: 'bg-amber-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
    archived: { label: '已归档', color: 'bg-slate-400' },
};

// 交付物状态配置
export const deliverableStatusConfigs = {
    pending: { label: '待开始', color: 'text-slate-500' },
    in_progress: { label: '进行中', color: 'text-blue-500' },
    completed: { label: '已完成', color: 'text-emerald-500' },
    delayed: { label: '已延期', color: 'text-red-500' },
};

// Tab配置
export const tabConfigs = [
    { id: 'overview', name: '概览', iconName: 'FileText' },
    { id: 'specs', name: '技术规格', iconName: 'Cpu' },
    { id: 'equipment', name: '设备配置', iconName: 'Package' },
    { id: 'deliverables', name: '交付物', iconName: 'Paperclip' },
    { id: 'cost', name: '成本估算', iconName: 'DollarSign' },
    { id: 'history', name: '版本历史', iconName: 'History' },
];
