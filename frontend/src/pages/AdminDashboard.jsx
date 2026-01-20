/**
 * Admin Dashboard - Main dashboard for system administrators
 * Features: System overview, User management, Role & permission management, System configuration, System health monitoring
 * Core Functions: System configuration, User management, Permission assignment, System maintenance
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import api from "../services/api";
import {
  Users,
  Shield,
  Cog,
  Database,
  Server,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  UserPlus,
  UserCog,
  Key,
  Settings,
  BarChart3,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  FileText,
  Lock,
  Unlock,
  HardDrive,
  Cpu,
  Network,
  Bell,
  Eye,
  Edit,
  Trash2,
  RefreshCw,
  Download,
  Upload,
  Archive,
  ShieldCheck,
  AlertCircle,
  XCircle,
  Info,
  Search } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { ApiIntegrationError } from "../components/ui";

// 默认统计数据（加载前显示）
const defaultStats = {
  totalUsers: 0,
  activeUsers: 0,
  inactiveUsers: 0,
  newUsersThisMonth: 0,
  usersWithRoles: 0,
  usersWithoutRoles: 0,
  totalRoles: 0,
  systemRoles: 0,
  customRoles: 0,
  activeRoles: 0,
  inactiveRoles: 0,
  totalPermissions: 0,
  assignedPermissions: 0,
  unassignedPermissions: 0,
  systemUptime: 99.9,
  databaseSize: 0,
  storageUsed: 0,
  apiResponseTime: 0,
  errorRate: 0,
  loginCountToday: 0,
  loginCountThisWeek: 0,
  lastBackup: null,
  auditLogsToday: 0,
  auditLogsThisWeek: 0
};

// Mock data - 已移除，使用真实API

// Mock data - 已移除，使用真实API

const DEFAULT_PERMISSION_MODULES = [
{ code: "users", name: "用户管理", description: "创建、停用和分配用户角色" },
{ code: "roles", name: "角色配置", description: "维护角色及权限组合" },
{
  code: "permissions",
  name: "权限策略",
  description: "配置模块、菜单与 API 授权"
},
{ code: "system", name: "系统监控", description: "查看系统运行状态与告警" }];


const cloneRolePermissions = (roles) => {
  if (!Array.isArray(roles)) {return [];}
  return roles.map((role) => ({
    ...role,
    permissions: Array.isArray(role.permissions) ? [...role.permissions] : []
  }));
};

const StatCard = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  color,
  bg,
  onClick
}) => {
  return (
    <motion.div
      variants={fadeIn}
      onClick={onClick}
      className={cn(
        "relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg",
        onClick && "cursor-pointer"
      )}>

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn("text-2xl font-bold mb-1", color)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {trend !== undefined &&
          <div className="flex items-center gap-1 mt-2">
              {trend > 0 ?
            <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}</span>
            </> :
            trend < 0 ?
            <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}</span>
            </> :
            null}
          </div>
          }
        </div>
        {Icon &&
        <div className={cn("p-3 rounded-lg", bg)}>
            <Icon className={cn("w-5 h-5", color)} />
        </div>
        }
      </div>
    </motion.div>);

};

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(defaultStats);
  const [rolePermissions, setRolePermissions] = useState([]);
  const [savedRolePermissions, setSavedRolePermissions] = useState([]);
  const [selectedRoleCode, setSelectedRoleCode] = useState("");
  const [roleSearchKeyword, _setRoleSearchKeyword] = useState("");
  const [_savingPermissions, setSavingPermissions] = useState(false);
  const [permissionNotice, setPermissionNotice] = useState(null);
  const _permissionModules = DEFAULT_PERMISSION_MODULES;

  useEffect(() => {
    // 从后端获取真实统计数据
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null); // 清除之前的错误
        const response = await api.get("/admin/stats");
        if (response.data?.data) {
          setStats(response.data.data);
          setError(null); // 成功时清除错误
        } else {
          console.warn("API 返回数据格式异常:", response.data);
          setError(new Error("API 返回数据格式异常"));
        }
      } catch (err) {
        console.error("获取统计数据失败:", err);
        setError(err);
        setStats(defaultStats);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    if (!permissionNotice) {return;}
    const timer = setTimeout(() => setPermissionNotice(null), 3000);
    return () => clearTimeout(timer);
  }, [permissionNotice]);

  const handleStatCardClick = (type) => {
    switch (type) {
      case "users":
        navigate("/user-management");
        break;
      case "roles":
        navigate("/role-management");
        break;
      case "permissions":
        navigate("/permission-management");
        break;
      case "system":
        navigate("/settings");
        break;
      default:
        break;
    }
  };

  const selectedRole =
  rolePermissions.find((role) => role.roleCode === selectedRoleCode) || null;

  const isRolePermissionsChanged = (role) => {
    if (!role) {return false;}
    const savedRole = savedRolePermissions.find(
      (item) => item.roleCode === role.roleCode
    );
    if (!savedRole) {return true;}
    if (savedRole.permissions.length !== role.permissions.length) {return true;}
    const savedSet = new Set(savedRole.permissions);
    return role.permissions.some((perm) => !savedSet.has(perm));
  };

  const keyword = roleSearchKeyword.trim().toLowerCase();
  const _filteredRoles = keyword ?
  rolePermissions.filter((role) => {
    const roleName = (role.role || "").toLowerCase();
    const roleCode = (role.roleCode || "").toLowerCase();
    const desc = (role.description || "").toLowerCase();
    return (
      roleName.includes(keyword) ||
      roleCode.includes(keyword) ||
      desc.includes(keyword));

  }) :
  rolePermissions;

  const hasPendingChanges = rolePermissions.some((role) =>
  isRolePermissionsChanged(role)
  );
  const _selectedRoleChanged = isRolePermissionsChanged(selectedRole);

  const _handleRoleSelect = (roleCode) => {
    setSelectedRoleCode(roleCode);
  };

  const _handleTogglePermission = (moduleCode) => {
    if (!selectedRoleCode) {return;}
    setRolePermissions((prev) =>
    prev.map((role) => {
      if (role.roleCode !== selectedRoleCode) {return role;}
      const hasPermission = role.permissions.includes(moduleCode);
      return {
        ...role,
        permissions: hasPermission ?
        role.permissions.filter((code) => code !== moduleCode) :
        [...role.permissions, moduleCode]
      };
    })
    );
  };

  const _handleResetPermissions = () => {
    setRolePermissions(cloneRolePermissions(savedRolePermissions));
    setPermissionNotice({
      type: "info",
      message: "已恢复到最近保存的配置（模拟数据）"
    });
  };

  const _handleSavePermissions = () => {
    if (!hasPendingChanges) {
      setPermissionNotice({
        type: "warning",
        message: "当前没有新的变更需要保存"
      });
      return;
    }
    setSavingPermissions(true);
    setTimeout(() => {
      setSavingPermissions(false);
      setSavedRolePermissions(cloneRolePermissions(rolePermissions));
      setPermissionNotice({
        type: "success",
        message: "权限配置已保存（仅 UI 演示）"
      });
    }, 600);
  };

  // Show error state
  if (error && loading === false) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader
          title="管理员工作台"
          subtitle="系统配置、用户管理、权限分配、系统维护" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/admin/stats"
          onRetry={() => {
            const fetchStats = async () => {
              try {
                setLoading(true);
                setError(null);
                const response = await api.get("/admin/stats");
                if (response.data?.data) {
                  setStats(response.data.data);
                }
              } catch (err) {
                setError(err);
                setStats(defaultStats);
              } finally {
                setLoading(false);
              }
            };
            fetchStats();
          }} />

      </div>);

  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-slate-400">加载中...</div>
      </div>);

  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6">

      <PageHeader
        title="管理员工作台"
        subtitle="系统配置、用户管理、权限分配、系统维护" />


      {/* System Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="总用户数"
          value={stats.totalUsers}
          subtitle={`活跃: ${stats.activeUsers} | 未激活: ${stats.inactiveUsers}`}
          trend={stats.newUsersThisMonth}
          icon={Users}
          color="text-blue-400"
          bg="bg-blue-500/10"
          onClick={() => handleStatCardClick("users")} />

        <StatCard
          title="角色总数"
          value={stats.totalRoles}
          subtitle={`系统角色: ${stats.systemRoles} | 自定义: ${stats.customRoles}`}
          trend={stats.activeRoles}
          icon={Shield}
          color="text-purple-400"
          bg="bg-purple-500/10"
          onClick={() => handleStatCardClick("roles")} />

        <StatCard
          title="权限总数"
          value={stats.totalPermissions}
          subtitle={`已分配: ${stats.assignedPermissions} | 未分配: ${stats.unassignedPermissions}`}
          icon={Key}
          color="text-amber-400"
          bg="bg-amber-500/10"
          onClick={() => handleStatCardClick("permissions")} />

        <StatCard
          title="系统可用性"
          value={`${stats.systemUptime}%`}
          subtitle={`API响应: ${stats.apiResponseTime}ms | 错误率: ${stats.errorRate}%`}
          icon={Activity}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
          onClick={() => handleStatCardClick("system")} />

      </div>

      {/* Quick Actions */}
      <motion.div variants={fadeIn}>
        <Card className="border-slate-700/50 bg-slate-800/50">
          <CardHeader>
            <CardTitle className="text-white">快捷操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {/* 快捷操作 - 需要从API获取数据 */}
              {}
              <div className="text-center py-8 text-slate-500">
                <p>快捷操作数据需要从API获取</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Navigation Tabs */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 bg-slate-800/50 border border-slate-700/50 rounded-lg p-1">
          <button
            onClick={() => {
              // 系统概览保持在当前页面，滚动到顶部
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all bg-slate-700 text-white hover:bg-slate-600">

            系统概览
          </button>
          <button
            onClick={() => navigate("/user-management")}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all text-slate-300 hover:bg-slate-700 hover:text-white">

            用户管理
          </button>
          <button
            onClick={() => navigate("/role-management")}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all text-slate-300 hover:bg-slate-700 hover:text-white">

            角色权限
          </button>
          <button
            onClick={() => navigate("/scheduler-monitoring")}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all text-slate-300 hover:bg-slate-700 hover:text-white">

            系统监控
          </button>
          <button
            onClick={() => navigate("/scheduler-monitoring")}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all text-slate-300 hover:bg-slate-700 hover:text-white">

            活动日志
          </button>
        </div>

        {/* System Overview Content */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* System Health */}
            <Card className="border-slate-700/50 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  系统健康状态
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">系统可用性</span>
                    <span className="text-sm font-medium text-emerald-400">
                      {stats.systemUptime}%
                    </span>
                  </div>
                  <Progress value={stats.systemUptime} className="h-2" />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">存储使用率</span>
                    <span className="text-sm font-medium text-amber-400">
                      {stats.storageUsed}%
                    </span>
                  </div>
                  <Progress value={stats.storageUsed} className="h-2" />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">数据库大小</span>
                    <span className="text-sm font-medium text-blue-400">
                      {stats.databaseSize} GB
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">
                      API 平均响应时间
                    </span>
                    <span className="text-sm font-medium text-cyan-400">
                      {stats.apiResponseTime} ms
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">错误率</span>
                    <span className="text-sm font-medium text-emerald-400">
                      {stats.errorRate}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* System Alerts */}
            <Card className="border-slate-700/50 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  系统提醒
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* 系统提醒 - 需要从API获取数据 */}
                  {}
                </div>
              </CardContent>
            </Card>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="border-slate-700/50 bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-white text-sm">今日登录</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-blue-400">
                    {stats.loginCountToday}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    本周总计: {stats.loginCountThisWeek}
                  </p>
                </CardContent>
              </Card>
              <Card className="border-slate-700/50 bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-white text-sm">
                    今日审计日志
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-purple-400">
                    {stats.auditLogsToday}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    本周总计: {stats.auditLogsThisWeek}
                  </p>
                </CardContent>
              </Card>
              <Card className="border-slate-700/50 bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-white text-sm">最后备份</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-medium text-emerald-400">
                    {stats.lastBackup}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">自动备份已启用</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </motion.div>);

}