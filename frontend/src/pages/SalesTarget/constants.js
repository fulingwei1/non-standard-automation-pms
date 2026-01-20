export const targetTypeConfigs = {
    revenue: { label: '营收目标', icon: 'DollarSign', color: 'bg-emerald-500' },
    orders: { label: '订单目标', icon: 'ShoppingCart', color: 'bg-blue-500' },
    customers: { label: '客户目标', icon: 'Users', color: 'bg-purple-500' },
};

export const periodConfigs = {
    monthly: { label: '月度', periods: 12 },
    quarterly: { label: '季度', periods: 4 },
    yearly: { label: '年度', periods: 1 },
};

export const completionLevelConfigs = {
    excellent: { min: 100, label: '优秀', color: 'text-emerald-500' },
    good: { min: 80, label: '良好', color: 'text-blue-500' },
    warning: { min: 60, label: '警告', color: 'text-amber-500' },
    danger: { min: 0, label: '危险', color: 'text-red-500' },
};
