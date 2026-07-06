/**
 * 用户统计组件 (User Stats)
 *
 * 之前这里是完全写死的假数据（256/48/12/15），跟旁边"关键指标"卡片
 * 算出来的真实用户数/角色数对不上。现在读同一个 /dashboard/stats/admin
 * 接口，跟"关键指标"共用一个数据源，不会再出现两张卡片各算一遍、
 * 数字却不一致的问题。"在线用户"这个指标系统里没有任何会话/心跳追踪
 * 基础设施支撑，换成"本月活跃"（本月登录过的用户数）。
 */
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import api from '../../../../services/api';

const defaultStats = {
  users: 0,
  new_this_month: 0,
  active_this_month: 0,
  roles: 0,
};

export default function UserStats({ data }) {
  const [stats, setStats] = useState(defaultStats);

  useEffect(() => {
    const statsList = data?.data?.stats ?? data?.stats;
    if (statsList) {
      const byKey = Object.fromEntries(statsList.map((s) => [s.key, s.value]));
      setStats({ ...defaultStats, ...byKey });
      return;
    }

    let active = true;
    api.get('/dashboard/stats/admin')
      .then((response) => {
        if (!active) {return;}
        const statsList2 = response.data?.data?.stats ?? response.data?.stats;
        if (statsList2) {
          const byKey = Object.fromEntries(statsList2.map((s) => [s.key, s.value]));
          setStats({ ...defaultStats, ...byKey });
        }
      })
      .catch(() => {
        if (active) {setStats(defaultStats);}
      });

    return () => {
      active = false;
    };
  }, [data]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">用户统计</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold">{stats.users}</p>
            <p className="text-xs text-muted-foreground">总用户</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{stats.active_this_month}</p>
            <p className="text-xs text-muted-foreground">本月活跃</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{stats.new_this_month}</p>
            <p className="text-xs text-muted-foreground">新增本月</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold">{stats.roles}</p>
            <p className="text-xs text-muted-foreground">角色数</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
