export const skillConfigs = {
    mechanical: { label: '机械设计', color: 'bg-blue-500' },
    electrical: { label: '电气设计', color: 'bg-amber-500' },
    plc: { label: 'PLC编程', color: 'bg-purple-500' },
    vision: { label: '视觉检测', color: 'bg-cyan-500' },
    assembly: { label: '装配调试', color: 'bg-emerald-500' },
    pm: { label: '项目管理', color: 'bg-indigo-500' },
};

export const matchScoreConfigs = {
    excellent: { min: 90, label: '优秀匹配', color: 'text-emerald-500' },
    good: { min: 70, label: '良好匹配', color: 'text-blue-500' },
    fair: { min: 50, label: '一般匹配', color: 'text-amber-500' },
    poor: { min: 0, label: '较差匹配', color: 'text-red-500' },
};

export const roleConfigs = {
    lead: { label: '项目负责人', level: 1 },
    engineer: { label: '工程师', level: 2 },
    technician: { label: '技术员', level: 3 },
    assistant: { label: '助理', level: 4 },
};
