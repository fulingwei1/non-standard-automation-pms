export const userStatusConfigs = {
    active: { label: '正常', color: 'bg-emerald-500' },
    inactive: { label: '停用', color: 'bg-slate-500' },
    locked: { label: '锁定', color: 'bg-red-500' },
};

export const roleConfigs = {
    admin: { label: '管理员', color: 'bg-purple-500' },
    manager: { label: '经理', color: 'bg-blue-500' },
    engineer: { label: '工程师', color: 'bg-cyan-500' },
    operator: { label: '操作员', color: 'bg-emerald-500' },
    viewer: { label: '查看者', color: 'bg-slate-500' },
};

export const initialUserForm = {
    username: '',
    email: '',
    password: '',
    name: '',
    phone: '',
    department_id: '',
    role: 'viewer',
    is_active: true,
};
