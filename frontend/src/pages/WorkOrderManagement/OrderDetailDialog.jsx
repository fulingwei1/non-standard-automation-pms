

import { formatDate } from "../../lib/utils";
import { statusConfigs, priorityConfigs } from "./statusConstants";

export default function OrderDetailDialog({
  open,
  onOpenChange,
  selectedOrder,
  onAssign,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedOrder?.task_name} - {selectedOrder?.work_order_no}
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">
                    {selectedOrder.work_order_no}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">状态</div>
                  <Badge
                    className={statusConfigs[selectedOrder.status]?.color}
                  >
                    {statusConfigs[selectedOrder.status]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div>{selectedOrder.project_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">优先级</div>
                  <Badge
                    className={priorityConfigs[selectedOrder.priority]?.color}
                  >
                    {priorityConfigs[selectedOrder.priority]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划数量</div>
                  <div className="font-medium">
                    {selectedOrder.plan_qty || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">完成数量</div>
                  <div className="font-medium">
                    {selectedOrder.completed_qty || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">进度</div>
                  <div className="space-y-1">
                    <div className="text-lg font-bold">
                      {selectedOrder.progress || 0}%
                    </div>
                    <Progress
                      value={selectedOrder.progress || 0}
                      className="h-2"
                    />
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">标准工时</div>
                  <div>{selectedOrder.standard_hours || 0} 小时</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划开始</div>
                  <div>
                    {selectedOrder.plan_start_date
                      ? formatDate(selectedOrder.plan_start_date)
                      : "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划结束</div>
                  <div>
                    {selectedOrder.plan_end_date
                      ? formatDate(selectedOrder.plan_end_date)
                      : "-"}
                  </div>
                </div>
              </div>
              {selectedOrder.work_content && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">工作内容</div>
                  <div>{selectedOrder.work_content}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedOrder && selectedOrder.status === "PENDING" && (
            <Button onClick={onAssign}>
              <User className="w-4 h-4 mr-2" />
              派工
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
