/**
 * ECN列表组件 (ECN List)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function EcnList({ filter, limit = 5, data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">待处理ECN</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          ECN列表组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
