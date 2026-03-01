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

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Plus,
    Search,
    Edit3,
    Trash2,
    Eye,
    Shield,
    GitBranch,
    Copy,
    ChevronDown,
    ChevronRight,
    Check,
    FileText,
    ArrowRight,
    CheckSquare,
    Square,
    Filter,
} from 'lucide-react';
import { PageHeader } from '../../components/layout';
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    CardDescription,
} from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '../../components/ui/table';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogBody,
    DialogFooter,
} from '../../components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { fadeIn, staggerContainer } from '../../lib/animations';

// 使用自定义Hook
import { useRoleData } from './hooks';

// 数据权限范围映射
import { confirmAction } from "@/lib/confirmAction";
const DATA_SCOPE_MAP = {
    'OWN': { label: '仅本人', color: 'bg-blue-100 text-blue-700' },
    'SUBORDINATE': { label: '本人及下属', color: 'bg-green-100 text-green-700' },
    'DEPT': { label: '本部门', color: 'bg-yellow-100 text-yellow-700' },
    'DEPT_SUB': { label: '本部门及下级', color: 'bg-orange-100 text-orange-700' },
    'PROJECT': { label: '所属项目', color: 'bg-purple-100 text-purple-700' },
    'ALL': { label: '全部', color: 'bg-red-100 text-red-700' },
    'CUSTOM': { label: '自定义', color: 'bg-gray-100 text-gray-700' },
};

export default function RoleManagement() {
    // 使用自定义Hook管理数据
    const roleData = useRoleData();

    // 对话框状态
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [showCompareDialog, setShowCompareDialog] = useState(false);
    const [showTemplateDialog, setShowTemplateDialog] = useState(false);

    // 表单状态
    const [createForm, setCreateForm] = useState({
        role_code: '',
        role_name: '',
        description: '',
        data_scope: 'OWN',
        parent_id: null,
    });
    const [editForm, setEditForm] = useState({
        id: null,
        role_code: '',
        role_name: '',
        description: '',
        data_scope: 'OWN',
        parent_id: null,
    });
    const [selectedRole, setSelectedRole] = useState(null);

    // 对比状态
    const [selectedForCompare, setSelectedForCompare] = useState([]);
    const [compareResult, setCompareResult] = useState(null);

    // 模板创建状态
    const [templateForm, setTemplateForm] = useState({
        template_id: null,
        role_code: '',
        role_name: '',
        description: '',
    });

    // 权限管理状态
    const [selectedPermissionIds, setSelectedPermissionIds] = useState([]);
    const [inheritedPermissionIds, setInheritedPermissionIds] = useState([]);
    const [permissionSearch, setPermissionSearch] = useState('');
    const [permissionModuleFilter, setPermissionModuleFilter] = useState('all');
    const [activeEditTab, setActiveEditTab] = useState('basic');

    // 使用 roleData 中的权限数据
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
        // 先更新基本信息
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

        // 然后更新权限
        const permResult = await roleData.assignPermissions(editForm.id, selectedPermissionIds);
        if (!permResult.success) {
            alert('权限更新失败: ' + permResult.error);
            return;
        }

        setShowEditDialog(false);
    };

    // 权限选择处理
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
            // 取消选择所有筛选的权限
            setSelectedPermissionIds(prev =>
                (prev || []).filter(id => !(filteredPermissions || []).some(p => p.id === id))
            );
        } else {
            // 选择所有筛选的权限
            const newIds = [...new Set([...selectedPermissionIds, ...(filteredPermissions || []).map(p => p.id)])];
            setSelectedPermissionIds(newIds);
        }
    };

    // 获取筛选后的权限
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

        // 排序：已授予权限在前，未授予权限在后
        return filtered.sort((a, b) => {
            const aGranted = selectedPermissionIds.includes(a.id);
            const bGranted = selectedPermissionIds.includes(b.id);

            if (aGranted && !bGranted) return -1;
            if (!aGranted && bGranted) return 1;

            // 同类型下，按模块排序
            if (a.module !== b.module) {
                return (a.module || '').localeCompare(b.module || '');
            }

            // 同模块下，按权限码排序
            return ((a.perm_code || a.permission_code || '')).localeCompare((b.perm_code || b.permission_code || ''));
        });
    };

    // 获取所有模块
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
                id: role.id,
                role_code: role.role_code,
                role_name: role.role_name,
                description: role.description || '',
                data_scope: role.data_scope || 'OWN',
                parent_id: role.parent_id,
            });

            // 加载角色的权限
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

    // 对比功能
    const toggleCompareSelection = (roleId) => {
        setSelectedForCompare(prev => {
            if (prev.includes(roleId)) {
                return (prev || []).filter(id => id !== roleId);
            }
            if (prev.length >= 5) {
                alert('最多选择5个角色进行对比');
                return prev;
            }
            return [...prev, roleId];
        });
    };

    const handleCompare = async () => {
        if (selectedForCompare.length < 2) {
            alert('请至少选择2个角色进行对比');
            return;
        }

        const result = await roleData.compareRoles(selectedForCompare);
        if (result.success) {
            setCompareResult(result.data);
            setShowCompareDialog(true);
        } else {
            alert('对比失败: ' + result.error);
        }
    };

    // 模板创建
    const handleTemplateCreate = async () => {
        if (!templateForm.template_id || !templateForm.role_code || !templateForm.role_name) {
            alert('请填写完整信息');
            return;
        }

        const result = await roleData.createRoleFromTemplate(templateForm.template_id, {
            role_code: templateForm.role_code,
            role_name: templateForm.role_name,
            description: templateForm.description,
        });

        if (result.success) {
            setShowTemplateDialog(false);
            setTemplateForm({ template_id: null, role_code: '', role_name: '', description: '' });
        } else {
            alert('创建失败: ' + result.error);
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
                                    <button
                                        className="ml-2 text-xs underline"
                                        onClick={() => setSelectedForCompare([])}
                                    >
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
                                            <input
                                                type="checkbox"
                                                className="rounded"
                                                onChange={() => {}}
                                                checked={false}
                                            />
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
                                        <TableRow
                                            key={role.id}
                                            className={selectedForCompare.includes(role.id) ? 'bg-blue-50' : ''}
                                        >
                                            <TableCell>
                                                <input
                                                    type="checkbox"
                                                    className="rounded"
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
                                                        <span className="text-blue-500 ml-1">
                                                            (+{role.inherited_permission_count})
                                                        </span>
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
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleViewDetail(role.id)}
                                                        title="查看详情"
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleEdit(role.id)}
                                                        title="编辑"
                                                    >
                                                        <Edit3 className="w-4 h-4" />
                                                    </Button>
                                                    {!role.is_system && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => handleDelete(role.id)}
                                                            title="删除"
                                                        >
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

            {/* 创建角色对话框 */}
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>新建角色</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色编码 *</label>
                                <Input
                                    value={createForm.role_code}
                                    onChange={(e) => handleCreateChange('role_code', e.target.value)}
                                    placeholder="如: SALES_MANAGER"
                                />
                                <p className="text-xs text-slate-500 mt-1">唯一标识，建议使用大写字母和下划线</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色名称 *</label>
                                <Input
                                    value={createForm.role_name}
                                    onChange={(e) => handleCreateChange('role_name', e.target.value)}
                                    placeholder="如: 销售经理"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">继承自</label>
                                <Select
                                    value={createForm.parent_id?.toString() || ''}
                                    onValueChange={(v) => handleCreateChange('parent_id', v ? parseInt(v) : null)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="选择父角色（可选）" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="__none__">无（顶级角色）</SelectItem>
                                        {(roles || []).filter(r => r.is_active).map((role) => (
                                            <SelectItem key={role.id} value={role.id.toString()}>
                                                {role.role_name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-slate-500 mt-1">子角色会自动继承父角色的所有权限</p>
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">数据权限范围</label>
                                <Select
                                    value={createForm.data_scope}
                                    onValueChange={(v) => handleCreateChange('data_scope', v)}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(DATA_SCOPE_MAP).map(([key, config]) => (
                                            <SelectItem key={key} value={key || "unknown"}>
                                                {config.label}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">描述</label>
                                <Input
                                    value={createForm.description}
                                    onChange={(e) => handleCreateChange('description', e.target.value)}
                                    placeholder="角色描述"
                                />
                            </div>
                        </div>
                    </DialogBody>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                            取消
                        </Button>
                        <Button onClick={handleCreateSubmit}>创建</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* 编辑角色对话框 */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
                <DialogContent className="max-w-6xl w-[95vw] h-[90vh] bg-slate-900 border-slate-700 text-white p-0 overflow-hidden flex flex-col">
                    <DialogHeader className="px-6 py-4 border-b border-slate-700 shrink-0">
                        <DialogTitle>编辑角色 - {editForm.role_name}</DialogTitle>
                    </DialogHeader>
                    <DialogBody className="flex-1 overflow-y-auto px-6">
                        <Tabs value={activeEditTab || "unknown"} onValueChange={setActiveEditTab} className="w-full h-full flex flex-col">
                            <TabsList className="grid w-full grid-cols-2 shrink-0">
                                <TabsTrigger value="basic">基本信息</TabsTrigger>
                                <TabsTrigger value="permissions">
                                    权限管理
                                    <Badge variant="secondary" className="ml-2">
                                        {selectedPermissionIds.length}
                                    </Badge>
                                </TabsTrigger>
                            </TabsList>

                            <TabsContent value="basic" className="mt-6 space-y-4">
                                <div>
                                    <label className="text-sm font-medium mb-2 block">角色编码</label>
                                    <Input value={editForm.role_code} disabled className="bg-slate-800 border-slate-700" />
                                </div>
                                <div>
                                    <label className="text-sm font-medium mb-2 block">角色名称</label>
                                    <Input
                                        value={editForm.role_name}
                                        onChange={(e) => handleEditChange('role_name', e.target.value)}
                                        className="bg-slate-800 border-slate-700"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm font-medium mb-2 block">继承自</label>
                                    <Select
                                        value={editForm.parent_id?.toString() || ''}
                                        onValueChange={(v) => handleEditChange('parent_id', v ? parseInt(v) : null)}
                                    >
                                        <SelectTrigger className="bg-slate-800 border-slate-700">
                                            <SelectValue placeholder="选择父角色（可选）" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="__none__">无（顶级角色）</SelectItem>
                                            {roles
                                                .filter(r => r.is_active && r.id !== editForm.id)
                                                .map((role) => (
                                                    <SelectItem key={role.id} value={role.id.toString()}>
                                                        {role.role_name}
                                                    </SelectItem>
                                                ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div>
                                    <label className="text-sm font-medium mb-2 block">数据权限范围</label>
                                    <Select
                                        value={editForm.data_scope}
                                        onValueChange={(v) => handleEditChange('data_scope', v)}
                                    >
                                        <SelectTrigger className="bg-slate-800 border-slate-700">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {Object.entries(DATA_SCOPE_MAP).map(([key, config]) => (
                                                <SelectItem key={key} value={key || "unknown"}>
                                                    {config.label}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div>
                                    <label className="text-sm font-medium mb-2 block">描述</label>
                                    <Input
                                        value={editForm.description}
                                        onChange={(e) => handleEditChange('description', e.target.value)}
                                        className="bg-slate-800 border-slate-700"
                                    />
                                </div>
                            </TabsContent>

                            <TabsContent value="permissions" className="mt-6 flex-1 overflow-hidden flex flex-col">
                                <div className="space-y-4 h-full flex flex-col">
                                    {/* 搜索和筛选 */}
                                    <div className="flex items-center gap-4 shrink-0">
                                        <div className="relative flex-1">
                                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                            <Input
                                                placeholder="搜索权限编码或名称..."
                                                value={permissionSearch || "unknown"}
                                                onChange={(e) => setPermissionSearch(e.target.value)}
                                                className="pl-9 bg-slate-800 border-slate-700"
                                            />
                                        </div>
                                        <Select
                                            value={permissionModuleFilter || "unknown"}
                                            onValueChange={setPermissionModuleFilter}
                                        >
                                            <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                                                <SelectValue placeholder="模块" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="all">全部模块</SelectItem>
                                                {getAllModules().map(module => (
                                                    <SelectItem key={module} value={module || "unknown"}>
                                                        {module}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleToggleAllPermissions}
                                            className="shrink-0"
                                        >
                                            {getFilteredPermissions().length > 0 && getFilteredPermissions().every(p => selectedPermissionIds.includes(p.id))
                                                ? '取消全选'
                                                : '全选'}
                                        </Button>
                                        <div className="text-sm text-slate-400">
                                            已选: {selectedPermissionIds.length} / 总数: {allPermissions.length}
                                        </div>
                                    </div>

                                    {/* 权限表格 */}
                                    <div className="flex-1 border border-slate-700 rounded-lg overflow-hidden flex flex-col">
                                        {allPermissions.length === 0 ? (
                                            <div className="flex-1 flex items-center justify-center text-slate-400">
                                                加载权限中...
                                            </div>
                                        ) : getFilteredPermissions().length === 0 ? (
                                            <div className="flex-1 flex items-center justify-center text-slate-400">
                                                没有找到匹配的权限
                                            </div>
                                        ) : (
                                            <div className="flex-1 overflow-auto">
                                                <Table>
                                                    <TableHeader className="sticky top-0 bg-slate-800 z-10">
                                                        <TableRow className="hover:bg-slate-800">
                                                            <TableHead className="w-12">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={getFilteredPermissions().length > 0 && getFilteredPermissions().every(p => selectedPermissionIds.includes(p.id))}
                                                                    onChange={handleToggleAllPermissions}
                                                                    className="w-4 h-4"
                                                                />
                                                            </TableHead>
                                                            <TableHead>权限编码</TableHead>
                                                            <TableHead>权限名称</TableHead>
                                                            <TableHead>功能描述</TableHead>
                                                            <TableHead>模块</TableHead>
                                                            <TableHead className="text-right">操作</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {getFilteredPermissions().map((permission) => {
                                                            const isInherited = inheritedPermissionIds.includes(permission.id);
                                                            const isDirectSelected = selectedPermissionIds.includes(permission.id);

                                                            return (
                                                            <TableRow
                                                                key={permission.id}
                                                                className={
                                                                    isInherited ? 'bg-purple-500/5 opacity-75' :
                                                                    isDirectSelected ? 'bg-blue-500/10' : ''
                                                                }
                                                            >
                                                                <TableCell>
                                                                    {isInherited ? (
                                                                        <div className="flex items-center justify-center w-6 h-6 text-purple-400" title="继承权限">
                                                                            <CheckSquare className="w-4 h-4" />
                                                                        </div>
                                                                    ) : (
                                                                        <button
                                                                            onClick={() => handleTogglePermission(permission.id)}
                                                                            className="flex items-center justify-center w-6 h-6 rounded border border-slate-600 hover:border-blue-500 transition-colors"
                                                                        >
                                                                            {isDirectSelected ? (
                                                                                <CheckSquare className="w-4 h-4 text-blue-500" />
                                                                            ) : (
                                                                                <Square className="w-4 h-4 text-slate-500" />
                                                                            )}
                                                                        </button>
                                                                    )}
                                                                </TableCell>
                                                                <TableCell className="font-mono text-sm">
                                                                    {permission.perm_code || permission.permission_code}
                                                                    {isInherited && (
                                                                        <Badge variant="outline" className="ml-2 text-xs text-purple-400 border-purple-500/30">
                                                                            继承
                                                                        </Badge>
                                                                    )}
                                                                </TableCell>
                                                                <TableCell className={isInherited ? 'text-slate-500' : ''}>
                                                                    {permission.perm_name || permission.permission_name}
                                                                </TableCell>
                                                                <TableCell className="text-sm text-slate-400 max-w-xs truncate" title={permission.description}>
                                                                    {permission.description || '-'}
                                                                </TableCell>
                                                                <TableCell>
                                                                    <Badge variant="outline">{permission.module || '-'}</Badge>
                                                                </TableCell>
                                                                <TableCell className="text-right">
                                                                    {isInherited ? (
                                                                        <span className="text-xs text-slate-500">来自父角色</span>
                                                                    ) : (
                                                                        <Button
                                                                            variant="ghost"
                                                                            size="sm"
                                                                            onClick={() => handleTogglePermission(permission.id)}
                                                                            className={isDirectSelected
                                                                                ? 'text-red-400 hover:text-red-300'
                                                                                : 'text-blue-400 hover:text-blue-300'}
                                                                        >
                                                                            {isDirectSelected ? '移除' : '添加'}
                                                                        </Button>
                                                                    )}
                                                                </TableCell>
                                                            </TableRow>
                                                        );})}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </TabsContent>
                        </Tabs>
                    </DialogBody>
                    <DialogFooter className="px-6 py-4 border-t border-slate-700 shrink-0">
                        <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                            取消
                        </Button>
                        <Button onClick={handleEditSubmit} className="bg-blue-600 hover:bg-blue-700">
                            保存
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* 角色详情对话框 */}
            <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
                <DialogContent className="max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>角色详情</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        {selectedRole && (
                            <div className="space-y-6">
                                {/* 基本信息 */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">角色编码</div>
                                        <div className="font-mono">{selectedRole.role_code}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">角色名称</div>
                                        <div>{selectedRole.role_name}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">继承自</div>
                                        <div>
                                            {selectedRole.parent_name ? (
                                                <span className="text-blue-600">
                                                    <GitBranch className="w-4 h-4 inline mr-1" />
                                                    {selectedRole.parent_name}
                                                </span>
                                            ) : (
                                                <span className="text-slate-400">无（顶级角色）</span>
                                            )}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">数据权限</div>
                                        <div>{renderDataScopeBadge(selectedRole.data_scope)}</div>
                                    </div>
                                </div>

                                {selectedRole.description && (
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">描述</div>
                                        <div>{selectedRole.description}</div>
                                    </div>
                                )}

                                {/* 权限列表 */}
                                <Tabs defaultValue="direct" className="w-full">
                                    <TabsList>
                                        <TabsTrigger value="direct">
                                            直接权限
                                            <Badge variant="secondary" className="ml-2">
                                                {selectedRole.direct_permissions?.length || 0}
                                            </Badge>
                                        </TabsTrigger>
                                        <TabsTrigger value="inherited">
                                            继承权限
                                            <Badge variant="secondary" className="ml-2">
                                                {selectedRole.inherited_permissions?.length || 0}
                                            </Badge>
                                        </TabsTrigger>
                                    </TabsList>
                                    <TabsContent value="direct" className="mt-4">
                                        {selectedRole.direct_permissions?.length > 0 ? (
                                            <div className="max-h-60 overflow-y-auto border rounded">
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>权限编码</TableHead>
                                                            <TableHead>权限名称</TableHead>
                                                            <TableHead>模块</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {(selectedRole.direct_permissions || []).map((perm) => (
                                                            <TableRow key={perm.id}>
                                                                <TableCell className="font-mono text-xs">
                                                                    {perm.permission_code}
                                                                </TableCell>
                                                                <TableCell>{perm.permission_name}</TableCell>
                                                                <TableCell>
                                                                    <Badge variant="outline">{perm.module || '-'}</Badge>
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        ) : (
                                            <div className="text-center py-4 text-slate-400">暂无直接分配的权限</div>
                                        )}
                                    </TabsContent>
                                    <TabsContent value="inherited" className="mt-4">
                                        {selectedRole.inherited_permissions?.length > 0 ? (
                                            <div className="max-h-60 overflow-y-auto border rounded">
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>权限编码</TableHead>
                                                            <TableHead>权限名称</TableHead>
                                                            <TableHead>继承自</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {(selectedRole.inherited_permissions || []).map((perm) => (
                                                            <TableRow key={perm.id}>
                                                                <TableCell className="font-mono text-xs">
                                                                    {perm.permission_code}
                                                                </TableCell>
                                                                <TableCell>{perm.permission_name}</TableCell>
                                                                <TableCell>
                                                                    <span className="text-blue-600 text-sm">
                                                                        {perm.inherited_from}
                                                                    </span>
                                                                </TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        ) : (
                                            <div className="text-center py-4 text-slate-400">无继承权限</div>
                                        )}
                                    </TabsContent>
                                </Tabs>
                            </div>
                        )}
                    </DialogBody>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
                            关闭
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* 角色对比对话框 */}
            <Dialog open={showCompareDialog} onOpenChange={setShowCompareDialog}>
                <DialogContent className="max-w-4xl">
                    <DialogHeader>
                        <DialogTitle>角色权限对比</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        {compareResult && (
                            <div className="space-y-6">
                                {/* 对比角色列表 */}
                                <div className="flex gap-4 overflow-x-auto pb-2">
                                    {compareResult.roles?.map((role) => (
                                        <div key={role.role_id} className="min-w-[200px] p-3 border rounded-lg">
                                            <div className="font-medium">{role.role_name}</div>
                                            <div className="text-xs text-slate-500">{role.role_code}</div>
                                            <div className="mt-2">
                                                {renderDataScopeBadge(role.data_scope)}
                                            </div>
                                            <div className="mt-2 text-sm">
                                                权限数: {role.permissions?.length || 0}
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                {/* 共同权限 */}
                                <div>
                                    <h4 className="font-medium mb-2 flex items-center">
                                        <Check className="w-4 h-4 mr-2 text-green-500" />
                                        共同权限 ({compareResult.common_permissions?.length || 0})
                                    </h4>
                                    <div className="flex flex-wrap gap-1">
                                        {compareResult.common_permissions?.map((perm) => (
                                            <Badge key={perm} variant="secondary" className="text-xs">
                                                {perm}
                                            </Badge>
                                        ))}
                                        {(!compareResult.common_permissions || compareResult.common_permissions?.length === 0) && (
                                            <span className="text-slate-400 text-sm">无共同权限</span>
                                        )}
                                    </div>
                                </div>

                                {/* 差异权限 */}
                                <div>
                                    <h4 className="font-medium mb-2">差异权限</h4>
                                    <div className="space-y-3">
                                        {Object.entries(compareResult.diff_permissions || {}).map(([roleId, perms]) => {
                                            const role = compareResult.roles?.find(r => r.role_id.toString() === roleId);
                                            return (
                                                <div key={roleId} className="border rounded p-3">
                                                    <div className="font-medium text-sm mb-2">
                                                        {role?.role_name} 独有权限 ({perms.length})
                                                    </div>
                                                    <div className="flex flex-wrap gap-1">
                                                        {(perms || []).map((perm) => (
                                                            <Badge key={perm} variant="outline" className="text-xs">
                                                                {perm}
                                                            </Badge>
                                                        ))}
                                                        {perms.length === 0 && (
                                                            <span className="text-slate-400 text-sm">无独有权限</span>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        )}
                    </DialogBody>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => {
                            setShowCompareDialog(false);
                            setSelectedForCompare([]);
                            setCompareResult(null);
                        }}>
                            关闭
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* 从模板创建对话框 */}
            <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>从模板创建角色</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-2 block">选择模板 *</label>
                                <Select
                                    value={templateForm.template_id?.toString() || ''}
                                    onValueChange={(v) => setTemplateForm({ ...templateForm, template_id: parseInt(v) })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="选择角色模板" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {(templates || []).map((tpl) => (
                                            <SelectItem key={tpl.id} value={tpl.id.toString()}>
                                                {tpl.template_name}
                                                <span className="text-slate-400 ml-2">
                                                    ({DATA_SCOPE_MAP[tpl.data_scope]?.label || tpl.data_scope})
                                                </span>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色编码 *</label>
                                <Input
                                    value={templateForm.role_code}
                                    onChange={(e) => setTemplateForm({ ...templateForm, role_code: e.target.value })}
                                    placeholder="如: SALES_MANAGER_NORTH"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色名称 *</label>
                                <Input
                                    value={templateForm.role_name}
                                    onChange={(e) => setTemplateForm({ ...templateForm, role_name: e.target.value })}
                                    placeholder="如: 华北区销售经理"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">描述</label>
                                <Input
                                    value={templateForm.description}
                                    onChange={(e) => setTemplateForm({ ...templateForm, description: e.target.value })}
                                    placeholder="角色描述"
                                />
                            </div>
                        </div>
                    </DialogBody>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowTemplateDialog(false)}>
                            取消
                        </Button>
                        <Button onClick={handleTemplateCreate}>
                            <FileText className="w-4 h-4 mr-2" />
                            创建角色
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </motion.div>
    );
}
