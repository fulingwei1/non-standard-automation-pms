/**
 * 客户列表组件 (Customer List)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { customerApi } from '../../../../services/api/crm';

const statusMap = {
  active: { label: '活跃', cls: 'bg-green-100 text-green-800' },
  inactive: { label: '不活跃', cls: 'bg-gray-100 text-gray-800' },
  potential: { label: '潜在', cls: 'bg-blue-100 text-blue-800' },
};

export default function CustomerList({ limit = 5, data: propData }) {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setCustomers(propData.slice(0, limit)); return; }
    customerApi.list({ page_size: limit }).then(res => {
      setCustomers(res.data?.items || res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData, limit]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">重点客户</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground text-center py-4">加载中...</div>
        ) : customers.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无客户</div>
        ) : (
          <div className="space-y-2">
            {(customers || []).map((c, i) => (
              <div key={c.id || i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{c.name || c.company_name}</div>
                  <div className="text-xs text-muted-foreground">{c.contact_person || c.contact_name || '-'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {c.last_interaction ? new Date(c.last_interaction).toLocaleDateString() : '-'}
                  </span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${statusMap[c.status]?.cls || 'bg-gray-100 text-gray-800'}`}>
                    {statusMap[c.status]?.label || c.status || '-'}
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
