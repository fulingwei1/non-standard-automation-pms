export const qualificationStatusConfigs = {
    valid: { label: '有效', color: 'bg-emerald-500' },
    expiring: { label: '即将到期', color: 'bg-amber-500' },
    expired: { label: '已过期', color: 'bg-red-500' },
    revoked: { label: '已撤销', color: 'bg-slate-500' },
};

export const qualificationTypeConfigs = {
    iso9001: { label: 'ISO 9001', category: '质量管理' },
    iso14001: { label: 'ISO 14001', category: '环境管理' },
    safety: { label: '安全生产许可证', category: '安全' },
    ce: { label: 'CE认证', category: '产品认证' },
    ul: { label: 'UL认证', category: '产品认证' },
};
