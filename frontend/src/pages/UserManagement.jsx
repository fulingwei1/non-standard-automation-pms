import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Shield,
  RefreshCw,
  Key,
  ToggleLeft,
  ToggleRight,
  Info,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  Users,
  ArrowRight,
  Loader2,
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
  getRoleColor,
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
  const [bulkMode, setBulkMode] = useState("replace"); // "replace" | "remove"
  const [bulkSaving, setBulkSaving] = useState(false);
  const [bulkResult, setBulkResult] = useState(null); // { success: [], failed: [] }
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

  const openBulkPermissionDialog = async (mode = "replace") => {
    if (selectedUserIds.length === 0) {
      toast.error("请先选择用户");
      return;
    }
    try {
      const response = await roleApi.list({ page_size: 100 });
      const listData = response.formatted || response.data;
      const allRoles = listData?.items || listData || [];
      setAvailableRoles(allRoles);
      setBulkSelectedRoles([]);
      setBulkMode(mode);
      setBulkResult(null);
      setShowBulkDialog(true);
    } catch (error) {
      console.error("Failed to load roles:", error);
      toast.error("加载角色列表失败");
    }
  };

  // 批量预览统计（memoized）
  const bulkPreviewStats = useMemo(() => {
    if (!showBulkDialog || selectedUserIds.length === 0) return null;
    const selectedUsers = (users || []).filter((u) => selectedUserIds.includes(u.id));
    const alreadyHave = selectedUsers.filter((u) =>
      bulkSelectedRoles.length > 0 &&
      bulkSelectedRoles.every((rid) => (u.role_ids || []).includes(rid)),
    ).length;
    const willChange = selectedUsers.length - alreadyHave;

    // 每个角色有多少用户已拥有
    const roleOwnership = (availableRoles || [])
      .filter((r) => bulkSelectedRoles.includes(r.id))
      .map((r) => ({
        ...r,
        ownedCount: selectedUsers.filter((u) => (u.role_ids || []).includes(r.id)).length,
        newCount: selectedUsers.filter((u) => !(u.role_ids || []).includes(r.id)).length,
      }));

    return { selectedUsers, alreadyHave, willChange, roleOwnership };
  }, [showBulkDialog, selectedUserIds, bulkSelectedRoles, users, availableRoles]);

  const handleBulkRoleToggle = (roleId) => {
    setBulkSelectedRoles((prev) =>
      prev.includes(roleId)
        ? (prev || []).filter((id) => id !== roleId)
        : [...prev, roleId],
    );
  };

  const handleBulkSavePermissions = async () => {
    if (bulkSelectedRoles.length === 0 && bulkMode === "remove") {
      toast.error("请选择要移除的角色");
      return;
    }
    setBulkSaving(true);
    setBulkResult(null);
    try {
      const response = await userApi.batchAssignRoles(
        selectedUserIds,
        bulkSelectedRoles,
        bulkMode,
      );
      const result = response.formatted || response.data;
      setBulkResult(result);

      const ok = result?.success?.length || 0;
      const fail = result?.failed?.length || 0;
      if (fail === 0) {
        toast.success(`${bulkMode === "remove" ? "移除" : "分配"}成功：${ok} 个用户已更新`);
      } else {
        toast.error(`${ok} 成功，${fail} 失败，请查看详情`);
      }
      fetchUsers();
    } catch (error) {
      console.error("Failed to update bulk permissions:", error);
      toast.error("批量操作失败：" + (error.message || "未知错误"));
    } finally {
      setBulkSaving(false);
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
                    onClick={() => openBulkPermissionDialog("replace")}
                    className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
                  >
                    <Key className="w-4 h-4 mr-1" />
                    批量分配角色
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openBulkPermissionDialog("remove")}
                    className="text-red-400 hover:text-red-300 border-red-500/50 hover:border-red-400"
                  >
                    <MinusCircle className="w-4 h-4 mr-1" />
                    批量移除角色
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
            ) : users?.length === 0 ? (
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
                          selectedUserIds.length === users?.length &&
                          users?.length > 0
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
                  {(users || []).map((user) => (
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
                            <SelectItem key={value} value={value || "unknown"}>
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
                              <SelectItem key={value} value={value || "unknown"}>
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
                            <SelectItem key={value} value={value || "unknown"}>
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
                            <SelectItem key={value} value={value || "unknown"}>
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
                              <SelectItem key={value} value={value || "unknown"}>
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
                            <SelectItem key={value} value={value || "unknown"}>
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
                      (availableRoles || []).map((role) => (
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

        {/* Bulk Permission Dialog - Enhanced */}
        {showBulkDialog && (
          <Dialog open={showBulkDialog} onOpenChange={(open) => {
            if (!bulkSaving) {
              setShowBulkDialog(open);
              if (!open) setBulkResult(null);
            }
          }}>
            <DialogContent className="sm:max-w-[700px] bg-slate-900 border-slate-700 text-white">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {bulkMode === "remove" ? (
                    <MinusCircle className="w-5 h-5 text-red-400" />
                  ) : (
                    <Key className="w-5 h-5 text-blue-400" />
                  )}
                  {bulkMode === "remove" ? "批量移除角色" : "批量分配角色"} - {selectedUserIds.length} 个用户
                </DialogTitle>
              </DialogHeader>
              <DialogBody>
                {/* 操作完成结果面板 */}
                {bulkResult && (
                  <div className="mb-4 space-y-2">
                    <div className={cn(
                      "p-3 rounded-lg border",
                      bulkResult.failed?.length > 0
                        ? "bg-yellow-500/10 border-yellow-500/30"
                        : "bg-green-500/10 border-green-500/30",
                    )}>
                      <div className="flex items-center gap-2 font-medium mb-2">
                        {bulkResult.failed?.length > 0 ? (
                          <AlertTriangle className="w-4 h-4 text-yellow-400" />
                        ) : (
                          <CheckCircle2 className="w-4 h-4 text-green-400" />
                        )}
                        <span>
                          操作完成：{bulkResult.success?.length || 0} 成功
                          {bulkResult.failed?.length > 0 && `，${bulkResult.failed.length} 失败`}
                        </span>
                      </div>
                      {bulkResult.failed?.length > 0 && (
                        <div className="space-y-1 text-sm">
                          {bulkResult.failed.map((f) => {
                            const failUser = (users || []).find((u) => u.id === f.user_id);
                            return (
                              <div key={f.user_id} className="flex items-center gap-2 text-red-400">
                                <XCircle className="w-3 h-3 shrink-0" />
                                <span>{failUser?.real_name || failUser?.username || `用户#${f.user_id}`}：{f.reason}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="space-y-4">
                  {/* 影响预览面板 */}
                  {bulkPreviewStats && bulkSelectedRoles.length > 0 && !bulkResult && (
                    <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-slate-300">
                        <Users className="w-4 h-4" />
                        影响预览
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div className="p-2 rounded bg-slate-800">
                          <div className="text-lg font-bold text-white">{selectedUserIds.length}</div>
                          <div className="text-xs text-slate-400">影响用户数</div>
                        </div>
                        {bulkMode === "replace" ? (
                          <>
                            <div className="p-2 rounded bg-blue-500/10">
                              <div className="text-lg font-bold text-blue-400">{bulkPreviewStats.willChange}</div>
                              <div className="text-xs text-slate-400">将发生变更</div>
                            </div>
                            <div className="p-2 rounded bg-slate-800">
                              <div className="text-lg font-bold text-slate-400">{bulkPreviewStats.alreadyHave}</div>
                              <div className="text-xs text-slate-400">已全部拥有</div>
                            </div>
                          </>
                        ) : (
                          <>
                            <div className="p-2 rounded bg-red-500/10">
                              <div className="text-lg font-bold text-red-400">{bulkSelectedRoles.length}</div>
                              <div className="text-xs text-slate-400">待移除角色</div>
                            </div>
                            <div className="p-2 rounded bg-slate-800">
                              <div className="text-lg font-bold text-slate-400">
                                {bulkPreviewStats.roleOwnership.reduce((s, r) => s + r.ownedCount, 0)}
                              </div>
                              <div className="text-xs text-slate-400">影响授权条数</div>
                            </div>
                          </>
                        )}
                      </div>
                      {/* 每个角色的影响明细 */}
                      {bulkPreviewStats.roleOwnership.length > 0 && (
                        <div className="text-xs space-y-1 pt-2 border-t border-slate-700/50">
                          {bulkPreviewStats.roleOwnership.map((r) => (
                            <div key={r.id} className="flex items-center justify-between text-slate-400">
                              <span>{r.role_name || r.name}</span>
                              <span>
                                {bulkMode === "replace" ? (
                                  <>
                                    <span className="text-slate-500">{r.ownedCount} 已有</span>
                                    {r.newCount > 0 && (
                                      <span className="text-blue-400 ml-2">+{r.newCount} 新增</span>
                                    )}
                                  </>
                                ) : (
                                  <span className="text-red-400">{r.ownedCount} 将移除</span>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 快速模板（仅分配模式） */}
                  {bulkMode === "replace" && (
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
                            disabled={bulkSaving}
                          >
                            {tmpl.label}
                          </Button>
                        ))}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => applyBulkRoleTemplate("admin")}
                          className="text-xs"
                          disabled={bulkSaving}
                        >
                          全部权限
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setBulkSelectedRoles([])}
                          className="text-xs text-red-400 hover:text-red-300"
                          disabled={bulkSaving}
                        >
                          清空
                        </Button>
                      </div>
                    </div>
                  )}

                  {bulkMode === "remove" && (
                    <p className="text-sm text-red-400/80">
                      选择要从 {selectedUserIds.length} 个用户移除的角色。仅移除选中的角色，其余角色保留不变。
                    </p>
                  )}

                  <div className="max-h-[350px] overflow-y-auto space-y-2">
                    {(availableRoles || []).map((role) => {
                      const isSelected = bulkSelectedRoles.includes(role.id);
                      const isRemove = bulkMode === "remove";
                      return (
                        <div
                          key={role.id}
                          className={cn(
                            "flex items-center justify-between p-3 rounded-lg border transition-colors",
                            isSelected
                              ? isRemove
                                ? "bg-red-500/20 border-red-500/50"
                                : "bg-blue-500/20 border-blue-500/50"
                              : "bg-slate-800 border-slate-700 hover:border-slate-600",
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <Shield
                              className={cn(
                                "w-5 h-5",
                                isSelected
                                  ? isRemove ? "text-red-400" : "text-blue-400"
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
                            disabled={bulkSaving}
                            className={cn(
                              "w-12 h-6 rounded-full transition-colors relative",
                              isSelected
                                ? bulkMode === "remove" ? "bg-red-600" : "bg-blue-600"
                                : "bg-slate-700",
                            )}
                          >
                            <span
                              className={cn(
                                "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                                isSelected
                                  ? "translate-x-7"
                                  : "translate-x-1",
                              )}
                            />
                          </button>
                        </div>
                      );
                    })}
                  </div>

                  <div className="flex items-center gap-2 text-sm text-slate-400 pt-2 border-t border-slate-700">
                    <Info className="w-4 h-4" />
                    <span>
                      已选择 {bulkSelectedRoles.length} 个角色，将{bulkMode === "remove" ? "从" : "应用到"}{" "}
                      {selectedUserIds.length} 个用户{bulkMode === "remove" ? "移除" : ""}
                    </span>
                  </div>
                </div>
              </DialogBody>
              <DialogFooter>
                {bulkResult ? (
                  <Button
                    onClick={() => {
                      setShowBulkDialog(false);
                      setSelectedUserIds([]);
                      setBulkResult(null);
                    }}
                    className="bg-slate-700 hover:bg-slate-600"
                  >
                    关闭
                  </Button>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => setShowBulkDialog(false)}
                      disabled={bulkSaving}
                    >
                      取消
                    </Button>
                    <Button
                      onClick={handleBulkSavePermissions}
                      disabled={bulkSaving || bulkSelectedRoles.length === 0}
                      className={cn(
                        bulkMode === "remove"
                          ? "bg-red-600 hover:bg-red-700"
                          : "bg-blue-600 hover:bg-blue-700",
                      )}
                    >
                      {bulkSaving && <Loader2 className="w-4 h-4 mr-1 animate-spin" />}
                      {bulkSaving
                        ? "处理中..."
                        : bulkMode === "remove"
                          ? `移除 ${bulkSelectedRoles.length} 个角色`
                          : `分配到 ${selectedUserIds.length} 个用户`}
                    </Button>
                  </>
                )}
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </AnimatePresence>
    </motion.div>
  );
}