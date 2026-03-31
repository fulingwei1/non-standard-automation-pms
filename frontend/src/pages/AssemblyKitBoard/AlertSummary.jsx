/**
 * Alert Summary Cards - 预警汇总
 */
import { AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { alertLevelConfig } from "./constants";

export default function AlertSummary({ alertSummary }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {["L1", "L2", "L3", "L4"].map((level) => {
        const config = alertLevelConfig[level];
        const count = alertSummary[level] || 0;
        return (
          <Card
            key={level}
            className={cn(
              count > 0 && "border-l-4",
              count > 0 && config.bgLight.split(" ")[1]
            )}>

            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">
                    {config.label}
                  </div>
                  <div
                    className={cn(
                      "text-2xl font-bold",
                      count > 0 ? config.textColor : "text-slate-400"
                    )}>

                    {count}
                  </div>
                </div>
                <AlertTriangle
                  className={cn(
                    "w-8 h-8",
                    count > 0 ? config.textColor : "text-slate-300"
                  )} />

              </div>
            </CardContent>
          </Card>);

      })}
    </div>
  );
}
