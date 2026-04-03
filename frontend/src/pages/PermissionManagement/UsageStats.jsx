import { Users, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import {
  getActionLabel,
  getActionColor,
  getModuleLabel,
  generatePermissionLabel,
} from "../../config/permissionLabels";
import { UNUSED_DISPLAY_LIMIT } from "./constants";

function MostUsedPermissions({ mostUsed }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <Users className="h-4 w-4 text-blue-400" />
          最常用权限 (TOP 10)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {mostUsed?.length > 0 ? (
          <div className="space-y-2">
            {(mostUsed || []).map((perm, index) => (
              <div
                key={perm.permission_code}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 w-4">{index + 1}</span>
                    <span className="font-medium text-white text-sm truncate">
                      {perm.permission_code}
                    </span>
                    <Badge
                      className={cn("text-xs", getActionColor(perm.action))}
                    >
                      {getActionLabel(perm.action)}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 ml-6 truncate">
                    {generatePermissionLabel(perm)}
                  </p>
                </div>
                <div className="text-right ml-2">
                  <div className="text-lg font-bold text-blue-400">{perm.roleCount}</div>
                  <div className="text-xs text-slate-500">个角色</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-slate-500 py-4 text-sm">
            暂无数据
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function UnusedPermissions({ unused, unusedCount }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <AlertCircle className="h-4 w-4 text-amber-400" />
          未分配的权限 ({unusedCount})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {unused?.length > 0 ? (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {unused.slice(0, UNUSED_DISPLAY_LIMIT).map((perm) => (
              <div
                key={perm.permission_code}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50 border border-amber-500/20"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white text-sm truncate">
                      {perm.permission_code}
                    </span>
                    <Badge
                      className={cn("text-xs", getActionColor(perm.action))}
                    >
                      {getActionLabel(perm.action)}
                    </Badge>
                    <Badge variant="outline" className="text-xs border-amber-500/30 text-amber-400">
                      未使用
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 truncate">
                    {generatePermissionLabel(perm)}
                  </p>
                  {perm.module && (
                    <p className="text-xs text-slate-600">
                      模块: {getModuleLabel(perm.module)}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {unused?.length > UNUSED_DISPLAY_LIMIT && (
              <div className="text-center text-xs text-slate-500 pt-2">
                还有 {unused?.length - UNUSED_DISPLAY_LIMIT} 个未分配权限...
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-slate-500 py-4 text-sm">
            所有权限都已分配
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function UsageStats({ permissionUsageStats, unusedCount }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <MostUsedPermissions mostUsed={permissionUsageStats.mostUsed} />
      <UnusedPermissions
        unused={permissionUsageStats.unused}
        unusedCount={unusedCount}
      />
    </div>
  );
}
