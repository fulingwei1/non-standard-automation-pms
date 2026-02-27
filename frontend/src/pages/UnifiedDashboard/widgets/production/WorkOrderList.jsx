/**
 * 工单列表组件 (Work Order List)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { productionApi } from '../../../../services/api/production';

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
};

export default function WorkOrderList({ filter, data: propData }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setOrders(propData); return; }
    productionApi.workOrders.list({ page_size: 10, ...filter }).then(res => {
      setOrders(res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData, filter]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">工单列表</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground text-center py-4">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无工单</div>
        ) : (
          <div className="space-y-2">
            {orders.map((o, i) => (
              <div key={o.id || i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{o.order_no || o.work_order_no || `WO-${o.id}`}</div>
                  <div className="text-xs text-muted-foreground">
                    {o.type || o.order_type || '-'} · {o.assignee || o.worker_name || '-'}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${statusColors[o.status] || 'bg-gray-100 text-gray-800'}`}>
                    {o.status || '-'}
                  </span>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {o.due_date ? new Date(o.due_date).toLocaleDateString() : '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
