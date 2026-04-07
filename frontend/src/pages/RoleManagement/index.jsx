/**
 * 角色管理页面（增强版本）
 *
 * 新增功能：
 * - 角色继承（parent_id）展示
 * - 数据权限范围展示
 * - 权限数量统计（直接 + 继承）
 * - 角色详情含直接/继承权限分离
 * - 角色对比功能
 * - 角色模板快速创建
 */

import { useState } from 'react';






import { fadeIn, staggerContainer } from '../../lib/animations';
import { confirmAction } from "@/lib/confirmAction";
import { DATA_SCOPE_MAP } from './constants';

import { useRoleData } from './hooks';

export default function RoleManagement() {
    const roleData = useRoleData();

    // 对话框状态
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [showCompareDialog, setShowCompareDialog] = useState(false);
    const [showTemplateDialog, setShowTemplateDialog] = useState(false);
    const [_showSaveAsTemplateDialog, setShowSaveAsTemplateDialog] = useState(false);
    const [_showTemplateCenterDialog, setShowTemplateCenterDialog] = useState(false);

    // 表单状态
    const [createForm, setCreateForm] = useState({
        role_code: '', role_name: '', description: '', data_scope: 'OWN', parent_id: null,
    });
    const [editForm, setEditForm] = useState({
        id: null, role_code: '', role_name: '', description: '', data_scope: 'OWN', parent_id: null,
    });
    const [selectedRole, setSelectedRole] = useState(null);

    // 对比状态
    const [selectedForCompare, setSelectedForCompare] = useState([]);
    const [compareResult, setCompareResult] = useState(null);

    // 模板创建状态
    const [templateForm, setTemplateForm] = useState({
        template_id: null, role_code: '', role_name: '', description: '',
    });

    // 另存为模板状态
    const [saveAsTemplateForm, setSaveAsTemplateForm] = useState({
        role_id: null,
        role_name: '',
        template_code: '',
        template_name: '',
        description: '',
    });

    // 权限管理状态
    const [selectedPermissionIds, setSelectedPermissionIds] = useState([]);
    const [inheritedPermissionIds, setInheritedPermissionIds] = useState([]);
    const [permissionSearch, setPermissionSearch] = useState('');
    const [permissionModuleFilter, setPermissionModuleFilter] = useState('all');
    const [activeEditTab, setActiveEditTab] = useState('basic');

    const allPermissions = roleData.permissions || [];
    const roles = roleData.roles || [];
    const templates = roleData.templates || [];

    // 处理函数
    const handleCreateChange = (field, value) => {
        setCreateForm({ ...createForm, [field]: value });
    };

    const handleEditChange = (field, value) => {
        setEditForm({ ...editForm, [field]: value });
    };

    const handleCreateSubmit = async () => {
        if (!createForm.role_code || !createForm.role_name) {
            alert('请填写必填字段');
            return;
        }
        const result = await roleData.createRole({
            role_code: createForm.role_code,
            role_name: createForm.role_name,
            description: createForm.description,
            data_scope: createForm.data_scope,
            parent_id: createForm.parent_id || null,
        });
        if (result.success) {
            setShowCreateDialog(false);
            setCreateForm({ role_code: '', role_name: '', description: '', data_scope: 'OWN', parent_id: null });
        } else {
            alert('创建失败: ' + result.error);
        }
    };

    const handleEditSubmit = async () => {
        const result = await roleData.updateRole(editForm.id, {
            role_name: editForm.role_name,
            description: editForm.description,
            data_scope: editForm.data_scope,
            parent_id: editForm.parent_id || null,
        });
        if (!result.success) {
            alert('更新失败: ' + result.error);
            return;
        }
        const permResult = await roleData.assignPermissions(editForm.id, selectedPermissionIds);
        if (!permResult.success) {
            alert('权限更新失败: ' + permResult.error);
            return;
        }
        setShowEditDialog(false);
    };

    const handleTogglePermission = (permissionId) => {
        setSelectedPermissionIds(prev =>
            prev.includes(permissionId)
                ? (prev || []).filter(id => id !== permissionId)
                : [...prev, permissionId]
        );
    };

    const handleToggleAllPermissions = () => {
        const filteredPermissions = getFilteredPermissions();
        const allSelected = (filteredPermissions || []).every(p => selectedPermissionIds.includes(p.id));
        if (allSelected) {
            setSelectedPermissionIds(prev =>
                (prev || []).filter(id => !(filteredPermissions || []).some(p => p.id === id))
            );
        } else {
            const newIds = [...new Set([...selectedPermissionIds, ...(filteredPermissions || []).map(p => p.id)])];
            setSelectedPermissionIds(newIds);
        }
    };

    const getFilteredPermissions = () => {
        if (!Array.isArray(allPermissions)) return [];
        let filtered = allPermissions;
        if (permissionSearch) {
            filtered = (filtered || []).filter(p =>
                (p.perm_code || p.permission_code || '')?.toLowerCase().includes(permissionSearch.toLowerCase()) ||
                (p.perm_name || p.permission_name || '')?.toLowerCase().includes(permissionSearch.toLowerCase())
            );
        }
        if (permissionModuleFilter !== 'all') {
            filtered = (filtered || []).filter(p => p.module === permissionModuleFilter);
        }
        return filtered.sort((a, b) => {
            const aGranted = selectedPermissionIds.includes(a.id);
            const bGranted = selectedPermissionIds.includes(b.id);
            if (aGranted && !bGranted) return -1;
            if (!aGranted && bGranted) return 1;
            if (a.module !== b.module) return (a.module || '').localeCompare(b.module || '');
            return ((a.perm_code || a.permission_code || '')).localeCompare((b.perm_code || b.permission_code || ''));
        });
    };

    const getAllModules = () => {
        if (!Array.isArray(allPermissions)) return [];
        const modules = new Set((allPermissions || []).map(p => p.module).filter(Boolean));
        return Array.from(modules).sort();
    };

    const handleViewDetail = async (id) => {
        try {
            const role = await roleData.getRoleDetail(id);
            setSelectedRole(role);
            setShowDetailDialog(true);
        } catch (error) {
            console.error('Failed to load role detail:', error);
        }
    };

    const handleEdit = async (id) => {
        try {
            const role = await roleData.getRole(id);
            setEditForm({
                id: role.id, role_code: role.role_code, role_name: role.role_name,
                description: role.description || '', data_scope: role.data_scope || 'OWN', parent_id: role.parent_id,
            });
            const roleDetail = await roleData.getRoleDetail(id);
            setSelectedPermissionIds(roleDetail.direct_permissions?.map(p => p.id) || []);
            setInheritedPermissionIds(roleDetail.inherited_permissions?.map(p => p.id) || []);
            setActiveEditTab('basic');
            setShowEditDialog(true);
        } catch (error) {
            console.error('Failed to load role for edit:', error);
        }
    };

    const handleDelete = async (id) => {
        if (!await confirmAction('确定要删除该角色吗？删除后将影响拥有此角色的用户。')) return;
        const result = await roleData.deleteRole(id);
        if (!result.success) {
            alert('删除失败: ' + result.error);
        }
    };

    const toggleCompareSelection = (roleId) => {
        setSelectedForCompare(prev => {
            if (prev.includes(roleId)) return (prev || []).filter(id => id !== roleId);
            if (prev.length >= 5) { alert('最多选择5个角色进行对比'); return prev; }
            return [...prev, roleId];
        });
    };

    const handleCompare = async () => {
        if (selectedForCompare.length < 2) { alert('请至少选择2个角色进行对比'); return; }
        const result = await roleData.compareRoles(selectedForCompare);
        if (result.success) {
            setCompareResult(result.data);
            setShowCompareDialog(true);
        } else {
            alert('对比失败: ' + result.error);
        }
    };

    const handleTemplateCreate = async () => {
        if (!templateForm.template_id || !templateForm.role_code || !templateForm.role_name) {
            alert('请填写完整信息');
            return;
        }
        const result = await roleData.createRoleFromTemplate(templateForm.template_id, {
            role_code: templateForm.role_code, role_name: templateForm.role_name, description: templateForm.description,
        });
        if (result.success) {
            setShowTemplateDialog(false);
            setTemplateForm({ template_id: null, role_code: '', role_name: '', description: '' });
        } else {
            alert('创建失败: ' + result.error);
        }
    };

    // 另存为模板
    const handleOpenSaveAsTemplate = (role) => {
        setSaveAsTemplateForm({
            role_id: role.id,
            role_name: role.role_name,
            template_code: `TPL_${role.role_code}`,
            template_name: `${role.role_name}模板`,
            description: role.description || '',
        });
        setShowSaveAsTemplateDialog(true);
    };

    const _handleSaveAsTemplateSubmit = async () => {
        if (!saveAsTemplateForm.template_code || !saveAsTemplateForm.template_name) {
            alert('请填写完整信息');
            return;
        }

        const result = await roleData.saveRoleAsTemplate(saveAsTemplateForm.role_id, {
            template_code: saveAsTemplateForm.template_code,
            template_name: saveAsTemplateForm.template_name,
            description: saveAsTemplateForm.description,
        });

        if (result.success) {
            setShowSaveAsTemplateDialog(false);
            setSaveAsTemplateForm({ role_id: null, role_name: '', template_code: '', template_name: '', description: '' });
        } else {
            alert('保存失败: ' + result.error);
        }
    };

    // 删除模板
    const _handleDeleteTemplate = async (templateId) => {
        if (!await confirmAction('确定要删除该模板吗？')) return;
        const result = await roleData.deleteTemplate(templateId);
        if (!result.success) {
            alert('删除失败: ' + result.error);
        }
    };

    // 渲染数据权限标签
    const renderDataScopeBadge = (scope) => {
        const config = DATA_SCOPE_MAP[scope] || DATA_SCOPE_MAP['OWN'];
        return (
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
                {config.label}
            </span>
        );
    };

    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <PageHeader
                title="角色管理"
                description="管理系统角色、权限配置和角色继承关系"
            />

            {/* 搜索和操作 */}
            <motion.div variants={fadeIn} className="flex items-center justify-between gap-4">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                        placeholder="搜索角色..."
                        value={roleData.searchKeyword}
                        onChange={(e) => roleData.setSearchKeyword(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <div className="flex gap-2">
                    {selectedForCompare.length >= 2 && (
                        <Button variant="outline" onClick={handleCompare}>
                            <GitBranch className="w-4 h-4 mr-2" />
                            对比 ({selectedForCompare.length})
                        </Button>
                    )}
                    <Button variant="outline" onClick={() => setShowTemplateCenterDialog(true)}>
                        <LayoutGrid className="w-4 h-4 mr-2" />
                        模板中心
                        {templates.length > 0 && (
                            <Badge variant="secondary" className="ml-1">{templates.length}</Badge>
                        )}
                    </Button>
                    {templates.length > 0 && (
                        <Button variant="outline" onClick={() => setShowTemplateDialog(true)}>
                            <FileText className="w-4 h-4 mr-2" />
                            从模板创建
                        </Button>
                    )}
                    <Button onClick={() => setShowCreateDialog(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        新建角色
                    </Button>
                </div>
            </motion.div>

            {/* 角色列表 */}
            <motion.div variants={fadeIn}>
                <Card>
                    <CardHeader>
                        <CardTitle>角色列表</CardTitle>
                        <CardDescription>
                            共 {roles.length} 个角色
                            {selectedForCompare.length > 0 && (
                                <span className="ml-2 text-blue-600">
                                    | 已选择 {selectedForCompare.length} 个角色
                                    <button className="ml-2 text-xs underline" onClick={() => setSelectedForCompare([])}>
                                        清除
                                    </button>
                                </span>
                            )}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {roleData.loading ? (
                            <div className="text-center py-8 text-slate-400">加载中...</div>
                        ) : roles.length === 0 ? (
                            <div className="text-center py-8 text-slate-400">暂无角色数据</div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-10">
                                            <input type="checkbox" className="rounded" onChange={() => {}} checked={false} />
                                        </TableHead>
                                        <TableHead>角色编码</TableHead>
                                        <TableHead>角色名称</TableHead>
                                        <TableHead>继承自</TableHead>
                                        <TableHead>数据权限</TableHead>
                                        <TableHead>权限数</TableHead>
                                        <TableHead>状态</TableHead>
                                        <TableHead className="text-right">操作</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {(roles || []).map((role) => (
                                        <TableRow key={role.id} className={selectedForCompare.includes(role.id) ? 'bg-blue-50' : ''}>
                                            <TableCell>
                                                <input
                                                    type="checkbox" className="rounded"
                                                    checked={selectedForCompare.includes(role.id)}
                                                    onChange={() => toggleCompareSelection(role.id)}
                                                />
                                            </TableCell>
                                            <TableCell className="font-mono text-sm">{role.role_code}</TableCell>
                                            <TableCell className="font-medium">{role.role_name}</TableCell>
                                            <TableCell>
                                                {role.parent_name ? (
                                                    <span className="text-blue-600 text-sm">
                                                        <GitBranch className="w-3 h-3 inline mr-1" />
                                                        {role.parent_name}
                                                    </span>
                                                ) : (
                                                    <span className="text-slate-400 text-sm">-</span>
                                                )}
                                            </TableCell>
                                            <TableCell>{renderDataScopeBadge(role.data_scope)}</TableCell>
                                            <TableCell>
                                                <span className="text-sm">
                                                    {role.permission_count || 0}
                                                    {role.inherited_permission_count > 0 && (
                                                        <span className="text-blue-500 ml-1">(+{role.inherited_permission_count})</span>
                                                    )}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                {role.is_system ? (
                                                    <Badge variant="secondary">系统</Badge>
                                                ) : role.is_active ? (
                                                    <Badge variant="success">启用</Badge>
                                                ) : (
                                                    <Badge variant="destructive">禁用</Badge>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex items-center justify-end gap-1">
                                                    <Button variant="ghost" size="sm" onClick={() => handleViewDetail(role.id)} title="查看详情">
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    <Button variant="ghost" size="sm" onClick={() => handleEdit(role.id)} title="编辑">
                                                        <Edit3 className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleOpenSaveAsTemplate(role)}
                                                        title="另存为模板"
                                                    >
                                                        <Copy className="w-4 h-4 text-purple-500" />
                                                    </Button>
                                                    {!role.is_system && (
                                                        <Button variant="ghost" size="sm" onClick={() => handleDelete(role.id)} title="删除">
                                                            <Trash2 className="w-4 h-4 text-red-500" />
                                                        </Button>
                                                    )}
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </motion.div>

            {/* Dialogs */}
            <CreateRoleDialog
                open={showCreateDialog} onOpenChange={setShowCreateDialog}
                form={createForm} onChange={handleCreateChange} onSubmit={handleCreateSubmit}
                roles={roles}
            />

            <EditRoleDialog
                open={showEditDialog} onOpenChange={setShowEditDialog}
                form={editForm} onChange={handleEditChange} onSubmit={handleEditSubmit}
                roles={roles}
                activeTab={activeEditTab} onTabChange={setActiveEditTab}
                allPermissions={allPermissions}
                selectedPermissionIds={selectedPermissionIds}
                inheritedPermissionIds={inheritedPermissionIds}
                permissionSearch={permissionSearch} onPermissionSearchChange={setPermissionSearch}
                permissionModuleFilter={permissionModuleFilter} onPermissionModuleFilterChange={setPermissionModuleFilter}
                onTogglePermission={handleTogglePermission}
                onToggleAllPermissions={handleToggleAllPermissions}
                getFilteredPermissions={getFilteredPermissions}
                getAllModules={getAllModules}
            />

            <RoleDetailDialog
                open={showDetailDialog} onOpenChange={setShowDetailDialog}
                role={selectedRole}
            />

            <CompareDialog
                open={showCompareDialog}
                onClose={() => {
                    setShowCompareDialog(false);
                    setSelectedForCompare([]);
                    setCompareResult(null);
                }}
                compareResult={compareResult}
            />

            <TemplateDialog
                open={showTemplateDialog} onOpenChange={setShowTemplateDialog}
                form={templateForm} onFormChange={setTemplateForm}
                onSubmit={handleTemplateCreate} templates={templates}
            />
        </motion.div>
    );
}
