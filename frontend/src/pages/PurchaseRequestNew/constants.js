export const requestTypeConfigs = {
    project: { label: '项目采购', color: 'bg-blue-500' },
    stock: { label: '库存补充', color: 'bg-emerald-500' },
    emergency: { label: '紧急采购', color: 'bg-red-500' },
};

export const urgencyConfigs = {
    normal: { label: '普通', color: 'bg-slate-500' },
    urgent: { label: '紧急', color: 'bg-amber-500' },
    critical: { label: '特急', color: 'bg-red-500' },
};

export const initialRequestForm = {
    project_id: '',
    type: 'project',
    urgency: 'normal',
    expected_date: '',
    items: [],
    notes: '',
};
