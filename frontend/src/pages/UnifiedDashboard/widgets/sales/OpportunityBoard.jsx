/**
 * 商机看板组件 (Opportunity Board)
 */
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { opportunityApi } from '../../../../services/api/sales';

const stages = ['初步接触', '需求确认', '方案报价', '商务谈判', '赢单'];
const stageColors = ['bg-blue-50', 'bg-yellow-50', 'bg-orange-50', 'bg-purple-50', 'bg-green-50'];

export default function OpportunityBoard({ _view, data: propData }) {
  const [opps, setOpps] = useState([]);
  const [loading, setLoading] = useState(!propData);

  useEffect(() => {
    if (propData) { setOpps(propData); return; }
    opportunityApi.list({ page_size: 20 }).then(res => {
      setOpps(res.data?.items || res.data || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [propData]);

  if (loading) return (
    <Card><CardHeader className="pb-2"><CardTitle className="text-sm font-medium">商机看板</CardTitle></CardHeader>
      <CardContent><div className="text-sm text-muted-foreground text-center py-4">加载中...</div></CardContent></Card>
  );

  const grouped = {};
  stages.forEach(s => { grouped[s] = []; });
  opps.forEach(o => {
    const stage = o.stage || o.status || '初步接触';
    if (!grouped[stage]) grouped[stage] = [];
    grouped[stage].push(o);
  });

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">商机看板</CardTitle>
      </CardHeader>
      <CardContent>
        {opps.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">暂无商机</div>
        ) : (
          <div className="grid grid-cols-5 gap-1 text-xs">
            {stages.map((stage, si) => (
              <div key={stage} className={`${stageColors[si]} rounded p-1.5`}>
                <div className="font-medium mb-1">{stage} ({grouped[stage]?.length || 0})</div>
                {(grouped[stage] || []).slice(0, 3).map((o, i) => (
                  <div key={o.id || i} className="bg-white rounded p-1 mb-1 shadow-sm">
                    <div className="font-medium truncate">{o.name || o.title}</div>
                    <div className="text-muted-foreground">¥{(o.amount || 0).toLocaleString()}</div>
                    <div className="text-muted-foreground">{o.win_probability || o.probability || 0}%</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
