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
  DialogFooter,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
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
  getUserStatusLabel,
  getUserRoleLabel,
  getUserDepartmentLabel,
  getUserStatusColor,
  getRoleColor,
  getDepartmentColor
} from "../components/user-management";

// 配置常量 - 使用新的配置系统
const statusConfig = {
  [USER_STATUS.ACTIVE]: { label: USER_STATUS_LABELS[USER_STATUS.ACTIVE], color: USER_STATUS_COLORS[USER_STATUS.ACTIVE] },
  [USER_STATUS.INACTIVE]: { label: USER_STATUS_LABELS[USER_STATUS.INACTIVE], color: USER_STATUS_COLORS[USER_STATUS.INACTIVE] },
  [USER_STATUS.SUSPENDED]: { label: USER_STATUS_LABELS[USER_STATUS.SUSPENDED], color: USER_STATUS_COLORS[USER_STATUS.SUSPENDED] },
  [USER_STATUS.PENDING]: { label: USER_STATUS_LABELS[USER_STATUS.PENDING], color: USER_STATUS_COLORS[USER_STATUS.PENDING] },
};

const roleConfig = {
  [USER_ROLE.ADMIN]: { label: USER_ROLE_LABELS[USER_ROLE.ADMIN], color: getRoleColor(USER_ROLE.ADMIN) },
  [USER_ROLE.MANAGER]: { label: USER_ROLE_LABELS[USER_ROLE.MANAGER], color: getRoleColor(USER_ROLE.MANAGER) },
  [USER_ROLE.SUPERVISOR]: { label: USER_ROLE_LABELS[USER_ROLE.SUPERVISOR], color: getRoleColor(USER_ROLE.SUPERVISOR) },
  [USER_ROLE.ENGINEER]: { label: USER_ROLE_LABELS[USER_ROLE.ENGINEER], color: getRoleColor(USER_ROLE.ENGINEER) },
  [USER_ROLE.TECHNICIAN]: { label: USER_ROLE_LABELS[USER_ROLE.TECHNICIAN], color: getRoleColor(USER_ROLE.TECHNICIAN) },
  [USER_ROLE.SALESPERSON]: { label: USER_ROLE_LABELS[USER_ROLE.SALESPERSON], color: getRoleColor(USER_ROLE.SALESPERSON) },
  [USER_ROLE.CUSTOMER_SERVICE]: { label: USER_ROLE_LABELS[USER_ROLE.CUSTOMER_SERVICE], color: getRoleColor(USER_ROLE.CUSTOMER_SERVICE) },
  [USER_ROLE.FINANCE]: { label: USER_ROLE_LABELS[USER_ROLE.FINANCE], color: getRoleColor(USER_ROLE.FINANCE) },
  [USER_ROLE.HR]: { label: USER_ROLE_LABELS[USER_ROLE.HR], color: getRoleColor(USER_ROLE.HR) },
  [USER_ROLE.OPERATIONS]: { label: USER_ROLE_LABELS[USER_ROLE.OPERATIONS], color: getRoleColor(USER_ROLE.OPERATIONS) },
};

export default function UserManagement() {
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterRole, setFilterRole] = useState("");
  const [filterDepartment, setFilterDepartment] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
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
        search: searchQuery,
        status: filterStatus || undefined,
        role: filterRole || undefined,
        department: filterDepartment || undefined,
      };

      const response = await userApi.list(params);
      const data = response.data || response;
      setUsers(data.items || data || []);
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
      const data = response.data || response;
      setRoles(data.items || data || []);
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
    if (!confirm("确定要删除这个用户吗？")) return;

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
      const newStatus = user.status === USER_STATUS.ACTIVE ? USER_STATUS.INACTIVE : USER_STATUS.ACTIVE;
      await userApi.update(user.id, { ...user, status: newStatus });
      toast.success(`用户状态已${newStatus === USER_STATUS.ACTIVE ? "激活" : "停用"}`);
      fetchUsers();
    } catch (error) {
      console.error("Failed to toggle user status:", error);
      toast.error("更改用户状态失败");
    }
  };

  const handleSyncFromEmployees = async () => {
    try {
      const response = await userApi.syncFromEmployees({
        sync_existing: true,
        default_role: USER_ROLE.ENGINEER,
        default_department: USER_DEPARTMENT.ENGINEERING,
      });
      toast.success(`同步成功，创建了 ${response.data.created} 个用户，更新了 ${response.data.updated} 个用户`);
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
    if (!config) return <Badge variant="secondary">{status}</Badge>;

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
    if (!config) return <Badge variant="secondary">{role}</Badge>;

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
      case 'createUser':
        setShowCreateDialog(true);
        break;
      case 'manageRoles':
        setShowRoleDialog(true);
        break;
      case 'viewInactive':
        setFilterStatus(USER_STATUS.INACTIVE);
        break;
      case 'userAnalytics':
        toast.info('用户分析功能开发中...');
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
        onQuickAction={handleQuickAction}
      />

      {/* Filters Section */}
      <Card variants={fadeIn}>
        <CardHeader>
          <CardTitle>用户列表</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索用户..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
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
              <SelectTrigger>
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
              <SelectTrigger>
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

          {/* Users Table */}
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    邮箱
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    角色
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    部门
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center">
                      加载中...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center">
                      暂无用户
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <motion.tr
                      key={user.id}
                      variants={fadeIn}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-4 py-4">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                              <Users className="h-6 w-6 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {user.full_name || user.username}
                            </div>
                            <div className="text-sm text-gray-500">{user.phone}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">{user.email}</div>
                      </td>
                      <td className="px-4 py-4">
                        {getRoleBadge(user.role)}
                      </td>
                      <td className="px-4 py-4">
                        <Badge variant="outline">
                          {USER_DEPARTMENT_LABELS[user.department] || user.department}
                        </Badge>
                      </td>
                      <td className="px-4 py-4">
                        {getStatusBadge(user.status)}
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditDialog(user)}
                          >
                            <Edit3 className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleUserStatus(user)}
                          >
                            {user.status === USER_STATUS.ACTIVE ? (
                              <ToggleRight className="h-4 w-4 text-green-600" />
                            ) : (
                              <ToggleLeft className="h-4 w-4 text-gray-600" />
                            )}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

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
                        {Object.entries(USER_ROLE).map(([key, value]) => (
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
                        {Object.entries(USER_DEPARTMENT).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {USER_DEPARTMENT_LABELS[value]}
                          </SelectItem>
                        ))}
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
                        {Object.entries(USER_STATUS).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {USER_STATUS_LABELS[value]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
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
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="edit-username">用户名</Label>
                    <Input
                      id="edit-username"
                      value={selectedUser.username}
                      onChange={(e) =>
                        setSelectedUser({ ...selectedUser, username: e.target.value })
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
                        setSelectedUser({ ...selectedUser, email: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-full_name">姓名</Label>
                    <Input
                      id="edit-full_name"
                      value={selectedUser.full_name}
                      onChange={(e) =>
                        setSelectedUser({ ...selectedUser, full_name: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-phone">电话</Label>
                    <Input
                      id="edit-phone"
                      value={selectedUser.phone}
                      onChange={(e) =>
                        setSelectedUser({ ...selectedUser, phone: e.target.value })
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
                        {Object.entries(USER_ROLE).map(([key, value]) => (
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
                        setSelectedUser({ ...selectedUser, department: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择部门" />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(USER_DEPARTMENT).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {USER_DEPARTMENT_LABELS[value]}
                          </SelectItem>
                        ))}
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
                        {Object.entries(USER_STATUS).map(([key, value]) => (
                          <SelectItem key={value} value={value}>
                            {USER_STATUS_LABELS[value]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                    取消
                  </Button>
                  <Button onClick={handleUpdateUser}>更新</Button>
                </DialogFooter>
              </DialogContent>
            </motion.div>
          </Dialog>
        )}
      </AnimatePresence>
    </motion.div>
  );
}