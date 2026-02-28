import { motion } from "framer-motion";
import { Target, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Progress } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export default function KeyMetricsCard({ keyMetrics }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-5 w-5 text-purple-400" />
            关键运营指标
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {keyMetrics.length > 0 ? (
              (keyMetrics || []).map((metric, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">{metric.label}</span>
                    <div className="flex items-center gap-2">
                      {metric.trend > 0 ? (
                        <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                      ) : metric.trend < 0 ? (
                        <ArrowDownRight className="w-3 h-3 text-red-400" />
                      ) : null}
                      <span className={cn("font-semibold", metric.color)}>
                        {metric.value.toFixed(1)}
                        {metric.unit}
                      </span>
                    </div>
                  </div>
                  {metric.target > 0 && (
                    <Progress
                      value={Math.min(
                        (metric.value / metric.target) * 100,
                        100
                      )}
                      className="h-2 bg-slate-700/50"
                    />
                  )}
                  <div className="flex items-center justify-between text-xs">
                    {metric.target > 0 && (
                      <span className="text-slate-500">
                        目标: {metric.target}
                        {metric.unit}
                      </span>
                    )}
                    {metric.trend !== 0 && (
                      <span className="text-slate-500">
                        {metric.trend > 0 ? "+" : ""}
                        {metric.trend}%
                      </span>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-2 text-center py-8 text-slate-500">
                <Target className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                <p className="text-sm">关键指标数据需要从API获取</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
