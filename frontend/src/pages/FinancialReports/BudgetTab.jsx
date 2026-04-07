import { cn, formatCurrency } from "../../lib/utils";

export default function BudgetTab({ costBreakdown }) {
  return (
    <TabsContent value="budget" className="space-y-6 mt-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">
          预算执行分析
        </h3>
        <div className="space-y-3">
          {(costBreakdown || []).map((item, index) => {
            const used = item.amount / item.budget * 100;
            return (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">
                    {item.category}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-slate-500 text-xs">
                      预算: {formatCurrency(item.budget)}
                    </span>
                    <span className="text-white font-medium">
                      实际: {formatCurrency(item.amount)}
                    </span>
                    {item.variance !== 0 &&
                    <span
                      className={cn(
                        "text-xs",
                        item.variance > 0 ?
                        "text-red-400" :
                        "text-emerald-400"
                      )}>
                        {item.variance > 0 ? "+" : ""}
                        {formatCurrency(item.variance)}
                    </span>
                    }
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Progress
                    value={used || "unknown"}
                    className={cn(
                      "flex-1 h-2",
                      used > 100 ?
                      "bg-red-500/20" :
                      used > 90 ?
                      "bg-amber-500/20" :
                      "bg-slate-700/50"
                    )} />
                  <span className="text-xs text-slate-400 w-16 text-right">
                    {used.toFixed(1)}%
                  </span>
                </div>
              </div>);
          })}
        </div>
      </div>
    </TabsContent>
  );
}
