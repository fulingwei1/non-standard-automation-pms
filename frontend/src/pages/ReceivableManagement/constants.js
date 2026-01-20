export const statusConfigs = {
    pending: { label: '待收款', color: 'bg-amber-500' },
    partial: { label: '部分收款', color: 'bg-blue-500' },
    completed: { label: '已收款', color: 'bg-emerald-500' },
    overdue: { label: '逾期', color: 'bg-red-500' },
};

export const agingConfigs = {
    current: { label: '未到期', color: 'bg-emerald-500', range: '0天' },
    '1-30': { label: '1-30天', color: 'bg-amber-500', range: '1-30天' },
    '31-60': { label: '31-60天', color: 'bg-orange-500', range: '31-60天' },
    '61-90': { label: '61-90天', color: 'bg-red-400', range: '61-90天' },
    '90+': { label: '90天以上', color: 'bg-red-600', range: '>90天' },
};
