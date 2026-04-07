/**
 * Shortage Alerts Table - 缺料预警明细
 */






import { alertLevelConfig } from "./constants";

export default function ShortageAlerts({ alerts }) {
  if (!alerts || !alerts.items || !alerts.items?.length) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          缺料预警明细
          <Badge variant="outline" className="ml-2">
            {alerts.total} 条
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>预警级别</TableHead>
              <TableHead>项目</TableHead>
              <TableHead>物料</TableHead>
              <TableHead>装配阶段</TableHead>
              <TableHead>缺料数量</TableHead>
              <TableHead>是否阻塞</TableHead>
              <TableHead>响应截止</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(alerts.items || []).map((alert) => {
              const config =
                alertLevelConfig[alert.alert_level] || alertLevelConfig.L4;
              return (
                <TableRow key={alert.shortage_id}>
                  <TableCell>
                    <Badge className={config.color}>{config.label}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{alert.project_name}</div>
                    {alert.machine_no &&
                  <div className="text-xs text-slate-500">
                        {alert.machine_no}
                  </div>
                  }
                  </TableCell>
                  <TableCell>
                    <div>{alert.material_name}</div>
                    <div className="text-xs text-slate-500">
                      {alert.material_code}
                    </div>
                  </TableCell>
                  <TableCell>{alert.stage_name}</TableCell>
                  <TableCell className="text-red-600 font-medium">
                    {alert.shortage_qty}
                  </TableCell>
                  <TableCell>
                    {alert.is_blocking ?
                  <XCircle className="w-5 h-5 text-red-500" /> :

                  <CheckCircle2 className="w-5 h-5 text-slate-300" />
                  }
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(alert.response_deadline).toLocaleString()}
                  </TableCell>
                </TableRow>);

            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
