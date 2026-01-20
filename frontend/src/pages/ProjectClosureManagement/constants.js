// 结项状态配置
export const closureStatusConfigs = {
    pending: { label: '待结项', color: 'bg-amber-500' },
    submitted: { label: '已提交', color: 'bg-blue-500' },
    under_review: { label: '审核中', color: 'bg-purple-500' },
    approved: { label: '已通过', color: 'bg-emerald-500' },
    rejected: { label: '已驳回', color: 'bg-red-500' },
    closed: { label: '已结项', color: 'bg-slate-500' },
};

// 交付物检查项
export const deliverableChecklist = [
    { id: 'design_docs', label: '设计文档', required: true },
    { id: 'source_code', label: '源代码', required: true },
    { id: 'test_report', label: '测试报告', required: true },
    { id: 'user_manual', label: '用户手册', required: true },
    { id: 'training_materials', label: '培训材料', required: false },
    { id: 'maintenance_guide', label: '维护指南', required: false },
];

// 结项评估维度
export const evaluationDimensions = [
    { id: 'schedule', label: '进度管理', weight: 20 },
    { id: 'quality', label: '质量管理', weight: 25 },
    { id: 'cost', label: '成本控制', weight: 20 },
    { id: 'customer', label: '客户满意度', weight: 20 },
    { id: 'team', label: '团队协作', weight: 15 },
];
