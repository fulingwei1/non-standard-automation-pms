/**
 * Stage Statistics Grid - 阶段统计卡片
 */
import { cn } from "../../lib/utils";
import { stageOptions } from "./constants";

export function StageStatsGrid({ assemblyAttrs, filterStage, setFilterStage }) {
  const stageStats = (stageOptions || []).map((stage) => {
    const items = (assemblyAttrs || []).filter(
      (a) => a.assembly_stage === stage.value
    );
    return {
      ...stage,
      total: items?.length,
      blocking: (items || []).filter((i) => i.is_blocking).length,
    };
  });

  return (
    <div className="grid grid-cols-6 gap-4">
      {(stageStats || []).map((stage) => {
        const Icon = stage.icon;
        return (
          <Card
            key={stage.value}
            className={cn(
              "cursor-pointer transition-all hover:shadow-md",
              filterStage === stage.value && "ring-2 ring-blue-500"
            )}
            onClick={() =>
              setFilterStage(
                filterStage === stage.value ? "all" : stage.value
              )
            }
          >
            <CardContent className="pt-4 pb-3">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center",
                    stage.color
                  )}
                >
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium">{stage.label}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">共 {stage.total} 项</span>
                <span className="text-red-600">{stage.blocking} 阻塞</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
