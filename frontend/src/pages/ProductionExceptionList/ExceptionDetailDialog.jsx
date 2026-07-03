/**
 * ExceptionDetailDialog — read-only detail view for a single exception,
 * with action buttons to trigger Handle or Close flows.
 */
import { Edit, CheckCircle2 } from "lucide-react";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { formatDate } from "../../lib/utils";
import { statusConfigs, typeConfigs, levelConfigs } from "./constants";

export function ExceptionDetailDialog({
  open,
  onOpenChange,
  selectedException,
  onOpenHandleDialog,
  onClose,
}) {
  const exc = selectedException;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {exc?.title} - {exc?.exception_no}
          </DialogTitle>
          <DialogDescription>查看生产异常详情、处理记录和关闭动作。</DialogDescription>
        </DialogHeader>
        <DialogBody>
          {exc && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常编号</div>
                  <div className="font-mono">{exc.exception_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">状态</div>
                  <Badge className={statusConfigs[exc.status]?.color}>
                    {statusConfigs[exc.status]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常类型</div>
                  <Badge className={typeConfigs[exc.exception_type]?.color}>
                    {typeConfigs[exc.exception_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常级别</div>
                  <Badge className={levelConfigs[exc.exception_level]?.color}>
                    {levelConfigs[exc.exception_level]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div>{exc.project_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">工单号</div>
                  <div className="font-mono">{exc.work_order_no || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">上报人</div>
                  <div>{exc.reporter_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">上报时间</div>
                  <div>
                    {exc.report_time ? formatDate(exc.report_time) : "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">影响工时</div>
                  <div>{exc.impact_hours || 0} 小时</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">影响成本</div>
                  <div>¥{exc.impact_cost || 0}</div>
                </div>
              </div>

              {exc.description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">异常描述</div>
                  <div>{exc.description}</div>
                </div>
              )}
              {exc.handle_plan && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">处理方案</div>
                  <div>{exc.handle_plan}</div>
                </div>
              )}
              {exc.handle_result && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">处理结果</div>
                  <div>{exc.handle_result}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {exc &&
            (exc.status === "REPORTED" || exc.status === "IN_PROGRESS") && (
              <Button
                onClick={() => {
                  onOpenChange(false);
                  onOpenHandleDialog(exc);
                }}
              >
                <Edit className="w-4 h-4 mr-2" />
                处理异常
              </Button>
            )}
          {exc && exc.status === "RESOLVED" && (
            <Button onClick={() => onClose(exc.id)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              关闭异常
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
