export const bidStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待提交', color: 'bg-amber-500' },
    submitted: { label: '已投标', color: 'bg-blue-500' },
    won: { label: '中标', color: 'bg-emerald-500' },
    lost: { label: '未中标', color: 'bg-red-500' },
    cancelled: { label: '已取消', color: 'bg-slate-400' },
};

export const bidTypeConfigs = {
    public: { label: '公开招标', icon: 'Globe' },
    invited: { label: '邀请招标', icon: 'Mail' },
    negotiation: { label: '竞争性谈判', icon: 'MessageSquare' },
    single: { label: '单一来源', icon: 'Target' },
};

export const evaluationCriteria = [
    { id: 'price', label: '价格', weight: 30 },
    { id: 'technical', label: '技术方案', weight: 30 },
    { id: 'experience', label: '项目经验', weight: 20 },
    { id: 'service', label: '售后服务', weight: 10 },
    { id: 'delivery', label: '交付周期', weight: 10 },
];
