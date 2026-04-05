import { cn } from "../../lib/utils";
import { Card } from "../../components/ui";

export default function StatCards({ statCards }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {(statCards || []).map((stat, i) => (
        <Card key={i} className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div
              className={cn(
                "p-2 rounded-lg",
                stat.color === "primary" && "bg-primary/20",
                stat.color === "emerald" && "bg-emerald-500/20",
                stat.color === "indigo" && "bg-indigo-500/20",
                stat.color === "amber" && "bg-amber-500/20",
              )}
            >
              <stat.icon
                className={cn(
                  "h-4 w-4",
                  stat.color === "primary" && "text-primary",
                  stat.color === "emerald" && "text-emerald-400",
                  stat.color === "indigo" && "text-indigo-400",
                  stat.color === "amber" && "text-amber-400",
                )}
               />
            </div>
          </div>
          <p className="text-xs text-slate-400 mb-1">{stat.label}</p>
          <p className="text-xl font-semibold text-white">{stat.value}</p>
          {stat.subtext && (
            <p className="text-xs text-slate-500 mt-1">{stat.subtext}</p>
          )}
        </Card>
      ))}
    </div>
  );
}
