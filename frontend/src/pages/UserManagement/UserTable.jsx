import {
  Edit3,
  Trash2,
  Key,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import { cn } from "../../lib/utils";
import {
  USER_STATUS,
  USER_DEPARTMENT_LABELS,
} from "../../components/user-management";
import { statusConfig, roleConfig } from "./constants";

const getStatusBadge = (status) => {
  const config = statusConfig[status];
  if (!config) {
    return <Badge variant="secondary">{status}</Badge>;
  }

  return (
    <Badge
      variant="secondary"
      className={cn("border-0", {
        "bg-green-500 text-white": status === USER_STATUS.ACTIVE,
        "bg-gray-500 text-white": status === USER_STATUS.INACTIVE,
        "bg-red-500 text-white": status === USER_STATUS.SUSPENDED,
        "bg-yellow-500 text-white": status === USER_STATUS.PENDING,
      })}
    >
      {config.label}
    </Badge>
  );
};

const getRoleBadge = (role) => {
  const config = roleConfig[role];
  if (!config) {
    return <Badge variant="secondary">{role}</Badge>;
  }

  return (
    <Badge
      variant="secondary"
      className="border-0"
      style={{ backgroundColor: config.color + "20", color: config.color }}
    >
      {config.label}
    </Badge>
  );
};

export default function UserTable({
  loading,
  users,
  selectedUserIds,
  onSelectAll,
  onSelectUser,
  onOpenEditDialog,
  onOpenPermissionDialog,
  onToggleUserStatus,
  onDeleteUser,
  onOpenBulkPermissionDialog,
  onClearSelection,
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>用户列表</CardTitle>
          {selectedUserIds.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-400">
                已选择 {selectedUserIds.length} 个用户
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenBulkPermissionDialog}
                className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600"
              >
                <Key className="w-4 h-4 mr-1" />
                批量分配权限
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onClearSelection}
              >
                取消选择
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : users?.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            暂无用户数据
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <input
                    type="checkbox"
                    checked={
                      selectedUserIds.length === users?.length &&
                      users?.length > 0
                    }
                    onChange={onSelectAll}
                    className="w-4 h-4 rounded border-slate-600 bg-slate-800"
                  />
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
              {Array.isArray(users) ? users.map((user) => (
                <TableRow
                  key={user.id}
                  className={
                    selectedUserIds.includes(user.id)
                      ? "bg-blue-500/10"
                      : ""
                  }
                >
                  <TableCell>
                    <input
                      type="checkbox"
                      checked={selectedUserIds.includes(user.id)}
                      onChange={() => onSelectUser(user.id)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-800"
                    />
                  </TableCell>
                  <TableCell>
                    <span className="font-medium">
                      {user.real_name || user.full_name || user.username}
                    </span>
                  </TableCell>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {USER_DEPARTMENT_LABELS[user.department] ||
                        user.department ||
                        "-"}
                    </Badge>
                  </TableCell>
                  <TableCell>{user.position || "-"}</TableCell>
                  <TableCell>{getRoleBadge(user.role)}</TableCell>
                  <TableCell>{getStatusBadge(user.status)}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenEditDialog(user)}
                        title="编辑"
                      >
                        <Edit3 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpenPermissionDialog(user)}
                        title="管理权限"
                        className="text-blue-600 hover:text-blue-700"
                      >
                        <Key className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onToggleUserStatus(user)}
                        title={
                          user.status === USER_STATUS.ACTIVE
                            ? "停用"
                            : "启用"
                        }
                      >
                        {user.status === USER_STATUS.ACTIVE ? (
                          <ToggleRight className="w-4 h-4 text-green-600" />
                        ) : (
                          <ToggleLeft className="w-4 h-4 text-slate-400" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteUser(user.id)}
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )) : <TableRow><TableCell colSpan="8" className="text-center py-8 text-slate-400">加载中...</TableCell></TableRow>}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
