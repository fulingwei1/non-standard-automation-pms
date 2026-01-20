import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";

export const RiskProjectsCard = ({ riskProjects }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              风险预警项目
            </CardTitle>
            <Badge
              variant="outline"
              className="bg-red-500/20 text-red-400 border-red-500/30">

              {riskProjects ? riskProjects.length : 0}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {riskProjects && riskProjects.length > 0 ?
            riskProjects.map((project) => {
              const projectCode =
              project.project_code ||
              project.projectCode ||
              project.id;
              const projectName =
              project.project_name ||
              project.projectName ||
              project.name;
              const customer =
              project.customer_name || project.customer || "";
              const health = project.health || "H2";
              const issue =
              project.issue ||
              project.risk_description ||
              "需要关注";
              const delayDays =
              project.delay_days || project.delayDays || 0;
              return (
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-red-500/50 transition-colors cursor-pointer group">

                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono text-slate-400">
                          {projectCode}
                        </span>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            health === "H3" &&
                            "bg-red-500/20 text-red-400 border-red-500/30",
                            health === "H2" &&
                            "bg-amber-500/20 text-amber-400 border-amber-500/30"
                          )}>

                          {health === "H3" ? "预警" : "关注"}
                        </Badge>
                      </div>
                      <p className="font-medium text-white text-sm group-hover:text-red-400 transition-colors">
                        {projectName}
                      </p>
                      {customer &&
                      <p className="text-xs text-slate-400 mt-1">
                        {customer}
                      </p>
                      }
                    </div>
                  </div>
                  {issue &&
                  <div className="flex items-center justify-between text-xs mt-2">
                    <span className="text-slate-400">{issue}</span>
                    {delayDays > 0 &&
                    <span className="font-medium text-red-400">
                      延期 {delayDays} 天
                    </span>
                    }
                  </div>
                  }
                </Link>);

            }) :

            <div className="text-center py-8 text-slate-500">
              <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500/50" />
              <p className="text-sm">暂无风险预警项目</p>
            </div>
            }
            <Button variant="outline" className="w-full mt-3" asChild>
              <Link to="/alerts">
                查看全部预警 <ArrowRight className="w-3 h-3 ml-2" />
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default RiskProjectsCard;
