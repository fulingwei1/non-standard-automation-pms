/**
 * Reminder Settings Dialog
 */

import { CheckCircle2, AlertTriangle } from "lucide-react";
import {
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../../components/ui";
import { formatDate } from "../../lib/utils";

export default function ReminderDialog({
  open,
  onOpenChange,
  reminder,
  onAcknowledge,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>物料成本更新提醒设置</DialogTitle>
          <DialogDescription>
            配置定期更新提醒，系统将自动提醒您更新物料成本信息
          </DialogDescription>
        </DialogHeader>

        {reminder && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>提醒间隔（天）</Label>
                <Input
                  type="number"
                  value={reminder.reminder_interval_days || 30}
                  disabled
                  className="bg-slate-800"
                />
                <div className="text-xs text-slate-400 mt-1">
                  当前设置为每 {reminder.reminder_interval_days || 30}{" "}
                  天提醒一次
                </div>
              </div>
              <div>
                <Label>下次提醒日期</Label>
                <Input
                  value={
                    reminder.next_reminder_date
                      ? formatDate(reminder.next_reminder_date)
                      : "-"
                  }
                  disabled
                  className="bg-slate-800"
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={reminder.is_enabled}
                disabled
                className="rounded"
              />
              <Label>启用提醒</Label>
            </div>

            {reminder.is_due && (
              <div className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />
                  <div>
                    <div className="font-medium text-amber-400 mb-1">
                      提醒已到期
                    </div>
                    <div className="text-sm text-slate-300">
                      请及时更新物料成本信息，更新后点击"确认提醒"按钮。
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {reminder?.is_due && (
            <Button onClick={onAcknowledge}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              我已更新，确认提醒
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
