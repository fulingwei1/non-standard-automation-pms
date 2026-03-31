import { motion } from "framer-motion";
import {
  Eye,
  Package,
  ChevronDown,
  ChevronRight,
  Key,
  FileText,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import {
  getActionLabel,
  getActionColor,
  getModuleLabel,
  generatePermissionLabel,
} from "../../config/permissionLabels";
import { ANIMATION_VARIANTS } from "./constants";

function PermissionItem({ permission, permissionUsageStats, onViewDetail }) {
  const usageInfo = (permissionUsageStats.mostUsed || []).find(
    p => p.permission_code === permission.permission_code
  );
  const roleCount = usageInfo?.roleCount || 0;
  const isUnused = (permissionUsageStats.unused || []).some(
    p => p.permission_code === permission.permission_code
  );

  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 rounded-lg transition-colors",
        "bg-slate-800/50 hover:bg-slate-800",
        isUnused && "border border-amber-500/20 bg-amber-500/5"
      )}
    >
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <Key className="h-4 w-4 text-slate-400" />
          <span className="font-medium text-white">
            {permission.permission_code}
          </span>
          {permission.action &&
            <Badge
              className={cn("text-xs", getActionColor(permission.action))}
            >
              {getActionLabel(permission.action)}
            </Badge>
          }
          {permission.is_active === false &&
            <Badge variant="destructive" className="text-xs">
              已禁用
            </Badge>
          }
          {isUnused &&
            <Badge
              variant="outline"
              className="text-xs border-amber-500/30 text-amber-400"
            >
              未使用
            </Badge>
          }
        </div>
        <p className="text-sm text-slate-400 ml-6">
          {generatePermissionLabel(permission)}
        </p>
        {permission.description &&
          <p className="text-xs text-slate-500 ml-6 mt-1">
            {permission.description}
          </p>
        }
        {permission.resource &&
          <div className="flex items-center gap-2 mt-2 ml-6">
            <FileText className="h-3 w-3 text-slate-500" />
            <span className="text-xs text-slate-500">
              资源: {permission.resource}
            </span>
          </div>
        }
      </div>
      <div className="flex items-center gap-3 ml-4">
        <div className="text-right">
          <div className={cn(
            "text-lg font-bold",
            roleCount > 0 ? "text-blue-400" : "text-slate-500"
          )}>
            {roleCount}
          </div>
          <div className="text-xs text-slate-500">
            个角色
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetail(permission)}
        >
          <Eye className="h-4 w-4 mr-1" />
          详情
        </Button>
      </div>
    </div>
  );
}

export function PermissionList({
  loading,
  isDemoAccount,
  searchKeyword,
  filteredPermissions,
  expandedModules,
  permissionUsageStats,
  toggleModule,
  handleViewDetail,
}) {
  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-slate-400">加载中...</div>
        </CardContent>
      </Card>
    );
  }

  if (isDemoAccount) {
    return null;
  }

  if (Object.keys(filteredPermissions).length === 0) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-slate-400">
            {searchKeyword ? "未找到匹配的权限" : "暂无权限数据"}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {Object.entries(filteredPermissions).map(([module, perms]) =>
        <motion.div
          key={module}
          initial={ANIMATION_VARIANTS.initial}
          animate={ANIMATION_VARIANTS.animate}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleModule(module)}
              >
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5 text-blue-400" />
                  <span>{getModuleLabel(module)}</span>
                  <Badge variant="secondary" className="ml-2">
                    {perms.length}
                  </Badge>
                </CardTitle>
                {expandedModules[module] === true ?
                  <ChevronDown className="h-5 w-5 text-slate-400" /> :
                  <ChevronRight className="h-5 w-5 text-slate-400" />
                }
              </div>
            </CardHeader>
            {expandedModules[module] === true &&
              <CardContent>
                <div className="space-y-2">
                  {(perms || []).map((permission) => (
                    <PermissionItem
                      key={permission.id}
                      permission={permission}
                      permissionUsageStats={permissionUsageStats}
                      onViewDetail={handleViewDetail}
                    />
                  ))}
                </div>
              </CardContent>
            }
          </Card>
        </motion.div>
      )}
    </div>
  );
}
