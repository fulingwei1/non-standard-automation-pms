/**
 * 角色管理页面状态与操作逻辑 Hook
 * 负责对话框状态、表单、权限编辑等业务逻辑
 */

import { useState } from 'react';
import { confirmAction } from "@/lib/confirmAction";
import { useRoleData } from './useRoleData';
import {
  DEFAULT_CREATE_FORM,
  DEFAULT_EDIT_FORM,
  DEFAULT_TEMPLATE_FORM,
} from '../constants';

export function useRoleManagement() {
  // 数据层
  const roleData = useRoleData();

  // 对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showCompareDialog, setShowCompareDialog] = useState(false);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);

  // 表单状态
  const [createForm, setCreateForm] = useState(DEFAULT_CREATE_FORM);
  const [editForm, setEditForm] = useState(DEFAULT_EDIT_FORM);
  const [selectedRole, setSelectedRole] = useState(null);

  // 对比状态
  const [selectedForCompare, setSelectedForCompare] = useState([]);
  const [compareResult, setCompareResult] = useState(null);

  // 模板创建状态
  const [templateForm, setTemplateForm] = useState(DEFAULT_TEMPLATE_FORM);

  // 权限管理状态
  const [selectedPermissionIds, setSelectedPermissionIds] = useState([]);
  const [inheritedPermissionIds, setInheritedPermissionIds] = useState([]);
  const [permissionSearch, setPermissionSearch] = useState('');
  const [permissionModuleFilter, setPermissionModuleFilter] = useState('all');
  const [activeEditTab, setActiveEditTab] = useState('basic');

  // 使用 roleData 中的数据
  const allPermissions = roleData.permissions || [];
  const roles = roleData.roles || [];
  const templates = roleData.templates || [];

  // 表单变更处理
  const handleCreateChange = (field, value) => {
    setCreateForm({ ...createForm, [field]: value });
  };

  const handleEditChange = (field, value) => {
    setEditForm({ ...editForm, [field]: value });
  };

  // 创建角色
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
      setCreateForm(DEFAULT_CREATE_FORM);
    } else {
      alert('创建失败: ' + result.error);
    }
  };

  // 编辑角色提交
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

  // 获取所有模块
  const getAllModules = () => {
    if (!Array.isArray(allPermissions)) return [];
    const modules = new Set((allPermissions || []).map(p => p.module).filter(Boolean));
    return Array.from(modules).sort();
  };

  // 查看详情
  const handleViewDetail = async (id) => {
    try {
      const role = await roleData.getRoleDetail(id);
      setSelectedRole(role);
      setShowDetailDialog(true);
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  };

  // 编辑
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
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  };

  // 删除
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
      setTemplateForm(DEFAULT_TEMPLATE_FORM);
    } else {
      alert('创建失败: ' + result.error);
    }
  };

  return {
    // 数据
    roleData,
    roles,
    templates,
    allPermissions,

    // 对话框状态
    showCreateDialog, setShowCreateDialog,
    showEditDialog, setShowEditDialog,
    showDetailDialog, setShowDetailDialog,
    showCompareDialog, setShowCompareDialog,
    showTemplateDialog, setShowTemplateDialog,

    // 表单
    createForm, handleCreateChange, handleCreateSubmit,
    editForm, handleEditChange, handleEditSubmit,
    selectedRole,
    templateForm, setTemplateForm, handleTemplateCreate,

    // 权限管理
    selectedPermissionIds,
    inheritedPermissionIds,
    permissionSearch, setPermissionSearch,
    permissionModuleFilter, setPermissionModuleFilter,
    activeEditTab, setActiveEditTab,
    handleTogglePermission,
    handleToggleAllPermissions,
    getFilteredPermissions,
    getAllModules,

    // 操作
    handleViewDetail,
    handleEdit,
    handleDelete,

    // 对比
    selectedForCompare, setSelectedForCompare,
    compareResult, setCompareResult,
    toggleCompareSelection,
    handleCompare,
  };
}
