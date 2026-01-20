export const ticketStatusConfigs = {
    pending: { label: '待处理', color: 'bg-amber-500' },
    in_progress: { label: '处理中', color: 'bg-blue-500' },
    resolved: { label: '已解决', color: 'bg-emerald-500' },
    closed: { label: '已关闭', color: 'bg-slate-500' },
};

export const ticketTypeConfigs = {
    quote: { label: '报价支持', icon: 'DollarSign' },
    contract: { label: '合同支持', icon: 'FileText' },
    delivery: { label: '交付支持', icon: 'Truck' },
    billing: { label: '开票支持', icon: 'Receipt' },
    other: { label: '其他', icon: 'HelpCircle' },
};

export const priorityConfigs = {
    low: { label: '低', color: 'bg-slate-400' },
    normal: { label: '普通', color: 'bg-blue-500' },
    high: { label: '高', color: 'bg-amber-500' },
    urgent: { label: '紧急', color: 'bg-red-500' },
};
