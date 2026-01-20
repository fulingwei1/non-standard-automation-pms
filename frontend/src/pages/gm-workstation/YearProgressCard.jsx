import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { formatCurrency } from "./formatCurrency";

export default function YearProgressCard({ businessStats }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-5 w-5 text-cyan-400" />
            年度经营目标进度
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">年度营收目标</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {formatCurrency(businessStats.yearTarget || 0)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400">已完成</p>
                <p className="text-3xl font-bold text-emerald-400 mt-1">
                  {formatCurrency(businessStats.yearRevenue || 0)}
                </p>
              </div>
            </div>
            <Progress
              value={businessStats.yearProgress || 0}
              className="h-4 bg-slate-700/50"
            />
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">
                完成率: {(businessStats.yearProgress || 0).toFixed(1)}%
              </span>
              <span className="text-slate-400">
                剩余:{" "}
                {formatCurrency(
                  (businessStats.yearTarget || 0) -
                    (businessStats.yearRevenue || 0)
                )}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
