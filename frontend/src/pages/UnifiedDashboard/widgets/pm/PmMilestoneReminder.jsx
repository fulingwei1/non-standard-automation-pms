/**
 * PM视图 - 近期里程碑提醒
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { CalendarClock, Flag } from 'lucide-react';

export default function PmMilestoneReminder({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <CalendarClock className="h-4 w-4" />
          近期里程碑提醒
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无近期里程碑</p>
        ) : (
          <div className="space-y-2">
            {items.map((ms, idx) => (
              <div key={idx} className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted/50">
                {ms.is_key && <Flag className="h-4 w-4 text-orange-500 mt-0.5 shrink-0" />}
                {!ms.is_key && <div className="w-4" />}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{ms.milestone_name}</p>
                  <p className="text-xs text-muted-foreground truncate">{ms.project_name}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-xs">{ms.planned_date}</p>
                  <Badge variant={ms.days_remaining <= 3 ? 'destructive' : ms.days_remaining <= 7 ? 'outline' : 'secondary'} className="text-xs">
                    {ms.days_remaining}天
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
