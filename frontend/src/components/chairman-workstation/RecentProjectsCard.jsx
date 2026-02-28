import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Briefcase, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";

export const RecentProjectsCard = ({ projects }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-5 w-5 text-cyan-400" />
              最近项目
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary"
              asChild>

              <Link to="/projects">
                项目列表 <ChevronRight className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {projects && projects?.length > 0 ?
            (projects || []).map((project) =>
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-cyan-500/50 transition-colors cursor-pointer group">

              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-slate-400">
                      {project.project_code ||
                      project.projectCode ||
                      project.id}
                    </span>
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-xs",
                        (project.health === "H1" ||
                        project.health_status === "H1") &&
                        "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
                        (project.health === "H2" ||
                        project.health_status === "H2") &&
                        "bg-amber-500/20 text-amber-400 border-amber-500/30"
                      )}>

                      {project.health === "H1" ||
                      project.health_status === "H1" ?
                      "正常" :
                      "关注"}
                    </Badge>
                  </div>
                  <p className="font-medium text-white text-sm group-hover:text-cyan-400 transition-colors">
                    {project.project_name ||
                    project.projectName ||
                    project.name}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {project.customer_name ||
                    project.customer ||
                    ""}
                  </p>
                </div>
              </div>
              <div className="space-y-2 mt-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">进度</span>
                  <span className="text-white font-medium">
                    {project.progress || 0}%
                  </span>
                </div>
                <Progress
                  value={project.progress || 0}
                  className="h-1.5 bg-slate-700/50" />

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">
                    阶段:{" "}
                    {project.current_stage || project.stage || ""}
                  </span>
                  <span className="text-slate-400">
                    {project.planned_end_date ||
                    project.plannedEndDate ||
                    ""}
                  </span>
                </div>
              </div>
            </Link>
            ) :

            <div className="text-center py-8 text-slate-500">
              <p>暂无项目数据</p>
            </div>
            }
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default RecentProjectsCard;
