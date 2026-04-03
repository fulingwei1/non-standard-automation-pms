import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { cn } from "../../lib/utils";

export function KpiCard({ kpi }) {
  return (
    <Card className="bg-surface-1/50 hover:bg-surface-1/70 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className={cn("p-3 rounded-xl", kpi.bgColor)}>
            <kpi.icon className={cn("w-6 h-6", kpi.color)} />
          </div>
          <div
            className={cn(
              "flex items-center gap-1 text-xs font-medium",
              kpi.trend === "up" ? "text-emerald-400" : "text-red-400",
            )}
          >
            {kpi.trend === "up" ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : (
              <ArrowDownRight className="w-4 h-4" />
            )}
            {kpi.changePercent}
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-400">{kpi.label}</p>
          <p className="text-3xl font-bold text-white mt-1">{kpi.value}</p>
        </div>
      </CardContent>
    </Card>
  );
}
