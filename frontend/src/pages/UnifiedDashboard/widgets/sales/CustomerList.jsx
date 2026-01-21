/**
 * 客户列表组件 (Customer List)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function CustomerList({ limit = 5, data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">重点客户</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          客户列表组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
