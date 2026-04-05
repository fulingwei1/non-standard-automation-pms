/**
 * Stage Progress Visualization - 装配阶段齐套率
 */
import {
  PlayCircle,
  Package,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { stageIcons, getKitRateColor } from "./constants";

export default function StageProgress({ stageStats }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <PlayCircle className="w-5 h-5" />
          装配阶段齐套率
        </CardTitle>
        <CardDescription>
          六个装配阶段的齐套情况，阻塞齐套率需达到100%才能开始该阶段
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-6 gap-4">
          {(stageStats || []).map((stage, index) => {
            const Icon = stageIcons[stage.stage_code] || Package;
            const isBlocked = stage.blocked_count > 0;
            return (
              <div key={stage.stage_code} className="relative">
                {/* Connection line */}
                {index < stageStats.length - 1 &&
                <div className="absolute top-8 left-1/2 w-full h-0.5 bg-slate-200 z-0" />
                }
                <div
                  className={cn(
                    "relative z-10 flex flex-col items-center p-4 rounded-lg border-2 transition-all",
                    isBlocked ?
                    "border-red-300 bg-red-50" :
                    "border-emerald-300 bg-emerald-50"
                  )}>

                  <div
                    className={cn(
                      "w-12 h-12 rounded-full flex items-center justify-center mb-2",
                      isBlocked ? "bg-red-100" : "bg-emerald-100"
                    )}>

                    <Icon
                      className={cn(
                        "w-6 h-6",
                        isBlocked ? "text-red-600" : "text-emerald-600"
                      )} />

                  </div>
                  <div className="text-sm font-medium text-center mb-1">
                    {stage.stage_name}
                  </div>
                  <div
                    className={cn(
                      "text-lg font-bold",
                      getKitRateColor(stage.avg_kit_rate)
                    )}>

                    {stage.avg_kit_rate}%
                  </div>
                  <div className="flex gap-2 mt-2 text-xs">
                    <span className="text-emerald-600">
                      {stage.can_start_count} 可开
                    </span>
                    <span className="text-red-600">
                      {stage.blocked_count} 阻塞
                    </span>
                  </div>
                </div>
              </div>);

          })}
        </div>
      </CardContent>
    </Card>
  );
}
