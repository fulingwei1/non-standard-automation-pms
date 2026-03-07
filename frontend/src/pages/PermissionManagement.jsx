import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Shield,
  Filter,
  Eye,
  Users,
  Package,
  ChevronDown,
  ChevronRight,
  Key,
  FileText,
  AlertCircle } from
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
  DialogTitle } from
"../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { cn } from "../lib/utils";
import { roleApi } from "../services/api";
import {
 getModuleLabel,
 getActionLabel,
 getActionColor,
 generatePermissionLabel,
} from "../config/permissionLabels";

export default function PermissionManagement() {
  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterModule, setFilterModule] = useState("all");
  const [expandedModules, setExpandedModules] = useState({});
  const [selectedPermission, setSelectedPermission] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [permissionRoles, setPermissionRoles] = useState([]);
 const [permissionUsageStats, setPermissionUsageStats] = useState({ mostUsed: [], unused: [] });

 const token = localStorage.getItem("token");
  const isDemoAccount = token?.startsWith("demo_token_") || false;

  // 加载权限列表
  const loadPermissions = async () => {
    setLoading(true);
    try {
      // 检查token是否存在
      const token = localStorage.getItem("token");
      console.log("[权限管理] 开始加载权限列表...");
      console.log(
        "[权限管理] Token检查:",
        token ?
        token.startsWith("demo_token_") ?
        "演示账号token" :
        `真实token (${token.substring(0, 30)}...)` :
        "❌ 未找到token"
      );

      if (!token) {
        console.error("[权限管理] ❌ 未找到token，请重新登录");
        alert("未找到认证token，请重新登录");
        window.location.href = "/";
        return;
      }

      if (token.startsWith("demo_token_")) {
        console.warn("[权限管理] ⚠️ 这是演示账号token，不会发送到后端");
        // 不直接返回，而是设置一个状态来显示友好的提示界面
        setPermissions([]);
        setLoading(false);
        return;
      }

      console.log("[权限管理] ✅ Token存在，发送请求...");
      let response;
      if (filterModule !== "all") {
        // 如果指定了模块，需要传递module参数
        response = await roleApi.permissions({ module: filterModule });
      } else {
        response = await roleApi.permissions();
      }
      console.log(
        "[权限管理] ✅ 成功获取权限列表:",
        response.formatted?.length || response.data?.data?.length || 0,
        "条"
      );
      // 使用统一响应格式处理
 const permData = response.formatted || response.data?.data || response.data;
      setPermissions(Array.isArray(permData) ? permData : []);
    } catch (error) {
      console.error("[权限管理] ❌ 加载权限列表失败:", error);
      const errorDetail = error.response?.data?.detail || error.message;
      const statusCode = error.response?.status;
      console.error("[权限管理] 错误详情:", {
        status: statusCode,
        detail: errorDetail,
        message: error.message,
        response: error.response?.data
      });

      // 如果是认证错误，提示重新登录
      if (
      statusCode === 401 ||
      statusCode === 403 ||
      errorDetail?.includes("Not authenticated") ||
      errorDetail?.includes("认证") ||
      errorDetail?.includes("无效的认证凭据"))
      {
        console.error("[权限管理] 认证失败，清除token并跳转登录页");
        alert("认证失败，请重新登录");
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.location.href = "/";
      } else {
        // 格式化错误信息
        let errorMessage = errorDetail;
        if (typeof errorDetail === "object") {
          errorMessage = JSON.stringify(errorDetail, null, 2);
        }
        alert("加载权限列表失败: " + errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  // 加载角色列表
  const loadRoles = async () => {
    try {
      const response = await roleApi.list({ page_size: 100 });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      const roleItems = listData?.items || listData;
      setRoles(Array.isArray(roleItems) ? roleItems : []);
    } catch (error) {
      console.error("加载角色列表失败:", error);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token && token.startsWith("demo_token_")) {
      console.log("[权限管理] 演示账号，跳过数据加载");
      return;
    }
    loadPermissions();
    loadRoles();
  }, [filterModule]);

  // 获取所有模块列表
  const modules = Array.from(
    new Set((permissions || []).map((p) => p.module).filter(Boolean))
  ).sort();

  // 按模块分组权限
  const groupedPermissions = (permissions || []).reduce((acc, permission) => {
    const module = permission.module || "其他";
    if (!acc[module]) {
      acc[module] = [];
    }
    acc[module].push(permission);
    return acc;
  }, {});

  // 过滤权限
  const filteredPermissions = Object.entries(groupedPermissions).reduce(
    (acc, [module, perms]) => {
      const filtered = (perms || []).filter((p) => {
        if (!searchKeyword) {return true;}
        const keyword = searchKeyword.toLowerCase();
        return (
          p.permission_code?.toLowerCase().includes(keyword) ||
          p.permission_name?.toLowerCase().includes(keyword) ||
          p.description?.toLowerCase().includes(keyword));

      });
      if (filtered.length > 0) {
        acc[module] = filtered;
      }
      return acc;
    },
    {}
  );

  // 切换模块展开/收起
  const toggleModule = (module) => {
    setExpandedModules((prev) => ({
      ...prev,
      [module]: !prev[module]
    }));
  };

 // 查看权限详情
 const handleViewDetail = (permission) => {
 setSelectedPermission(permission);
 setShowDetailDialog(true);

 // 直接从已加载的角色数据中查找拥有该权限的角色
 // 这样保证与列表显示的统计数据一致
  const rolesWithPermission = (roles || []).filter(role => {
 const rolePermissions = role.permissions || [];
  return rolePermissions.includes(permission.permission_name) ||
   rolePermissions.includes(permission.permission_code);
  });
  setPermissionRoles(rolesWithPermission);
 };

 // 计算权限使用统计
 useEffect(() => {
 if (permissions.length === 0 || roles.length === 0) return;

  // 直接使用已加载的角色权限数据，不再逐个调用 API
 const usageMap = {};

 // 初始化所有权限的统计
 for (const permission of permissions) {
 usageMap[permission.permission_code] = {
 permission,
 roleCount: 0,
 roles: []
 };
 }

 // 遍历角色，统计每个权限被多少角色使用
 for (const role of roles) {
 // 角色已经包含 permissions 数组（权限名称列表）
 const rolePermissions = role.permissions || [];

 for (const permission of permissions) {
 // 检查权限名称或编码是否匹配
 if (rolePermissions.includes(permission.permission_name) ||
  rolePermissions.includes(permission.permission_code)) {
 if (usageMap[permission.permission_code]) {
 usageMap[permission.permission_code].roleCount++;
  usageMap[permission.permission_code].roles.push(role);
 }
 }
 }
  }

 // 找出使用最多的权限（前10）
 const mostUsed = Object.values(usageMap)
 .filter(item => item.roleCount > 0)
 .sort((a, b) => b.roleCount - a.roleCount)
 .slice(0, 10)
 .map(item => ({
 ...item.permission,
 roleCount: item.roleCount,
 roleNames: (item.roles || []).map(r => r.role_name).join(', ')
 }));

 // 找出未使用的权限
 const unused = Object.values(usageMap)
 .filter(item => item.roleCount === 0)
 .map(item => item.permission);

 setPermissionUsageStats({ mostUsed, unused });
 }, [permissions, roles]);

  // 统计信息
  const stats = {
    total: permissions.length,
    modules: modules.length,
    active: (permissions || []).filter((p) => p.is_active !== false).length,
    unused: permissionUsageStats.unused?.length
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="权限管理"
        description="查看和管理系统中的所有权限配置"
        icon={Shield} />


      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">权限总数</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stats.total}
                  </p>
                </div>
                <Key className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">模块数量</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stats.modules}
                  </p>
                </div>
                <Package className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">启用权限</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stats.active}
                  </p>
                </div>
                <Shield className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 权限使用统计 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 最常用权限 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Users className="h-4 w-4 text-blue-400" />
              最常用权限 (TOP 10)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {permissionUsageStats.mostUsed?.length > 0 ? (
              <div className="space-y-2">
                {(permissionUsageStats.mostUsed || []).map((perm, index) => (
                  <div
                    key={perm.permission_code}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500 w-4">{index + 1}</span>
                        <span className="font-medium text-white text-sm truncate">
                          {perm.permission_code}
                        </span>
                        <Badge
                          className={cn("text-xs", getActionColor(perm.action))}
                        >
                          {getActionLabel(perm.action)}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 ml-6 truncate">
                        {generatePermissionLabel(perm)}
                      </p>
                    </div>
                    <div className="text-right ml-2">
                      <div className="text-lg font-bold text-blue-400">{perm.roleCount}</div>
                      <div className="text-xs text-slate-500">个角色</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-slate-500 py-4 text-sm">
                暂无数据
              </div>
            )}
          </CardContent>
        </Card>

        {/* 未使用的权限 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertCircle className="h-4 w-4 text-amber-400" />
              未分配的权限 ({stats.unused})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {permissionUsageStats.unused?.length > 0 ? (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {permissionUsageStats.unused.slice(0, 20).map((perm) => (
                  <div
                    key={perm.permission_code}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 border border-amber-500/20"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm truncate">
                          {perm.permission_code}
                        </span>
                        <Badge
                          className={cn("text-xs", getActionColor(perm.action))}
                        >
                          {getActionLabel(perm.action)}
                        </Badge>
                        <Badge variant="outline" className="text-xs border-amber-500/30 text-amber-400">
                          未使用
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 truncate">
                        {generatePermissionLabel(perm)}
                      </p>
                      {perm.module && (
                        <p className="text-xs text-slate-600">
                          模块: {getModuleLabel(perm.module)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
                {permissionUsageStats.unused?.length > 20 && (
                  <div className="text-center text-xs text-slate-500 pt-2">
                    还有 {permissionUsageStats.unused?.length - 20} 个未分配权限...
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-slate-500 py-4 text-sm">
                ✅ 所有权限都已分配
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索权限编码、名称或描述..."
                value={searchKeyword || "unknown"}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterModule || "unknown"} onValueChange={setFilterModule}>
              <SelectTrigger className="w-full sm:w-[200px]">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="选择模块" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">所有模块</SelectItem>
                {(modules || []).map((module) =>
                <SelectItem key={module} value={module || "unknown"}>
                    {getModuleLabel(module)}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {}
      {isDemoAccount &&
      <Card className="border-amber-500/50 bg-amber-500/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <Shield className="h-8 w-8 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-amber-400 mb-2">
                  演示账号限制
                </h3>
                <p className="text-slate-300 mb-4">
                  权限管理功能需要连接真实的后端服务，演示账号无法访问此功能。
                  如需使用权限管理功能，请使用真实账号登录。
                </p>
                <div className="flex gap-3">
                  <Button
                  onClick={() => {
                    localStorage.removeItem("token");
                    localStorage.removeItem("user");
                    window.location.href = "/";
                  }}
                  className="bg-amber-500 hover:bg-amber-600 text-white">

                    切换到真实账号登录
                  </Button>
                  <Button
                  variant="outline"
                  onClick={() => window.history.back()}
                  className="border-slate-600 text-slate-300 hover:bg-slate-800">

                    返回上一页
                  </Button>
                </div>
                <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-xs text-slate-400 mb-1">💡 提示：</p>
                  <p className="text-xs text-slate-400">
                    真实账号需要后端服务支持。请使用数据库中的真实用户账号登录（如：admin/admin）。
                    如果后端服务未启动或数据库中没有用户，请联系系统管理员。
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
      </Card>
      }

      {/* 权限列表 */}
      {loading ?
      <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">加载中...</div>
          </CardContent>
      </Card> :
      isDemoAccount ? null : Object.keys(filteredPermissions).length ===
      0 ?
      <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-slate-400">
              {searchKeyword ? "未找到匹配的权限" : "暂无权限数据"}
            </div>
          </CardContent>
      </Card> :

      <div className="space-y-4">
          {Object.entries(filteredPermissions).map(([module, perms]) =>
        <motion.div
          key={module}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}>

              <Card>
                <CardHeader>
                  <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleModule(module)}>

                    <CardTitle className="flex items-center gap-2">
                      <Package className="h-5 w-5 text-blue-400" />
                      <span>{getModuleLabel(module)}</span>
                      <Badge variant="secondary" className="ml-2">
                        {perms.length}
                      </Badge>
                    </CardTitle>
                    {expandedModules[module] === true ?
                <ChevronDown className="h-5 w-5 text-slate-400" /> :

                <ChevronRight className="h-5 w-5 text-slate-400" />
                }
                  </div>
                </CardHeader>
                {expandedModules[module] === true &&
            <CardContent>
                    <div className="space-y-2">
                      {(perms || []).map((permission) => {
                        // 从缓存的统计中获取使用次数
                        const usageInfo = (permissionUsageStats.mostUsed || []).find(
                          p => p.permission_code === permission.permission_code
                        );
                        const roleCount = usageInfo?.roleCount || 0;
                        const isUnused = (permissionUsageStats.unused || []).some(
                          p => p.permission_code === permission.permission_code
                        );

                        return (
                          <div
                            key={permission.id}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-lg transition-colors",
                              "bg-slate-800/50 hover:bg-slate-800",
                              isUnused && "border border-amber-500/20 bg-amber-500/5"
                            )}>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Key className="h-4 w-4 text-slate-400" />
                              <span className="font-medium text-white">
                                {permission.permission_code}
                              </span>
                              {permission.action &&
                                <Badge
                                  className={cn(
                                    "text-xs",
                                    getActionColor(permission.action)
                                  )}>
                                  {getActionLabel(permission.action)}
                                </Badge>
                              }
                              {permission.is_active === false &&
                                <Badge
                                  variant="destructive"
                                  className="text-xs">
                                  已禁用
                                </Badge>
                              }
                              {isUnused &&
                                <Badge
                                  variant="outline"
                                  className="text-xs border-amber-500/30 text-amber-400">
                                  未使用
                                </Badge>
                              }
                            </div>
                            <p className="text-sm text-slate-400 ml-6">
                              {generatePermissionLabel(permission)}
                            </p>
                            {permission.description &&
                              <p className="text-xs text-slate-500 ml-6 mt-1">
                                {permission.description}
                              </p>
                            }
                            {permission.resource &&
                              <div className="flex items-center gap-2 mt-2 ml-6">
                                <FileText className="h-3 w-3 text-slate-500" />
                                <span className="text-xs text-slate-500">
                                  资源: {permission.resource}
                                </span>
                              </div>
                            }
                          </div>
                          <div className="flex items-center gap-3 ml-4">
                            {/* 使用次数 */}
                            <div className="text-right">
                              <div className={cn(
                                "text-lg font-bold",
                                roleCount > 0 ? "text-blue-400" : "text-slate-500"
                              )}>
                                {roleCount}
                              </div>
                              <div className="text-xs text-slate-500">
                                个角色
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewDetail(permission)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              详情
                            </Button>
                          </div>
                        </div>
                        );
                      })}
                    </div>
            </CardContent>
            }
              </Card>
        </motion.div>
        )}
      </div>
      }

      {/* 权限详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              权限详情
            </DialogTitle>
          </DialogHeader>
          {selectedPermission &&
          <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-400">
                  权限编码
                </label>
                <p className="text-white mt-1 font-mono">
                  {selectedPermission.permission_code}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-400">
                  权限名称
                </label>
                <p className="text-white mt-1">
                  {generatePermissionLabel(selectedPermission)}
                </p>
              </div>
              {selectedPermission.description &&
            <div>
                  <label className="text-sm font-medium text-slate-400">
                    描述
                  </label>
                  <p className="text-white mt-1">
                    {selectedPermission.description}
                  </p>
            </div>
            }
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-400">
                    所属模块
                  </label>
                  <p className="text-white mt-1">
                    {getModuleLabel(selectedPermission.module)}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">
                    资源类型
                  </label>
                  <p className="text-white mt-1">
                    {selectedPermission.resource || "未指定"}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">
                    操作类型
                  </label>
                  <p className="text-white mt-1">
                    {selectedPermission.action ?
                  <Badge
                    className={getActionColor(selectedPermission.action)}>

                        {getActionLabel(selectedPermission.action)}
                  </Badge> :

                  "未指定"
                  }
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-400">
                    状态
                  </label>
                  <p className="text-white mt-1">
                    {selectedPermission.is_active !== false ?
                  <Badge className="bg-green-500/10 text-green-400">
                        启用
                  </Badge> :

                  <Badge variant="destructive">禁用</Badge>
                  }
                  </p>
                </div>
              </div>
              {selectedPermission.created_at &&
            <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-400">
                      创建时间
                    </label>
                    <p className="text-white mt-1">
                      {new Date(selectedPermission.created_at).toLocaleString(
                    "zh-CN"
                  )}
                    </p>
                  </div>
                  {selectedPermission.updated_at &&
              <div>
                      <label className="text-sm font-medium text-slate-400">
                        更新时间
                      </label>
                      <p className="text-white mt-1">
                        {new Date(selectedPermission.updated_at).toLocaleString(
                    "zh-CN"
                  )}
                      </p>
              </div>
              }
            </div>
            }
              <div className="pt-4 border-t border-slate-700">
                <label className="text-sm font-medium text-slate-400 mb-2 block">
                  拥有此权限的角色
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {permissionRoles.length > 0 ?
                (permissionRoles || []).map((role) =>
                <div
                  key={role.id}
                  className="flex items-center gap-2 p-2 rounded bg-slate-800/50">

                        <Users className="h-4 w-4 text-slate-400" />
                        <span className="text-sm text-white">
                          {role.role_name}
                        </span>
                        <Badge variant="secondary" className="ml-auto text-xs">
                          {role.role_code}
                        </Badge>
                </div>
                ) :

                <p className="text-sm text-slate-500 text-center py-4">
                      暂无角色拥有此权限
                </p>
                }
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  提示：权限通常通过角色管理页面进行分配
                </p>
              </div>
          </div>
          }
        </DialogContent>
      </Dialog>
    </div>);

}