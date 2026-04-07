

import { PRIORITY_CONFIG } from "./constants";

export default function PriorityPanel({ priorityDistribution, stats }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-amber-400" />
          优先级管理
        </CardTitle>
        <CardDescription>按优先级分布识别资源倾斜，避免高优工单堆积。</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {priorityDistribution.map((item) => {
          const config = PRIORITY_CONFIG[item.priority];
          const progressColor =
            item.priority === "URGENT"
              ? "danger"
              : item.priority === "HIGH"
                ? "warning"
                : "primary";

          return (
            <div key={item.priority} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <Badge className={config.badgeClass}>{config.label}</Badge>
                <span className="text-slate-300">
                  {item.count} 单 ({item.percent.toFixed(1)}%)
                </span>
              </div>
              <Progress value={item.percent} color={progressColor} />
            </div>
          );
        })}

        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-300">
          高优先级（高+紧急）共 {stats.highPriority} 单，建议每日站会优先过单。
        </div>
      </CardContent>
    </Card>
  );
}
