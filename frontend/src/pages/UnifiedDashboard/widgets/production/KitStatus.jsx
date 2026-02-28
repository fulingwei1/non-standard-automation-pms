/**
 * 齐套状态组件 (Kit Status)
 */
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';

const defaultKitData = [
  { project: 'PJ250101-001', status: 'ready', rate: 100 },
  { project: 'PJ250101-002', status: 'partial', rate: 75 },
  { project: 'PJ250101-003', status: 'shortage', rate: 45 },
];

export default function KitStatus({ view: _view, data }) {
  const kitData = data?.kits || defaultKitData;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">齐套状态</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(kitData || []).map(kit => (
            <div key={kit.project} className="flex items-center justify-between">
              <span className="text-sm">{kit.project}</span>
              <Badge variant={kit.status === 'ready' ? 'default' : kit.status === 'partial' ? 'secondary' : 'destructive'}>
                {kit.rate}%
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
