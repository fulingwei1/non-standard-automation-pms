

import { getCategoryConfig } from "./categoryConstants";

export default function DetailDialog({ open, onOpenChange, position }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>岗位详情</DialogTitle>
        </DialogHeader>
        {position && (
          <div className="grid gap-4 py-4 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">岗位编码</Label>
                <p className="font-medium font-mono">{position.position_code}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">岗位名称</Label>
                <p className="font-medium">{position.position_name}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">岗位类别</Label>
                <p className="font-medium">
                  <Badge variant="outline" className={getCategoryConfig(position.position_category).color}>
                    {getCategoryConfig(position.position_category).label}
                  </Badge>
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">状态</Label>
                <p className="font-medium">
                  <Badge variant={position.is_active ? "default" : "secondary"}>
                    {position.is_active ? "启用" : "禁用"}
                  </Badge>
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">所属组织</Label>
                <p className="font-medium">{position.org_unit_name || "不限制"}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">排序号</Label>
                <p className="font-medium">{position.sort_order || 0}</p>
              </div>
              {position.description && (
                <div className="col-span-2">
                  <Label className="text-muted-foreground">描述</Label>
                  <p className="font-medium">{position.description}</p>
                </div>
              )}
              <div className="col-span-2">
                <Label className="text-muted-foreground">默认角色</Label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {position.roles?.length > 0 ? (
                    (position.roles || []).map((role, idx) => (
                      <Badge key={idx} variant="secondary">
                        <Shield className="h-3 w-3 mr-1" />
                        {role.role_name || role}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-muted-foreground">未配置默认角色</span>
                  )}
                </div>
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
