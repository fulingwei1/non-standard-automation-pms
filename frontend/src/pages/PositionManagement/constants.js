export const positionLevelConfigs = {
    executive: { label: '高管', level: 1, color: 'bg-purple-500' },
    director: { label: '总监', level: 2, color: 'bg-blue-500' },
    manager: { label: '经理', level: 3, color: 'bg-cyan-500' },
    senior: { label: '高级', level: 4, color: 'bg-emerald-500' },
    regular: { label: '普通', level: 5, color: 'bg-slate-500' },
    junior: { label: '初级', level: 6, color: 'bg-amber-500' },
};

export const statusConfigs = {
    active: { label: '启用', color: 'bg-emerald-500' },
    inactive: { label: '停用', color: 'bg-slate-500' },
};

export const initialPositionForm = {
    name: '',
    code: '',
    level: 'regular',
    department_id: '',
    description: '',
    is_active: true,
};
