// 线索状态配置
export const leadStatusConfigs = {
    new: { label: '新线索', color: 'bg-blue-500' },
    contacted: { label: '已联系', color: 'bg-cyan-500' },
    qualified: { label: '已验证', color: 'bg-emerald-500' },
    unqualified: { label: '不合格', color: 'bg-slate-500' },
    converted: { label: '已转化', color: 'bg-purple-500' },
};

// 商机阶段配置
export const opportunityStageConfigs = {
    initial: { label: '初步接触', color: 'bg-slate-500', probability: 10 },
    qualified: { label: '需求确认', color: 'bg-blue-500', probability: 30 },
    proposal: { label: '方案报价', color: 'bg-cyan-500', probability: 50 },
    negotiation: { label: '商务谈判', color: 'bg-amber-500', probability: 75 },
    closed_won: { label: '赢单', color: 'bg-emerald-500', probability: 100 },
    closed_lost: { label: '丢单', color: 'bg-red-500', probability: 0 },
};

// 线索来源配置
export const leadSourceConfigs = {
    website: '官网',
    referral: '转介绍',
    exhibition: '展会',
    cold_call: '陌生拜访',
    advertisement: '广告',
    other: '其他',
};

// 销售漏斗阶段（用于管道视图）
export const pipelineStages = [
    { id: 'initial', label: '初步接触' },
    { id: 'qualified', label: '需求确认' },
    { id: 'proposal', label: '方案报价' },
    { id: 'negotiation', label: '商务谈判' },
    { id: 'closed', label: '已成交' },
];

// 仪表板卡片配置
export const dashboardCards = [
    { id: 'leads', label: '线索总数', icon: 'Users', color: 'blue' },
    { id: 'newLeads', label: '本月新增', icon: 'TrendingUp', color: 'emerald' },
    { id: 'conversion', label: '转化率', icon: 'Percent', color: 'purple' },
    { id: 'revenue', label: '预期收入', icon: 'DollarSign', color: 'amber' },
];
