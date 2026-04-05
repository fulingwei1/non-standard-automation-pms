/**
 * PM视图 - 项目健康度一览
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';
import { Badge } from '../../../../components/ui/badge';

const healthLabels = { H1: '健康', H2: '关注', H3: '风险', H4: '严重' };
const healthColors = { H1: 'bg-green-500', H2: 'bg-yellow-500', H3: 'bg-orange-500', H4: 'bg-red-500' };
const healthBadge = { H1: 'default', H2: 'secondary', H3: 'outline', H4: 'destructive' };

export default function PmProjectHealth({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">项目健康度一览</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无项目</p>
        ) : (
          <div className="space-y-3">
            {items.map((p) => (
              <div key={p.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50">
                <div className={`w-2 h-2 rounded-full ${healthColors[p.health] || 'bg-gray-400'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium truncate">{p.project_name}</span>
                    <Badge variant={healthBadge[p.health] || 'default'} className="text-xs ml-2">
                      {healthLabels[p.health] || p.health}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Progress value={p.progress_pct} className="h-1.5 flex-1" />
                    <span className="text-xs text-muted-foreground w-10 text-right">{p.progress_pct}%</span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-muted-foreground">{p.project_code}</span>
                    <span className="text-xs text-muted-foreground">{p.current_stage}</span>
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
