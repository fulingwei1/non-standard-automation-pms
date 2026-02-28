import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Users,
  UserPlus,
  UserCheck,
  UserX,
  Shield,
  Building2,
  TrendingUp,
  AlertCircle,
  Calendar,
  BarChart3,
  Activity } from
'lucide-react';
import {
  USER_STATUS,
  USER_STATUS_LABELS,
  USER_STATUS_COLORS,
  USER_ROLE_LABELS,
  USER_DEPARTMENT_LABELS,
  getUserStatusStats,
  getRoleDistributionStats,
  getDepartmentDistributionStats,
  getMonthlyNewUsers,
  calculateUserGrowthRate,
  getRoleColor } from
'@/lib/constants/userManagement';

const UserManagementOverview = ({
  users = [],
  roles = [],
  totalUsers: propTotalUsers,
  onQuickAction
}) => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    inactiveUsers: 0,
    suspendedUsers: 0,
    pendingUsers: 0,
    newUsersThisMonth: 0,
    userGrowthRate: 0
  });

  const [roleStats, setRoleStats] = useState({});
  const [departmentStats, setDepartmentStats] = useState({});

  useEffect(() => {
    if (users.length > 0) {
      const statusStats = getUserStatusStats(users);
      const roleStatsData = getRoleDistributionStats(users);
      const departmentStatsData = getDepartmentDistributionStats(users);
      const newUsersCount = getMonthlyNewUsers(users);

      // 使用传入的总用户数，如果没有则使用当前加载的用户数
      const actualTotalUsers = propTotalUsers || users.length;

      // 模拟上个月的用户数量来计算增长率
      const previousMonthUsers = actualTotalUsers - newUsersCount;
      const growthRate = calculateUserGrowthRate(actualTotalUsers, previousMonthUsers);

      setStats({
        totalUsers: actualTotalUsers, // 使用实际总用户数
        activeUsers: statusStats.active,
        inactiveUsers: statusStats.inactive,
        suspendedUsers: statusStats.suspended,
        pendingUsers: statusStats.pending,
        newUsersThisMonth: newUsersCount,
        userGrowthRate: parseFloat(growthRate)
      });

      setRoleStats(roleStatsData);
      setDepartmentStats(departmentStatsData);
    }
  }, [users, propTotalUsers]);

  const getTopRoles = () => {
    return Object.entries(roleStats).
    filter(([_role, count]) => count > 0).
    sort(([, a], [, b]) => b - a).
    slice(0, 3).
    map(([role, count]) => ({
      role,
      label: USER_ROLE_LABELS[role],
      count,
      percentage: stats.totalUsers > 0 ? (count / stats.totalUsers * 100).toFixed(1) : 0
    }));
  };

  const getTopDepartments = () => {
    return Object.entries(departmentStats).
    filter(([_department, count]) => count > 0).
    sort(([, a], [, b]) => b - a).
    slice(0, 3).
    map(([department, count]) => ({
      department,
      label: USER_DEPARTMENT_LABELS[department],
      count,
      percentage: stats.totalUsers > 0 ? (count / stats.totalUsers * 100).toFixed(1) : 0
    }));
  };

  const getInactiveUsers = () => {
    return users.filter((user) =>
    user.status === USER_STATUS.INACTIVE || user.status === USER_STATUS.SUSPENDED
    );
  };

  const getPendingUsers = () => {
    return users.filter((user) => user.status === USER_STATUS.PENDING);
  };

  const topRoles = getTopRoles();
  const topDepartments = getTopDepartments();
  const _inactiveUsers = getInactiveUsers();
  const _pendingUsers = getPendingUsers();

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总用户数</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalUsers}</div>
            <p className="text-xs text-muted-foreground">
              本月新增: {stats.newUsersThisMonth}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃用户</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.activeUsers}</div>
            <p className="text-xs text-muted-foreground">
              活跃率: {stats.totalUsers > 0 ? (stats.activeUsers / stats.totalUsers * 100).toFixed(1) : 0}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">非活跃用户</CardTitle>
            <UserX className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.inactiveUsers}</div>
            <p className="text-xs text-muted-foreground">
              包含暂停: {stats.suspendedUsers}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">用户增长率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats.userGrowthRate >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {stats.userGrowthRate >= 0 ? '+' : ''}{stats.userGrowthRate}%
            </div>
            <p className="text-xs text-muted-foreground">
              相对上个月
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布和角色分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>用户状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(USER_STATUS).map(([key, value]) => {
                const count = stats[`${key.toLowerCase()}Users`] || 0;
                const percentage = stats.totalUsers > 0 ? (count / stats.totalUsers * 100).toFixed(1) : 0;

                return (
                  <div key={value} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: USER_STATUS_COLORS[value] }} />

                      <span className="text-sm">{USER_STATUS_LABELS[value]}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{count}</Badge>
                      <span className="text-xs text-muted-foreground">{percentage}%</span>
                    </div>
                  </div>);

              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>用户状态提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-yellow-400" />
                  <span className="text-sm font-medium text-slate-200">待激活用户</span>
                </div>
                <Badge variant="secondary">{stats.pendingUsers}</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <UserX className="h-4 w-4 text-red-400" />
                  <span className="text-sm font-medium text-slate-200">暂停用户</span>
                </div>
                <Badge variant="destructive">{stats.suspendedUsers}</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-500/10 border border-slate-500/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <UserX className="h-4 w-4 text-slate-400" />
                  <span className="text-sm font-medium text-slate-200">非活跃用户</span>
                </div>
                <Badge variant="outline">{stats.inactiveUsers}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 角色和部门分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>主要角色分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topRoles.map((roleData, _index) =>
              <div key={roleData.role} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: getRoleColor(roleData.role) }} />

                    <span className="text-sm font-medium">{roleData.label}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">{roleData.count}</Badge>
                    <span className="text-xs text-muted-foreground">{roleData.percentage}%</span>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>部门分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topDepartments.map((deptData, _index) =>
              <div key={deptData.department} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Building2 className="h-3 w-3" />
                    <span className="text-sm font-medium">{deptData.label}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">{deptData.count}</Badge>
                    <span className="text-xs text-muted-foreground">{deptData.percentage}%</span>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('createUser')}>

              <UserPlus className="h-6 w-6" />
              <span className="text-sm">新建用户</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('manageRoles')}>

              <Shield className="h-6 w-6" />
              <span className="text-sm">角色管理</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewInactive')}>

              <UserX className="h-6 w-6" />
              <span className="text-sm">非活跃用户</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('userAnalytics')}>

              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">用户分析</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 详细统计 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">角色总数</CardTitle>
            <Shield className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{roles.length}</div>
            <p className="text-xs text-muted-foreground">
              系统角色配置
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">活跃度</CardTitle>
            <Activity className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.totalUsers > 0 ? (stats.activeUsers / stats.totalUsers * 100).toFixed(1) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">
              用户活跃率
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">本月增长</CardTitle>
            <Calendar className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{stats.newUsersThisMonth}</div>
            <p className="text-xs text-muted-foreground">
              新增用户数
            </p>
          </CardContent>
        </Card>
      </div>
    </div>);

};

export default UserManagementOverview;