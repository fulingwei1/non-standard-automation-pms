/**
 * 成员视图 - 参与项目进度
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Progress } from '../../../../components/ui/progress';
import { Badge } from '../../../../components/ui/badge';
import { FolderOpen } from 'lucide-react';

const healthColors = { H1: 'bg-green-500', H2: 'bg-yellow-500', H3: 'bg-orange-500', H4: 'bg-red-500' };

export default function MemberProjectProgress({ data }) {
  const items = data?.items || [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <FolderOpen className="h-4 w-4" />
          参与项目进度
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">暂无参与项目</p>
        ) : (
          <div className="space-y-3">
            {items.map((p) => (
              <div key={p.id} className="p-2 rounded-lg hover:bg-muted/50">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${healthColors[p.health] || 'bg-gray-400'}`} />
                  <span className="text-sm font-medium truncate flex-1">{p.project_name}</span>
                  <Badge variant="outline" className="text-xs">{p.my_role}</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={p.progress_pct} className="h-1.5 flex-1" />
                  <span className="text-xs text-muted-foreground w-10 text-right">{p.progress_pct}%</span>
                </div>
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>分配: {p.my_allocation}%</span>
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
