

import { cn, formatDate } from "../../lib/utils";
import { statusConfigs, levelConfigs, TERMINAL_STATUSES } from "./constants";

export default function AlertDetailDialog({
  open,
  onOpenChange,
  selectedAlert,
  onAcknowledge,
  onOpenHandle,
}) {
  const handleOpenHandle = () => {
    onOpenChange(false);
    onOpenHandle(selectedAlert);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle className="text-slate-200">缺料预警详情</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedAlert && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">项目</div>
                  <div className="font-medium text-slate-200">
                    {selectedAlert.project_name || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">状态</div>
                  <Badge className={statusConfigs[selectedAlert.status]?.color}>
                    {statusConfigs[selectedAlert.status]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">物料编码</div>
                  <div className="font-mono text-slate-200">
                    {selectedAlert.material_code}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">物料名称</div>
                  <div className="text-slate-200">{selectedAlert.material_name}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">需求数量</div>
                  <div className="font-medium text-slate-200">
                    {selectedAlert.required_qty || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">可用数量</div>
                  <div
                    className={cn(
                      "text-slate-200",
                      selectedAlert.available_qty < selectedAlert.required_qty &&
                        "text-red-400",
                    )}
                  >
                    {selectedAlert.available_qty || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">缺料数量</div>
                  <div className="font-medium text-red-400">
                    {selectedAlert.shortage_qty || 0}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">需求日期</div>
                  <div className="text-slate-200">
                    {selectedAlert.required_date
                      ? formatDate(selectedAlert.required_date)
                      : "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">预警级别</div>
                  <Badge className={levelConfigs[selectedAlert.alert_level]?.color}>
                    {levelConfigs[selectedAlert.alert_level]?.label}
                  </Badge>
                </div>
                {selectedAlert.resolved_at && (
                  <div>
                    <div className="text-sm text-slate-400 mb-1">解决时间</div>
                    <div className="text-slate-200">
                      {formatDate(selectedAlert.resolved_at)}
                    </div>
                  </div>
                )}
              </div>
              {selectedAlert.solution && (
                <div>
                  <div className="text-sm text-slate-400 mb-1">解决方案</div>
                  <div className="text-slate-200">{selectedAlert.solution}</div>
                </div>
              )}
              {selectedAlert.remark && (
                <div>
                  <div className="text-sm text-slate-400 mb-1">备注</div>
                  <div className="text-slate-200">{selectedAlert.remark}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedAlert?.status === "PENDING" && (
            <Button onClick={() => onAcknowledge(selectedAlert.id)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              确认预警
            </Button>
          )}
          {selectedAlert && !TERMINAL_STATUSES.has(selectedAlert.status) && (
            <Button onClick={handleOpenHandle}>
              <Package className="w-4 h-4 mr-2" />
              处理预警
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
