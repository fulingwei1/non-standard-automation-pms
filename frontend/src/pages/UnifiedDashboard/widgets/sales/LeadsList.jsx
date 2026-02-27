/**
 * 线索列表组件 (Leads List)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { leadApi } from '../../../../services/api/sales';

const statusColors = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  lost: 'bg-gray-100 text-gray-800',
};

export default function LeadsList({ limit = 5, data: propData }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setLeads(propData.slice(0, limit)); return; }
    leadApi.list({ page_size: limit }).then(res => {
      setLeads(res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData, limit]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">最新线索</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-muted-foreground text-center py-4">加载中...</div>
        ) : leads.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无线索</div>
        ) : (
          <div className="space-y-2">
            {leads.map((lead, i) => (
              <div key={lead.id || i} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{lead.name || lead.company_name}</div>
                  <div className="text-xs text-muted-foreground">{lead.source || '未知来源'}</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${statusColors[lead.status] || 'bg-gray-100 text-gray-800'}`}>
                    {lead.status || '-'}
                  </span>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {lead.created_at ? new Date(lead.created_at).toLocaleDateString() : ''}
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
