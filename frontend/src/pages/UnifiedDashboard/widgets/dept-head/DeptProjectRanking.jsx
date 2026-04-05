/**
 * 部门负责人视图 - 项目绩效排行
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';
import { Badge } from '../../../../components/ui/badge';
import { Trophy } from 'lucide-react';

const healthLabel = { H1: '健康', H2: '关注', H3: '风险', H4: '严重' };
const healthBadge = { H1: 'default', H2: 'secondary', H3: 'outline', H4: 'destructive' };

export default function DeptProjectRanking({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Trophy className="h-4 w-4 text-yellow-500" />
          部门项目绩效排行
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无数据</p>
        ) : (
          <div className="space-y-3">
            {items.map((p, idx) => (
              <div key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50">
                <span className="text-sm font-bold text-muted-foreground w-6">{idx + 1}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate">{p.project_name}</span>
                    <Badge variant={healthBadge[p.health]} className="text-xs ml-2">
                      {healthLabel[p.health] || p.health}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={p.progress_pct} className="h-1.5 flex-1" />
                    <span className="text-xs text-muted-foreground w-10 text-right">{p.progress_pct}%</span>
                  </div>
                  <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                    <span>PM: {p.pm_name || '-'}</span>
                    <span>预算执行: {p.budget_exec_rate}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
