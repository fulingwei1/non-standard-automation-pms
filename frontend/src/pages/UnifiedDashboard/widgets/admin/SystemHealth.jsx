/**
 * 系统健康组件 (System Health)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

export default function SystemHealth({ data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">系统状态</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">API 服务</span>
            <Badge variant="default" className="gap-1">
              <CheckCircle2 className="h-3 w-3" /> 正常
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">数据库</span>
            <Badge variant="default" className="gap-1">
              <CheckCircle2 className="h-3 w-3" /> 正常
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm">消息队列</span>
            <Badge variant="secondary" className="gap-1">
              <AlertTriangle className="h-3 w-3" /> 延迟
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
