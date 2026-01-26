/**
 * 工时汇总组件 (Timesheet Summary)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function TimesheetSummary({ data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">本周工时</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center h-24">
          <div className="text-center">
            <p className="text-3xl font-bold">32.5</p>
            <p className="text-sm text-muted-foreground">小时 / 40小时</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
