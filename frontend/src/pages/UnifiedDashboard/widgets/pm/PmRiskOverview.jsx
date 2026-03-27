/**
 * PM视图 - 活跃风险 TOP
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { AlertTriangle } from 'lucide-react';

const levelColors = {
  CRITICAL: 'destructive',
  HIGH: 'destructive',
  MEDIUM: 'outline',
  LOW: 'secondary',
};

export default function PmRiskOverview({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-orange-500" />
          活跃风险 TOP
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无活跃风险</p>
        ) : (
          <div className="space-y-2">
            {items.map((r, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50">
                <span className="text-xs text-muted-foreground w-6">{idx + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{r.risk_name}</p>
                  <p className="text-xs text-muted-foreground truncate">{r.project_name}</p>
                </div>
                <Badge variant={levelColors[r.risk_level] || 'default'} className="text-xs">
                  {r.risk_level}
                </Badge>
                <span className="text-xs font-mono text-muted-foreground w-8 text-right">{r.risk_score}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
