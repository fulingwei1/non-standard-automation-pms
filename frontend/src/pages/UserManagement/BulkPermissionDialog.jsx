import { Shield, Info } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Label } from "../../components/ui/label";
import { cn } from "../../lib/utils";
import { ROLE_TEMPLATES } from "./constants";

export default function BulkPermissionDialog({
  open,
  onOpenChange,
  selectedUserIds,
  availableRoles,
  bulkSelectedRoles,
  onBulkRoleToggle,
  onBulkSavePermissions,
  onApplyBulkRoleTemplate,
  onClearBulkRoles,
}) {
  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] bg-slate-900 border-slate-700 text-white">
        <DialogHeader>
          <DialogTitle>
            批量分配权限 - {selectedUserIds.length} 个用户
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <p className="text-sm text-slate-400">
              为选中的 {selectedUserIds.length} 个用户分配相同的角色权限。
            </p>

            {/* 快速模板 */}
            <div>
              <Label className="text-sm text-slate-300 mb-2 block">
                快速角色模板
              </Label>
              <div className="flex flex-wrap gap-2">
                {Object.entries(ROLE_TEMPLATES).map(([key, tmpl]) => (
                  <Button
                    key={key}
                    variant="outline"
                    size="sm"
                    onClick={() => onApplyBulkRoleTemplate(key)}
                    className="text-xs"
                    title={tmpl.codes.join(" + ")}
                  >
                    {tmpl.label}
                  </Button>
                ))}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onApplyBulkRoleTemplate("admin")}
                  className="text-xs"
                >
                  全部权限
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onClearBulkRoles}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  清空
                </Button>
              </div>
            </div>

            <div className="max-h-[400px] overflow-y-auto space-y-2">
              {(availableRoles || []).map((role) => (
                <div
                  key={role.id}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg border transition-colors",
                    bulkSelectedRoles.includes(role.id)
                      ? "bg-blue-500/20 border-blue-500/50"
                      : "bg-slate-800 border-slate-700 hover:border-slate-600",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Shield
                      className={cn(
                        "w-5 h-5",
                        bulkSelectedRoles.includes(role.id)
                          ? "text-blue-400"
                          : "text-slate-500",
                      )}
                    />
                    <div>
                      <div className="font-medium">
                        {role.role_name || role.name}
                      </div>
                      <div className="text-xs text-slate-400">
                        {role.description || role.role_code}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => onBulkRoleToggle(role.id)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-colors relative",
                      bulkSelectedRoles.includes(role.id)
                        ? "bg-blue-600"
                        : "bg-slate-700",
                    )}
                  >
                    <span
                      className={cn(
                        "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
                        bulkSelectedRoles.includes(role.id)
                          ? "translate-x-7"
                          : "translate-x-1",
                      )}
                    />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-2 text-sm text-slate-400 pt-2 border-t border-slate-700">
              <Info className="w-4 h-4" />
              <span>
                已选择 {bulkSelectedRoles.length} 个角色，将应用到{" "}
                {selectedUserIds.length} 个用户
              </span>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            取消
          </Button>
          <Button
            onClick={onBulkSavePermissions}
            className="bg-blue-600 hover:bg-blue-700"
          >
            批量保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
