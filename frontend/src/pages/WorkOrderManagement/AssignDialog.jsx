import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";

export default function AssignDialog({
  open,
  onOpenChange,
  selectedOrder,
  assignData,
  setAssignData,
  onSubmit,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>派工</DialogTitle>
          <DialogDescription>为当前工单指定生产人员和可选工位。</DialogDescription>
        </DialogHeader>
        <DialogBody>
          {selectedOrder && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">工单号</div>
                <div className="font-mono">{selectedOrder.work_order_no}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">任务名称</div>
                <div className="font-medium">{selectedOrder.task_name}</div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  分配人员
                </label>
                <Input
                  type="number"
                  value={assignData.assigned_to || ""}
                  onChange={(e) =>
                    setAssignData({
                      ...assignData,
                      assigned_to: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    })
                  }
                  placeholder="人员ID"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">工位</label>
                <Input
                  type="number"
                  value={assignData.workstation_id || ""}
                  onChange={(e) =>
                    setAssignData({
                      ...assignData,
                      workstation_id: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    })
                  }
                  placeholder="工位ID"
                />
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit}>确认派工</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
