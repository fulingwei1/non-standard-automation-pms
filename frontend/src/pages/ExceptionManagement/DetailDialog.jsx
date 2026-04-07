

import { formatDate } from "../../lib/utils";
import { statusConfigs, severityConfigs, typeConfigs } from "./constants";

/**
 * DetailDialog
 * Read-only detail view for a selected exception event.
 * Exposes an "处理异常" CTA when the event is still OPEN.
 */
export function DetailDialog({
  open,
  onOpenChange,
  selectedException,
  onOpenHandle,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {selectedException?.event_title} - {selectedException?.event_no}
          </DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedException && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常编号</div>
                  <div className="font-mono">{selectedException.event_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">状态</div>
                  <Badge
                    className={
                      statusConfigs[selectedException.status]?.color
                    }
                  >
                    {statusConfigs[selectedException.status]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div>{selectedException.project_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常类型</div>
                  <Badge
                    className={
                      typeConfigs[selectedException.event_type]?.color
                    }
                  >
                    {typeConfigs[selectedException.event_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">严重程度</div>
                  <Badge
                    className={
                      severityConfigs[selectedException.severity]?.color
                    }
                  >
                    {severityConfigs[selectedException.severity]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">发现时间</div>
                  <div>
                    {selectedException.discovered_at
                      ? formatDate(selectedException.discovered_at)
                      : "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">进度影响</div>
                  <div>{selectedException.schedule_impact || 0} 天</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">成本影响</div>
                  <div>¥{selectedException.cost_impact || 0}</div>
                </div>
              </div>

              {selectedException.event_description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常描述</div>
                  <div>{selectedException.event_description}</div>
                </div>
              )}

              {selectedException.impact_description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">影响说明</div>
                  <div>{selectedException.impact_description}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedException?.status === "OPEN" && (
            <Button
              onClick={() => {
                onOpenChange(false);
                onOpenHandle(selectedException);
              }}
            >
              <Edit className="w-4 h-4 mr-2" />
              处理异常
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
