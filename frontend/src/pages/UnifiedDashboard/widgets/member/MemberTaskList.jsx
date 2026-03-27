/**
 * 成员视图 - 我的任务
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { CheckSquare } from 'lucide-react';
import { cn } from '../../../../lib/utils';

const statusConfig = {
  TODO: { label: '待办', variant: 'secondary' },
  IN_PROGRESS: { label: '进行中', variant: 'default' },
  BLOCKED: { label: '阻塞', variant: 'destructive' },
};

export default function MemberTaskList({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <CheckSquare className="h-4 w-4" />
          我的任务
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无待办任务</p>
        ) : (
          <div className="space-y-2">
            {items.map((t, idx) => {
              const config = statusConfig[t.status] || statusConfig.TODO;
              return (
                <div
                  key={idx}
                  className={cn(
                    "p-2 rounded-lg hover:bg-muted/50",
                    t.overdue && "border-l-2 border-red-400"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium truncate flex-1">{t.task_name}</span>
                    <Badge variant={config.variant} className="text-xs ml-2">{config.label}</Badge>
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                    <span className="truncate">{t.project_name}</span>
                    <span>{t.plan_end || '-'}</span>
                  </div>
                  {t.overdue && (
                    <p className="text-xs text-red-500 mt-1">已逾期</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
