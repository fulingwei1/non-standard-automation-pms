/**
 * Admin Dashboard - Main dashboard for system administrators
 * Features: System overview, User management, Role & permission management, System configuration, System health monitoring
 * Core Functions: System configuration, User management, Permission assignment, System maintenance
 */

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
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

// Mock data for admin dashboard
const mockSystemStats = {
  // User statistics
  totalUsers: 186,
  activeUsers: 178,
  inactiveUsers: 8,
  newUsersThisMonth: 12,
  usersWithRoles: 175,
  usersWithoutRoles: 11,
  
  // Role statistics
  totalRoles: 28,
  systemRoles: 8,
  customRoles: 20,
  activeRoles: 26,
  inactiveRoles: 2,
  
  // Permission statistics
  totalPermissions: 156,
  assignedPermissions: 1420,
  unassignedPermissions: 36,
  
  // System health
  systemUptime: 99.8,
  databaseSize: 2.5, // GB
  storageUsed: 68.5, // %
  apiResponseTime: 125, // ms
  errorRate: 0.02, // %
  
  // Activity statistics
  loginCountToday: 145,
  loginCountThisWeek: 892,
  lastBackup: '2025-01-06 02:00',
  auditLogsToday: 234,
  auditLogsThisWeek: 1456,
}

const mockRecentActivities = [
  {
    id: 1,
    type: 'user_created',
    action: '创建用户',
    target: '张工程师',
    operator: '系统管理员',
    timestamp: '2025-01-06 14:30',
    status: 'success',
  },
  {
    id: 2,
    type: 'role_assigned',
    action: '分配角色',
    target: '李项目经理',
    operator: '系统管理员',
    timestamp: '2025-01-06 13:45',
    status: 'success',
  },
  {
    id: 3,
    type: 'permission_updated',
    action: '更新权限',
    target: '项目经理角色',
    operator: '系统管理员',
    timestamp: '2025-01-06 12:20',
    status: 'success',
  },
  {
    id: 4,
    type: 'user_deactivated',
    action: '停用用户',
    target: '王测试',
    operator: '系统管理员',
    timestamp: '2025-01-06 11:15',
    status: 'success',
  },
  {
    id: 5,
    type: 'config_updated',
    action: '更新系统配置',
    target: '邮件服务器设置',
    operator: '系统管理员',
    timestamp: '2025-01-06 10:00',
    status: 'success',
  },
  {
    id: 6,
    type: 'backup_completed',
    action: '系统备份',
    target: '数据库备份',
    operator: '系统',
    timestamp: '2025-01-06 02:00',
    status: 'success',
  },
]

const mockSystemAlerts = [
  {
    id: 1,
    type: 'warning',
    title: '存储空间使用率较高',
    message: '当前存储使用率 68.5%，建议清理历史数据',
    timestamp: '2025-01-06 09:00',
    action: '查看详情',
  },
  {
    id: 2,
    type: 'info',
    title: '11 个用户未分配角色',
    message: '建议为新用户分配适当的角色权限',
    timestamp: '2025-01-06 08:30',
    action: '分配角色',
  },
  {
    id: 3,
    type: 'success',
    title: '系统备份完成',
    message: '数据库备份已于 02:00 完成',
    timestamp: '2025-01-06 02:00',
    action: '查看备份',
  },
]

const permissionModules = [
  {
    code: 'MODULE_PRODUCTION',
    name: '生产管理',
    description: '生产驾驶舱、生产计划、工单、车间任务',
  },
  {
    code: 'MODULE_SHORTAGE',
    name: '缺料管理',
    description: '缺料预警、到货跟踪、物料替代/调拨',
  },
  {
    code: 'MODULE_FINANCE',
    name: '财务管理',
    description: '应收应付、收款计划、发票核销',
  },
  {
    code: 'MODULE_PROCUREMENT',
    name: '采购与物料',
    description: '采购订单、物料管理、齐套分析',
  },
  {
    code: 'MODULE_SALES',
    name: '销售管理',
    description: '线索机会、报价合同、销售驾驶舱',
  },
]

const mockRolePermissions = [
  {
    role: '生产部经理',
    roleCode: 'production_manager',
    description: '负责生产计划及执行的主要角色',
    permissions: ['MODULE_PRODUCTION', 'MODULE_SHORTAGE'],
  },
  {
    role: 'PMC 计划员',
    roleCode: 'pmc',
    description: '负责物料计划与缺料预警跟踪',
    permissions: ['MODULE_SHORTAGE', 'MODULE_PROCUREMENT'],
  },
  {
    role: '采购经理',
    roleCode: 'procurement_manager',
    description: '负责采购订单、供应商与齐套协同',
    permissions: ['MODULE_PROCUREMENT'],
  },
  {
    role: '财务经理',
    roleCode: 'finance_manager',
    description: '负责应收应付、核销及资金监控',
    permissions: ['MODULE_FINANCE', 'MODULE_SALES'],
  },
  {
    role: '总经理',
    roleCode: 'gm',
    description: '公司管理层，默认拥有全部模块',
    permissions: permissionModules.map((m) => m.code),
  },
  {
    role: '销售总监',
    roleCode: 'sales_director',
    description: '负责销售漏斗、合同及回款跟进',
    permissions: ['MODULE_SALES', 'MODULE_FINANCE'],
  },
]

const cloneRolePermissions = (source) =>
  source.map((role) => ({
    ...role,
    permissions: [...role.permissions],
  }))

const mockQuickActions = [
  {
    id: 1,
    title: '创建新用户',
    description: '添加新的系统用户',
    icon: UserPlus,
    path: '/users?action=create',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
  },
  {
    id: 2,
    title: '管理角色',
    description: '配置角色和权限',
    icon: Shield,
    path: '/roles',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
  },
  {
    id: 3,
    title: '系统配置',
    description: '修改系统设置',
    icon: Settings,
    path: '/config',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
  },
  {
    id: 4,
    title: '审计日志',
    description: '查看系统操作记录',
    icon: FileText,
    path: '/audit-logs',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  {
    id: 5,
    title: '数据备份',
    description: '执行系统备份',
    icon: Archive,
    path: '/backup',
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
  },
  {
    id: 6,
    title: '系统监控',
    description: '查看系统运行状态',
    icon: Activity,
    path: '/monitoring',
    color: 'text-red-400',
    bg: 'bg-red-500/10',
  },
]

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
  const [stats] = useState(mockSystemStats)
  const [rolePermissions, setRolePermissions] = useState(() => cloneRolePermissions(mockRolePermissions))
  const [savedRolePermissions, setSavedRolePermissions] = useState(() => cloneRolePermissions(mockRolePermissions))
  const [selectedRoleCode, setSelectedRoleCode] = useState(mockRolePermissions[0]?.roleCode ?? '')
  const [roleSearchKeyword, setRoleSearchKeyword] = useState('')
  const [savingPermissions, setSavingPermissions] = useState(false)
  const [permissionNotice, setPermissionNotice] = useState(null)

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setLoading(false)
    }, 500)
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!permissionNotice) return
    const timer = setTimeout(() => setPermissionNotice(null), 3000)
    return () => clearTimeout(timer)
  }, [permissionNotice])

  const handleQuickAction = (path) => {
    navigate(path)
  }

  const handleStatCardClick = (type) => {
    switch (type) {
      case 'users':
        navigate('/users')
        break
      case 'roles':
        navigate('/roles')
        break
      case 'permissions':
        navigate('/roles')
        break
      case 'system':
        navigate('/config')
        break
      default:
        break
    }
  }

  const selectedRole = rolePermissions.find((role) => role.roleCode === selectedRoleCode)

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
              {mockQuickActions.map((action) => {
                const Icon = action.icon
                return (
                  <motion.button
                    key={action.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleQuickAction(action.path)}
                    className={cn(
                      'flex flex-col items-center justify-center p-4 rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 transition-all hover:border-slate-600/80 hover:shadow-lg',
                      action.bg
                    )}
                  >
                    <div className={cn('p-2 rounded-lg mb-2', action.bg)}>
                      <Icon className={cn('w-6 h-6', action.color)} />
                    </div>
                    <p className="text-sm font-medium text-white mb-1">{action.title}</p>
                    <p className="text-xs text-slate-400 text-center">{action.description}</p>
                  </motion.button>
                )
              })}
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
                  {mockSystemAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-3 p-3 rounded-lg border border-slate-700/50 bg-slate-900/50"
                    >
                      {alert.type === 'warning' && (
                        <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                      )}
                      {alert.type === 'info' && (
                        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                      )}
                      {alert.type === 'success' && (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white mb-1">{alert.title}</p>
                        <p className="text-xs text-slate-400 mb-2">{alert.message}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-500">{alert.timestamp}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-6"
                            onClick={() => {
                              // Handle action
                            }}
                          >
                            {alert.action}
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Activity Statistics */}
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
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          <Card className="border-slate-700/50 bg-slate-800/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">用户管理</CardTitle>
                <Button onClick={() => navigate('/users')}>
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
                <Button onClick={() => navigate('/roles')}>
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
                <Button variant="outline" size="sm" onClick={() => navigate('/audit-logs')}>
                  <Eye className="w-4 h-4 mr-2" />
                  查看全部
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockRecentActivities.map((activity) => (
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
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}


