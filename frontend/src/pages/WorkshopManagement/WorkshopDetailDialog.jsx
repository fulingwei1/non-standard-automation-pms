import { Edit } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { typeConfigs } from "./constants";

export function WorkshopDetailDialog({
  open,
  onOpenChange,
  selectedWorkshop,
  onEditClick,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>
            {selectedWorkshop?.workshop_name} - 车间详情
          </DialogTitle>
          <DialogDescription>查看车间基础资料、产能和启用状态。</DialogDescription>
        </DialogHeader>
        <DialogBody>
          {selectedWorkshop && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">车间编码</div>
                  <div className="font-mono">
                    {selectedWorkshop.workshop_code}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">车间名称</div>
                  <div>{selectedWorkshop.workshop_name}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">车间类型</div>
                  <Badge
                    className={
                      typeConfigs[selectedWorkshop.workshop_type]?.color
                    }
                  >
                    {typeConfigs[selectedWorkshop.workshop_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">车间主管</div>
                  <div>{selectedWorkshop.manager_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">位置</div>
                  <div>{selectedWorkshop.location || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">产能（小时）</div>
                  <div>{selectedWorkshop.capacity_hours || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">状态</div>
                  {selectedWorkshop.is_active !== false ? (
                    <Badge className="bg-emerald-500">启用</Badge>
                  ) : (
                    <Badge className="bg-gray-500">停用</Badge>
                  )}
                </div>
              </div>
              {selectedWorkshop.description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">描述</div>
                  <div>{selectedWorkshop.description}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedWorkshop && (
            <Button
              onClick={() => {
                onOpenChange(false);
                onEditClick(selectedWorkshop);
              }}
            >
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
