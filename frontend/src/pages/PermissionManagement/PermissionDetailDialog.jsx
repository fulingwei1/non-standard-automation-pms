

import {
  getActionLabel,
  getActionColor,
  getModuleLabel,
  generatePermissionLabel,
} from "../../config/permissionLabels";

export function PermissionDetailDialog({
  open,
  onOpenChange,
  selectedPermission,
  permissionRoles,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
                    <Badge className={getActionColor(selectedPermission.action)}>
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
                    {new Date(selectedPermission.created_at).toLocaleString("zh-CN")}
                  </p>
                </div>
                {selectedPermission.updated_at &&
                  <div>
                    <label className="text-sm font-medium text-slate-400">
                      更新时间
                    </label>
                    <p className="text-white mt-1">
                      {new Date(selectedPermission.updated_at).toLocaleString("zh-CN")}
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
                      className="flex items-center gap-2 p-2 rounded bg-slate-800/50"
                    >
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
  );
}
