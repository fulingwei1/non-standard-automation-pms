/**
 * Admin Dashboard - Main dashboard for system administrators
 * Features: System overview, User management, Role & permission management, System configuration, System health monitoring
 * Core Functions: System configuration, User management, Permission assignment, System maintenance
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
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
  Search,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Input,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { ApiIntegrationError } from '../components/ui'

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
  auditLogsThisWeek: 0,
}

// 演示账号的演示数据
const demoStats = {
  totalUsers: 183,
  activeUsers: 174,
  inactiveUsers: 9,
  newUsersThisMonth: 5,
  usersWithRoles: 8,
  usersWithoutRoles: 175,
  totalRoles: 34,
  systemRoles: 5,
  customRoles: 29,
  activeRoles: 34,
  inactiveRoles: 0,
  totalPermissions: 67,
  assignedPermissions: 249,
  unassignedPermissions: 0,
  systemUptime: 99.9,
  databaseSize: 2.5,
  storageUsed: 45,
  apiResponseTime: 120,
  errorRate: 0.1,
  loginCountToday: 42,
  loginCountThisWeek: 287,
  lastBackup: '2025-01-09 02:00:00',
  auditLogsToday: 156,
  auditLogsThisWeek: 1024,
}

// Mock data - 已移除，使用真实API

const DEFAULT_PERMISSION_MODULES = [
  { code: 'users', name: '用户管理', description: '创建、停用和分配用户角色' },
  { code: 'roles', name: '角色配置', description: '维护角色及权限组合' },
  { code: 'permissions', name: '权限策略', description: '配置模块、菜单与 API 授权' },
  { code: 'system', name: '系统监控', description: '查看系统运行状态与告警' },
]

const cloneRolePermissions = (roles) => {
  if (!Array.isArray(roles)) return []
  return roles.map((role) => ({
    ...role,
    permissions: Array.isArray(role.permissions) ? [...role.permissions] : [],
  }))
}


const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg, onClick }) => {
  return (
    <motion.div
      variants={fadeIn}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg',
        onClick && 'cursor-pointer'
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}</span>
                </>
              ) : null}
            </div>
          )}
        </div>
        {Icon && (
          <div className={cn('p-3 rounded-lg', bg)}>
            <Icon className={cn('w-5 h-5', color)} />
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(defaultStats)
  const [rolePermissions, setRolePermissions] = useState([])
  const [savedRolePermissions, setSavedRolePermissions] = useState([])
  const [selectedRoleCode, setSelectedRoleCode] = useState('')
  const [roleSearchKeyword, setRoleSearchKeyword] = useState('')
  const [savingPermissions, setSavingPermissions] = useState(false)
  const [permissionNotice, setPermissionNotice] = useState(null)
  const permissionModules = DEFAULT_PERMISSION_MODULES

  useEffect(() => {
    // 从后端获取真实统计数据
    const fetchStats = async () => {
      // 检查是否是演示账号
      const token = localStorage.getItem('token')
      const isDemoAccount = token && token.startsWith('demo_token_')
      
      if (isDemoAccount) {
        // 演示账号不调用真实API，使用演示数据
        console.log('[管理员工作台] 演示账号，使用演示数据')
        setStats(demoStats)
        setError(null)
        setLoading(false)
        return
      }
      
      try {
        setLoading(true)
        setError(null) // 清除之前的错误
        const response = await api.get('/admin/stats')
        if (response.data?.data) {
          setStats(response.data.data)
          setError(null) // 成功时清除错误
        } else {
          console.warn('API 返回数据格式异常:', response.data)
          setError(new Error('API 返回数据格式异常'))
        }
      } catch (err) {
        console.error('获取统计数据失败:', err)
        setError(err)
        setStats(defaultStats)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  useEffect(() => {
    if (!permissionNotice) return
    const timer = setTimeout(() => setPermissionNotice(null), 3000)
    return () => clearTimeout(timer)
  }, [permissionNotice])

  const handleStatCardClick = (type) => {
    switch (type) {
      case 'users':
        navigate('/user-management')
        break
      case 'roles':
        navigate('/role-management')
        break
      case 'permissions':
        navigate('/permission-management')
        break
      case 'system':
        navigate('/settings')
        break
      default:
        break
    }
  }

  const selectedRole = rolePermissions.find((role) => role.roleCode === selectedRoleCode) || null

  const isRolePermissionsChanged = (role) => {
    if (!role) return false
    const savedRole = savedRolePermissions.find((item) => item.roleCode === role.roleCode)
    if (!savedRole) return true
    if (savedRole.permissions.length !== role.permissions.length) return true
    const savedSet = new Set(savedRole.permissions)
    return role.permissions.some((perm) => !savedSet.has(perm))
  }

  const keyword = roleSearchKeyword.trim().toLowerCase()
  const filteredRoles = keyword
    ? rolePermissions.filter((role) => {
        const roleName = (role.role || '').toLowerCase()
        const roleCode = (role.roleCode || '').toLowerCase()
        const desc = (role.description || '').toLowerCase()
        return roleName.includes(keyword) || roleCode.includes(keyword) || desc.includes(keyword)
      })
    : rolePermissions

  const hasPendingChanges = rolePermissions.some((role) => isRolePermissionsChanged(role))
  const selectedRoleChanged = isRolePermissionsChanged(selectedRole)

  const handleRoleSelect = (roleCode) => {
    setSelectedRoleCode(roleCode)
  }

  const handleTogglePermission = (moduleCode) => {
    if (!selectedRoleCode) return
    setRolePermissions((prev) =>
      prev.map((role) => {
        if (role.roleCode !== selectedRoleCode) return role
        const hasPermission = role.permissions.includes(moduleCode)
        return {
          ...role,
          permissions: hasPermission
            ? role.permissions.filter((code) => code !== moduleCode)
            : [...role.permissions, moduleCode],
        }
      })
    )
  }

  const handleResetPermissions = () => {
    setRolePermissions(cloneRolePermissions(savedRolePermissions))
    setPermissionNotice({
      type: 'info',
      message: '已恢复到最近保存的配置（模拟数据）',
    })
  }

  const handleSavePermissions = () => {
    if (!hasPendingChanges) {
      setPermissionNotice({
        type: 'warning',
        message: '当前没有新的变更需要保存',
      })
      return
    }
    setSavingPermissions(true)
    setTimeout(() => {
      setSavingPermissions(false)
      setSavedRolePermissions(cloneRolePermissions(rolePermissions))
      setPermissionNotice({
        type: 'success',
        message: '权限配置已保存（仅 UI 演示）',
      })
    }, 600)
  }

  // Show error state
  if (error && loading === false) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader
          title="管理员工作台"
          subtitle="系统配置、用户管理、权限分配、系统维护"
        />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/admin/stats"
          onRetry={() => {
            const fetchStats = async () => {
              try {
                setLoading(true)
                setError(null)
                const response = await api.get('/admin/stats')
                if (response.data?.data) {
                  setStats(response.data.data)
                }
              } catch (err) {
                setError(err)
                setStats(defaultStats)
              } finally {
                setLoading(false)
              }
            }
            fetchStats()
          }}
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-slate-400">加载中...</div>
      </div>
    )
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      <PageHeader
        title="管理员工作台"
        subtitle="系统配置、用户管理、权限分配、系统维护"
      />

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
          onClick={() => handleStatCardClick('users')}
        />
        <StatCard
          title="角色总数"
          value={stats.totalRoles}
          subtitle={`系统角色: ${stats.systemRoles} | 自定义: ${stats.customRoles}`}
          trend={stats.activeRoles}
          icon={Shield}
          color="text-purple-400"
          bg="bg-purple-500/10"
          onClick={() => handleStatCardClick('roles')}
        />
        <StatCard
          title="权限总数"
          value={stats.totalPermissions}
          subtitle={`已分配: ${stats.assignedPermissions} | 未分配: ${stats.unassignedPermissions}`}
          icon={Key}
          color="text-amber-400"
          bg="bg-amber-500/10"
          onClick={() => handleStatCardClick('permissions')}
        />
        <StatCard
          title="系统可用性"
          value={`${stats.systemUptime}%`}
          subtitle={`API响应: ${stats.apiResponseTime}ms | 错误率: ${stats.errorRate}%`}
          icon={Activity}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
          onClick={() => handleStatCardClick('system')}
        />
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

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="bg-slate-800/50 border-slate-700/50">
          <TabsTrigger value="overview" className="data-[state=active]:bg-slate-700">
            系统概览
          </TabsTrigger>
          <TabsTrigger value="users" className="data-[state=active]:bg-slate-700">
            用户管理
          </TabsTrigger>
          <TabsTrigger value="roles" className="data-[state=active]:bg-slate-700">
            角色权限
          </TabsTrigger>
          <TabsTrigger value="system" className="data-[state=active]:bg-slate-700">
            系统监控
          </TabsTrigger>
          <TabsTrigger value="activity" className="data-[state=active]:bg-slate-700">
            活动日志
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
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
                    <span className="text-sm font-medium text-emerald-400">{stats.systemUptime}%</span>
                  </div>
                  <Progress value={stats.systemUptime} className="h-2" />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">存储使用率</span>
                    <span className="text-sm font-medium text-amber-400">{stats.storageUsed}%</span>
                  </div>
                  <Progress value={stats.storageUsed} className="h-2" />
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">数据库大小</span>
                    <span className="text-sm font-medium text-blue-400">{stats.databaseSize} GB</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">API 平均响应时间</span>
                    <span className="text-sm font-medium text-cyan-400">{stats.apiResponseTime} ms</span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">错误率</span>
                    <span className="text-sm font-medium text-emerald-400">{stats.errorRate}%</span>
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
                  <p className="text-2xl font-bold text-blue-400">{stats.loginCountToday}</p>
                  <p className="text-xs text-slate-400 mt-1">本周总计: {stats.loginCountThisWeek}</p>
                </CardContent>
              </Card>
              <Card className="border-slate-700/50 bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-white text-sm">今日审计日志</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-purple-400">{stats.auditLogsToday}</p>
                  <p className="text-xs text-slate-400 mt-1">本周总计: {stats.auditLogsThisWeek}</p>
                </CardContent>
              </Card>
              <Card className="border-slate-700/50 bg-slate-800/50">
                <CardHeader>
                  <CardTitle className="text-white text-sm">最后备份</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm font-medium text-emerald-400">{stats.lastBackup}</p>
                  <p className="text-xs text-slate-400 mt-1">自动备份已启用</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card className="border-slate-700/50 bg-slate-800/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">用户管理</CardTitle>
                <Button onClick={() => navigate('/user-management')}>
                  <UserPlus className="w-4 h-4 mr-2" />
                  管理用户
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">总用户数</span>
                    <Users className="w-5 h-5 text-blue-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{stats.totalUsers}</p>
                  <p className="text-xs text-slate-500 mt-1">本月新增: {stats.newUsersThisMonth}</p>
                </div>
                <div className="p-4 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">已分配角色</span>
                    <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{stats.usersWithRoles}</p>
                  <p className="text-xs text-slate-500 mt-1">未分配: {stats.usersWithoutRoles} 人</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Roles Tab */}
        <TabsContent value="roles" className="space-y-4">
          <Card className="border-slate-700/50 bg-slate-800/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">角色权限管理</CardTitle>
                <Button onClick={() => navigate('/role-management')}>
                  <Shield className="w-4 h-4 mr-2" />
                  管理角色
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">总角色数</span>
                    <Shield className="w-5 h-5 text-purple-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{stats.totalRoles}</p>
                  <p className="text-xs text-slate-500 mt-1">系统角色: {stats.systemRoles}</p>
                </div>
                <div className="p-4 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">自定义角色</span>
                    <UserCog className="w-5 h-5 text-amber-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{stats.customRoles}</p>
                  <p className="text-xs text-slate-500 mt-1">活跃角色: {stats.activeRoles}</p>
                </div>
                <div className="p-4 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">权限总数</span>
                    <Key className="w-5 h-5 text-cyan-400" />
                  </div>
                  <p className="text-2xl font-bold text-white">{stats.totalPermissions}</p>
                  <p className="text-xs text-slate-500 mt-1">已分配: {stats.assignedPermissions}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-700/50 bg-slate-800/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Settings className="w-5 h-5 text-emerald-400" />
                菜单模块权限配置
              </CardTitle>
              <p className="text-sm text-slate-400">
                管理员可通过勾选功能开关控制不同角色可见的菜单模块，本界面为 UI 演示，尚未与后台联动。
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="rounded-lg border border-slate-700/70 bg-slate-900/50 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-white">角色列表</span>
                    <Badge variant="outline" className="text-xs text-slate-300 border-slate-600">
                      {rolePermissions.length} 个
                    </Badge>
                  </div>
                  <div className="relative">
                    <Input
                      value={roleSearchKeyword}
                      onChange={(event) => setRoleSearchKeyword(event.target.value)}
                      placeholder="搜索角色 / 编码"
                      className="bg-slate-900/70 border-slate-700/70 text-slate-100 pl-9 placeholder:text-slate-500"
                    />
                    <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  </div>
                  <div className="mt-4 space-y-2 max-h-80 overflow-y-auto pr-1">
                    {filteredRoles.length > 0 ? (
                      filteredRoles.map((role) => {
                        const active = role.roleCode === selectedRoleCode
                        const modified = isRolePermissionsChanged(role)
                        return (
                          <button
                            key={role.roleCode}
                            onClick={() => handleRoleSelect(role.roleCode)}
                            className={cn(
                              'w-full text-left p-3 rounded-lg border transition-all',
                              active
                                ? 'border-emerald-500/60 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                                : 'border-slate-700/60 bg-slate-900/60 hover:border-slate-600'
                            )}
                          >
                            <div className="flex items-center justify-between">
                              <p className="text-sm font-medium text-white">{role.role}</p>
                              {modified && (
                                <Badge variant="outline" className="text-[10px] text-amber-300 border-amber-400/60">
                                  已修改
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-slate-400 mt-1">{role.description}</p>
                            <div className="mt-2 flex items-center gap-2 text-[10px] text-slate-500">
                              <span>编码: {role.roleCode}</span>
                              <span>•</span>
                              <span>模块 {role.permissions.length}</span>
                            </div>
                          </button>
                        )
                      })
                    ) : (
                      <div className="text-xs text-slate-500 text-center py-8 border border-dashed border-slate-700/60 rounded-lg">
                        未找到匹配的角色
                      </div>
                    )}
                  </div>
                </div>
                <div className="lg:col-span-2 rounded-lg border border-slate-700/70 bg-slate-900/50 p-4">
                  {selectedRole ? (
                    <>
                      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                        <div>
                          <p className="text-base font-semibold text-white flex items-center gap-2">
                            {selectedRole.role}
                            {selectedRoleChanged && (
                              <Badge variant="outline" className="text-[10px] text-amber-300 border-amber-400/60">
                                有未保存变更
                              </Badge>
                            )}
                          </p>
                          <p className="text-xs text-slate-400">{selectedRole.description}</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                          <Badge variant="outline" className="text-[10px] text-slate-300 border-slate-600">
                            角色编码: {selectedRole.roleCode}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="text-[10px] text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
                          >
                            可见模块: {selectedRole.permissions.length}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {permissionModules.map((module) => {
                          const active = selectedRole.permissions.includes(module.code)
                          return (
                            <button
                              key={module.code}
                              type="button"
                              onClick={() => handleTogglePermission(module.code)}
                              className={cn(
                                'text-left rounded-lg border p-3 transition-all',
                                active
                                  ? 'border-emerald-500/60 bg-emerald-500/10 shadow-lg shadow-emerald-500/10'
                                  : 'border-slate-700/60 bg-slate-900/60 hover:border-slate-600'
                              )}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div>
                                  <p className="text-sm font-medium text-white">{module.name}</p>
                                  <p className="text-xs text-slate-400 mt-1">{module.description}</p>
                                </div>
                                <Badge
                                  variant={active ? 'default' : 'outline'}
                                  className={cn(
                                    'text-[10px]',
                                    active
                                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                                      : 'text-slate-300 border-slate-600'
                                  )}
                                >
                                  {active ? '已开启' : '关闭'}
                                </Badge>
                              </div>
                            </button>
                          )
                        })}
                      </div>
                      <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        {permissionNotice && (
                          <div
                            className={cn(
                              'text-xs font-medium px-3 py-2 rounded-md border',
                              permissionNotice.type === 'success' &&
                                'text-emerald-300 border-emerald-500/40 bg-emerald-500/5',
                              permissionNotice.type === 'info' &&
                                'text-blue-300 border-blue-500/40 bg-blue-500/5',
                              permissionNotice.type === 'warning' &&
                                'text-amber-300 border-amber-500/40 bg-amber-500/5'
                            )}
                          >
                            {permissionNotice.message}
                          </div>
                        )}
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            onClick={handleResetPermissions}
                            disabled={!hasPendingChanges || savingPermissions}
                            className="text-sm"
                          >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            重置
                          </Button>
                          <Button
                            onClick={handleSavePermissions}
                            disabled={!hasPendingChanges || savingPermissions}
                            className="text-sm"
                          >
                            <ShieldCheck className="w-4 h-4 mr-2" />
                            {savingPermissions ? '保存中...' : '保存配置'}
                          </Button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <div className="h-full flex items-center justify-center text-sm text-slate-400">
                      暂无可配置的角色
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Monitoring Tab */}
        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-slate-700/50 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white">系统资源</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <HardDrive className="w-5 h-5 text-blue-400" />
                    <div>
                      <p className="text-sm font-medium text-white">存储空间</p>
                      <p className="text-xs text-slate-400">已使用 {stats.storageUsed}%</p>
                    </div>
                  </div>
                  <Badge variant={stats.storageUsed > 80 ? 'destructive' : 'default'}>
                    {stats.storageUsed}%
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-purple-400" />
                    <div>
                      <p className="text-sm font-medium text-white">数据库</p>
                      <p className="text-xs text-slate-400">{stats.databaseSize} GB</p>
                    </div>
                  </div>
                  <Badge variant="default">正常</Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <Cpu className="w-5 h-5 text-amber-400" />
                    <div>
                      <p className="text-sm font-medium text-white">API 响应时间</p>
                      <p className="text-xs text-slate-400">平均 {stats.apiResponseTime} ms</p>
                    </div>
                  </div>
                  <Badge variant={stats.apiResponseTime > 200 ? 'destructive' : 'default'}>
                    {stats.apiResponseTime}ms
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-700/50 bg-slate-800/50">
              <CardHeader>
                <CardTitle className="text-white">系统状态</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-white">系统可用性</p>
                      <p className="text-xs text-slate-400">{stats.systemUptime}%</p>
                    </div>
                  </div>
                  <Badge variant="default" className="bg-emerald-500/20 text-emerald-400">
                    正常
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                    <div>
                      <p className="text-sm font-medium text-white">错误率</p>
                      <p className="text-xs text-slate-400">{stats.errorRate}%</p>
                    </div>
                  </div>
                  <Badge variant={stats.errorRate > 1 ? 'destructive' : 'default'}>
                    {stats.errorRate}%
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg border border-slate-700/50 bg-slate-900/50">
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-cyan-400" />
                    <div>
                      <p className="text-sm font-medium text-white">服务器状态</p>
                      <p className="text-xs text-slate-400">运行正常</p>
                    </div>
                  </div>
                  <Badge variant="default" className="bg-emerald-500/20 text-emerald-400">
                    在线
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Activity Log Tab */}
        <TabsContent value="activity" className="space-y-4">
          <Card className="border-slate-700/50 bg-slate-800/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">最近活动</CardTitle>
                <Button variant="outline" size="sm" disabled title="审计日志功能开发中">
                  <Eye className="w-4 h-4 mr-2" />
                  查看全部
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* 最近活动 - 需要从API获取数据 */}
                {/* {mockRecentActivities.map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-slate-700/50 bg-slate-900/50"
                  >
                    <div className="p-2 rounded-lg bg-blue-500/10">
                      {activity.type === 'user_created' && (
                        <UserPlus className="w-4 h-4 text-blue-400" />
                      )}
                      {activity.type === 'role_assigned' && (
                        <Shield className="w-4 h-4 text-purple-400" />
                      )}
                      {activity.type === 'permission_updated' && (
                        <Key className="w-4 h-4 text-amber-400" />
                      )}
                      {activity.type === 'user_deactivated' && (
                        <Lock className="w-4 h-4 text-red-400" />
                      )}
                      {activity.type === 'config_updated' && (
                        <Settings className="w-4 h-4 text-cyan-400" />
                      )}
                      {activity.type === 'backup_completed' && (
                        <Archive className="w-4 h-4 text-emerald-400" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-white">{activity.action}</p>
                        <Badge variant="outline" className="text-xs">
                          {activity.target}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <span>操作人: {activity.operator}</span>
                        <span>•</span>
                        <span>{activity.timestamp}</span>
                      </div>
                    </div>
                    {activity.status === 'success' && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    )}
                  </div>
                ))} */}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
