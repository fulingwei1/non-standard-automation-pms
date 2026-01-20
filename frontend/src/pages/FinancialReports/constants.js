export const reportTypeConfigs = {
    revenue: { label: '收入报表', icon: 'TrendingUp', color: 'text-emerald-500' },
    expense: { label: '支出报表', icon: 'TrendingDown', color: 'text-red-500' },
    profit: { label: '利润报表', icon: 'DollarSign', color: 'text-blue-500' },
    cash_flow: { label: '现金流', icon: 'Wallet', color: 'text-purple-500' },
    project: { label: '项目核算', icon: 'Briefcase', color: 'text-amber-500' },
};

export const periodConfigs = {
    monthly: { label: '月度', value: 'monthly' },
    quarterly: { label: '季度', value: 'quarterly' },
    yearly: { label: '年度', value: 'yearly' },
};

export const exportFormats = [
    { id: 'xlsx', label: 'Excel', icon: 'FileSpreadsheet' },
    { id: 'pdf', label: 'PDF', icon: 'FileText' },
    { id: 'csv', label: 'CSV', icon: 'File' },
];
