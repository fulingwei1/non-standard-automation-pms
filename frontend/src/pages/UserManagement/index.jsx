/**
 * 用户管理页面 - 薄壳组件
 * 1,346 行单体拆分为: constants + hook + 3 个对话框组件
 */

import { motion } from "framer-motion";
import {
  Plus, Search, Edit3, Trash2, Key,
  ToggleLeft, ToggleRight, RefreshCw,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../../components/ui/select";

import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import {
  UserManagementOverview,
  USER_STATUS, USER_DEPARTMENT_LABELS,
  USER_STATUS_FILTER_OPTIONS, ROLE_FILTER_OPTIONS, DEPARTMENT_FILTER_OPTIONS,
} from "../../components/user-management";
import { statusConfig, roleConfig } from "./constants";
import { useUserManagement } from "./hooks/useUserManagement";
import { UserFormDialog } from "./components/UserFormDialog";
import { PermissionDialog } from "./components/PermissionDialog";

// Badge 渲染辅助
function StatusBadge({ status }) {
  const config = statusConfig[status];
  if (!config) return <Badge variant="secondary">{status}</Badge>;
  return (
    <Badge variant="secondary" className={cn("border-0", {
      "bg-green-500 text-white": status === USER_STATUS.ACTIVE,
      "bg-gray-500 text-white": status === USER_STATUS.INACTIVE,
      "bg-red-500 text-white": status === USER_STATUS.SUSPENDED,
      "bg-yellow-500 text-white": status === USER_STATUS.PENDING,
    })}>
      {config.label}
    </Badge>
  );
}

function RoleBadge({ role }) {
  const config = roleConfig[role];
  if (!config) return <Badge variant="secondary">{role}</Badge>;
  return (
    <Badge variant="secondary" className="border-0" style={{ backgroundColor: config.color + "20", color: config.color }}>
      {config.label}
    </Badge>
  );
}

export default function UserManagement() {
  const ctx = useUserManagement();

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer} className="space-y-6">
      <PageHeader
        title="用户管理"
        description="管理系统用户、角色和权限"
        actions={
          <div className="flex space-x-2">
            <Button variant="outline" onClick={ctx.handleSyncFromEmployees}>
              <RefreshCw className="mr-2 h-4 w-4" />同步员工
            </Button>
            <Button onClick={() => ctx.setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />新建用户
            </Button>
          </div>
        }
      />

      <UserManagementOverview
        users={ctx.users} roles={ctx.roles} totalUsers={ctx.totalUsers}
        onQuickAction={ctx.handleQuickAction}
      />

      {/* 筛选 */}
      <motion.div variants={fadeIn} className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input placeholder="搜索用户..." value={ctx.searchQuery || "unknown"} onChange={(e) => ctx.setSearchQuery(e.target.value)} className="pl-10" />
        </div>
        <div className="flex gap-2">
          <Select value={ctx.filterStatus || "unknown"} onValueChange={ctx.setFilterStatus}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder="状态" /></SelectTrigger>
            <SelectContent>
              {USER_STATUS_FILTER_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={ctx.filterRole || "unknown"} onValueChange={ctx.setFilterRole}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder="角色" /></SelectTrigger>
            <SelectContent>
              {ROLE_FILTER_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={ctx.filterDepartment || "unknown"} onValueChange={ctx.setFilterDepartment}>
            <SelectTrigger className="w-[140px]"><SelectValue placeholder="部门" /></SelectTrigger>
            <SelectContent>
              {DEPARTMENT_FILTER_OPTIONS.map((opt) => <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
      </motion.div>

      {/* 用户列表 */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>用户列表</CardTitle>
              {ctx.selectedUserIds.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-400">已选择 {ctx.selectedUserIds.length} 个用户</span>
                  <Button variant="outline" size="sm" onClick={ctx.openBulkPermissionDialog} className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600">
                    <Key className="w-4 h-4 mr-1" />批量分配权限
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => ctx.setSelectedUserIds([])}>取消选择</Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {ctx.loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : ctx.users?.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无用户数据</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <input type="checkbox" checked={ctx.selectedUserIds.length === ctx.users?.length && ctx.users?.length > 0} onChange={ctx.handleSelectAll} className="w-4 h-4 rounded border-slate-600 bg-slate-800" />
                    </TableHead>
                    <TableHead>姓名</TableHead>
                    <TableHead>用户名</TableHead>
                    <TableHead>部门</TableHead>
                    <TableHead>级别</TableHead>
                    <TableHead>角色</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(ctx.users || []).map((user) => (
                    <TableRow key={user.id} className={ctx.selectedUserIds.includes(user.id) ? "bg-blue-500/10" : ""}>
                      <TableCell>
                        <input type="checkbox" checked={ctx.selectedUserIds.includes(user.id)} onChange={() => ctx.handleSelectUser(user.id)} className="w-4 h-4 rounded border-slate-600 bg-slate-800" />
                      </TableCell>
                      <TableCell><span className="font-medium">{user.real_name || user.full_name || user.username}</span></TableCell>
                      <TableCell>{user.username}</TableCell>
                      <TableCell><Badge variant="outline">{USER_DEPARTMENT_LABELS[user.department] || user.department || "-"}</Badge></TableCell>
                      <TableCell>{user.position || "-"}</TableCell>
                      <TableCell><RoleBadge role={user.role} /></TableCell>
                      <TableCell><StatusBadge status={user.status} /></TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="ghost" size="sm" onClick={() => ctx.openEditDialog(user)} title="编辑"><Edit3 className="w-4 h-4" /></Button>
                          <Button variant="ghost" size="sm" onClick={() => ctx.openPermissionDialog(user)} title="管理权限" className="text-blue-600 hover:text-blue-700"><Key className="w-4 h-4" /></Button>
                          <Button variant="ghost" size="sm" onClick={() => ctx.handleToggleUserStatus(user)} title={user.status === USER_STATUS.ACTIVE ? "停用" : "启用"}>
                            {user.status === USER_STATUS.ACTIVE ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4 text-slate-400" />}
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => ctx.handleDeleteUser(user.id)} title="删除"><Trash2 className="w-4 h-4 text-red-500" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 对话框 */}
      <UserFormDialog
        open={ctx.showCreateDialog} onOpenChange={ctx.setShowCreateDialog}
        title="新建用户" userData={ctx.newUser} setUserData={ctx.setNewUser}
        onSubmit={ctx.handleCreateUser} submitLabel="创建" showPassword
      />
      {ctx.selectedUser && (
        <UserFormDialog
          open={ctx.showEditDialog} onOpenChange={ctx.setShowEditDialog}
          title="编辑用户" userData={ctx.selectedUser} setUserData={ctx.setSelectedUser}
          onSubmit={ctx.handleUpdateUser} submitLabel="更新"
        />
      )}
      {ctx.showPermissionDialog && ctx.selectedUser && (
        <PermissionDialog
          open={ctx.showPermissionDialog} onOpenChange={ctx.setShowPermissionDialog}
          title={`管理用户权限 - ${ctx.selectedUser.username}`}
          description="为用户分配角色以管理其权限。用户将拥有所选角色的所有权限。"
          availableRoles={ctx.availableRoles}
          selectedRoleIds={ctx.selectedRoles} onRoleToggle={ctx.handleRoleToggle}
          onApplyTemplate={ctx.applyRoleTemplate} onClearRoles={() => ctx.setSelectedRoles([])}
          onSave={ctx.handleSavePermissions}
        />
      )}
      {ctx.showBulkDialog && (
        <PermissionDialog
          open={ctx.showBulkDialog} onOpenChange={ctx.setShowBulkDialog}
          title={`批量分配权限 - ${ctx.selectedUserIds.length} 个用户`}
          description={`为选中的 ${ctx.selectedUserIds.length} 个用户分配相同的角色权限。`}
          availableRoles={ctx.availableRoles}
          selectedRoleIds={ctx.bulkSelectedRoles} onRoleToggle={ctx.handleBulkRoleToggle}
          onApplyTemplate={ctx.applyBulkRoleTemplate} onClearRoles={() => ctx.setBulkSelectedRoles([])}
          onSave={ctx.handleBulkSavePermissions} saveLabel="批量保存"
        />
      )}
    </motion.div>
  );
}
