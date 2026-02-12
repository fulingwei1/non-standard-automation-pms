/**
 * 线索列表组件 (Leads List)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function LeadsList({ limit: _limit = 5, data: _data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">最新线索</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          线索列表组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
