/**
 * Role Assignment Component
 * 角色分配对话框组件
 */

import { useState, useEffect } from "react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Checkbox } from
"../../components/ui/checkbox";
import {
  Label } from
"../../components/ui/label";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../../components/ui/tabs";
import {
  Alert,
  AlertDescription,
  AlertTitle } from
"../../components/ui/alert";
import {
  Shield,
  Users,
  Lock,
  Key,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Info,
  Plus,
  Minus,
  Save,
  RotateCcw,
  Eye,
  EyeOff } from
"lucide-react";
import {
  userRoleConfigs,
  permissionAuditConfigs as _permissionAuditConfigs,
  getUserRoleConfig as _getUserRoleConfig,
  formatUserRole as _formatUserRole } from
"./userManagementConstants";
import { cn } from "../../lib/utils";
import { Checkbox } from "../ui/checkbox";

export function RoleAssignment({
  user,
  isOpen,
  onOpenChange,
  onSave,
  availableRoles = [],
  availablePermissions = [],
  className
}) {
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [selectedPermissions, setSelectedPermissions] = useState({});
  const [dataScope, setDataScope] = useState("OWN");
  const [showPermissionDetails, setShowPermissionDetails] = useState({});
  const [isSaving, setIsSaving] = useState(false);

  // 初始化选中状态
  useEffect(() => {
    if (user?.roles) {
      const roleIds = user.roles.map((ur) => ur.role_id);
      setSelectedRoles(roleIds);

      // 初始化权限选中状态
      const permissions = {};
      user.roles.forEach((ur) => {
        ur.role.permissions.forEach((rp) => {
          permissions[rp.permission_id] = true;
        });
      });
      setSelectedPermissions(permissions);
    }
  }, [user]);

  // 角色变化处理
  const handleRoleChange = (roleId, checked) => {
    if (checked) {
      setSelectedRoles([...selectedRoles, roleId]);
    } else {
      setSelectedRoles(selectedRoles.filter((id) => id !== roleId));
    }
  };

  // 权限变化处理
  const handlePermissionChange = (permissionId, checked) => {
    setSelectedPermissions((prev) => ({
      ...prev,
      [permissionId]: checked
    }));
  };

  // 权限详情切换
  const togglePermissionDetails = (permissionId) => {
    setShowPermissionDetails((prev) => ({
      ...prev,
      [permissionId]: !prev[permissionId]
    }));
  };

  // 获取角色包含的权限
  const _getRolePermissions = (roleId) => {
    const role = availableRoles.find((r) => r.id === roleId);
    return role?.permissions || [];
  };

  // 检查权限是否被选中
  const isPermissionSelected = (permissionId) => {
    return selectedPermissions[permissionId] || false;
  };

  // 保存角色分配
  const handleSave = async () => {
    if (isSaving) {return;}

    setIsSaving(true);
    try {
      const assignmentData = {
        userId: user.id,
        roleIds: selectedRoles,
        permissions: Object.entries(selectedPermissions).
        filter(([_, selected]) => selected).
        map(([permissionId]) => parseInt(permissionId)),
        dataScope
      };

      await onSave?.(assignmentData);
      onOpenChange(false);
    } finally {
      setIsSaving(false);
    }
  };

  // 重置选择
  const handleReset = () => {
    setSelectedRoles([]);
    setSelectedPermissions({});
    setDataScope("OWN");
  };

  // 渲染角色选择
  const renderRoleSelection = () =>
  <div className="space-y-3">
      <Label className="text-sm font-medium">选择角色</Label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto">
        {availableRoles.map((role) => {
        const isSelected = selectedRoles.includes(role.id);
        const roleConfig = userRoleConfigs[role.role_code];

        return (
          <div
            key={role.id}
            className={cn(
              "border rounded-lg p-3 cursor-pointer transition-colors",
              isSelected ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
            )}
            onClick={() => handleRoleChange(role.id, !isSelected)}>

              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{roleConfig.icon}</span>
                    <span className="font-medium">{roleConfig.label}</span>
                    <Badge
                    variant={isSelected ? "default" : "secondary"}
                    className={cn(
                      "text-xs",
                      isSelected && roleConfig.color?.replace('bg-', 'bg-')
                    )}>

                      {role.users?.length || 0} 用户
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    {role.description || "暂无描述"}
                  </p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <span>数据范围:</span>
                    <span>{role.data_scope || "OWN"}</span>
                  </div>
                </div>
                <Checkbox
                checked={isSelected}
                onChange={() => handleRoleChange(role.id, !isSelected)}
                className="mt-1" />

              </div>
          </div>);

      })}
      </div>
  </div>;


  // 渲染权限选择
  const renderPermissionSelection = () => {
    // 按模块分组权限
    const permissionsByModule = {};
    availablePermissions.forEach((permission) => {
      if (!permissionsByModule[permission.module]) {
        permissionsByModule[permission.module] = [];
      }
      permissionsByModule[permission.module].push(permission);
    });

    return (
      <div className="space-y-4">
        <Label className="text-sm font-medium">选择权限</Label>
        <div className="max-h-96 overflow-y-auto space-y-4">
          {Object.entries(permissionsByModule).map(([module, permissions]) =>
          <div key={module} className="border rounded-lg p-3">
              <div className="flex items-center gap-2 mb-3">
                <Shield className="h-4 w-4" />
                <span className="font-medium text-sm">{module}</span>
                <span className="text-xs text-muted-foreground">
                  ({permissions.length} 个权限)
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {permissions.map((permission) =>
              <div key={permission.id} className="flex items-start gap-2">
                    <Checkbox
                  id={`permission-${permission.id}`}
                  checked={isPermissionSelected(permission.id)}
                  onCheckedChange={(checked) =>
                  handlePermissionChange(permission.id, checked)
                  } />

                    <div className="flex-1">
                      <Label
                    htmlFor={`permission-${permission.id}`}
                    className="text-sm cursor-pointer">

                        {permission.permission_name}
                      </Label>
                      <p className="text-xs text-muted-foreground mt-1">
                        {permission.description || "暂无描述"}
                      </p>
                      <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 p-1 mt-1"
                    onClick={() => togglePermissionDetails(permission.id)}>

                        {showPermissionDetails[permission.id] ?
                    <EyeOff className="h-3 w-3" /> :

                    <Eye className="h-3 w-3" />
                    }
                      </Button>
                    </div>
              </div>
              )}
              </div>
          </div>
          )}
        </div>
      </div>);

  };

  // 渲染数据权限
  const renderDataScope = () =>
  <div className="space-y-3">
      <Label className="text-sm font-medium">数据权限范围</Label>
      <Select value={dataScope} onValueChange={setDataScope}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="ALL">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-600" />
              全部数据
            </div>
          </SelectItem>
          <SelectItem value="DEPT">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-600" />
              本部门
            </div>
          </SelectItem>
          <SelectItem value="OWN">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-600" />
              仅本人
            </div>
          </SelectItem>
          <SelectItem value="CUSTOM">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-orange-600" />
              自定义
            </div>
          </SelectItem>
          <SelectItem value="NONE">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-gray-600" />
              无权限
            </div>
          </SelectItem>
        </SelectContent>
      </Select>
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>数据权限说明</AlertTitle>
        <AlertDescription className="text-xs">
          数据权限控制用户能查看和操作的数据范围。超级管理员拥有全部数据权限。
        </AlertDescription>
      </Alert>
  </div>;


  // 渲染权限冲突提示
  const renderPermissionConflicts = () => {
    const conflicts = [];
    const hasSuperAdmin = selectedRoles.some((roleId) => {
      const role = availableRoles.find((r) => r.id === roleId);
      return role?.role_code === "SUPER_ADMIN";
    });

    if (hasSuperAdmin && selectedRoles.length > 1) {
      conflicts.push({
        type: "warning",
        message: "超级管理员角色拥有所有权限，其他角色将被忽略"
      });
    }

    if (dataScope !== "ALL" && hasSuperAdmin) {
      conflicts.push({
        type: "warning",
        message: "超级管理员自动拥有全部数据权限"
      });
    }

    return conflicts.length > 0 ?
    <div className="space-y-2">
        {conflicts.map((conflict, index) =>
      <Alert key={index} variant={conflict.type === "warning" ? "default" : "destructive"}>
            {conflict.type === "warning" ?
        <AlertTriangle className="h-4 w-4" /> :

        <XCircle className="h-4 w-4" />
        }
            <AlertDescription className="text-xs">
              {conflict.message}
            </AlertDescription>
      </Alert>
      )}
    </div> :
    null;
  };

  // 计算总权限数
  const totalPermissions = availablePermissions.length;
  const selectedPermissionsCount = Object.values(selectedPermissions).filter(Boolean).length;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className={cn("max-w-4xl max-h-[90vh] overflow-y-auto", className)}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            角色权限分配 - {user?.real_name || user?.username}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="roles" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="roles">角色分配</TabsTrigger>
            <TabsTrigger value="permissions">权限管理</TabsTrigger>
            <TabsTrigger value="scope">数据权限</TabsTrigger>
          </TabsList>

          <TabsContent value="roles" className="space-y-4">
            {renderRoleSelection()}
            {renderPermissionConflicts()}
          </TabsContent>

          <TabsContent value="permissions" className="space-y-4">
            {renderPermissionSelection()}
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>已选择 {selectedPermissionsCount} / {totalPermissions} 个权限</span>
              <Button variant="ghost" size="sm" onClick={handleReset}>
                <RotateCcw className="mr-1 h-3 w-3" />
                重置选择
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="scope" className="space-y-4">
            {renderDataScope()}
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex justify-between gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleReset}>
              <RotateCcw className="mr-2 h-3 w-3" />
              重置
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ?
              <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  保存中...
              </> :

              <>
                  <Save className="mr-2 h-4 w-4" />
                  保存分配
              </>
              }
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}