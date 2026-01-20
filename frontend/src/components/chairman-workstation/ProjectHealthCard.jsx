import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { PieChart, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";

export const ProjectHealthCard = ({ projectHealthDistribution }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <PieChart className="h-5 w-5 text-purple-400" />
              项目健康度分布
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary"
              asChild>

              <Link to="/board">
                项目看板 <ChevronRight className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {projectHealthDistribution && projectHealthDistribution.length > 0 ?
            projectHealthDistribution.map((item) => {
              const health =
              item.health || item.health_status || "H1";
              const label =
              item.label || (
              health === "H1" ?
              "正常" :
              health === "H2" ?
              "关注" :
              "预警");
              const count = item.count || item.project_count || 0;
              const percentage =
              item.percentage || item.percentage || 0;
              const color =
              item.color || (
              health === "H1" ?
              "emerald" :
              health === "H2" ?
              "amber" :
              "red");
              return (
                <div key={health} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "w-3 h-3 rounded-full",
                          color === "emerald" && "bg-emerald-500",
                          color === "amber" && "bg-amber-500",
                          color === "red" && "bg-red-500"
                        )} />

                      <span className="text-slate-300">{label}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400 text-xs">
                        {count} 个项目
                      </span>
                      <span
                        className={cn(
                          "font-semibold",
                          color === "emerald" && "text-emerald-400",
                          color === "amber" && "text-amber-400",
                          color === "red" && "text-red-400"
                        )}>

                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <Progress
                    value={percentage}
                    className={cn(
                      "h-2 bg-slate-700/50",
                      color === "emerald" && "bg-emerald-500/20",
                      color === "amber" && "bg-amber-500/20",
                      color === "red" && "bg-red-500/20"
                    )} />

                </div>);

            }) :

            <div className="text-center py-8 text-slate-500">
              <PieChart className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
              <p className="text-sm">项目健康度数据需要从API获取</p>
            </div>
            }
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ProjectHealthCard;
