export const dependencyStatusConfigs = {
    satisfied: { label: '满足', color: 'bg-emerald-500' },
    partial: { label: '部分满足', color: 'bg-amber-500' },
    blocked: { label: '阻塞', color: 'bg-red-500' },
};

export const dependencyTypeConfigs = {
    material: { label: '物料依赖' },
    task: { label: '任务依赖' },
    resource: { label: '资源依赖' },
    approval: { label: '审批依赖' },
};

// Severity color classes for issue cards in the dependency check page
export const severityColors = {
    HIGH: "text-red-600 bg-red-50 border-red-200",
    URGENT: "text-red-700 bg-red-100 border-red-300",
    MEDIUM: "text-amber-600 bg-amber-50 border-amber-200",
    LOW: "text-blue-600 bg-blue-50 border-blue-200",
};

export const ISSUE_TYPES = {
    TIMING_CONFLICT: "TIMING_CONFLICT",
    MISSING_PREDECESSOR: "MISSING_PREDECESSOR",
};
