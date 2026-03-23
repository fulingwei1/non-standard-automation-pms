/**
 * User Card Component
 * 用户信息卡片组件
 */

import { useState } from "react";




import {
  userRoleConfigs,
  accountStatusConfigs,
  getAccountStatusConfig,
  formatUserRole,
  cn } from
"@/lib/constants/userManagement";
import { formatDate, formatDateTime } from "../../lib/utils";

export function UserCard({
  user,
  onView,
  onEdit,
  onDelete,
  onToggleStatus,
  onResetPassword,
  onAssignRole,
  className,
  showActions = true
}) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [isToggling, setIsToggling] = useState(false);

  // 获取用户状态配置
  const _statusConfig = getAccountStatusConfig(user.is_active ? "NORMAL" : "DISABLED");

  // 获取用户角色
  const userRoles = user.roles?.map((role) => role.role) || [];
  const _primaryRole = userRoles[0];

  // 头像信息
  const avatarInitials = user.real_name ?
  user.real_name.charAt(0).toUpperCase() :
  user.username?.charAt(0).toUpperCase() || "U";

  // 处理删除操作
  const handleDelete = async () => {
    if (!user.id) {return;}

    setIsDeleting(true);
    try {
      await onDelete?.(user.id);
    } finally {
      setIsDeleting(false);
    }
  };

  // 处理状态切换
  const handleToggleStatus = async () => {
    if (!user.id) {return;}

    setIsToggling(true);
    try {
      await onToggleStatus?.(user.id, !user.is_active);
    } finally {
      setIsToggling(false);
    }
  };

  // 处理重置密码
  const handleResetPassword = async () => {
    if (!user.id) {return;}
    await onResetPassword?.(user.id);
  };

  // 处理角色分配
  const handleAssignRole = () => {
    if (!user.id) {return;}
    onAssignRole?.(user);
  };

  // 渲染角色标签
  const renderRoleBadges = () => {
    if (!userRoles || userRoles.length === 0) {
      return (
        <Badge variant="secondary" className="text-xs">
          <UserCheck className="w-3 h-3 mr-1" />
          无角色
        </Badge>);

    }

    return (
      <div className="flex flex-wrap gap-1">
        {userRoles.slice(0, 2).map((role) =>
        <Badge
          key={role.id}
          variant="outline"
          className="text-xs"
          style={{
            borderColor: userRoleConfigs[role.role_code]?.color?.replace('bg-', 'border-') || '#e5e7eb'
          }}>

            {formatUserRole(role.role_code)}
        </Badge>
        )}
        {userRoles.length > 2 &&
        <Badge variant="outline" className="text-xs">
            +{userRoles.length - 2}
        </Badge>
        }
      </div>);

  };

  // 渲染状态指示器
  const renderStatusIndicator = () => {
    const status = user.is_active ? "NORMAL" : "DISABLED";
    const config = accountStatusConfigs[status];

    return (
      <div className={cn(
        "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
        config.color,
        config.textColor
      )}>
        {config.icon}
        {config.label}
      </div>);

  };

  // 渲染最后登录信息
  const renderLastLogin = () => {
    if (!user.last_login_at) {
      return (
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="w-3 h-3" />
          未登录
        </div>);

    }

    const loginDate = new Date(user.last_login_at);
    const now = new Date();
    const diffMinutes = Math.floor((now - loginDate) / (1000 * 60));

    let timeAgo;
    if (diffMinutes < 1) {
      timeAgo = "刚刚";
    } else if (diffMinutes < 60) {
      timeAgo = `${diffMinutes}分钟前`;
    } else if (diffMinutes < 1440) {
      timeAgo = `${Math.floor(diffMinutes / 60)}小时前`;
    } else {
      timeAgo = formatDateTime(user.last_login_at);
    }

    return (
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        <Activity className="w-3 h-3" />
        {timeAgo}
      </div>);

  };

  // 渲染积分信息
  const renderCredits = () => {
    const credits = user.solution_credits || 0;
    let creditColor = "text-green-600";
    let creditIcon = "💎";

    if (credits < 50) {creditColor = "text-red-600";}else
    if (credits < 100) {creditColor = "text-yellow-600";}

    return (
      <div className={cn("flex items-center gap-1 text-xs", creditColor)}>
        <span className="font-medium">{creditIcon}</span>
        <span>{credits}</span>
      </div>);

  };

  return (
    <Card className={cn("group hover:shadow-md transition-shadow", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {/* 头像 */}
            <div className="relative">
              <Avatar className="w-12 h-12">
                <AvatarImage src={user.avatar} alt={user.real_name || user.username} />
                <AvatarFallback className="font-semibold">
                  {avatarInitials}
                </AvatarFallback>
              </Avatar>
              {/* 在线状态指示器 */}
              {user.last_login_at && new Date() - new Date(user.last_login_at) < 30 * 60 * 1000 &&
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-green-500 border-2 border-background rounded-full" />
              }
            </div>

            {/* 用户基本信息 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <CardTitle className="text-lg font-semibold truncate">
                  {user.real_name || user.username}
                </CardTitle>
                {renderStatusIndicator()}
              </div>

              <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                <span className="truncate">@{user.username}</span>
                {user.employee_no &&
                <span className="text-xs">({user.employee_no})</span>
                }
              </div>

              {renderRoleBadges()}
            </div>
          </div>

          {/* 操作按钮 */}
          {showActions &&
          <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity">

                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => onView?.(user)}>
                  <Eye className="mr-2 h-4 w-4" />
                  查看详情
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit?.(user)}>
                  <Edit className="mr-2 h-4 w-4" />
                  编辑用户
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleAssignRole}>
                  <Shield className="mr-2 h-4 w-4" />
                  分配角色
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleResetPassword}>
                  <Key className="mr-2 h-4 w-4" />
                  重置密码
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                onClick={handleToggleStatus}
                disabled={isToggling}
                className={user.is_active ? "text-orange-600" : "text-green-600"}>

                  {isToggling ?
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> :
                user.is_active ?
                <Ban className="mr-2 h-4 w-4" /> :

                <Check className="mr-2 h-4 w-4" />
                }
                  {user.is_active ? "禁用用户" : "启用用户"}
                </DropdownMenuItem>
                <DropdownMenuItem
                onClick={handleDelete}
                disabled={isDeleting}
                className="text-red-600">

                  {isDeleting ?
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> :

                <Trash2 className="mr-2 h-4 w-4" />
                }
                  删除用户
                </DropdownMenuItem>
              </DropdownMenuContent>
          </DropdownMenu>
          }
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* 联系信息 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
          {user.email &&
          <div className="flex items-center gap-2 text-sm">
              <Mail className="w-4 h-4 text-muted-foreground" />
              <span className="truncate">{user.email}</span>
          </div>
          }
          {user.phone &&
          <div className="flex items-center gap-2 text-sm">
              <Phone className="w-4 h-4 text-muted-foreground" />
              <span className="truncate">{user.phone}</span>
          </div>
          }
          {user.department &&
          <div className="flex items-center gap-2 text-sm">
              <Building2 className="w-4 h-4 text-muted-foreground" />
              <span className="truncate">{user.department}</span>
          </div>
          }
          {user.position &&
          <div className="flex items-center gap-2 text-sm">
              <UserIcon className="w-4 h-4 text-muted-foreground" />
              <span className="truncate">{user.position}</span>
          </div>
          }
        </div>

        {/* 底部信息 */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {renderLastLogin()}
            {user.solution_credits !== undefined && renderCredits()}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="w-3 h-3" />
            {formatDate(user.created_at)}
          </div>
        </div>

        {/* 认证信息 */}
        {user.auth_type &&
        <div className="mt-2 flex items-center gap-1">
            <Lock className="w-3 h-3 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              认证方式: {user.auth_type}
            </span>
        </div>
        }

        {/* 系统标识 */}
        {user.is_superuser &&
        <div className="mt-2">
            <Badge variant="default" className="bg-gradient-to-r from-purple-500 to-pink-500">
              <Shield className="w-3 h-3 mr-1" />
              超级管理员
            </Badge>
        </div>
        }
      </CardContent>
    </Card>);

}