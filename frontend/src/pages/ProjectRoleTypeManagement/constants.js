export const roleTypeConfigs = {
    manager: { label: '项目经理', color: 'bg-purple-500', icon: 'Crown' },
    engineer: { label: '工程师', color: 'bg-blue-500', icon: 'Wrench' },
    designer: { label: '设计师', color: 'bg-cyan-500', icon: 'Pencil' },
    technician: { label: '技术员', color: 'bg-emerald-500', icon: 'Settings' },
    qa: { label: '质量工程师', color: 'bg-amber-500', icon: 'CheckCircle' },
};

export const permissionLevels = [
    { id: 'read', label: '只读', level: 1 },
    { id: 'write', label: '读写', level: 2 },
    { id: 'admin', label: '管理', level: 3 },
];

export const initialRoleTypeForm = {
    name: '',
    display_name: '',
    description: '',
    permissions: [],
    is_active: true,
};
