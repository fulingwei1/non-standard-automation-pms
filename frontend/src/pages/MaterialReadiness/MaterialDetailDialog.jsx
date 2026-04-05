import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { getMaterialTypeLabel } from "../../components/material-readiness";
import { getStatusBadge, getPriorityBadge } from "./BadgeHelpers";

export default function MaterialDetailDialog({ open, onOpenChange, material }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>物料详情</DialogTitle>
        </DialogHeader>

        {material && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">物料名称</p>
                <p className="font-medium">{material.name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">类型</p>
                <p className="font-medium">
                  {getMaterialTypeLabel(material.type)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">状态</p>
                <div className="mt-1">{getStatusBadge(material.status)}</div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">优先级</p>
                <div className="mt-1">{getPriorityBadge(material.priority)}</div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">数量</p>
                <p className="font-medium">
                  {material.quantity} {material.unit}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">供应商</p>
                <p className="font-medium">
                  {material.supplier?.name || "-"}
                </p>
              </div>
            </div>

            {material.description && (
              <div>
                <p className="text-sm text-muted-foreground">描述</p>
                <p className="font-medium">{material.description}</p>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
