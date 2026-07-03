import { useState, useEffect } from "react";
import { roleApi } from "../../services/api";
import { ROLES_PAGE_SIZE, TOP_USED_LIMIT } from "./constants";

export function usePermissionData() {
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
      const token = localStorage.getItem("token");
      console.log("[权限管理] 开始加载权限列表...");
      console.log(
        "[权限管理] Token检查:",
        token ?
        token.startsWith("demo_token_") ?
        "演示账号token" :
        `真实token (${token.substring(0, 30)}...)` :
        "未找到token"
      );

      if (!token) {
        console.error("[权限管理] 未找到token，请重新登录");
        alert("未找到认证token，请重新登录");
        window.location.href = "/";
        return;
      }

      if (token.startsWith("demo_token_")) {
        console.warn("[权限管理] 这是演示账号token，不会发送到后端");
        setPermissions([]);
        setLoading(false);
        return;
      }

      console.log("[权限管理] Token存在，发送请求...");
      let response;
      if (filterModule !== "all") {
        response = await roleApi.permissions({ module: filterModule });
      } else {
        response = await roleApi.permissions();
      }
      console.log(
        "[权限管理] 成功获取权限列表:",
        response.formatted?.length || response.data?.data?.length || 0,
        "条"
      );
      const permData = response.formatted || response.data?.data || response.data;
      setPermissions(Array.isArray(permData) ? permData : []);
    } catch (error) {
      const errorDetail = error.response?.data?.detail || error.message;
      const statusCode = error.response?.status;
      const log = statusCode === 403 ? console.warn : console.error;
      log("[权限管理] 加载权限列表失败:", error);
      log("[权限管理] 错误详情:", {
        status: statusCode,
        detail: errorDetail,
        message: error.message,
        response: error.response?.data
      });

      if (statusCode === 403) {
        console.warn("[权限管理] 当前账号无权限访问权限列表");
        setPermissions([]);
      } else if (
        statusCode === 401 ||
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
      const response = await roleApi.list({ page_size: ROLES_PAGE_SIZE });
      const listData = response.formatted || response.data;
      const roleItems = listData?.items || listData;
      setRoles(Array.isArray(roleItems) ? roleItems : []);
    } catch (error) {
      if (error?.response?.status === 403) {
        console.warn("加载角色列表失败:", error);
      } else {
        console.error("加载角色列表失败:", error);
      }
      setRoles([]);
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

    const usageMap = {};

    for (const permission of permissions) {
      usageMap[permission.permission_code] = {
        permission,
        roleCount: 0,
        roles: []
      };
    }

    for (const role of roles) {
      const rolePermissions = role.permissions || [];

      for (const permission of permissions) {
        if (rolePermissions.includes(permission.permission_name) ||
          rolePermissions.includes(permission.permission_code)) {
          if (usageMap[permission.permission_code]) {
            usageMap[permission.permission_code].roleCount++;
            usageMap[permission.permission_code].roles.push(role);
          }
        }
      }
    }

    const mostUsed = Object.values(usageMap)
      .filter(item => item.roleCount > 0)
      .sort((a, b) => b.roleCount - a.roleCount)
      .slice(0, TOP_USED_LIMIT)
      .map(item => ({
        ...item.permission,
        roleCount: item.roleCount,
        roleNames: (item.roles || []).map(r => r.role_name).join(', ')
      }));

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

  return {
    permissions,
    loading,
    searchKeyword,
    setSearchKeyword,
    filterModule,
    setFilterModule,
    expandedModules,
    selectedPermission,
    showDetailDialog,
    setShowDetailDialog,
    permissionRoles,
    permissionUsageStats,
    isDemoAccount,
    modules,
    filteredPermissions,
    stats,
    toggleModule,
    handleViewDetail,
  };
}
