import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Eye,
  UserPlus,
  Users,
  Shield,
  Mail,
  Phone,
  Building2,
  Briefcase,
  RefreshCw,
  Key,
  ToggleLeft,
  ToggleRight,
  CheckSquare,
  Square,
  UserCog,
  Info,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { userApi, roleApi } from "../services/api";
import { toast } from "../components/ui/toast";
import {
  UserManagementOverview,
  USER_STATUS,
  USER_STATUS_LABELS,
  USER_STATUS_COLORS,
  USER_ROLE,
  USER_ROLE_LABELS,
  USER_DEPARTMENT,
  USER_DEPARTMENT_LABELS,
  USER_STATUS_FILTER_OPTIONS,
  ROLE_FILTER_OPTIONS,
  DEPARTMENT_FILTER_OPTIONS,
  validateUserData,
  getUserStatusLabel as _getUserStatusLabel,
  getUserRoleLabel as _getUserRoleLabel,
  getUserDepartmentLabel as _getUserDepartmentLabel,
  getUserStatusColor as _getUserStatusColor,
  getRoleColor,
  getDepartmentColor as _getDepartmentColor,
} from "../components/user-management";

// 配置常量 - 使用新的配置系统
import { confirmAction } from "@/lib/confirmAction";
const statusConfig = {
  [USER_STATUS.ACTIVE]: {
    label: USER_STATUS_LABELS[USER_STATUS.ACTIVE],
    color: USER_STATUS_COLORS[USER_STATUS.ACTIVE],
  },
  [USER_STATUS.INACTIVE]: {
    label: USER_STATUS_LABELS[USER_STATUS.INACTIVE],
    color: USER_STATUS_COLORS[USER_STATUS.INACTIVE],
  },
  [USER_STATUS.SUSPENDED]: {
    label: USER_STATUS_LABELS[USER_STATUS.SUSPENDED],
    color: USER_STATUS_COLORS[USER_STATUS.SUSPENDED],
  },
  [USER_STATUS.PENDING]: {
    label: USER_STATUS_LABELS[USER_STATUS.PENDING],
    color: USER_STATUS_COLORS[USER_STATUS.PENDING],
  },
};

const roleConfig = {
  [USER_ROLE.ADMIN]: {
    label: USER_ROLE_LABELS[USER_ROLE.ADMIN],
    color: getRoleColor(USER_ROLE.ADMIN),
  },
  [USER_ROLE.MANAGER]: {
    label: USER_ROLE_LABELS[USER_ROLE.MANAGER],
    color: getRoleColor(USER_ROLE.MANAGER),
  },
  [USER_ROLE.SUPERVISOR]: {
    label: USER_ROLE_LABELS[USER_ROLE.SUPERVISOR],
    color: getRoleColor(USER_ROLE.SUPERVISOR),
  },
  [USER_ROLE.ENGINEER]: {
    label: USER_ROLE_LABELS[USER_ROLE.ENGINEER],
    color: getRoleColor(USER_ROLE.ENGINEER),
  },
  [USER_ROLE.TECHNICIAN]: {
    label: USER_ROLE_LABELS[USER_ROLE.TECHNICIAN],
    color: getRoleColor(USER_ROLE.TECHNICIAN),
  },
  [USER_ROLE.SALESPERSON]: {
    label: USER_ROLE_LABELS[USER_ROLE.SALESPERSON],
    color: getRoleColor(USER_ROLE.SALESPERSON),
  },
  [USER_ROLE.CUSTOMER_SERVICE]: {
    label: USER_ROLE_LABELS[USER_ROLE.CUSTOMER_SERVICE],
    color: getRoleColor(USER_ROLE.CUSTOMER_SERVICE),
  },
  [USER_ROLE.FINANCE]: {
    label: USER_ROLE_LABELS[USER_ROLE.FINANCE],
    color: getRoleColor(USER_ROLE.FINANCE),
  },
  [USER_ROLE.HR]: {
    label: USER_ROLE_LABELS[USER_ROLE.HR],
    color: getRoleColor(USER_ROLE.HR),
  },
  [USER_ROLE.OPERATIONS]: {
    label: USER_ROLE_LABELS[USER_ROLE.OPERATIONS],
    color: getRoleColor(USER_ROLE.OPERATIONS),
  },
};

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
      setSelectedRoles(userRoles.map((r) => r.id));
    } catch (error) {
      console.error("Failed to load roles:", error);
      toast.error("加载角色列表失败");
    }
    setShowPermissionDialog(true);
  };

  const handleRoleToggle = (roleId) => {
    setSelectedRoles((prev) =>
      prev.includes(roleId)
        ? prev.filter((id) => id !== roleId)
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

  // 快速角色模板定义
  const ROLE_TEMPLATES = {
    presales: {
      label: "售前技术包",
      codes: ["SALES_DIR", "SA", "SALES", "CTO", "ENGINEER"],
    },
    project: {
      label: "项目管理包",
      codes: ["PM", "ENGINEER", "ME", "EE", "SW"],
    },
    sales: {
      label: "销售管理包",
      codes: ["SALES_DIR", "SA", "SALES"],
    },
    rnd: {
      label: "研发设计包",
      codes: ["CTO", "ME", "EE", "SW", "ENGINEER"],
    },
    production: {
      label: "生产装配包",
      codes: ["PM", "ASSEMBLER", "DEBUG", "ENGINEER"],
    },
    purchase: {
      label: "采购供应包",
      codes: ["PU_MGR", "PU", "PURCHASER"],
    },
    finance: {
      label: "财务核算包",
      codes: ["CFO", "FI", "FINANCE"],
    },
    quality: {
      label: "质量管控包",
      codes: ["QA_MGR", "QA"],
    },
    pmc: {
      label: "计划调度包",
      codes: ["PMC", "PM", "ENGINEER"],
    },
    executive: {
      label: "高管总览包",
      codes: ["GM", "CTO", "CFO", "SALES_DIR"],
    },
  };

  const resolveTemplateRoleIds = (templateType) => {
    const roleMap = {};
    availableRoles.forEach((role) => {
      roleMap[role.role_code] = role.id;
    });

    if (templateType === "admin") {
      return availableRoles.map((r) => r.id);
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
      setSelectedUserIds(users.map((u) => u.id));
    } else {
      setSelectedUserIds([]);
    }
  };

  const handleSelectUser = (userId) => {
    setSelectedUserIds((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
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
      const allRoles = response.data?.items || response.data || [];
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
        ? prev.filter((id) => id !== roleId)
        : [...prev, roleId],
    );
  };

  const handleBulkSavePermissions = async () => {
    try {
      await Promise.all(
        selectedUserIds.map((userId) =>
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

  const getStatusBadge = (status) => {
    const config = statusConfig[status];
    if (!config) {
      return <Badge variant="secondary">{status}</Badge>;
    }

    return (
      <Badge
        variant="secondary"
        className={cn("border-0", {
          "bg-green-500 text-white": status === USER_STATUS.ACTIVE,
          "bg-gray-500 text-white": status === USER_STATUS.INACTIVE,
          "bg-red-500 text-white": status === USER_STATUS.SUSPENDED,
          "bg-yellow-500 text-white": status === USER_STATUS.PENDING,
        })}
      >
        {config.label}
      </Badge>
    );
  };

  const getRoleBadge = (role) => {
    const config = roleConfig[role];
    if (!config) {
      return <Badge variant="secondary">{role}</Badge>;
    }

    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{ backgroundColor: config.color + "20", color: config.color }}
      >
        {config.label}
      </Badge>
    );
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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={filterStatus} onValueChange={setFilterStatus}>
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

          <Select value={filterRole} onValueChange={setFilterRole}>
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

          <Select value={filterDepartment} onValueChange={setFilterDepartment}>
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
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>用户列表</CardTitle>
              {selectedUserIds.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">
                    已选择 {selectedUserIds.length} 个用户
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={openBulkPermissionDialog}
                    className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                  >
                    <Key className="w-4 h-4 mr-1" />
                    批量分配权限
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedUserIds([])}
                  >
                    取消选择
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : users.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                暂无用户数据
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <input
                        type="checkbox"
                        checked={
                          selectedUserIds.length === users.length &&
                          users.length > 0
                        }
                        onChange={handleSelectAll}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800"
                      />
                    </TableHead>
                    <TableHead>姓名</TableHead>
                    <TableHead>用户名</TableHead>
                    <TableHead>部门</TableHead>
                    <TableHead>级别</TableHead>
                    <TableHead>角色</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user) => (
                    <TableRow
                      key={user.id}
                      className={
                        selectedUserIds.includes(user.id)
                          ? "bg-blue-500/10"
                          : ""
                      }
                    >
                      <TableCell>
                        <input
                          type="checkbox"
                          checked={selectedUserIds.includes(user.id)}
                          onChange={() => handleSelectUser(user.id)}
                          className="w-4 h-4 rounded border-slate-600 bg-slate-800"
                        />
                      </TableCell>
                      <TableCell>
                        <span className="font-medium">
                          {user.real_name || user.full_name || user.username}
                        </span>
                      </TableCell>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {USER_DEPARTMENT_LABELS[user.department] ||
                            user.department ||
                            "-"}
                        </Badge>
                      </TableCell>
                      <TableCell>{user.position || "-"}</TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>{getStatusBadge(user.status)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(user)}
                            title="编辑"
                          >
                            <Edit3 className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openPermissionDialog(user)}
                            title="管理权限"
                            className="text-blue-600 hover:text-blue-700"
                          >
                            <Key className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleUserStatus(user)}
                            title={
                              user.status === USER_STATUS.ACTIVE
                                ? "停用"
                                : "启用"
                            }
                          >
                            {user.status === USER_STATUS.ACTIVE ? (
                              <ToggleRight className="w-4 h-4 text-green-600" />
                            ) : (
                              <ToggleLeft className="w-4 h-4 text-slate-400" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </Button>
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

      {/* Create User Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                  <DialogTitle>新建用户</DialogTitle>
                </DialogHeader>
                <DialogBody>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="username">用户名</Label>
                      <Input
                        id="username"
                        value={newUser.username}
                        onChange={(e) =>
                          setNewUser({ ...newUser, username: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">邮箱</Label>
                      <Input
                        id="email"
                        type="email"
                        value={newUser.email}
                        onChange={(e) =>
                          setNewUser({ ...newUser, email: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="password">密码</Label>
                      <Input
                        id="password"
                        type="password"
                        value={newUser.password}
                        onChange={(e) =>
                          setNewUser({ ...newUser, password: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="full_name">姓名</Label>
                      <Input
                        id="full_name"
                        value={newUser.full_name}
                        onChange={(e) =>
                          setNewUser({ ...newUser, full_name: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">电话</Label>
                      <Input
                        id="phone"
                        value={newUser.phone}
                        onChange={(e) =>
                          setNewUser({ ...newUser, phone: e.target.value })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="role">角色</Label>
                      <Select
                        value={newUser.role}
                        onValueChange={(value) =>
                          setNewUser({ ...newUser, role: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择角色" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_ROLE).map(([_key, value]) => (
                            <SelectItem key={value} value={value}>
                              {USER_ROLE_LABELS[value]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="department">部门</Label>
                      <Select
                        value={newUser.department}
                        onValueChange={(value) =>
                          setNewUser({ ...newUser, department: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择部门" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_DEPARTMENT).map(
                            ([_key, value]) => (
                              <SelectItem key={value} value={value}>
                                {USER_DEPARTMENT_LABELS[value]}
                              </SelectItem>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="status">状态</Label>
                      <Select
                        value={newUser.status}
                        onValueChange={(value) =>
                          setNewUser({ ...newUser, status: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_STATUS).map(([_key, value]) => (
                            <SelectItem key={value} value={value}>
                              {USER_STATUS_LABELS[value]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </DialogBody>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateDialog(false)}
                  >
                    取消
                  </Button>
                  <Button onClick={handleCreateUser}>创建</Button>
                </DialogFooter>
              </DialogContent>
            </motion.div>
          </Dialog>
        )}
      </AnimatePresence>

      {/* Edit User Dialog */}
      <AnimatePresence>
        {showEditDialog && selectedUser && (
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                  <DialogTitle>编辑用户</DialogTitle>
                </DialogHeader>
                <DialogBody>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="edit-username">用户名</Label>
                      <Input
                        id="edit-username"
                        value={selectedUser.username}
                        onChange={(e) =>
                          setSelectedUser({
                            ...selectedUser,
                            username: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-email">邮箱</Label>
                      <Input
                        id="edit-email"
                        type="email"
                        value={selectedUser.email}
                        onChange={(e) =>
                          setSelectedUser({
                            ...selectedUser,
                            email: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-full_name">姓名</Label>
                      <Input
                        id="edit-full_name"
                        value={selectedUser.full_name}
                        onChange={(e) =>
                          setSelectedUser({
                            ...selectedUser,
                            full_name: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-phone">电话</Label>
                      <Input
                        id="edit-phone"
                        value={selectedUser.phone}
                        onChange={(e) =>
                          setSelectedUser({
                            ...selectedUser,
                            phone: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-role">角色</Label>
                      <Select
                        value={selectedUser.role}
                        onValueChange={(value) =>
                          setSelectedUser({ ...selectedUser, role: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择角色" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_ROLE).map(([_key, value]) => (
                            <SelectItem key={value} value={value}>
                              {USER_ROLE_LABELS[value]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="edit-department">部门</Label>
                      <Select
                        value={selectedUser.department}
                        onValueChange={(value) =>
                          setSelectedUser({
                            ...selectedUser,
                            department: value,
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择部门" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_DEPARTMENT).map(
                            ([_key, value]) => (
                              <SelectItem key={value} value={value}>
                                {USER_DEPARTMENT_LABELS[value]}
                              </SelectItem>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="edit-status">状态</Label>
                      <Select
                        value={selectedUser.status}
                        onValueChange={(value) =>
                          setSelectedUser({ ...selectedUser, status: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="选择状态" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(USER_STATUS).map(([_key, value]) => (
                            <SelectItem key={value} value={value}>
                              {USER_STATUS_LABELS[value]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </DialogBody>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setShowEditDialog(false)}
                  >
                    取消
                  </Button>
                  <Button onClick={handleUpdateUser}>更新</Button>
                </DialogFooter>
              </DialogContent>
            </motion.div>
          </Dialog>
        )}

        {/* Permission Management Dialog */}
        {showPermissionDialog && selectedUser && (
          <Dialog
            open={showPermissionDialog}
            onOpenChange={setShowPermissionDialog}
          >
            <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>
                  管理用户权限 - {selectedUser.username}
                </DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="space-y-4">
                  {/* 快速模板 */}
                  <div>
                    <Label className="text-sm text-slate-300 mb-2 block">
                      快速角色模板
                    </Label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(ROLE_TEMPLATES).map(([key, tmpl]) => (
                        <Button
                          key={key}
                          variant="outline"
                          size="sm"
                          onClick={() => applyRoleTemplate(key)}
                          className="text-xs"
                          title={tmpl.codes.join(" + ")}
                        >
                          {tmpl.label}
                        </Button>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => applyRoleTemplate("admin")}
                        className="text-xs"
                      >
                        全部权限
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedRoles([])}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        清空
                      </Button>
                    </div>
                  </div>

                  <p className="text-sm text-slate-400">
                    为用户分配角色以管理其权限。用户将拥有所选角色的所有权限。
                  </p>

                  <div className="max-h-[400px] overflow-y-auto space-y-2">
                    {availableRoles.length === 0 ? (
                      <div className="text-center py-8 text-slate-500">
                        加载角色中...
                      </div>
                    ) : (
                      availableRoles.map((role) => (
                        <div
                          key={role.id}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-lg border transition-colors",
                            selectedRoles.includes(role.id)
                              ? "bg-blue-500/20 border-blue-500/50"
                              : "bg-slate-800 border-slate-700 hover:border-slate-600",
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <Shield
                              className={cn(
                                "w-5 h-5",
                                selectedRoles.includes(role.id)
                                  ? "text-blue-400"
                                  : "text-slate-500",
                              )}
                            />
                            <div>
                              <div className="font-medium">
                                {role.role_name || role.name}
                              </div>
                              <div className="text-xs text-slate-400">
                                {role.description || role.role_code}
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleRoleToggle(role.id)}
                            className={cn(
                              "w-12 h-6 rounded-full transition-colors relative",
                              selectedRoles.includes(role.id)
                                ? "bg-blue-600"
                                : "bg-slate-700",
                            )}
                          >
                            <span
                              className={cn(
                                "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                                selectedRoles.includes(role.id)
                                  ? "translate-x-7"
                                  : "translate-x-1",
                              )}
                            />
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-sm text-slate-400 pt-2 border-t border-slate-700">
                    <Info className="w-4 h-4" />
                    <span>已选择 {selectedRoles.length} 个角色</span>
                  </div>
                </div>
              </DialogBody>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowPermissionDialog(false)}
                >
                  取消
                </Button>
                <Button
                  onClick={handleSavePermissions}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  保存权限
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}

        {/* Bulk Permission Dialog */}
        {showBulkDialog && (
          <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
            <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle>
                  批量分配权限 - {selectedUserIds.length} 个用户
                </DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="space-y-4">
                  <p className="text-sm text-slate-400">
                    为选中的 {selectedUserIds.length} 个用户分配相同的角色权限。
                  </p>

                  {/* 快速模板 */}
                  <div>
                    <Label className="text-sm text-slate-300 mb-2 block">
                      快速角色模板
                    </Label>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(ROLE_TEMPLATES).map(([key, tmpl]) => (
                        <Button
                          key={key}
                          variant="outline"
                          size="sm"
                          onClick={() => applyBulkRoleTemplate(key)}
                          className="text-xs"
                          title={tmpl.codes.join(" + ")}
                        >
                          {tmpl.label}
                        </Button>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => applyBulkRoleTemplate("admin")}
                        className="text-xs"
                      >
                        全部权限
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setBulkSelectedRoles([])}
                        className="text-xs text-red-400 hover:text-red-300"
                      >
                        清空
                      </Button>
                    </div>
                  </div>

                  <div className="max-h-[400px] overflow-y-auto space-y-2">
                    {availableRoles.map((role) => (
                      <div
                        key={role.id}
                        className={cn(
                          "flex items-center justify-between p-3 rounded-lg border transition-colors",
                          bulkSelectedRoles.includes(role.id)
                            ? "bg-blue-500/20 border-blue-500/50"
                            : "bg-slate-800 border-slate-700 hover:border-slate-600",
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <Shield
                            className={cn(
                              "w-5 h-5",
                              bulkSelectedRoles.includes(role.id)
                                ? "text-blue-400"
                                : "text-slate-500",
                            )}
                          />
                          <div>
                            <div className="font-medium">
                              {role.role_name || role.name}
                            </div>
                            <div className="text-xs text-slate-400">
                              {role.description || role.role_code}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleBulkRoleToggle(role.id)}
                          className={cn(
                            "w-12 h-6 rounded-full transition-colors relative",
                            bulkSelectedRoles.includes(role.id)
                              ? "bg-blue-600"
                              : "bg-slate-700",
                          )}
                        >
                          <span
                            className={cn(
                              "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                              bulkSelectedRoles.includes(role.id)
                                ? "translate-x-7"
                                : "translate-x-1",
                            )}
                          />
                        </button>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 text-sm text-slate-400 pt-2 border-t border-slate-700">
                    <Info className="w-4 h-4" />
                    <span>
                      已选择 {bulkSelectedRoles.length} 个角色，将应用到{" "}
                      {selectedUserIds.length} 个用户
                    </span>
                  </div>
                </div>
              </DialogBody>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowBulkDialog(false)}
                >
                  取消
                </Button>
                <Button
                  onClick={handleBulkSavePermissions}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  批量保存
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    </motion.div>
  );
}