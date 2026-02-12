/**
 * 工单列表组件 (Work Order List)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function WorkOrderList({ filter: _filter, data: _data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">工单列表</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          工单列表组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
