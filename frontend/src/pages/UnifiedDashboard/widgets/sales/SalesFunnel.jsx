/**
 * 销售漏斗组件 (Sales Funnel)
 * 显示销售管道各阶段的数据
 */

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { cn } from '../../../../lib/utils';

const defaultFunnelData = [
  { stage: '线索', count: 150, value: '¥15,000,000', color: 'bg-blue-500' },
  { stage: '商机', count: 80, value: '¥8,000,000', color: 'bg-cyan-500' },
  { stage: '客户', count: 45, value: '¥4,500,000', color: 'bg-green-500' },
];

export default function SalesFunnel({ view, data }) {
  const [funnelData, setFunnelData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setTimeout(() => {
      setFunnelData(data?.funnel || defaultFunnelData);
      setLoading(false);
    }, 500);
  }, [data]);

  const maxCount = Math.max(...funnelData.map(d => d.count));

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
            {funnelData.map((item, index) => (
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
