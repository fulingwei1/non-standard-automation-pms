import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { TrendingUp, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";
import { formatCurrency } from "./utils";

export const RevenueTrendCard = ({ monthlyRevenue }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <TrendingUp className="h-5 w-5 text-emerald-400" />
              月度营收趋势
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary"
              asChild>

              <Link to="/business-reports">
                查看报表 <ChevronRight className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {monthlyRevenue && monthlyRevenue.length > 0 ?
            (monthlyRevenue || []).map((item, index) => {
              const revenue = item.revenue || item.amount || 0;
              const target = item.target || item.target_amount || 0;
              const month =
              item.month || item.period || `第${index + 1}月`;
              const achievement =
              target > 0 ? revenue / target * 100 : 0;
              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">{month}</span>
                    <div className="flex items-center gap-3">
                      {target > 0 &&
                      <span className="text-slate-400 text-xs">
                        目标: {formatCurrency(target)}
                      </span>
                      }
                      <span className="font-semibold text-white">
                        {formatCurrency(revenue)}
                      </span>
                      {target > 0 &&
                      <span
                        className={cn(
                          "text-xs font-medium",
                          achievement >= 100 ?
                          "text-emerald-400" :
                          achievement >= 90 ?
                          "text-amber-400" :
                          "text-red-400"
                        )}>

                        {achievement.toFixed(1)}%
                      </span>
                      }
                    </div>
                  </div>
                  {target > 0 &&
                  <Progress
                    value={Math.min(achievement, 100)}
                    className={cn(
                      "h-2 bg-slate-700/50",
                      achievement >= 100 && "bg-emerald-500/20",
                      achievement >= 90 &&
                      achievement < 100 &&
                      "bg-amber-500/20",
                      achievement < 90 && "bg-red-500/20"
                    )} />

                  }
                </div>);

            }) :

            <div className="text-center py-8 text-slate-500">
              <TrendingUp className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
              <p className="text-sm">月度营收数据需要从API获取</p>
            </div>
            }
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default RevenueTrendCard;
