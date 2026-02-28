import { motion } from "framer-motion";
import { BarChart3 } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "../../components/ui/card";
import { fadeIn } from "../../lib/animations";

export function ServiceTrends({ analytics }) {
  if (!analytics) return null;

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            工单趋势分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analytics.ticketTrends.map((item, index) => {
              const resolutionRate =
                item.count > 0
                  ? (item.resolved / item.count * 100).toFixed(1)
                  : 0;
              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-white">{item.month}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-slate-400">
                        总数: {item.count}
                      </span>
                      <span className="text-emerald-400">
                        已解决: {item.resolved}
                      </span>
                      <span className="text-blue-400">
                        解决率: {resolutionRate}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-800/50 rounded-full h-3 flex overflow-hidden">
                    <div
                      className="bg-emerald-500 h-3 transition-all"
                      style={{
                        width: `${item.resolved / item.count * 100}%`
                      }}
                    />
                    <div
                      className="bg-amber-500 h-3 transition-all"
                      style={{
                        width: `${
                          (item.count - item.resolved) / item.count * 100
                        }%`
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
