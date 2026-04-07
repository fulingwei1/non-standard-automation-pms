

import { cn } from "../../lib/utils";

export function AlertsPanel({ alerts }) {
  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          实时预警
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {alerts?.length === 0 ? (
          <div className="text-sm text-slate-400">暂无预警数据</div>
        ) : (
          (alerts || []).map((alert, index) => (
            <div
              key={index}
              className={cn(
                "p-3 rounded-lg flex items-start gap-3",
                alert.type === "urgent"
                  ? "bg-red-500/10"
                  : alert.type === "warning"
                    ? "bg-amber-500/10"
                    : "bg-blue-500/10",
              )}
            >
              {alert.type === "urgent" ? (
                <Zap className="w-4 h-4 text-red-400 mt-0.5" />
              ) : alert.type === "warning" ? (
                <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-blue-400 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    "text-sm",
                    alert.type === "urgent"
                      ? "text-red-300"
                      : alert.type === "warning"
                        ? "text-amber-300"
                        : "text-blue-300",
                  )}
                >
                  {alert.message}
                </p>
                <p className="text-xs text-slate-500 mt-1">{alert.time}</p>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
