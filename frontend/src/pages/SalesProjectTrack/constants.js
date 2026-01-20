export const stageConfigs = {
    lead: { label: '线索', color: 'bg-slate-500', order: 1 },
    qualified: { label: '确认', color: 'bg-blue-500', order: 2 },
    proposal: { label: '报价', color: 'bg-cyan-500', order: 3 },
    negotiation: { label: '谈判', color: 'bg-amber-500', order: 4 },
    won: { label: '赢单', color: 'bg-emerald-500', order: 5 },
    lost: { label: '丢单', color: 'bg-red-500', order: 6 },
};

export const followUpTypeConfigs = {
    call: { label: '电话', icon: 'Phone' },
    meeting: { label: '会议', icon: 'Users' },
    email: { label: '邮件', icon: 'Mail' },
    visit: { label: '拜访', icon: 'MapPin' },
};
