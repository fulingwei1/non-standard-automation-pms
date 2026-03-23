/**
 * 角色对比对话框组件
 * 展示多角色权限对比结果
 */

import { DATA_SCOPE_MAP } from '../constants';

// 渲染数据权限标签
function renderDataScopeBadge(scope) {
  const config = DATA_SCOPE_MAP[scope] || DATA_SCOPE_MAP['OWN'];
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  );
}

export default function CompareDialog({
  open,
  onOpenChange,
  compareResult,
  onClose,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>角色权限对比</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {compareResult && (
            <div className="space-y-6">
              {/* 对比角色列表 */}
              <div className="flex gap-4 overflow-x-auto pb-2">
                {compareResult.roles?.map((role) => (
                  <div key={role.role_id} className="min-w-[200px] p-3 border rounded-lg">
                    <div className="font-medium">{role.role_name}</div>
                    <div className="text-xs text-slate-500">{role.role_code}</div>
                    <div className="mt-2">
                      {renderDataScopeBadge(role.data_scope)}
                    </div>
                    <div className="mt-2 text-sm">
                      权限数: {role.permissions?.length || 0}
                    </div>
                  </div>
                ))}
              </div>

              {/* 共同权限 */}
              <div>
                <h4 className="font-medium mb-2 flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-500" />
                  共同权限 ({compareResult.common_permissions?.length || 0})
                </h4>
                <div className="flex flex-wrap gap-1">
                  {compareResult.common_permissions?.map((perm) => (
                    <Badge key={perm} variant="secondary" className="text-xs">
                      {perm}
                    </Badge>
                  ))}
                  {(!compareResult.common_permissions || compareResult.common_permissions?.length === 0) && (
                    <span className="text-slate-400 text-sm">无共同权限</span>
                  )}
                </div>
              </div>

              {/* 差异权限 */}
              <div>
                <h4 className="font-medium mb-2">差异权限</h4>
                <div className="space-y-3">
                  {Object.entries(compareResult.diff_permissions || {}).map(([roleId, perms]) => {
                    const role = compareResult.roles?.find(r => r.role_id.toString() === roleId);
                    return (
                      <div key={roleId} className="border rounded p-3">
                        <div className="font-medium text-sm mb-2">
                          {role?.role_name} 独有权限 ({perms.length})
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {(perms || []).map((perm) => (
                            <Badge key={perm} variant="outline" className="text-xs">
                              {perm}
                            </Badge>
                          ))}
                          {perms.length === 0 && (
                            <span className="text-slate-400 text-sm">无独有权限</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
