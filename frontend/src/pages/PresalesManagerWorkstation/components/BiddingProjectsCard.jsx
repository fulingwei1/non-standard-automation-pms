import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Target, ChevronRight, Timer } from "lucide-react";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { Progress } from "../../../components/ui/progress";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../../lib/formatters";

export default function BiddingProjectsCard({ biddingProjects }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-5 w-5 text-amber-400" />
              投标项目
            </CardTitle>
            <Link to="/presales/technical-solutions?tab=bids">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-primary">
                全部 <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {(!biddingProjects || biddingProjects.length === 0) && (
            <div className="py-6 text-center text-sm text-slate-500">暂无投标项目</div>
          )}
          {(biddingProjects || []).map((bid) =>
            <div
              key={bid.id}
              className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-white truncate">
                    {bid.name}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {bid.customer}
                  </p>
                </div>
                <Badge className={cn("text-xs", bid.statusColor)}>
                  {bid.status}
                </Badge>
              </div>
              <div className="space-y-2 mt-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Timer className="w-3 h-3" />
                    剩余{" "}
                    <span
                      className={cn(
                        "font-medium",
                        bid.daysLeft !== null && bid.daysLeft <= 7 ? "text-red-400" : "text-white"
                      )}>
                      {bid.daysLeft ?? "--"}
                    </span>{" "}
                    天
                  </span>
                  <span className="text-slate-400">
                    {formatCurrency(bid.amount)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    负责人: {bid.responsible}
                  </span>
                  <span className="text-slate-400">
                    进度: {bid.progress}%
                  </span>
                </div>
                <Progress
                  value={bid.progress}
                  className="h-1 bg-slate-700/50" />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
