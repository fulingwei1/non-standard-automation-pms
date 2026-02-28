/**
 * 生产看板组件 (Production Board)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { productionApi } from '../../../../services/api/production';

const statusColors = {
  pending: 'text-gray-600',
  in_progress: 'text-blue-600',
  completed: 'text-green-600',
  delayed: 'text-red-600',
};

export default function ProductionBoard({ _view, data: propData }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setItems(propData); return; }
    productionApi.productionPlans.list({ page_size: 10 }).then(res => {
      setItems(res.data?.items || res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">生产看板</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground text-center py-4">加载中...</div>
        ) : items?.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无生产计划</div>
        ) : (
          <div className="space-y-2">
            {(items || []).map((item, i) => (
              <div key={item.id || i} className="text-sm border-b pb-2 last:border-0">
                <div className="flex justify-between items-center">
                  <span className="font-medium truncate flex-1">{item.name || item.title || item.plan_name}</span>
                  <span className={`text-xs ${statusColors[item.status] || 'text-gray-600'}`}>
                    {item.status || '-'}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="text-xs text-muted-foreground">{item.current_stage || item.stage || '-'}</div>
                  <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                    <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${item.progress || 0}%` }} />
                  </div>
                  <span className="text-xs text-muted-foreground">{item.progress || 0}%</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
