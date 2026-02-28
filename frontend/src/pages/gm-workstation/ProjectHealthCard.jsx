import { motion } from "framer-motion";
import { Briefcase, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { formatCurrency } from "./formatCurrency";

const healthColors = {
  good: "bg-emerald-500",
  warning: "bg-amber-500",
  critical: "bg-red-500"
};

const riskColors = {
  low: "text-emerald-400",
  medium: "text-amber-400",
  high: "text-red-400"
};

export default function ProjectHealthCard({ projectHealth }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-5 w-5 text-blue-400" />
              重点项目健康度
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              查看全部 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {(projectHealth || []).map((project) => (
              <div
                key={project.id}
                className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white">
                        {project.name}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-xs bg-slate-700/40"
                      >
                        {project.stageLabel}
                      </Badge>
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full",
                          healthColors[project.health]
                        )}
                      />
                    </div>
                    <div className="text-xs text-slate-400">
                      {project.customer} · {project.id}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(project.amount)}
                    </div>
                    <div className="text-xs text-slate-400">
                      交付: {project.dueDate}
                    </div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">进度</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn("font-medium", riskColors[project.risk])}
                      >
                        风险:{" "}
                        {project.risk === "low"
                          ? "低"
                          : project.risk === "medium"
                            ? "中"
                            : "高"}
                      </span>
                      <span className="text-slate-300">{project.progress}%</span>
                    </div>
                  </div>
                  <Progress
                    value={project.progress}
                    className="h-1.5 bg-slate-700/50"
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
