/**
 * 回款提醒组件
 * 显示需要催收的付款记录提醒
 */
import { motion } from 'framer-motion';
import { Bell } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '../ui';
import { cn } from '../../lib/utils';
import { fadeIn } from '../../lib/animations';

/**
 * 回款提醒组件
 * @param {object} props
 * @param {array} props.reminders - 提醒列表
 * @param {boolean} props.showReminders - 是否展开
 * @param {function} props.onToggle - 切换展开/收起
 */
export default function PaymentReminders({ reminders, showReminders, onToggle }) {
  if (reminders.length === 0) {
    return null;
  }

  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Bell className="w-5 h-5 text-amber-400" />
              回款提醒
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggle && onToggle()}
            >
              {showReminders ? '收起' : '展开'}
            </Button>
          </div>
        </CardHeader>
        {showReminders && (
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {(reminders || []).map((reminder) => (
                <div
                  key={reminder.id}
                  className={cn(
                    'p-3 rounded-lg border',
                    reminder.reminder_level === 'urgent'
                      ? 'bg-red-500/10 border-red-500/20'
                      : reminder.reminder_level === 'warning'
                      ? 'bg-amber-500/10 border-amber-500/20'
                      : 'bg-blue-500/10 border-blue-500/20'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">
                          {reminder.customer_name || '未知客户'}
                        </span>
                        <Badge
                          variant={
                            reminder.reminder_level === 'urgent'
                              ? 'destructive'
                              : reminder.reminder_level === 'warning'
                              ? 'default'
                              : 'secondary'
                          }
                        >
                          {reminder.is_overdue
                            ? `逾期${reminder.overdue_days}天`
                            : `还有${reminder.days_until_due}天到期`}
                        </Badge>
                      </div>
                      <div className="mt-1 text-sm text-slate-400">
                        {reminder.contract_code &&
                          `合同：${reminder.contract_code} | `}
                        {reminder.project_code &&
                          `项目：${reminder.project_code} | `}
                        未收金额：¥
                        {(reminder.unpaid_amount / 10000).toFixed(2)}万
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-white">
                        {reminder.due_date}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>
    </motion.div>
  );
}
