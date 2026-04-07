

import { cn } from "../../lib/utils";

export function DepartmentPerformance({ data }) {
  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Users className="w-5 h-5" />
          部门绩效
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data?.length === 0 ? (
          <div className="text-sm text-slate-400">暂无部门绩效数据</div>
        ) : (
          (data || []).map((dept, index) => {
            const onTimeValue = Number.isFinite(dept.onTime) ? dept.onTime : null;
            return (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white">{dept.name}</span>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-slate-400">{dept.projects} 项目</span>
                    <span
                      className={cn(
                        onTimeValue === null
                          ? "text-slate-400"
                          : onTimeValue >= 90
                            ? "text-emerald-400"
                            : onTimeValue >= 80
                              ? "text-amber-400"
                              : "text-red-400",
                      )}
                    >
                      准时率 {onTimeValue === null ? "--" : `${onTimeValue}%`}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={dept.utilization} className="h-2 flex-1" />
                  <span
                    className={cn(
                      "text-xs font-medium w-10 text-right",
                      dept.utilization >= 90
                        ? "text-amber-400"
                        : "text-emerald-400",
                    )}
                  >
                    {dept.utilization}%
                  </span>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
