/**
 * 销售漏斗组件 (Sales Funnel)
 * 显示销售管道各阶段的数据
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { salesStatisticsApi } from '../../../../services/api/sales';
import { cn } from '../../../../lib/utils';

const defaultFunnelData = [
  { stage: '线索', count: 0, value: '¥0', color: 'bg-blue-500' },
  { stage: '商机', count: 0, value: '¥0', color: 'bg-cyan-500' },
  { stage: '客户', count: 0, value: '¥0', color: 'bg-green-500' },
];

const STAGE_COLORS = {
  '线索': 'bg-blue-500',
  '商机': 'bg-cyan-500',
  '客户': 'bg-green-500',
};

export default function SalesFunnel({ view: _view, data }) {
  const [funnelData, setFunnelData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (data?.funnel) {
      setFunnelData(data.funnel);
      setLoading(false);
      return;
    }
    const loadFunnel = async () => {
      setLoading(true);
      try {
        const res = await salesStatisticsApi.funnel();
        const items = res.data?.items || res.data || res;
        if (Array.isArray(items) && items?.length > 0) {
          setFunnelData((items || []).map(item => ({
            ...item,
            color: STAGE_COLORS[item.stage] || 'bg-blue-500',
          })));
        } else {
          setFunnelData(defaultFunnelData);
        }
      } catch {
        setFunnelData(defaultFunnelData);
      } finally {
        setLoading(false);
      }
    };
    loadFunnel();
  }, [data]);

  const maxCount = Math.max(...(funnelData || []).map(d => d.count));

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">销售漏斗</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="h-48 bg-muted/50 rounded-lg animate-pulse" />
        ) : (
          <div className="space-y-3">
            {(funnelData || []).map((item) => (
              <div key={item.stage} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>{item.stage}</span>
                  <span className="text-muted-foreground">{item.count} | {item.value}</span>
                </div>
                <div className="h-6 bg-muted rounded-full overflow-hidden">
                  <div
                    className={cn('h-full rounded-full transition-all', item.color)}
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
