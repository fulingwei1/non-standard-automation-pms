export const stageConfigs = {
    initial: { label: '初步接触', color: 'bg-slate-500', order: 1 },
    qualified: { label: '需求确认', color: 'bg-blue-500', order: 2 },
    proposal: { label: '方案报价', color: 'bg-cyan-500', order: 3 },
    negotiation: { label: '商务谈判', color: 'bg-amber-500', order: 4 },
    closed_won: { label: '赢单', color: 'bg-emerald-500', order: 5 },
    closed_lost: { label: '丢单', color: 'bg-red-500', order: 6 },
};

export const sourceConfigs = {
    website: '官网',
    referral: '转介绍',
    exhibition: '展会',
    cold_call: '陌生拜访',
    advertisement: '广告',
};

export const initialOpportunityForm = {
    name: '',
    customer_id: '',
    expected_revenue: 0,
    stage: 'initial',
    source: '',
    expected_close_date: '',
    description: '',
};
