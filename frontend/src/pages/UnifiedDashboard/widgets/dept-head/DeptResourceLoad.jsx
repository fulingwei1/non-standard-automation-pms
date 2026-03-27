/**
 * 部门负责人视图 - 资源负荷
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';
import { Badge } from '../../../../components/ui/badge';
import { Users } from 'lucide-react';
import { cn } from '../../../../lib/utils';

export default function DeptResourceLoad({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Users className="h-4 w-4" />
          部门资源负荷
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无数据</p>
        ) : (
          <div className="space-y-2">
            {items.map((r, idx) => (
              <div key={idx} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50">
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm">成员 #{r.user_id}</span>
                    <span className="text-xs text-muted-foreground">{r.project_count} 个项目</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Progress
                      value={Math.min(r.total_allocation, 150)}
                      max={150}
                      className={cn("h-2 flex-1", r.overloaded && "[&>div]:bg-red-500")}
                    />
                    <Badge variant={r.overloaded ? 'destructive' : 'secondary'} className="text-xs">
                      {r.total_allocation}%
                    </Badge>
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
