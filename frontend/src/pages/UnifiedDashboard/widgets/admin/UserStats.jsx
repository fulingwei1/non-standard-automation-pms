/**
 * 用户统计组件 (User Stats)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';

export default function UserStats({ data: _data }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">用户统计</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold">256</p>
            <p className="text-xs text-muted-foreground">总用户</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">48</p>
            <p className="text-xs text-muted-foreground">在线用户</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">12</p>
            <p className="text-xs text-muted-foreground">新增本月</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">15</p>
            <p className="text-xs text-muted-foreground">角色数</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
