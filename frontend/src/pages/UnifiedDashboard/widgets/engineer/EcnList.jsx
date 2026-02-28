/**
 * ECN列表组件 (ECN List)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { ecnApi } from '../../../../services/api/ecn';

const statusColors = {
  draft: 'bg-gray-100 text-gray-800',
  submitted: 'bg-blue-100 text-blue-800',
  evaluating: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
};

export default function EcnList({ filter, limit = 5, data: propData }) {
  const [ecns, setEcns] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setEcns(propData.slice(0, limit)); return; }
    ecnApi.list({ page_size: limit, ...filter }).then(res => {
      setEcns(res.data?.items || res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData, limit, filter]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">待处理ECN</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground text-center py-4">加载中...</div>
        ) : ecns.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无ECN</div>
        ) : (
          <div className="space-y-2">
            {ecns.map((ecn, i) => (
              <div key={ecn.id || i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{ecn.ecn_no || ecn.ecn_number || `ECN-${ecn.id}`}</div>
                  <div className="text-xs text-muted-foreground truncate">{ecn.title || '-'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{ecn.change_type || '-'}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${statusColors[ecn.status] || 'bg-gray-100 text-gray-800'}`}>
                    {ecn.status || '-'}
                  </span>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {ecn.submitted_at || ecn.created_at ? new Date(ecn.submitted_at || ecn.created_at).toLocaleDateString() : '-'}
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
