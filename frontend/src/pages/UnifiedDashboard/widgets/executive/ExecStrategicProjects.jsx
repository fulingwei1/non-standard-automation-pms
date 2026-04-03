/**
 * 高管视图 - 战略项目进度
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';
import { Badge } from '../../../../components/ui/badge';
import { Target } from 'lucide-react';

const healthBadge = { H1: 'default', H2: 'secondary', H3: 'outline', H4: 'destructive' };
const healthLabel = { H1: '健康', H2: '关注', H3: '风险', H4: '严重' };

export default function ExecStrategicProjects({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Target className="h-4 w-4" />
          战略项目进度
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无战略项目</p>
        ) : (
          <div className="space-y-3">
            {items.map((p) => (
              <div key={p.id} className="p-2 rounded-lg hover:bg-muted/50">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium truncate flex-1">{p.project_name}</span>
                  <Badge variant={healthBadge[p.health]} className="text-xs ml-2">
                    {healthLabel[p.health] || p.health}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={p.progress_pct} className="h-1.5 flex-1" />
                  <span className="text-xs text-muted-foreground w-10 text-right">{p.progress_pct}%</span>
                </div>
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>PM: {p.pm_name || '-'}</span>
                  <span>合同: {(p.contract_amount / 10000).toFixed(1)}万</span>
                  <span>{p.planned_end_date || '-'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
