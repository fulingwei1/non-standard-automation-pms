import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  Check } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter } from
"../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { roleApi } from "../services/api";
import {
  allMenuGroups,
  buildNavGroupsFromSelection,
  extractMenuIdsFromNavGroups } from
"../lib/allMenuItems";

export default function RoleManagement() {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);
  const [showMenuDialog, setShowMenuDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  // 数据权限范围选项
  const dataScopeOptions = [
  { value: "ALL", label: "全部数据", description: "可访问系统所有数据" },
  { value: "BUSINESS_UNIT", label: "本事业部", description: "可访问本事业部及下属部门的数据" },
  { value: "DEPARTMENT", label: "本部门", description: "可访问本部门及下属团队的数据" },
  { value: "TEAM", label: "本团队", description: "仅可访问本团队的数据" },
  { value: "PROJECT", label: "参与项目", description: "仅可访问参与项目的数据" },
  { value: "OWN", label: "仅本人", description: "仅可访问自己创建或负责的数据" }];


  // 角色类别选项
  const roleCategoryOptions = [
  { value: "MANAGEMENT", label: "管理类" },
  { value: "TECHNICAL", label: "技术类" },
  { value: "SALES", label: "销售类" },
  { value: "FINANCE", label: "财务类" },
  { value: "PRODUCTION", label: "生产类" },
  { value: "SUPPORT", label: "支持类" },
  { value: "OTHER", label: "其他" }];


  const [newRole, setNewRole] = useState({
    role_code: "",
    role_name: "",
    description: "",
    data_scope: "OWN",
    role_category: "",
    permission_ids: []
  });

  const [editRole, setEditRole] = useState(null);
  const [selectedPermissionIds, setSelectedPermissionIds] = useState([]);

  // 菜单配置相关状态
  const [selectedMenuIds, setSelectedMenuIds] = useState([]);
  const [expandedGroups, setExpandedGroups] = useState({});
  const [savingMenu, setSavingMenu] = useState(false);

  // 加载角色列表
  const loadRoles = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterStatus !== "all") {
        params.is_active = filterStatus === "active";
      }

      const response = await roleApi.list(params);
      const data = response.data;
      setRoles(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("加载角色列表失败:", error);
      alert(
        "加载角色列表失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  // 加载权限列表
  const loadPermissions = async () => {
    try {
      const response = await roleApi.permissions();
      setPermissions(response.data || []);
    } catch (error) {
      console.error("加载权限列表失败:", error);
    }
  };

  useEffect(() => {
    loadRoles();
    loadPermissions();
  }, [page, searchKeyword, filterStatus]);

  const handleCreateChange = (e) => {
    const { name, value } = e.target;
    setNewRole((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditRole((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreateSubmit = async () => {
    try {
      await roleApi.create(newRole);
      setShowCreateDialog(false);
      setNewRole({
        role_code: "",
        role_name: "",
        description: "",
        data_scope: "OWN",
        role_category: "",
        permission_ids: []
      });
      loadRoles();
    } catch (error) {
      alert("创建角色失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditSubmit = async () => {
    try {
      await roleApi.update(editRole.id, editRole);
      setShowEditDialog(false);
      setEditRole(null);
      loadRoles();
    } catch (error) {
      alert("更新角色失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const response = await roleApi.get(id);
      setSelectedRole(response.data);
      setShowDetailDialog(true);
    } catch (error) {
      alert(
        "获取角色详情失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleEdit = async (id) => {
    try {
      const response = await roleApi.get(id);
      setEditRole(response.data);
      setShowEditDialog(true);
    } catch (error) {
      alert(
        "获取角色信息失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleAssignPermissions = async (id) => {
    try {
      const response = await roleApi.get(id);
      setSelectedRole(response.data);
      setSelectedPermissionIds(
        response.data.permissions?.
        map((p, _idx) => {
          // 如果permissions是字符串数组，需要找到对应的权限ID
          const perm = permissions.find((perm) => perm.permission_name === p);
          return perm ? perm.id : null;
        }).
        filter(Boolean) || []
      );
      setShowPermissionDialog(true);
    } catch (error) {
      alert(
        "获取角色信息失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleSavePermissions = async () => {
    try {
      await roleApi.assignPermissions(selectedRole.id, selectedPermissionIds);
      setShowPermissionDialog(false);
      loadRoles();
    } catch (error) {
      alert("分配权限失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 菜单配置相关函数
  const handleConfigureMenu = async (id) => {
    try {
      const response = await roleApi.getNavGroups(id);
      const data = response.data;
      setSelectedRole({
        id: data.role_id,
        role_code: data.role_code,
        role_name: data.role_name
      });

      // 从现有导航组提取选中的菜单ID
      const menuIds = extractMenuIdsFromNavGroups(data.nav_groups || []);
      setSelectedMenuIds(menuIds);

      // 默认展开所有分组
      const expanded = {};
      allMenuGroups.forEach((group) => {
        expanded[group.id] = true;
      });
      setExpandedGroups(expanded);

      setShowMenuDialog(true);
    } catch (error) {
      alert(
        "获取角色菜单配置失败: " + (
        error.response?.data?.detail || error.message)
      );
    }
  };

  const handleSaveMenuConfig = async () => {
    setSavingMenu(true);
    try {
      // 根据选中的菜单ID构建导航组
      const navGroups = buildNavGroupsFromSelection(selectedMenuIds);
      await roleApi.updateNavGroups(selectedRole.id, navGroups);
      setShowMenuDialog(false);
      alert("菜单配置保存成功！用户重新登录后将看到新的菜单。");
      loadRoles();
    } catch (error) {
      alert(
        "保存菜单配置失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setSavingMenu(false);
    }
  };

  const toggleMenuGroup = (groupId) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };

  const toggleMenuItem = (itemId) => {
    setSelectedMenuIds((prev) => {
      if (prev.includes(itemId)) {
        return prev.filter((id) => id !== itemId);
      } else {
        return [...prev, itemId];
      }
    });
  };

  const toggleGroupAll = (group) => {
    const groupItemIds = group.items.map((item) => item.id);
    const allSelected = groupItemIds.every((id) =>
    selectedMenuIds.includes(id)
    );

    if (allSelected) {
      // 取消选中该分组的所有菜单
      setSelectedMenuIds((prev) =>
      prev.filter((id) => !groupItemIds.includes(id))
      );
    } else {
      // 选中该分组的所有菜单
      setSelectedMenuIds((prev) => [...new Set([...prev, ...groupItemIds])]);
    }
  };

  const selectAllMenus = () => {
    const allIds = allMenuGroups.flatMap((group) =>
    group.items.map((item) => item.id)
    );
    setSelectedMenuIds(allIds);
  };

  const clearAllMenus = () => {
    setSelectedMenuIds([]);
  };

  // 按模块分组权限
  const permissionsByModule = permissions.reduce((acc, perm) => {
    const module = perm.module || "其他";
    if (!acc[module]) {
      acc[module] = [];
    }
    acc[module].push(perm);
    return acc;
  }, {});

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="角色管理"
        description="管理系统角色，包括创建、编辑、分配权限和菜单配置等操作。"
        actions={
        <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" /> 新增角色
          </Button>
        } />


      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>角色列表</CardTitle>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="搜索角色编码/名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="max-w-sm" />

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
            {loading ?
            <div className="p-4 text-center text-muted-foreground">
                加载中...
              </div> :

            <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          角色编码
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          角色名称
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          描述
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          权限数量
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          数据权限
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          状态
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-semibold text-foreground">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {roles.map((role) =>
                    <tr key={role.id}>
                          <td className="px-4 py-2 text-sm text-foreground font-mono">
                            {role.role_code}
                          </td>
                          <td className="px-4 py-2 text-sm text-foreground">
                            {role.role_name}
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {role.description || "-"}
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {role.permissions?.length || 0} 个权限
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            <Badge variant="outline">
                              {dataScopeOptions.find((opt) => opt.value === role.data_scope)?.label || role.data_scope || "未设置"}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center gap-1 flex-wrap">
                              <Badge
                            variant={role.is_active ? "default" : "secondary"}>

                                {role.is_active ? "启用" : "禁用"}
                              </Badge>
                              {role.role_type === "SYSTEM" || role.is_system ?
                          <Badge variant="destructive">
                                  <Shield className="h-3 w-3 mr-1" /> 系统
                                </Badge> :

                          <Badge variant="outline" className="text-blue-600 border-blue-300">
                                  自定义
                                </Badge>
                          }
                            </div>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-1">
                              <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(role.id)}
                            title="查看详情">

                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(role.id)}
                            disabled={role.is_system}
                            title="编辑角色">

                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleAssignPermissions(role.id)}
                            disabled={role.is_system}
                            title="分配API权限">

                                <Key className="h-4 w-4" />
                              </Button>
                              <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleConfigureMenu(role.id)}
                            title="配置菜单"
                            className="text-blue-600 hover:text-blue-700">

                                <Menu className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                    )}
                    </tbody>
                  </table>
                </div>
                {roles.length === 0 &&
              <p className="p-4 text-center text-muted-foreground">
                    没有找到符合条件的角色。
                  </p>
              }
                {total > pageSize &&
              <div className="mt-4 flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      共 {total} 条记录，第 {page} /{" "}
                      {Math.ceil(total / pageSize)} 页
                    </div>
                    <div className="flex space-x-2">
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}>

                        上一页
                      </Button>
                      <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                    setPage((p) =>
                    Math.min(Math.ceil(total / pageSize), p + 1)
                    )
                    }
                    disabled={page >= Math.ceil(total / pageSize)}>

                        下一页
                      </Button>
                    </div>
                  </div>
              }
              </>
            }
          </CardContent>
        </Card>
      </motion.div>

      {/* Create Dialog */}
      <Dialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          setShowCreateDialog(open);
          if (!open) {
            // 关闭对话框时重置表单
            setNewRole({
              role_code: "",
              role_name: "",
              description: "",
              data_scope: "OWN",
              role_category: "",
              permission_ids: []
            });
          }
        }}>

        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>新增角色</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-role-code" className="text-right">
                角色编码 *
              </Label>
              <div className="col-span-3 space-y-1">
                <Input
                  id="create-role-code"
                  name="role_code"
                  value={newRole.role_code}
                  onChange={handleCreateChange}
                  placeholder="如：SALES_MANAGER, TECH_LEAD"
                  className="font-mono"
                  required />

                <p className="text-xs text-muted-foreground">
                  建议使用大写字母和下划线，如 PROJECT_MANAGER
                </p>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-role-name" className="text-right">
                角色名称 *
              </Label>
              <Input
                id="create-role-name"
                name="role_name"
                value={newRole.role_name}
                onChange={handleCreateChange}
                className="col-span-3"
                required />

            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-description" className="text-right">
                描述
              </Label>
              <Textarea
                id="create-description"
                name="description"
                value={newRole.description}
                onChange={handleCreateChange}
                className="col-span-3"
                rows={2} />

            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="create-role-category" className="text-right">
                角色类别
              </Label>
              <Select
                value={newRole.role_category}
                onValueChange={(value) =>
                setNewRole((prev) => ({ ...prev, role_category: value }))
                }>

                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="请选择角色类别" />
                </SelectTrigger>
                <SelectContent>
                  {roleCategoryOptions.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-start gap-4">
              <Label htmlFor="create-data-scope" className="text-right pt-2">
                数据权限
              </Label>
              <div className="col-span-3 space-y-2">
                <Select
                  value={newRole.data_scope}
                  onValueChange={(value) =>
                  setNewRole((prev) => ({ ...prev, data_scope: value }))
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {dataScopeOptions.map((option) =>
                    <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {newRole.data_scope &&
                <p className="text-xs text-muted-foreground">
                    {dataScopeOptions.find((opt) => opt.value === newRole.data_scope)?.description}
                  </p>
                }
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

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
            <DialogTitle>编辑角色</DialogTitle>
          </DialogHeader>
          {editRole &&
          <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-role-name" className="text-right">
                  角色名称
                </Label>
                <Input
                id="edit-role-name"
                name="role_name"
                value={editRole.role_name || ""}
                onChange={handleEditChange}
                className="col-span-3" />

              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-description" className="text-right">
                  描述
                </Label>
                <Textarea
                id="edit-description"
                name="description"
                value={editRole.description || ""}
                onChange={handleEditChange}
                className="col-span-3"
                rows={2} />

              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-role-category" className="text-right">
                  角色类别
                </Label>
                <Select
                value={editRole.role_category || ""}
                onValueChange={(value) =>
                setEditRole((prev) => ({ ...prev, role_category: value }))
                }>

                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="请选择角色类别" />
                  </SelectTrigger>
                  <SelectContent>
                    {roleCategoryOptions.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                  )}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-start gap-4">
                <Label htmlFor="edit-data-scope" className="text-right pt-2">
                  数据权限
                </Label>
                <div className="col-span-3 space-y-2">
                  <Select
                  value={editRole.data_scope || "OWN"}
                  onValueChange={(value) =>
                  setEditRole((prev) => ({ ...prev, data_scope: value }))
                  }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {dataScopeOptions.map((option) =>
                    <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                    )}
                    </SelectContent>
                  </Select>
                  {editRole.data_scope &&
                <p className="text-xs text-muted-foreground">
                      {dataScopeOptions.find((opt) => opt.value === editRole.data_scope)?.description}
                    </p>
                }
                </div>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="edit-is-active" className="text-right">
                  状态
                </Label>
                <Select
                value={editRole.is_active ? "active" : "inactive"}
                onValueChange={(value) =>
                setEditRole((prev) => ({
                  ...prev,
                  is_active: value === "active"
                }))
                }>

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
          }
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleEditSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Permission Assignment Dialog */}
      <Dialog
        open={showPermissionDialog}
        onOpenChange={setShowPermissionDialog}>

        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>分配API权限 - {selectedRole?.role_name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {Object.entries(permissionsByModule).map(
              ([module, modulePermissions]) =>
              <div key={module} className="space-y-2">
                  <h4 className="font-semibold text-sm">{module}</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {modulePermissions.map((perm) =>
                  <label
                    key={perm.id}
                    className="flex items-center space-x-2 p-2 rounded border hover:bg-muted cursor-pointer">

                        <input
                      type="checkbox"
                      checked={selectedPermissionIds.includes(perm.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedPermissionIds([
                          ...selectedPermissionIds,
                          perm.id]
                          );
                        } else {
                          setSelectedPermissionIds(
                            selectedPermissionIds.filter(
                              (id) => id !== perm.id
                            )
                          );
                        }
                      }}
                      className="rounded" />

                        <span className="text-sm">{perm.permission_name}</span>
                      </label>
                  )}
                  </div>
                </div>

            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowPermissionDialog(false)}>

              取消
            </Button>
            <Button onClick={handleSavePermissions}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Menu Configuration Dialog */}
      <Dialog open={showMenuDialog} onOpenChange={setShowMenuDialog}>
        <DialogContent className="sm:max-w-[800px] max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>配置菜单权限 - {selectedRole?.role_name}</DialogTitle>
          </DialogHeader>

          <div className="flex items-center justify-between py-2 border-b">
            <div className="text-sm text-muted-foreground">
              已选择{" "}
              <span className="font-semibold text-foreground">
                {selectedMenuIds.length}
              </span>{" "}
              个菜单项
            </div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" onClick={selectAllMenus}>
                全选
              </Button>
              <Button variant="outline" size="sm" onClick={clearAllMenus}>
                清空
              </Button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto py-4 space-y-2">
            {allMenuGroups.map((group) => {
              const groupItemIds = group.items.map((item) => item.id);
              const selectedCount = groupItemIds.filter((id) =>
              selectedMenuIds.includes(id)
              ).length;
              const allSelected = selectedCount === groupItemIds.length;
              const someSelected =
              selectedCount > 0 && selectedCount < groupItemIds.length;

              return (
                <div key={group.id} className="border rounded-lg">
                  {/* 分组标题 */}
                  <div
                    className="flex items-center justify-between p-3 bg-muted/50 cursor-pointer hover:bg-muted"
                    onClick={() => toggleMenuGroup(group.id)}>

                    <div className="flex items-center space-x-2">
                      {expandedGroups[group.id] ?
                      <ChevronDown className="h-4 w-4" /> :

                      <ChevronRight className="h-4 w-4" />
                      }
                      <span className="font-medium">{group.label}</span>
                      <Badge variant="secondary" className="text-xs">
                        {selectedCount}/{groupItemIds.length}
                      </Badge>
                    </div>
                    <div
                      className="flex items-center space-x-2"
                      onClick={(e) => e.stopPropagation()}>

                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={allSelected}
                          ref={(el) => {
                            if (el) el.indeterminate = someSelected;
                          }}
                          onChange={() => toggleGroupAll(group)}
                          className="rounded" />

                        <span className="text-sm text-muted-foreground">
                          全选
                        </span>
                      </label>
                    </div>
                  </div>

                  {/* 菜单项列表 */}
                  {expandedGroups[group.id] &&
                  <div className="p-3 grid grid-cols-2 md:grid-cols-3 gap-2">
                      {group.items.map((item) =>
                    <label
                      key={item.id}
                      className={cn(
                        "flex items-center space-x-2 p-2 rounded border cursor-pointer transition-colors",
                        selectedMenuIds.includes(item.id) ?
                        "bg-primary/10 border-primary" :
                        "hover:bg-muted"
                      )}>

                          <input
                        type="checkbox"
                        checked={selectedMenuIds.includes(item.id)}
                        onChange={() => toggleMenuItem(item.id)}
                        className="rounded" />

                          <span className="text-sm">{item.name}</span>
                        </label>
                    )}
                    </div>
                  }
                </div>);

            })}
          </div>

          <DialogFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => setShowMenuDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveMenuConfig} disabled={savingMenu}>
              {savingMenu ? "保存中..." : "保存配置"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>角色详情</DialogTitle>
          </DialogHeader>
          {selectedRole &&
          <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">角色编码</Label>
                  <p className="font-medium font-mono">
                    {selectedRole.role_code}
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">角色名称</Label>
                  <p className="font-medium">{selectedRole.role_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">角色类型</Label>
                  <p className="font-medium">
                    {selectedRole.role_type === "SYSTEM" || selectedRole.is_system ?
                  <Badge variant="destructive">
                        <Shield className="h-3 w-3 mr-1" /> 系统角色
                      </Badge> :

                  <Badge variant="outline" className="text-blue-600 border-blue-300">
                        自定义角色
                      </Badge>
                  }
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">角色类别</Label>
                  <p className="font-medium">
                    {roleCategoryOptions.find((opt) => opt.value === selectedRole.role_category)?.label || "-"}
                  </p>
                </div>
                <div className="col-span-2">
                  <Label className="text-muted-foreground">描述</Label>
                  <p className="font-medium">
                    {selectedRole.description || "-"}
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">数据权限</Label>
                  <p className="font-medium">
                    <Badge variant="outline">
                      {dataScopeOptions.find((opt) => opt.value === selectedRole.data_scope)?.label || selectedRole.data_scope || "未设置"}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge
                    variant={selectedRole.is_active ? "default" : "secondary"}>

                      {selectedRole.is_active ? "启用" : "禁用"}
                    </Badge>
                  </p>
                </div>
                <div className="col-span-2">
                  <Label className="text-muted-foreground">API权限列表</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedRole.permissions &&
                  selectedRole.permissions.length > 0 ?
                  selectedRole.permissions.map((perm, idx) =>
                  <Badge key={idx} variant="secondary">
                          {perm}
                        </Badge>
                  ) :

                  <span className="text-muted-foreground">无权限</span>
                  }
                  </div>
                </div>
              </div>
            </div>
          }
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}