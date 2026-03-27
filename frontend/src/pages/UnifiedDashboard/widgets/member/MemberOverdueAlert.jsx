/**
 * 成员视图 - 逾期任务告警
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { AlertCircle } from 'lucide-react';

export default function MemberOverdueAlert({ data }) {
  const items = data?.items || [];

  return (
    <Card className={items.length > 0 ? 'border-red-200' : ''}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertCircle className={`h-4 w-4 ${items.length > 0 ? 'text-red-500' : 'text-muted-foreground'}`} />
          逾期任务告警
          {items.length > 0 && (
            <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded-full">{items.length}</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-green-600 text-center py-4">没有逾期任务</p>
        ) : (
          <div className="space-y-2">
            {items.map((t, idx) => (
              <div key={idx} className="p-2 rounded-lg bg-red-50 dark:bg-red-950/20">
                <p className="text-sm font-medium">{t.task_name}</p>
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>{t.project_name}</span>
                  <span className="text-red-600">截止: {t.plan_end}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
