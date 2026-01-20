import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Briefcase, ChevronRight, Building2, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";

export default function LinkedOpportunitiesCard({ opportunities }) {
  return (
    <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-blue-400" />
          商机支持
        </CardTitle>
        <Link to="/opportunities">
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
        {opportunities.map((opp, index) => (
          <motion.div
            key={opp.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-white truncate">
                  {opp.name}
                </h4>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                  <Building2 className="w-3 h-3" />
                  {opp.customer}
                  <span className="text-slate-600">|</span>
                  <Users className="w-3 h-3" />
                  {opp.salesPerson}
                </p>
              </div>
            </div>
            <div className="flex items-center justify-between text-xs">
              <Badge className={cn("text-xs", opp.stageColor)}>
                {opp.stage}
              </Badge>
              <div className="flex items-center gap-3">
                <span className="text-slate-400">
                  赢率 <span className="text-white">{opp.winRate}%</span>
                </span>
                <span className="text-emerald-400">¥{opp.amount}万</span>
              </div>
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
