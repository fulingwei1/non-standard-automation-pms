/**
 * PM视图 - 资源冲突告警
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Users } from 'lucide-react';

export default function PmResourceConflict({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Users className="h-4 w-4 text-red-500" />
          资源冲突告警
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无资源冲突</p>
        ) : (
          <div className="space-y-2">
            {items.map((r, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50">
                <div>
                  <p className="text-sm font-medium">用户 #{r.user_id}</p>
                  <p className="text-xs text-muted-foreground">参与 {r.project_count} 个项目</p>
                </div>
                <Badge variant={r.total_allocation > 150 ? 'destructive' : 'outline'} className="text-xs">
                  分配 {r.total_allocation}%
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
