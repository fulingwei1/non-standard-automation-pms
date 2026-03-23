/**
 * 用户管理 - 核心 Hook
 * 封装全部 state、数据加载、CRUD、权限管理
 */

import { useState, useEffect, useCallback } from "react";
import { userApi, roleApi } from "../../../services/api";
import { toast } from "../../../components/ui/toast";
import { confirmAction } from "@/lib/confirmAction";
import {
  USER_STATUS, USER_ROLE, USER_DEPARTMENT,
  validateUserData,
} from "../../../components/user-management";
import { INITIAL_NEW_USER, ROLE_TEMPLATES } from "../constants";

export function useUserManagement() {
  // 列表数据
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [totalUsers, setTotalUsers] = useState(0);

  // 筛选
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterDepartment, setFilterDepartment] = useState("");

  // 对话框
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [showBulkDialog, setShowBulkDialog] = useState(false);

  // 用户选中
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);

  // 表单
  const [newUser, setNewUser] = useState(INITIAL_NEW_USER);

  // 权限管理
  const [availableRoles, setAvailableRoles] = useState([]);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [bulkSelectedRoles, setBulkSelectedRoles] = useState([]);

  // ── 数据加载 ──────────────────────────────────────────────

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 100,
        search: searchQuery,
        status: filterStatus || undefined,
        role: filterRole || undefined,
        department: filterDepartment || undefined,
      };
      const response = await userApi.list(params);
      const paginatedData = response.formatted || response.data;
      setUsers(paginatedData?.items || paginatedData || []);
      setTotalUsers(paginatedData?.total || 0);
    } catch (_error) {
      toast.error("获取用户列表失败");
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filterStatus, filterRole, filterDepartment]);

  const fetchRoles = useCallback(async () => {
    try {
      const response = await roleApi.list({ page: 1, page_size: 100 });
      const listData = response.formatted || response.data;
      setRoles(listData?.items || listData || []);
    } catch (_error) {
      toast.error("获取角色列表失败");
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, [fetchUsers, fetchRoles]);

  // ── CRUD ──────────────────────────────────────────────────

  const handleCreateUser = useCallback(async () => {
    const validation = validateUserData(newUser);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }
    try {
      await userApi.create(newUser);
      toast.success("用户创建成功");
      setShowCreateDialog(false);
      setNewUser(INITIAL_NEW_USER);
      fetchUsers();
    } catch (_error) {
      toast.error("创建用户失败");
    }
  }, [newUser, fetchUsers]);

  const handleUpdateUser = useCallback(async () => {
    try {
      await userApi.update(selectedUser.id, selectedUser);
      toast.success("用户更新成功");
      setShowEditDialog(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (_error) {
      toast.error("更新用户失败");
    }
  }, [selectedUser, fetchUsers]);

  const handleDeleteUser = useCallback(async (userId) => {
    if (!await confirmAction("确定要删除这个用户吗？")) return;
    try {
      await userApi.delete(userId);
      toast.success("用户删除成功");
      fetchUsers();
    } catch (_error) {
      toast.error("删除用户失败");
    }
  }, [fetchUsers]);

  const handleToggleUserStatus = useCallback(async (user) => {
    try {
      const newStatus = user.status === USER_STATUS.ACTIVE
        ? USER_STATUS.INACTIVE
        : USER_STATUS.ACTIVE;
      await userApi.update(user.id, { ...user, status: newStatus });
      toast.success(`用户状态已${newStatus === USER_STATUS.ACTIVE ? "激活" : "停用"}`);
      fetchUsers();
    } catch (_error) {
      toast.error("更改用户状态失败");
    }
  }, [fetchUsers]);

  const openEditDialog = useCallback((user) => {
    setSelectedUser({ ...user });
    setShowEditDialog(true);
  }, []);

  const handleSyncFromEmployees = useCallback(async () => {
    try {
      const response = await userApi.syncFromEmployees({
        sync_existing: true,
        default_role: USER_ROLE.ENGINEER,
        default_department: USER_DEPARTMENT.ENGINEERING,
      });
      toast.success(
        `同步成功，创建了 ${response.data.created} 个用户，更新了 ${response.data.updated} 个用户`
      );
      fetchUsers();
    } catch (_error) {
      toast.error("同步员工失败");
    }
  }, [fetchUsers]);

  // ── 权限管理 ─────────────────────────────────────────────

  const resolveTemplateRoleIds = useCallback((templateType) => {
    const roleMap = {};
    (availableRoles || []).forEach((role) => { roleMap[role.role_code] = role.id; });
    if (templateType === "admin") return (availableRoles || []).map((r) => r.id);
    const template = ROLE_TEMPLATES[templateType];
    if (!template) return [];
    return template.codes.filter((code) => roleMap[code]).map((code) => roleMap[code]);
  }, [availableRoles]);

  const openPermissionDialog = useCallback(async (user) => {
    setSelectedUser(user);
    try {
      const response = await roleApi.list({ page_size: 100 });
      const listData = response.formatted || response.data;
      const allRoles = listData?.items || listData || [];
      setAvailableRoles(allRoles);

      const userResponse = await userApi.get(user.id);
      const userData = userResponse.formatted || userResponse.data;
      const userRoles = userData?.roles || [];
      setSelectedRoles((userRoles || []).map((r) => r.id));
    } catch (_error) {
      toast.error("加载角色列表失败");
    }
    setShowPermissionDialog(true);
  }, []);

  const handleRoleToggle = useCallback((roleId) => {
    setSelectedRoles((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    );
  }, []);

  const handleSavePermissions = useCallback(async () => {
    if (!selectedUser) return;
    try {
      await userApi.assignRoles(selectedUser.id, { role_ids: selectedRoles });
      toast.success("用户权限已更新");
      setShowPermissionDialog(false);
      fetchUsers();
    } catch (_error) {
      toast.error("更新用户权限失败");
    }
  }, [selectedUser, selectedRoles, fetchUsers]);

  const applyRoleTemplate = useCallback((templateType) => {
    const targetRoleIds = resolveTemplateRoleIds(templateType);
    setSelectedRoles(targetRoleIds);
    const label = templateType === "admin" ? "全部权限" : ROLE_TEMPLATES[templateType]?.label || templateType;
    toast.success(`已应用${label}模板`);
  }, [resolveTemplateRoleIds]);

  // ── 批量操作 ─────────────────────────────────────────────

  const handleSelectAll = useCallback((e) => {
    setSelectedUserIds(e.target.checked ? (users || []).map((u) => u.id) : []);
  }, [users]);

  const handleSelectUser = useCallback((userId) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  }, []);

  const openBulkPermissionDialog = useCallback(async () => {
    if (selectedUserIds.length === 0) { toast.error("请先选择用户"); return; }
    try {
      const response = await roleApi.list({ page_size: 100 });
      const allRoles = response.data?.items || response.data || [];
      setAvailableRoles(allRoles);
      setBulkSelectedRoles([]);
      setShowBulkDialog(true);
    } catch (_error) {
      toast.error("加载角色列表失败");
    }
  }, [selectedUserIds]);

  const handleBulkRoleToggle = useCallback((roleId) => {
    setBulkSelectedRoles((prev) =>
      prev.includes(roleId) ? prev.filter((id) => id !== roleId) : [...prev, roleId]
    );
  }, []);

  const handleBulkSavePermissions = useCallback(async () => {
    try {
      await Promise.all(
        (selectedUserIds || []).map((userId) =>
          userApi.assignRoles(userId, { role_ids: bulkSelectedRoles })
        )
      );
      toast.success(`已为 ${selectedUserIds.length} 个用户更新权限`);
      setShowBulkDialog(false);
      setSelectedUserIds([]);
      fetchUsers();
    } catch (_error) {
      toast.error("批量更新权限失败");
    }
  }, [selectedUserIds, bulkSelectedRoles, fetchUsers]);

  const applyBulkRoleTemplate = useCallback((templateType) => {
    const targetRoleIds = resolveTemplateRoleIds(templateType);
    setBulkSelectedRoles(targetRoleIds);
    const label = templateType === "admin" ? "全部权限" : ROLE_TEMPLATES[templateType]?.label || templateType;
    toast.success(`已应用${label}模板`);
  }, [resolveTemplateRoleIds]);

  // ── Quick Actions ────────────────────────────────────────

  const handleQuickAction = useCallback((action) => {
    switch (action) {
      case "createUser": setShowCreateDialog(true); break;
      case "viewInactive": setFilterStatus(USER_STATUS.INACTIVE); break;
      case "userAnalytics": toast.info("用户分析功能开发中..."); break;
      default: break;
    }
  }, []);

  return {
    // 数据
    loading, users, roles, totalUsers,
    // 筛选
    searchQuery, setSearchQuery,
    filterStatus, setFilterStatus,
    filterRole, setFilterRole,
    filterDepartment, setFilterDepartment,
    // 对话框
    showCreateDialog, setShowCreateDialog,
    showEditDialog, setShowEditDialog,
    showPermissionDialog, setShowPermissionDialog,
    showBulkDialog, setShowBulkDialog,
    // 选中
    selectedUser, setSelectedUser,
    selectedUserIds, setSelectedUserIds,
    // 表单
    newUser, setNewUser,
    // 权限
    availableRoles, selectedRoles, setSelectedRoles,
    bulkSelectedRoles, setBulkSelectedRoles,
    // 操作
    handleCreateUser, handleUpdateUser, handleDeleteUser,
    handleToggleUserStatus, openEditDialog, handleSyncFromEmployees,
    openPermissionDialog, handleRoleToggle, handleSavePermissions,
    applyRoleTemplate,
    handleSelectAll, handleSelectUser,
    openBulkPermissionDialog, handleBulkRoleToggle,
    handleBulkSavePermissions, applyBulkRoleTemplate,
    handleQuickAction,
  };
}
