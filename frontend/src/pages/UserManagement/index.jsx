import { useState, useEffect } from "react";




import { fadeIn, staggerContainer } from "../../lib/animations";
import { userApi, roleApi } from "../../services/api";
import { toast } from "../../components/ui/toast";
import {
  USER_STATUS,
  USER_ROLE,
  USER_DEPARTMENT,
  USER_STATUS_FILTER_OPTIONS,
  ROLE_FILTER_OPTIONS,
  DEPARTMENT_FILTER_OPTIONS,
  validateUserData,
} from "../../components/user-management";
import { confirmAction } from "@/lib/confirmAction";
import { ROLE_TEMPLATES } from "./constants";

export default function UserManagement() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [totalUsers, setTotalUsers] = useState(0); // 保存总用户数
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterDepartment, setFilterDepartment] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [_showRoleDialog, setShowRoleDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [_selectedRole, _setSelectedRole] = useState(null);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [showBulkDialog, setShowBulkDialog] = useState(false);
  const [bulkSelectedRoles, setBulkSelectedRoles] = useState([]);
  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    full_name: "",
    phone: "",
    role: USER_ROLE.ENGINEER,
    department: USER_DEPARTMENT.ENGINEERING,
    status: USER_STATUS.ACTIVE,
  });

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, [searchQuery, filterStatus, filterRole, filterDepartment]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 100, // 增加每页显示数量
        search: searchQuery,
        status: filterStatus || undefined,
        role: filterRole || undefined,
        department: filterDepartment || undefined,
      };

      const response = await userApi.list(params);
      // 使用统一响应格式处理（API拦截器自动处理，添加formatted字段）
      const paginatedData = response.formatted || response.data;
      setUsers(paginatedData?.items || paginatedData || []);
      setTotalUsers(paginatedData?.total || 0); // 保存总用户数
    } catch (error) {
      console.error("Failed to fetch users:", error);
      toast.error("获取用户列表失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchRoles = async () => {
    try {
      const response = await roleApi.list({ page: 1, page_size: 100 });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      setRoles(listData?.items || listData || []);
    } catch (error) {
      console.error("Failed to fetch roles:", error);
      toast.error("获取角色列表失败");
    }
  };

  const handleCreateUser = async () => {
    const validation = validateUserData(newUser);
    if (!validation.isValid) {
      toast.error(validation.errors.join(", "));
      return;
    }

    try {
      await userApi.create(newUser);
      toast.success("用户创建成功");
      setShowCreateDialog(false);
      setNewUser({
        username: "",
        email: "",
        password: "",
        full_name: "",
        phone: "",
        role: USER_ROLE.ENGINEER,
        department: USER_DEPARTMENT.ENGINEERING,
        status: USER_STATUS.ACTIVE,
      });
      fetchUsers();
    } catch (error) {
      console.error("Failed to create user:", error);
      toast.error("创建用户失败");
    }
  };

  const handleUpdateUser = async () => {
    try {
      await userApi.update(selectedUser.id, selectedUser);
      toast.success("用户更新成功");
      setShowEditDialog(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      console.error("Failed to update user:", error);
      toast.error("更新用户失败");
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!await confirmAction("确定要删除这个用户吗？")) {
      return;
    }

    try {
      await userApi.delete(userId);
      toast.success("用户删除成功");
      fetchUsers();
    } catch (error) {
      console.error("Failed to delete user:", error);
      toast.error("删除用户失败");
    }
  };

  const handleToggleUserStatus = async (user) => {
    try {
      const newStatus =
        user.status === USER_STATUS.ACTIVE
          ? USER_STATUS.INACTIVE
          : USER_STATUS.ACTIVE;
      await userApi.update(user.id, { ...user, status: newStatus });
      toast.success(
        `用户状态已${newStatus === USER_STATUS.ACTIVE ? "激活" : "停用"}`,
      );
      fetchUsers();
    } catch (error) {
      console.error("Failed to toggle user status:", error);
      toast.error("更改用户状态失败");
    }
  };

  // Permission management handlers
  const openPermissionDialog = async (user) => {
    setSelectedUser(user);
    try {
      const response = await roleApi.list({ page_size: 100 });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      const allRoles = listData?.items || listData || [];
      setAvailableRoles(allRoles);

      // Get user's current roles
      const userResponse = await userApi.get(user.id);
      // 使用统一响应格式处理
      const userData = userResponse.formatted || userResponse.data;
      const userRoles = userData?.roles || [];
      setSelectedRoles((userRoles || []).map((r) => r.id));
    } catch (error) {
      console.error("Failed to load roles:", error);
      toast.error("加载角色列表失败");
    }
    setShowPermissionDialog(true);
  };

  const handleRoleToggle = (roleId) => {
    setSelectedRoles((prev) =>
      prev.includes(roleId)
        ? (prev || []).filter((id) => id !== roleId)
        : [...prev, roleId],
    );
  };

  const handleSavePermissions = async () => {
    if (!selectedUser) return;

    try {
      await userApi.assignRoles(selectedUser.id, { role_ids: selectedRoles });
      toast.success("用户权限已更新");
      setShowPermissionDialog(false);
      fetchUsers();
    } catch (error) {
      console.error("Failed to update user permissions:", error);
      toast.error("更新用户权限失败");
    }
  };

  const resolveTemplateRoleIds = (templateType) => {
    const roleMap = {};
    (availableRoles || []).forEach((role) => {
      roleMap[role.role_code] = role.id;
    });

    if (templateType === "admin") {
      return (availableRoles || []).map((r) => r.id);
    }

    const template = ROLE_TEMPLATES[templateType];
    if (!template) return [];

    return template.codes
      .filter((code) => roleMap[code])
      .map((code) => roleMap[code]);
  };

  const applyRoleTemplate = (templateType) => {
    const targetRoleIds = resolveTemplateRoleIds(templateType);
    setSelectedRoles(targetRoleIds);
    const label =
      templateType === "admin"
        ? "全部权限"
        : ROLE_TEMPLATES[templateType]?.label || templateType;
    toast.success(`已应用${label}模板`);
  };

  // 批量操作
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedUserIds((users || []).map((u) => u.id));
    } else {
      setSelectedUserIds([]);
    }
  };

  const handleSelectUser = (userId) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId)
        ? (prev || []).filter((id) => id !== userId)
        : [...prev, userId],
    );
  };

  const openBulkPermissionDialog = async () => {
    if (selectedUserIds.length === 0) {
      toast.error("请先选择用户");
      return;
    }
    try {
      const response = await roleApi.list({ page_size: 100 });
      const allRoles = response.data?.items || response.data?.items || response.data || [];
      setAvailableRoles(allRoles);
      setBulkSelectedRoles([]);
      setShowBulkDialog(true);
    } catch (error) {
      console.error("Failed to load roles:", error);
      toast.error("加载角色列表失败");
    }
  };

  const handleBulkRoleToggle = (roleId) => {
    setBulkSelectedRoles((prev) =>
      prev.includes(roleId)
        ? (prev || []).filter((id) => id !== roleId)
        : [...prev, roleId],
    );
  };

  const handleBulkSavePermissions = async () => {
    try {
      await Promise.all(
        (selectedUserIds || []).map((userId) =>
          userApi.assignRoles(userId, { role_ids: bulkSelectedRoles }),
        ),
      );
      toast.success(`已为 ${selectedUserIds.length} 个用户更新权限`);
      setShowBulkDialog(false);
      setSelectedUserIds([]);
      fetchUsers();
    } catch (error) {
      console.error("Failed to update bulk permissions:", error);
      toast.error("批量更新权限失败");
    }
  };

  // 批量快速角色模板
  const applyBulkRoleTemplate = (templateType) => {
    const targetRoleIds = resolveTemplateRoleIds(templateType);
    setBulkSelectedRoles(targetRoleIds);
    const label =
      templateType === "admin"
        ? "全部权限"
        : ROLE_TEMPLATES[templateType]?.label || templateType;
    toast.success(`已应用${label}模板`);
  };

  const handleSyncFromEmployees = async () => {
    try {
      const response = await userApi.syncFromEmployees({
        sync_existing: true,
        default_role: USER_ROLE.ENGINEER,
        default_department: USER_DEPARTMENT.ENGINEERING,
      });
      toast.success(
        `同步成功，创建了 ${response.data.created} 个用户，更新了 ${response.data.updated} 个用户`,
      );
      fetchUsers();
    } catch (error) {
      console.error("Failed to sync users:", error);
      toast.error("同步员工失败");
    }
  };

  const openEditDialog = (user) => {
    setSelectedUser({ ...user });
    setShowEditDialog(true);
  };

  // Quick action handlers for overview component
  const handleQuickAction = (action) => {
    switch (action) {
      case "createUser":
        setShowCreateDialog(true);
        break;
      case "manageRoles":
        setShowRoleDialog(true);
        break;
      case "viewInactive":
        setFilterStatus(USER_STATUS.INACTIVE);
        break;
      case "userAnalytics":
        toast.info("用户分析功能开发中...");
        break;
      default:
        break;
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="用户管理"
        description="管理系统用户、角色和权限"
        actions={
          <div className="flex space-x-2">
            <Button variant="outline" onClick={handleSyncFromEmployees}>
              <RefreshCw className="mr-2 h-4 w-4" />
              同步员工
            </Button>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              新建用户
            </Button>
          </div>
        }
      />

      {/* Overview Section */}
      <UserManagementOverview
        users={users}
        roles={roles}
        totalUsers={totalUsers}
        onQuickAction={handleQuickAction}
      />

      {/* Filters Section */}
      <motion.div
        variants={fadeIn}
        className="flex items-center justify-between gap-4"
      >
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索用户..."
            value={searchQuery || "unknown"}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={filterStatus || "unknown"} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="状态" />
            </SelectTrigger>
            <SelectContent>
              {USER_STATUS_FILTER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterRole || "unknown"} onValueChange={setFilterRole}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="角色" />
            </SelectTrigger>
            <SelectContent>
              {ROLE_FILTER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterDepartment || "unknown"} onValueChange={setFilterDepartment}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="部门" />
            </SelectTrigger>
            <SelectContent>
              {DEPARTMENT_FILTER_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </motion.div>

      {/* Users List */}
      <motion.div variants={fadeIn}>
        <UserTable
          loading={loading}
          users={users}
          selectedUserIds={selectedUserIds}
          onSelectAll={handleSelectAll}
          onSelectUser={handleSelectUser}
          onOpenEditDialog={openEditDialog}
          onOpenPermissionDialog={openPermissionDialog}
          onToggleUserStatus={handleToggleUserStatus}
          onDeleteUser={handleDeleteUser}
          onOpenBulkPermissionDialog={openBulkPermissionDialog}
          onClearSelection={() => setSelectedUserIds([])}
        />
      </motion.div>

      {/* Create User Dialog */}
      <CreateUserDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        newUser={newUser}
        setNewUser={setNewUser}
        onCreateUser={handleCreateUser}
      />

      {/* Edit User Dialog */}
      <EditUserDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        selectedUser={selectedUser}
        setSelectedUser={setSelectedUser}
        onUpdateUser={handleUpdateUser}
      />

      {/* Permission Management Dialog */}
      <PermissionDialog
        open={showPermissionDialog}
        onOpenChange={setShowPermissionDialog}
        selectedUser={selectedUser}
        availableRoles={availableRoles}
        selectedRoles={selectedRoles}
        onRoleToggle={handleRoleToggle}
        onSavePermissions={handleSavePermissions}
        onApplyRoleTemplate={applyRoleTemplate}
        onClearRoles={() => setSelectedRoles([])}
      />

      {/* Bulk Permission Dialog */}
      <BulkPermissionDialog
        open={showBulkDialog}
        onOpenChange={setShowBulkDialog}
        selectedUserIds={selectedUserIds}
        availableRoles={availableRoles}
        bulkSelectedRoles={bulkSelectedRoles}
        onBulkRoleToggle={handleBulkRoleToggle}
        onBulkSavePermissions={handleBulkSavePermissions}
        onApplyBulkRoleTemplate={applyBulkRoleTemplate}
        onClearBulkRoles={() => setBulkSelectedRoles([])}
      />
    </motion.div>
  );
}
