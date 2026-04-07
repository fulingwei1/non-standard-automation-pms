

import { getUnitTypeConfig } from "./unitTypeConfig";

export default function DetailDialog({ open, onOpenChange, selectedUnit }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>组织详情</DialogTitle>
        </DialogHeader>
        {selectedUnit && (
          <div className="grid gap-4 py-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">组织编码</Label>
                <p className="font-medium font-mono">{selectedUnit.unit_code}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">组织名称</Label>
                <p className="font-medium">{selectedUnit.unit_name}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">组织类型</Label>
                <p className="font-medium">
                  <Badge variant="outline" className={getUnitTypeConfig(selectedUnit.unit_type).color}>
                    {getUnitTypeConfig(selectedUnit.unit_type).label}
                  </Badge>
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">状态</Label>
                <p className="font-medium">
                  <Badge variant={selectedUnit.is_active ? "default" : "secondary"}>
                    {selectedUnit.is_active ? "启用" : "禁用"}
                  </Badge>
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">上级组织</Label>
                <p className="font-medium">{selectedUnit.parent_name || "-"}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">负责人</Label>
                <p className="font-medium">{selectedUnit.manager_name || "-"}</p>
              </div>
              {selectedUnit.description && (
                <div className="col-span-2">
                  <Label className="text-muted-foreground">描述</Label>
                  <p className="font-medium">{selectedUnit.description}</p>
                </div>
              )}
              <div>
                <Label className="text-muted-foreground">层级</Label>
                <p className="font-medium">{selectedUnit.level || 1}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">路径</Label>
                <p className="font-medium font-mono text-xs">{selectedUnit.path || "-"}</p>
              </div>
            </div>
          </div>
        )}
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
