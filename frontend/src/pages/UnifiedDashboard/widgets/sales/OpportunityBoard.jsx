/**
 * 商机看板组件 (Opportunity Board)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function OpportunityBoard({ view, data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">商机看板</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground text-center py-8">
          商机看板组件 - 待实现
        </div>
      </CardContent>
    </Card>
  );
}
