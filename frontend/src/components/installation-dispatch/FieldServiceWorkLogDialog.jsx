import { ClipboardCheck, Loader2 } from "lucide-react";

import { Badge, Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, Input, Textarea } from "../ui";
import { formatDate } from "../../lib/utils";
import { getDispatchStatusLabel, getInstallationTypeLabel } from "./index";

export default function FieldServiceWorkLogDialog({
  open,
  onOpenChange,
  workLogDate,
  onWorkLogDateChange,
  context,
  contextLoading = false,
  logData,
  onLogDataChange,
  onSubmit,
  submitting = false,
}) {
  const items = context?.items || [];
  const hasSubmitted = context?.has_submitted_log;
  const disabled = submitting || contextLoading || items.length === 0 || hasSubmitted;

  const updateField = (field, value) => {
    onLogDataChange({ ...logData, [field]: value });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>今日外出日志</DialogTitle>
          <DialogDescription>提交当天外出服务工作记录</DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">工作日期</label>
              <Input
                type="date"
                value={workLogDate}
                onChange={(event) => onWorkLogDateChange(event.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium">工时</label>
              <Input
                type="number"
                min="0"
                max="24"
                step="0.5"
                value={logData.work_hours || ""}
                onChange={(event) => updateField("work_hours", event.target.value)}
                placeholder="小时"
              />
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">关联派工单</label>
              {contextLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            </div>
            {items.length === 0 ? (
              <div className="rounded-md border p-4 text-sm text-muted-foreground">
                当天没有负责的外出派工单
              </div>
            ) : (
              <div className="space-y-2">
                {items.map((item) => (
                  <div key={item.dispatch_order_id} className="rounded-md border p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{item.order_no}</span>
                      <Badge variant="secondary">{getDispatchStatusLabel(item.status)}</Badge>
                      <Badge variant="outline">{getInstallationTypeLabel(item.task_type)}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-muted-foreground">
                      {item.project_name || "-"} / {item.machine_name || "未关联设备"}
                    </div>
                    <div className="mt-1 text-sm">
                      {item.task_title} · {formatDate(item.scheduled_date)}
                      {item.progress !== undefined ? ` · ${item.progress}%` : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="text-sm font-medium">今日进展</label>
            <Textarea
              value={logData.today_progress || ""}
              onChange={(event) => updateField("today_progress", event.target.value)}
              rows={3}
              placeholder="完成了哪些现场工作"
            />
          </div>
          <div>
            <label className="text-sm font-medium">现场问题</label>
            <Textarea
              value={logData.issues_found || ""}
              onChange={(event) => updateField("issues_found", event.target.value)}
              rows={2}
              placeholder="没有问题可填暂无"
            />
          </div>
          <div>
            <label className="text-sm font-medium">下一步</label>
            <Textarea
              value={logData.next_plan || ""}
              onChange={(event) => updateField("next_plan", event.target.value)}
              rows={2}
              placeholder="后续计划"
            />
          </div>

          {hasSubmitted && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
              当天工作日志已提交
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} disabled={disabled}>
            <ClipboardCheck className="mr-2 h-4 w-4" />
            提交日志
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
