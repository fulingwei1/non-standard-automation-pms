/**
 * 生产看板组件 (Production Board)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function ProductionBoard({ view: _view, data: _data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">生产看板</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          生产看板组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
