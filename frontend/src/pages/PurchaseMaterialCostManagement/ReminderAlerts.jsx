/**
 * Reminder Alert Banner and Info Card Components
 */

import { motion } from "framer-motion";
import {
  CheckCircle2,
  Bell,
  AlertTriangle,
  Settings,
} from "lucide-react";
import {
  Card,
  CardContent,
  Button,
} from "../../components/ui";
import { formatDate } from "../../lib/utils";

export function ReminderDueAlert({ reminder, onAcknowledge, onOpenSettings }) {
  if (!reminder || !reminder.is_due) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-4 mb-6"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="font-medium text-amber-400 mb-1">
            物料成本更新提醒
          </div>
          <div className="text-sm text-slate-300 mb-3">
            距离上次更新已超过 {reminder.reminder_interval_days}{" "}
            天，请及时更新物料成本信息，确保报价成本准确性。
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={onAcknowledge}>
              <CheckCircle2 className="h-4 w-4 mr-2" />
              我已更新，确认提醒
            </Button>
            <Button size="sm" variant="outline" onClick={onOpenSettings}>
              <Settings className="h-4 w-4 mr-2" />
              设置提醒
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function ReminderInfoCard({ reminder, onOpenSettings }) {
  if (!reminder || reminder.is_due || reminder.days_until_next === null) {
    return null;
  }

  return (
    <Card className="mb-6 border-blue-500/30 bg-blue-900/10">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell className="h-5 w-5 text-blue-400" />
            <div>
              <div className="font-medium text-blue-400">下次更新提醒</div>
              <div className="text-sm text-slate-400">
                距离下次提醒还有{" "}
                <strong className="text-blue-300">
                  {reminder.days_until_next}
                </strong>{" "}
                天
                {reminder.next_reminder_date &&
                  ` (${formatDate(reminder.next_reminder_date)})`}
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenSettings}
          >
            <Settings className="h-4 w-4 mr-2" />
            设置
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
