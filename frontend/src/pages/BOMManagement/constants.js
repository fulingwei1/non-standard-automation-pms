export const bomTypeConfigs = {
    engineering: { label: '工程BOM', color: 'bg-blue-500' },
    manufacturing: { label: '制造BOM', color: 'bg-purple-500' },
    assembly: { label: '装配BOM', color: 'bg-cyan-500' },
};

export const bomStatusConfigs = {
    draft: { label: '草稿', color: 'bg-slate-500' },
    review: { label: '审核中', color: 'bg-amber-500' },
    released: { label: '已发布', color: 'bg-emerald-500' },
    obsolete: { label: '已废弃', color: 'bg-red-500' },
};

/**
 * Status configs keyed by uppercase API values (used in BOM list & detail).
 */
export const statusConfigs = {
    DRAFT:     { label: '草稿',  color: 'bg-slate-500' },
    REVIEWING: { label: '审核中', color: 'bg-blue-500' },
    APPROVED:  { label: '已审批', color: 'bg-emerald-500' },
    RELEASED:  { label: '已发布', color: 'bg-violet-500' },
    OBSOLETE:  { label: '已废弃', color: 'bg-red-500' },
};
