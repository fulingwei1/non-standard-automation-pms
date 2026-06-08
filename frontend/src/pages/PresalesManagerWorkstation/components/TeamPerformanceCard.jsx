import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Users, ChevronRight } from "lucide-react";
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

const RANK_COLORS = [
  "bg-gradient-to-br from-amber-500 to-orange-500",
  "bg-gradient-to-br from-blue-500 to-cyan-500",
  "bg-gradient-to-br from-slate-500 to-gray-600",
  "bg-gradient-to-br from-purple-500 to-pink-500",
];

export default function TeamPerformanceCard({
  teamPerformance,
  detailsPath = "/presales/technical-solutions?tab=reviews",
}) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-5 w-5 text-purple-400" />
              团队绩效排行
            </CardTitle>
            <Link to={detailsPath}>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-primary">
                查看详情 <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(!teamPerformance || teamPerformance.length === 0) && (
              <div className="py-8 text-center text-sm text-slate-500">暂无团队绩效数据</div>
            )}
            {(teamPerformance || []).map((member, index) =>
              <div
                key={member.id}
                className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm",
                        RANK_COLORS[index] || ""
                      )}>
                      {index + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">
                          {member.name}
                        </span>
                        <Badge
                          variant="outline"
                          className="text-xs bg-slate-700/40">
                          {member.role}
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        {member.activeSolutions} 个进行中 · 本月完成{" "}
                        {member.completedThisMonth} 个
                        {member.pendingReview > 0 &&
                          <span className="text-amber-400 ml-1">
                            · 待审核 {member.pendingReview}
                          </span>
                        }
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">
                      {member.avgQuality}%
                    </div>
                    <div className="text-xs text-slate-400">平均质量</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">质量评分</span>
                    <span
                      className={cn(
                        "font-medium",
                        member.avgQuality >= 90
                          ? "text-emerald-400"
                          : member.avgQuality >= 80
                          ? "text-amber-400"
                          : "text-red-400"
                      )}>
                      {member.avgQuality}%
                    </span>
                  </div>
                  <Progress
                    value={member.avgQuality}
                    className="h-1.5 bg-slate-700/50" />
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
