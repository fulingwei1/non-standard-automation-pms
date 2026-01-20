// 订单状态配置
export const statusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    pending: { label: '待审批', color: 'bg-amber-500' },
    approved: { label: '已批准', color: 'bg-blue-500' },
    ordered: { label: '已下单', color: 'bg-purple-500' },
    partial_received: { label: '部分到货', color: 'bg-cyan-500' },
    received: { label: '已到货', color: 'bg-emerald-500' },
    cancelled: { label: '已取消', color: 'bg-red-500' },
};

// 紧急程度配置
export const urgencyConfigs = {
    normal: { label: '普通', color: 'bg-slate-500' },
    urgent: { label: '紧急', color: 'bg-amber-500' },
    critical: { label: '特急', color: 'bg-red-500' },
};

// 初始表单
export const initialOrderForm = {
    supplier_id: '',
    project_id: '',
    order_no: '',
    title: '',
    urgency: 'normal',
    expected_date: '',
    items: [],
    notes: '',
};
