import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText,
  ChevronRight,
  Building2,
  Briefcase,
  DollarSign,
  Calendar,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { Progress } from "../../ui/progress";
import { cn } from "../../../lib/utils";

export default function OngoingSolutionsCard({ solutions }) {
  return (
    <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-violet-400" />
          进行中方案
        </CardTitle>
        <Link to="/solutions">
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
          >
            方案中心
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {solutions.map((solution, index) => (
          <motion.div
            key={solution.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-4 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="text-sm font-medium text-white">
                    {solution.name}
                  </h4>
                  <Badge variant="outline" className="text-xs">
                    {solution.version}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    {solution.customer}
                  </span>
                  <span className="flex items-center gap-1">
                    <Briefcase className="w-3 h-3" />
                    {solution.deviceType}
                  </span>
                  <span className="flex items-center gap-1">
                    <DollarSign className="w-3 h-3" />¥{solution.amount}万
                  </span>
                </div>
              </div>
              <Badge className={cn("text-xs", solution.statusColor)}>
                {solution.status}
              </Badge>
            </div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">完成进度</span>
                <span className="text-white">{solution.progress}%</span>
              </div>
              <Progress value={solution.progress} className="h-1.5" />
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                截止: {solution.deadline}
              </span>
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
