import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { cn } from '../lib/utils';
import { fadeIn, staggerContainer } from '../lib/animations';
import { userApi, roleApi } from '../services/api';

// 职位到角色的推荐映射
const getRecommendedRoles = (position, roles) => {
  if (!position || !roles || roles.length === 0) return [];

  const positionLower = position.toLowerCase();
  const recommended = [];

  // 管理层
  if (positionLower.includes('总经理') || positionLower.includes('总裁')) {
    recommended.push('GM');
  }
  if (positionLower.includes('财务总监') || positionLower.includes('cfo')) {
    recommended.push('CFO');
  }
  if (positionLower.includes('技术总监') || positionLower.includes('cto') || positionLower.includes('研发总监')) {
    recommended.push('CTO');
  }
  if (positionLower.includes('销售总监') || positionLower.includes('营销总监')) {
    recommended.push('SALES_DIR');
  }

  // 项目管理
  if (positionLower.includes('项目经理') || positionLower === 'pm') {
    recommended.push('PM');
  }
  if (positionLower.includes('计划') || positionLower === 'pmc' || positionLower.includes('pmc')) {
    recommended.push('PMC');
  }

  // 质量相关
  if (positionLower.includes('质量主管') || positionLower.includes('品质主管')) {
    recommended.push('QA_MGR');
  }
  if (positionLower.includes('质量') || positionLower.includes('品质') || positionLower.includes('qa')) {
    recommended.push('QA');
  }

  // 采购相关
  if (positionLower.includes('采购主管') || positionLower.includes('采购经理')) {
    recommended.push('PU_MGR');
  }
  if (positionLower.includes('采购')) {
    recommended.push('PU', 'PURCHASER');
  }

  // 工程师类
  if (positionLower.includes('机械') || positionLower.includes('结构')) {
    recommended.push('ME', 'ENGINEER');
  }
  if (positionLower.includes('电气') || positionLower.includes('电子') || positionLower.includes('硬件')) {
    recommended.push('EE', 'ENGINEER');
  }
  if (positionLower.includes('软件') || positionLower.includes('plc') || positionLower.includes('上位机') || positionLower.includes('程序')) {
    recommended.push('SW', 'ENGINEER');
  }
  if (positionLower.includes('工程师') && !recommended.includes('ENGINEER')) {
    recommended.push('ENGINEER');
  }

  // 装配调试
  if (positionLower.includes('装配') || positionLower.includes('组装')) {
    recommended.push('ASSEMBLER');
  }
  if (positionLower.includes('调试')) {
    recommended.push('DEBUG');
  }

  // 销售相关
  if (positionLower.includes('销售') || positionLower.includes('业务')) {
    recommended.push('SA', 'SALES');
  }

  // 财务相关
  if (positionLower.includes('财务') || positionLower.includes('会计') || positionLower.includes('出纳')) {
    recommended.push('FI', 'FINANCE');
  }

  // 根据推荐的角色编码找到对应的角色ID
  const recommendedIds = [];
  recommended.forEach(code => {
    const role = roles.find(r => r.role_code === code);
    if (role && !recommendedIds.includes(role.id)) {
      recommendedIds.push(role.id);
    }
  });

  return recommendedIds;
};

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [departments, setDepartments] = useState([]);

  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    email: '',
    phone: '',
    real_name: '',
    employee_no: '',
    department: '',
    position: '',
    role_ids: [],
  });

  const [editUser, setEditUser] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [showSyncDialog, setShowSyncDialog] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [showRoleDialog, setShowRoleDialog] = useState(false);
  const [roleAssignUser, setRoleAssignUser] = useState(null);

  // 加载用户列表
  const loadUsers = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterDepartment !== 'all') {
        params.department = filterDepartment;
      }
      if (filterStatus !== 'all') {
        params.is_active = filterStatus === 'active';
      }

      const response = await userApi.list(params);
      const data = response.data;
      setUsers(data.items || []);
      setTotal(data.total || 0);
      
      // 提取部门列表
      const deptSet = new Set();
      (data.items || []).forEach(user => {
        if (user.department) {
          deptSet.add(user.department);
        }
      });
      setDepartments(Array.from(deptSet).sort());
    } catch (error) {
      console.error('加载用户列表失败:', error);
      alert('加载用户列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await roleApi.list({ page: 1, page_size: 100 });
      const data = response.data;
      setRoles(data.items || []);
    } catch (error) {
      console.error('加载角色列表失败:', error);
    }
  };

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, [page, searchKeyword, filterDepartment, filterStatus]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewUser((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditUser((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      await userApi.create(newUser);
      setShowCreateDialog(false);
      setNewUser({
        username: '',
        password: '',
        email: '',
        phone: '',
        real_name: '',
        employee_no: '',
        department: '',
        position: '',
        role_ids: [],
      });
      loadUsers();
    } catch (error) {
      alert('创建用户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditSubmit = async () => {
    try {
      await userApi.update(editUser.id, editUser);
      setShowEditDialog(false);
      setEditUser(null);
      loadUsers();
    } catch (error) {
      alert('更新用户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('确定要禁用此用户吗？禁用后用户将无法登录系统。')) {
      return;
    }
    try {
      await userApi.delete(id);
      alert('用户已成功禁用');
      loadUsers();
    } catch (error) {
      alert('删除用户失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await userApi.get(id);
      setSelectedUser(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert('获取用户详情失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await userApi.get(id);
      setEditUser(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert('获取用户信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 打开角色分配对话框
  const handleOpenRoleDialog = async (userId) => {
    try {
      const response = await userApi.get(userId);
      setRoleAssignUser(response.data);
      setShowRoleDialog(true);
    } catch (error) {
      alert('获取用户信息失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 保存角色分配
  const handleSaveRoles = async () => {
    try {
      await userApi.assignRoles(roleAssignUser.id, { role_ids: roleAssignUser.role_ids || [] });
      setShowRoleDialog(false);
      setRoleAssignUser(null);
      loadUsers();
      alert('角色分配成功');
    } catch (error) {
      alert('角色分配失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 从员工同步用户
  const handleSyncFromEmployees = async () => {
    setSyncing(true);
    try {
      const response = await userApi.syncFromEmployees({
        only_active: true,
        auto_activate: false,
      });
      setSyncResult(response.data.data);
      setShowSyncDialog(true);
      loadUsers();
    } catch (error) {
      alert('同步失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSyncing(false);
    }
  };

  // 切换用户激活状态
  const handleToggleActive = async (userId, currentActive) => {
    try {
      await userApi.toggleActive(userId, !currentActive);
      loadUsers();
    } catch (error) {
      alert('操作失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 重置密码
  const handleResetPassword = async (userId, username) => {
    if (!window.confirm(`确定要重置用户 ${username} 的密码吗？密码将重置为初始密码。`)) {
      return;
    }
    try {
      const response = await userApi.resetPassword(userId);
      alert(`密码已重置为: ${response.data.data.new_password}`);
    } catch (error) {
      alert('重置密码失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 批量激活/禁用
  const handleBatchToggleActive = async (isActive) => {
    if (selectedUserIds.length === 0) {
      alert('请先选择要操作的用户');
      return;
    }
    const action = isActive ? '激活' : '禁用';
    if (!window.confirm(`确定要${action}选中的 ${selectedUserIds.length} 个用户吗？`)) {
      return;
    }
    try {
      await userApi.batchToggleActive(selectedUserIds, isActive);
      setSelectedUserIds([]);
      loadUsers();
      alert(`批量${action}成功`);
    } catch (error) {
      alert('批量操作失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 选择/取消选择用户
  const handleSelectUser = (userId) => {
    setSelectedUserIds(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  // 全选/取消全选
  const handleSelectAll = () => {
    if (selectedUserIds.length === users.length) {
      setSelectedUserIds([]);
    } else {
      setSelectedUserIds(users.map(u => u.id));
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
        title="用户管理"
        description="管理系统用户，包括创建、编辑、分配角色等操作。"
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={handleSyncFromEmployees}
              disabled={syncing}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", syncing && "animate-spin")} />
              {syncing ? '同步中...' : '从员工同步'}
            </Button>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" /> 新增用户
            </Button>
          </div>
        }
      />

      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div className="flex items-center space-x-4">
              <CardTitle>用户列表</CardTitle>
              {selectedUserIds.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-muted-foreground">
                    已选择 {selectedUserIds.length} 项
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBatchToggleActive(true)}
                  >
                    <ToggleRight className="mr-1 h-4 w-4" /> 批量激活
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBatchToggleActive(false)}
                  >
                    <ToggleLeft className="mr-1 h-4 w-4" /> 批量禁用
                  </Button>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="搜索用户名/姓名/工号/邮箱..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="max-w-sm"
              />
              <Select value={filterDepartment} onValueChange={setFilterDepartment}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="筛选部门" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有部门</SelectItem>
                  {departments.map((dept) => (
                    <SelectItem key={dept} value={dept}>
                      {dept}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="筛选状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="active">启用</SelectItem>
                  <SelectItem value="inactive">禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-4 text-center text-muted-foreground">加载中...</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="px-2 py-2 text-center">
                          <button
                            onClick={handleSelectAll}
                            className="p-1 hover:bg-muted rounded"
                          >
                            {selectedUserIds.length === users.length && users.length > 0 ? (
                              <CheckSquare className="h-4 w-4" />
                            ) : (
                              <Square className="h-4 w-4" />
                            )}
                          </button>
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">用户名</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">姓名</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">工号</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">部门/职位</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">角色</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">状态</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {users.map((user) => (
                        <tr key={user.id} className={cn(selectedUserIds.includes(user.id) && "bg-muted/50")}>
                          <td className="px-2 py-2 text-center">
                            <button
                              onClick={() => handleSelectUser(user.id)}
                              className="p-1 hover:bg-muted rounded"
                              disabled={user.is_superuser}
                            >
                              {selectedUserIds.includes(user.id) ? (
                                <CheckSquare className="h-4 w-4" />
                              ) : (
                                <Square className="h-4 w-4" />
                              )}
                            </button>
                          </td>
                          <td className="px-4 py-2 text-sm text-foreground">{user.username}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">{user.real_name || '-'}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">{user.employee_no || '-'}</td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            <div>{user.department || '-'}</div>
                            <div className="text-xs">{user.position || '-'}</div>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex flex-wrap gap-1">
                              {user.roles && user.roles.length > 0 ? (
                                user.roles.map((role, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs">
                                    {role}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-muted-foreground text-xs">无角色</span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleToggleActive(user.id, user.is_active)}
                                disabled={user.is_superuser}
                                className={cn(
                                  "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                                  user.is_active ? "bg-primary" : "bg-muted",
                                  user.is_superuser && "opacity-50 cursor-not-allowed"
                                )}
                                title={user.is_active ? '点击禁用' : '点击激活'}
                              >
                                <span
                                  className={cn(
                                    "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                                    user.is_active ? "translate-x-6" : "translate-x-1"
                                  )}
                                />
                              </button>
                              {user.is_superuser && (
                                <Badge variant="destructive" className="ml-1">
                                  <Shield className="h-3 w-3 mr-1" /> 超管
                                </Badge>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewDetail(user.id)}
                                title="查看详情"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(user.id)}
                                title="编辑"
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenRoleDialog(user.id)}
                                title="分配角色"
                                disabled={user.is_superuser}
                              >
                                <UserCog className="h-4 w-4 text-purple-500" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleResetPassword(user.id, user.username)}
                                title="重置密码"
                                disabled={user.is_superuser}
                              >
                                <Key className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(user.id)}
                                title="禁用"
                                disabled={user.is_superuser}
                              >
                                <Trash2 className="h-4 w-4 text-red-500" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {users.length === 0 && (
                  <p className="p-4 text-center text-muted-foreground">
                    没有找到符合条件的用户。
                  </p>
                )}
                {total > pageSize && (
                  <div className="mt-4 flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(Math.ceil(total / pageSize), p + 1))}
                        disabled={page >= Math.ceil(total / pageSize)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>新增用户</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-username" className="text-right">用户名 *</Label>
              <Input
                id="create-username"
                name="username"
                value={newUser.username}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-password" className="text-right">密码 *</Label>
              <Input
                id="create-password"
                name="password"
                type="password"
                value={newUser.password}
                onChange={handleCreateChange}
                className="col-span-3"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-real-name" className="text-right">姓名</Label>
              <Input
                id="create-real-name"
                name="real_name"
                value={newUser.real_name}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-email" className="text-right">邮箱</Label>
              <Input
                id="create-email"
                name="email"
                type="email"
                value={newUser.email}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-phone" className="text-right">手机号</Label>
              <Input
                id="create-phone"
                name="phone"
                value={newUser.phone}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-employee-no" className="text-right">工号</Label>
              <Input
                id="create-employee-no"
                name="employee_no"
                value={newUser.employee_no}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-department" className="text-right">部门</Label>
              <Input
                id="create-department"
                name="department"
                value={newUser.department}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-position" className="text-right">职位</Label>
              <Input
                id="create-position"
                name="position"
                value={newUser.position}
                onChange={handleCreateChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">角色</Label>
              <div className="col-span-3 space-y-2">
                <div className="max-h-[150px] overflow-y-auto border rounded-lg p-2 space-y-1">
                  {roles.map((role) => {
                    const isSelected = newUser.role_ids?.includes(role.id);
                    return (
                      <label
                        key={role.id}
                        className={cn(
                          "flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-muted/50",
                          isSelected && "bg-primary/10"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            const newRoleIds = e.target.checked
                              ? [...(newUser.role_ids || []), role.id]
                              : (newUser.role_ids || []).filter(id => id !== role.id);
                            setNewUser(prev => ({ ...prev, role_ids: newRoleIds }));
                          }}
                          className="rounded border-gray-300"
                        />
                        <div className="flex-1">
                          <span className="font-medium">{role.role_name}</span>
                          <span className="text-xs text-muted-foreground ml-2">({role.role_code})</span>
                        </div>
                      </label>
                    );
                  })}
                </div>
                <div className="text-xs text-muted-foreground">
                  已选择 {newUser.role_ids?.length || 0} 个角色
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreateSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>编辑用户</DialogTitle>
          </DialogHeader>
          {editUser && (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-real-name" className="text-right">姓名</Label>
                <Input
                  id="edit-real-name"
                  name="real_name"
                  value={editUser.real_name || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-email" className="text-right">邮箱</Label>
                <Input
                  id="edit-email"
                  name="email"
                  type="email"
                  value={editUser.email || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-phone" className="text-right">手机号</Label>
                <Input
                  id="edit-phone"
                  name="phone"
                  value={editUser.phone || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-department" className="text-right">部门</Label>
                <Input
                  id="edit-department"
                  name="department"
                  value={editUser.department || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-position" className="text-right">职位</Label>
                <Input
                  id="edit-position"
                  name="position"
                  value={editUser.position || ''}
                  onChange={handleEditChange}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-is-active" className="text-right">状态</Label>
                <Select
                  value={editUser.is_active ? 'active' : 'inactive'}
                  onValueChange={(value) =>
                    setEditUser((prev) => ({ ...prev, is_active: value === 'active' }))
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">启用</SelectItem>
                    <SelectItem value="inactive">禁用</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-start gap-4">
                <Label className="text-right pt-2">角色分配</Label>
                <div className="col-span-3 space-y-2">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-xs text-muted-foreground">
                      当前职位: {editUser.position || '未设置'}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const recommended = getRecommendedRoles(editUser.position, roles);
                        if (recommended.length > 0) {
                          setEditUser(prev => ({ ...prev, role_ids: recommended }));
                        } else {
                          alert('无法根据当前职位自动推荐角色，请手动选择');
                        }
                      }}
                    >
                      自动推荐角色
                    </Button>
                  </div>
                  <div className="max-h-[200px] overflow-y-auto border rounded-lg p-2 space-y-1">
                    {roles.map((role) => {
                      const isSelected = editUser.role_ids?.includes(role.id);
                      return (
                        <label
                          key={role.id}
                          className={cn(
                            "flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-muted/50",
                            isSelected && "bg-primary/10"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={(e) => {
                              const newRoleIds = e.target.checked
                                ? [...(editUser.role_ids || []), role.id]
                                : (editUser.role_ids || []).filter(id => id !== role.id);
                              setEditUser(prev => ({ ...prev, role_ids: newRoleIds }));
                            }}
                            className="rounded border-gray-300"
                          />
                          <div className="flex-1">
                            <span className="font-medium">{role.role_name}</span>
                            <span className="text-xs text-muted-foreground ml-2">({role.role_code})</span>
                            {role.description && (
                              <p className="text-xs text-muted-foreground">{role.description}</p>
                            )}
                          </div>
                        </label>
                      );
                    })}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    已选择 {editUser.role_ids?.length || 0} 个角色
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleEditSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>用户详情</DialogTitle>
          </DialogHeader>
          {selectedUser && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">用户名</Label>
                  <p className="font-medium">{selectedUser.username}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">姓名</Label>
                  <p className="font-medium">{selectedUser.real_name || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">工号</Label>
                  <p className="font-medium">{selectedUser.employee_no || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">邮箱</Label>
                  <p className="font-medium">{selectedUser.email || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">手机号</Label>
                  <p className="font-medium">{selectedUser.phone || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">部门</Label>
                  <p className="font-medium">{selectedUser.department || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">职位</Label>
                  <p className="font-medium">{selectedUser.position || '-'}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge variant={selectedUser.is_active ? 'default' : 'secondary'}>
                      {selectedUser.is_active ? '启用' : '禁用'}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">角色</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedUser.roles && selectedUser.roles.length > 0 ? (
                      selectedUser.roles.map((role, idx) => (
                        <Badge key={idx} variant="secondary">
                          {role}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-muted-foreground">无角色</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sync Result Dialog */}
      <Dialog open={showSyncDialog} onOpenChange={setShowSyncDialog}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>同步结果</DialogTitle>
          </DialogHeader>
          {syncResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-2xl font-bold">{syncResult.total_employees}</p>
                  <p className="text-sm text-muted-foreground">员工总数</p>
                </div>
                <div className="p-4 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{syncResult.created}</p>
                  <p className="text-sm text-muted-foreground">新创建账号</p>
                </div>
                <div className="p-4 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                  <p className="text-2xl font-bold text-yellow-600">{syncResult.skipped}</p>
                  <p className="text-sm text-muted-foreground">已有账号跳过</p>
                </div>
              </div>

              {syncResult.created_users && syncResult.created_users.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium">新创建的账号：</h4>
                  <div className="max-h-[300px] overflow-y-auto border rounded-lg">
                    <table className="min-w-full divide-y divide-border text-sm">
                      <thead className="bg-muted sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left">姓名</th>
                          <th className="px-3 py-2 text-left">工号</th>
                          <th className="px-3 py-2 text-left">用户名</th>
                          <th className="px-3 py-2 text-left">初始密码</th>
                          <th className="px-3 py-2 text-left">部门</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {syncResult.created_users.map((user, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2">{user.employee_name}</td>
                            <td className="px-3 py-2">{user.employee_code}</td>
                            <td className="px-3 py-2 font-mono">{user.username}</td>
                            <td className="px-3 py-2 font-mono text-primary">{user.initial_password}</td>
                            <td className="px-3 py-2">{user.department}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    注意：新账号默认未激活，需要管理员手动激活后才能登录。初始密码为：姓名拼音 + 工号后4位。
                  </p>
                </div>
              )}

              {syncResult.errors && syncResult.errors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-red-500">同步失败：</h4>
                  <div className="max-h-[150px] overflow-y-auto border border-red-200 rounded-lg p-2">
                    {syncResult.errors.map((err, idx) => (
                      <p key={idx} className="text-sm text-red-500">
                        {err.employee_name}: {err.error}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowSyncDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Role Assignment Dialog */}
      <Dialog open={showRoleDialog} onOpenChange={setShowRoleDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>分配角色</DialogTitle>
          </DialogHeader>
          {roleAssignUser && (
            <div className="space-y-4 py-4">
              <div className="flex items-center space-x-4 p-3 bg-muted rounded-lg">
                <div className="flex-1">
                  <p className="font-medium">{roleAssignUser.real_name || roleAssignUser.username}</p>
                  <p className="text-sm text-muted-foreground">
                    {roleAssignUser.department || '未设置部门'} | {roleAssignUser.position || '未设置职位'}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const recommended = getRecommendedRoles(roleAssignUser.position, roles);
                    if (recommended.length > 0) {
                      setRoleAssignUser(prev => ({ ...prev, role_ids: recommended }));
                    } else {
                      alert('无法根据当前职位自动推荐角色，请手动选择');
                    }
                  }}
                >
                  自动推荐
                </Button>
              </div>

              <div className="space-y-2">
                <Label>选择角色</Label>
                <div className="max-h-[300px] overflow-y-auto border rounded-lg p-2 space-y-1">
                  {roles.map((role) => {
                    const isSelected = roleAssignUser.role_ids?.includes(role.id);
                    return (
                      <label
                        key={role.id}
                        className={cn(
                          "flex items-center space-x-2 p-2 rounded cursor-pointer hover:bg-muted/50",
                          isSelected && "bg-primary/10"
                        )}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            const newRoleIds = e.target.checked
                              ? [...(roleAssignUser.role_ids || []), role.id]
                              : (roleAssignUser.role_ids || []).filter(id => id !== role.id);
                            setRoleAssignUser(prev => ({ ...prev, role_ids: newRoleIds }));
                          }}
                          className="rounded border-gray-300"
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{role.role_name}</span>
                            <Badge variant="outline" className="text-xs">{role.role_code}</Badge>
                          </div>
                          {role.description && (
                            <p className="text-xs text-muted-foreground mt-1">{role.description}</p>
                          )}
                        </div>
                      </label>
                    );
                  })}
                </div>
                <div className="text-sm text-muted-foreground">
                  已选择 {roleAssignUser.role_ids?.length || 0} 个角色
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRoleDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveRoles}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}

