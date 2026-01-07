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
    if (!window.confirm('确定要删除此用户吗？')) {
      return;
    }
    try {
      // 注意：后端可能没有实现DELETE，这里只是示例
      // await userApi.delete(id);
      alert('删除功能待实现');
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

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="用户管理"
        description="管理系统用户，包括创建、编辑、分配角色等操作。"
        actions={
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" /> 新增用户
          </Button>
        }
      />

      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>用户列表</CardTitle>
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
                        <tr key={user.id}>
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
                            <Badge variant={user.is_active ? 'default' : 'secondary'}>
                              {user.is_active ? '启用' : '禁用'}
                            </Badge>
                            {user.is_superuser && (
                              <Badge variant="destructive" className="ml-1">
                                <Shield className="h-3 w-3 mr-1" /> 超级管理员
                              </Badge>
                            )}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewDetail(user.id)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEdit(user.id)}
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(user.id)}
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
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-roles" className="text-right">角色</Label>
              <Select
                value={newUser.role_ids.join(',')}
                onValueChange={(value) =>
                  setNewUser((prev) => ({
                    ...prev,
                    role_ids: value ? value.split(',').map(Number) : [],
                  }))
                }
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择角色" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={String(role.id)}>
                      {role.role_name}
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
    </motion.div>
  );
}

