export const executionStatusConfigs = {
    pending: { label: '待执行', color: 'bg-slate-500' },
    in_progress: { label: '执行中', color: 'bg-blue-500' },
    completed: { label: '已完成', color: 'bg-emerald-500' },
    failed: { label: '未通过', color: 'bg-red-500' },
};

export const acceptanceTypeConfigs = {
    fat: { label: 'FAT', description: '出厂验收' },
    sat: { label: 'SAT', description: '现场验收' },
    final: { label: '终验', description: '最终验收' },
};

export const resultOptions = [
    { value: 'pass', label: '通过', color: 'bg-emerald-500' },
    { value: 'conditional', label: '有条件通过', color: 'bg-amber-500' },
    { value: 'fail', label: '不通过', color: 'bg-red-500' },
];

// Check item result statuses
export const resultStatusConfigs = {
    PENDING: { label: '待检查', color: 'bg-slate-500' },
    PASSED: { label: '通过', color: 'bg-emerald-500' },
    FAILED: { label: '不通过', color: 'bg-red-500' },
    NA: { label: '不适用', color: 'bg-gray-500' },
};

// Overall acceptance result options
export const overallResultConfigs = {
    PASS: { label: '通过', color: 'bg-emerald-500' },
    FAIL: { label: '不通过', color: 'bg-red-500' },
    CONDITIONAL: { label: '有条件通过', color: 'bg-amber-500' },
};

// Issue severity display labels
export const issueSeverityLabels = {
    CRITICAL: '严重',
    MAJOR: '重要',
    MINOR: '一般',
};

// Issue severity badge colors
export const issueSeverityColors = {
    CRITICAL: 'bg-red-500',
    MAJOR: 'bg-orange-500',
    MINOR: 'bg-amber-500',
};

// Issue status display labels
export const issueStatusLabels = {
    OPEN: '待处理',
    IN_PROGRESS: '处理中',
    RESOLVED: '已解决',
};

// Default form state for updating a check item
export const defaultItemResult = {
    result_status: 'PASSED',
    actual_value: '',
    deviation: '',
    remark: '',
};

// Default form state for creating an issue
export const defaultNewIssue = {
    item_id: null,
    category: '',
    severity: 'MINOR',
    description: '',
    photos: [],
};

// Default form state for completing acceptance
export const defaultCompleteData = {
    overall_result: 'PASS',
    conclusion: '',
    conditions: '',
};
