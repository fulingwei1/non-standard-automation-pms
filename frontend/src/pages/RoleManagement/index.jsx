/**
 * 角色管理页面（重构版本）
 * 
 * 原文件: 1055行
 * 目录结构:
 * RoleManagement/
 * ├── index.jsx         - 主组件
 * ├── hooks/
 * │   └── useRoleData.js - 角色数据管理
 * └── components/       - 待拆分的组件
 * 
 * TODO: 进一步拆分组件
 * - RoleTable.jsx       - 角色列表表格
 * - RoleDialog.jsx      - 创建/编辑对话框
 * - PermissionDialog.jsx - 权限分配对话框
 * - MenuConfigDialog.jsx - 菜单配置对话框
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Plus,
    Search,
    Edit3,
    Trash2,
    Eye,
    Shield,
    Users,
    Key,
    Menu,
    ChevronDown,
    ChevronRight,
    Check
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
import { fadeIn, staggerContainer } from '../../lib/animations';
import {
    allMenuGroups,
    buildNavGroupsFromSelection,
    extractMenuIdsFromNavGroups
} from '../../lib/allMenuItems';

// 使用自定义Hook
import { useRoleData } from './hooks';

export default function RoleManagement() {
    // 使用自定义Hook管理数据
    const roleData = useRoleData();

    // 对话框状态
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [showPermissionDialog, setShowPermissionDialog] = useState(false);
    const [showMenuConfigDialog, setShowMenuConfigDialog] = useState(false);

    // 表单状态
    const [createForm, setCreateForm] = useState({
        name: '',
        display_name: '',
        description: '',
    });
    const [editForm, setEditForm] = useState({
        id: null,
        name: '',
        display_name: '',
        description: '',
    });
    const [selectedRole, setSelectedRole] = useState(null);
    const [selectedPermissions, setSelectedPermissions] = useState([]);
    const [selectedMenus, setSelectedMenus] = useState([]);
    const [expandedGroups, setExpandedGroups] = useState({});

    // 处理函数
    const handleCreateChange = (e) => {
        setCreateForm({ ...createForm, [e.target.name]: e.target.value });
    };

    const handleEditChange = (e) => {
        setEditForm({ ...editForm, [e.target.name]: e.target.value });
    };

    const handleCreateSubmit = async () => {
        if (!createForm.name || !createForm.display_name) {
            alert('请填写必填字段');
            return;
        }

        const result = await roleData.createRole(createForm);
        if (result.success) {
            setShowCreateDialog(false);
            setCreateForm({ name: '', display_name: '', description: '' });
        } else {
            alert('创建失败: ' + result.error);
        }
    };

    const handleEditSubmit = async () => {
        const result = await roleData.updateRole(editForm.id, editForm);
        if (result.success) {
            setShowEditDialog(false);
        } else {
            alert('更新失败: ' + result.error);
        }
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
            const role = await roleData.getRoleDetail(id);
            setEditForm({
                id: role.id,
                name: role.name,
                display_name: role.display_name,
                description: role.description || '',
            });
            setShowEditDialog(true);
        } catch (error) {
            console.error('Failed to load role for edit:', error);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('确定要删除该角色吗？')) return;
        const result = await roleData.deleteRole(id);
        if (!result.success) {
            alert('删除失败: ' + result.error);
        }
    };

    // 菜单配置函数
    const toggleMenuGroup = (groupId) => {
        setExpandedGroups(prev => ({
            ...prev,
            [groupId]: !prev[groupId]
        }));
    };

    const toggleMenuItem = (itemId) => {
        setSelectedMenus(prev =>
            prev.includes(itemId)
                ? prev.filter(id => id !== itemId)
                : [...prev, itemId]
        );
    };

    const toggleGroupAll = (group) => {
        const groupItemIds = group.items.map(item => item.id);
        const allSelected = groupItemIds.every(id => selectedMenus.includes(id));

        if (allSelected) {
            setSelectedMenus(prev => prev.filter(id => !groupItemIds.includes(id)));
        } else {
            setSelectedMenus(prev => [...new Set([...prev, ...groupItemIds])]);
        }
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
                description="管理系统角色和权限配置"
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
                <Button onClick={() => setShowCreateDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    新建角色
                </Button>
            </motion.div>

            {/* 角色列表 */}
            <motion.div variants={fadeIn}>
                <Card>
                    <CardHeader>
                        <CardTitle>角色列表</CardTitle>
                        <CardDescription>共 {roleData.roles.length} 个角色</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {roleData.loading ? (
                            <div className="text-center py-8 text-slate-400">加载中...</div>
                        ) : roleData.roles.length === 0 ? (
                            <div className="text-center py-8 text-slate-400">暂无角色数据</div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>角色名称</TableHead>
                                        <TableHead>显示名称</TableHead>
                                        <TableHead>描述</TableHead>
                                        <TableHead>是否系统角色</TableHead>
                                        <TableHead className="text-right">操作</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {roleData.roles.map((role) => (
                                        <TableRow key={role.id}>
                                            <TableCell className="font-mono">{role.name}</TableCell>
                                            <TableCell className="font-medium">{role.display_name}</TableCell>
                                            <TableCell className="text-slate-500">{role.description || '-'}</TableCell>
                                            <TableCell>
                                                {role.is_system ? (
                                                    <Badge variant="secondary">系统角色</Badge>
                                                ) : (
                                                    <Badge variant="outline">自定义</Badge>
                                                )}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleViewDetail(role.id)}
                                                    >
                                                        <Eye className="w-4 h-4" />
                                                    </Button>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleEdit(role.id)}
                                                    >
                                                        <Edit3 className="w-4 h-4" />
                                                    </Button>
                                                    {!role.is_system && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => handleDelete(role.id)}
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
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>新建角色</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色名称 *</label>
                                <Input
                                    name="name"
                                    value={createForm.name}
                                    onChange={handleCreateChange}
                                    placeholder="如: project_manager"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">显示名称 *</label>
                                <Input
                                    name="display_name"
                                    value={createForm.display_name}
                                    onChange={handleCreateChange}
                                    placeholder="如: 项目经理"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">描述</label>
                                <Input
                                    name="description"
                                    value={createForm.description}
                                    onChange={handleCreateChange}
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
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>编辑角色</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-2 block">角色名称</label>
                                <Input
                                    name="name"
                                    value={editForm.name}
                                    onChange={handleEditChange}
                                    disabled
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">显示名称</label>
                                <Input
                                    name="display_name"
                                    value={editForm.display_name}
                                    onChange={handleEditChange}
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">描述</label>
                                <Input
                                    name="description"
                                    value={editForm.description}
                                    onChange={handleEditChange}
                                />
                            </div>
                        </div>
                    </DialogBody>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                            取消
                        </Button>
                        <Button onClick={handleEditSubmit}>保存</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* 角色详情对话框 */}
            <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>角色详情</DialogTitle>
                    </DialogHeader>
                    <DialogBody>
                        {selectedRole && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">角色名称</div>
                                        <div className="font-mono">{selectedRole.name}</div>
                                    </div>
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">显示名称</div>
                                        <div>{selectedRole.display_name}</div>
                                    </div>
                                </div>
                                {selectedRole.description && (
                                    <div>
                                        <div className="text-sm text-slate-500 mb-1">描述</div>
                                        <div>{selectedRole.description}</div>
                                    </div>
                                )}
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
        </motion.div>
    );
}
