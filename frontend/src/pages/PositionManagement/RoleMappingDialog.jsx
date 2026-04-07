

import { cn } from "../../lib/utils";

export default function RoleMappingDialog({
  open,
  onOpenChange,
  position,
  roles,
  selectedRoleIds,
  toggleRole,
  onSave,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>配置默认角色 - {position?.position_name}</DialogTitle>
          <DialogDescription>
            选择该岗位的默认角色，员工分配到此岗位时将自动获得这些角色的权限
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto py-4">
          <div className="space-y-2">
            {(roles || []).map((role) => (
              <label
                key={role.id}
                className={cn(
                  "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                  selectedRoleIds.includes(role.id)
                    ? "bg-primary/10 border-primary"
                    : "hover:bg-muted"
                )}
              >
                <input
                  type="checkbox"
                  checked={selectedRoleIds.includes(role.id)}
                  onChange={() => toggleRole(role.id)}
                  className="rounded"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{role.role_name}</span>
                    <Badge variant="outline" className="text-xs font-mono">
                      {role.role_code}
                    </Badge>
                    {role.role_type === "SYSTEM" && (
                      <Badge variant="destructive" className="text-xs">
                        <Shield className="h-3 w-3 mr-1" /> 系统
                      </Badge>
                    )}
                  </div>
                  {role.description && (
                    <p className="text-sm text-muted-foreground mt-1">{role.description}</p>
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>
        <DialogFooter className="border-t pt-4">
          <div className="flex-1 text-sm text-muted-foreground">
            已选择 {selectedRoleIds.length} 个角色
          </div>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button onClick={onSave}>保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
