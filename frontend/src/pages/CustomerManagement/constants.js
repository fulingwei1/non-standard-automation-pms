// 客户等级配置
export const levelConfigs = {
    VIP: { label: 'VIP客户', color: 'bg-purple-500' },
    A: { label: 'A级客户', color: 'bg-emerald-500' },
    B: { label: 'B级客户', color: 'bg-blue-500' },
    C: { label: 'C级客户', color: 'bg-amber-500' },
    D: { label: 'D级客户', color: 'bg-slate-500' },
};

// 行业配置
export const industryConfigs = {
    electronics: '电子电器',
    automotive: '汽车制造',
    medical: '医疗器械',
    semiconductor: '半导体',
    new_energy: '新能源',
    other: '其他',
};

// 初始表单
export const initialCustomerForm = {
    name: '',
    short_name: '',
    level: 'B',
    industry: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    address: '',
    description: '',
};
