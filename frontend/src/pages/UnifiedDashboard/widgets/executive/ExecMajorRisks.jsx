/**
 * 高管视图 - 重大风险/问题
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { ShieldAlert } from 'lucide-react';

const levelColors = {
  CRITICAL: 'destructive',
  HIGH: 'destructive',
};

export default function ExecMajorRisks({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-red-500" />
          重大风险/问题
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无重大风险</p>
        ) : (
          <div className="space-y-2">
            {items.map((r, idx) => (
              <div key={idx} className="p-2 rounded-lg hover:bg-muted/50 border-l-2 border-red-400">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate flex-1">{r.risk_name}</p>
                  <Badge variant={levelColors[r.risk_level] || 'outline'} className="text-xs ml-2">
                    {r.risk_level}
                  </Badge>
                </div>
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>{r.project_name} ({r.project_code})</span>
                  <span>{r.risk_type}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
