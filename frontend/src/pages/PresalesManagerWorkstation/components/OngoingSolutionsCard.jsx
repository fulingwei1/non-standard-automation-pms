import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  FileText,
  ChevronRight,
  Building2,
  Users,
  DollarSign,
  Calendar,
} from "lucide-react";
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
import { SOLUTION_CENTER_PATH } from "../constants";

export default function OngoingSolutionsCard({ ongoingSolutions }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-5 w-5 text-violet-400" />
              进行中方案
            </CardTitle>
            <Link to={SOLUTION_CENTER_PATH}>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-primary">
                方案中心 <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {(!ongoingSolutions || ongoingSolutions.length === 0) && (
            <div className="py-8 text-center text-sm text-slate-500">暂无进行中方案</div>
          )}
          {(ongoingSolutions || []).map((solution, _index) =>
            <div
              key={solution.id}
              className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

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
                      <Users className="w-3 h-3" />
                      {solution.author}
                    </span>
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      {formatCurrency(solution.amount)}
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
                <Progress
                  value={solution.progress}
                  className="h-1.5 bg-slate-700/50" />
              </div>
              <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  截止: {solution.deadline}
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
