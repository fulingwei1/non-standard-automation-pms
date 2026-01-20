import { Card, CardHeader, CardTitle, CardContent } from "../../components/ui";
import { AlertTriangle } from "lucide-react";

export default function AlertsTab() {
  return (
    <Card className="bg-surface-50 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-primary" />
          预警监控
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 预警信息 - 需要从API获取数据 */}
          <div className="text-center py-8 text-slate-500">
            <p>预警信息数据需要从API获取</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
