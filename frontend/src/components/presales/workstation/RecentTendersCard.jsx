import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Target, ChevronRight, Timer } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";

export default function RecentTendersCard({ tenders }) {
  return (
    <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
          <Target className="w-5 h-5 text-amber-400" />
          近期投标
        </CardTitle>
        <Link to="/bidding">
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
          >
            全部
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {tenders.map((bid, index) => (
          <motion.div
            key={bid.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-white truncate">
                  {bid.name}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">{bid.customer}</p>
              </div>
              <Badge className={cn("text-xs", bid.statusColor)}>
                {bid.status}
              </Badge>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1">
                <Timer className="w-3 h-3" />
                剩余{" "}
                <span
                  className={cn(
                    "font-medium",
                    bid.daysLeft <= 7 ? "text-red-400" : "text-white"
                  )}
                >
                  {bid.daysLeft}
                </span>{" "}
                天
              </span>
              <span className="text-slate-400">¥{bid.amount}万</span>
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
