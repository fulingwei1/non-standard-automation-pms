/**
 * 营收图表组件 (Revenue Chart)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function RevenueChart({ view, data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">营收趋势</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          营收图表组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
