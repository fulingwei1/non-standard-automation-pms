



import { cn, formatDate } from "../../lib/utils";
import { statusConfigs, levelConfigs, TERMINAL_STATUSES } from "./constants";

export default function AlertTable({
  loading,
  filteredAlerts,
  isUrgent,
  onViewDetail,
  onAcknowledge,
  onOpenHandle,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardHeader>
        <CardTitle className="text-slate-200">缺料预警列表</CardTitle>
        <CardDescription className="text-slate-400">
          共 {filteredAlerts.length} 个缺料预警
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无缺料预警</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-slate-700">
                <TableHead className="text-slate-400">项目</TableHead>
                <TableHead className="text-slate-400">物料编码</TableHead>
                <TableHead className="text-slate-400">物料名称</TableHead>
                <TableHead className="text-slate-400">需求数量</TableHead>
                <TableHead className="text-slate-400">可用数量</TableHead>
                <TableHead className="text-slate-400">缺料数量</TableHead>
                <TableHead className="text-slate-400">需求日期</TableHead>
                <TableHead className="text-slate-400">预警级别</TableHead>
                <TableHead className="text-slate-400">状态</TableHead>
                <TableHead className="text-right text-slate-400">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAlerts.map((alert) => {
                const urgent = isUrgent(alert);
                return (
                  <TableRow key={alert.id} className="border-slate-700">
                    <TableCell className="font-medium text-slate-200">
                      {alert.project_name || "-"}
                    </TableCell>
                    <TableCell className="font-mono text-sm text-slate-300">
                      {alert.material_code}
                    </TableCell>
                    <TableCell className="text-slate-200">
                      {alert.material_name}
                    </TableCell>
                    <TableCell className="text-slate-300">
                      {alert.required_qty || 0}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-slate-300",
                        alert.available_qty < alert.required_qty && "text-red-400",
                      )}
                    >
                      {alert.available_qty || 0}
                    </TableCell>
                    <TableCell className="font-medium text-red-400">
                      {alert.shortage_qty || 0}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-300">
                          {alert.required_date ? formatDate(alert.required_date) : "-"}
                        </span>
                        {urgent && (
                          <Badge className="bg-red-500 text-xs">
                            <AlertTriangle className="w-3 h-3 mr-1" />
                            紧急
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={levelConfigs[alert.alert_level]?.color || "bg-slate-500"}
                      >
                        {levelConfigs[alert.alert_level]?.label || alert.alert_level}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={statusConfigs[alert.status]?.color || "bg-slate-500"}
                      >
                        {statusConfigs[alert.status]?.label || alert.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewDetail(alert.id)}
                          className="text-slate-400 hover:text-slate-200"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {alert.status === "PENDING" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onAcknowledge(alert.id)}
                            className="text-slate-400 hover:text-slate-200"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </Button>
                        )}
                        {!TERMINAL_STATUSES.has(alert.status) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onOpenHandle(alert)}
                            className="text-slate-400 hover:text-slate-200"
                          >
                            <Package className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
