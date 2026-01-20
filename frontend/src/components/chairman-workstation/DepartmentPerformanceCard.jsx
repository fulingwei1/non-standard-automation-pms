import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Users, Building2, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { cn } from "../../lib/utils";
import { formatCurrency } from "./utils";

export const DepartmentPerformanceCard = ({ departmentPerformance }) => {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Users className="h-5 w-5 text-blue-400" />
              部门绩效总览
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-primary"
              asChild>

              <Link to="/departments">
                部门管理 <ChevronRight className="w-3 h-3 ml-1" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {departmentPerformance && departmentPerformance.length > 0 ?
            departmentPerformance.map((dept) => {
              const deptName =
              dept.name || dept.department_name || "";
              const manager = dept.manager || dept.manager_name || "";
              const employees =
              dept.employees || dept.employee_count || 0;
              const projects =
              dept.projects ||
              dept.project_count ||
              dept.orders ||
              dept.inspections ||
              0;
              const revenue = dept.revenue || dept.total_revenue || 0;
              const achievement =
              dept.achievement || dept.achievement_rate || 0;
              const status =
              dept.status || (
              achievement >= 90 ?
              "excellent" :
              achievement >= 70 ?
              "good" :
              "warning");
              return (
                <div
                  key={dept.id || dept.department_id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          status === "excellent" &&
                          "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10",
                          status === "good" &&
                          "bg-gradient-to-br from-blue-500/20 to-blue-600/10",
                          status === "warning" &&
                          "bg-gradient-to-br from-amber-500/20 to-amber-600/10"
                        )}>

                        <Building2
                          className={cn(
                            "h-5 w-5",
                            status === "excellent" &&
                            "text-emerald-400",
                            status === "good" && "text-blue-400",
                            status === "warning" && "text-amber-400"
                          )} />

                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">
                            {deptName}
                          </span>
                          {manager &&
                          <Badge
                            variant="outline"
                            className="text-xs bg-slate-700/40">

                            {manager}
                          </Badge>
                          }
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                          {employees} 人 · {projects} 项工作
                        </div>
                      </div>
                    </div>
                    {revenue > 0 &&
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">
                        {formatCurrency(revenue)}
                      </div>
                      {achievement > 0 &&
                      <div className="text-xs text-slate-400">
                        完成率: {achievement.toFixed(1)}%
                      </div>
                      }
                    </div>
                    }
                  </div>
                  {achievement > 0 &&
                  <Progress
                    value={achievement}
                    className="h-1.5 bg-slate-700/50" />

                  }
                </div>);

            }) :

            <div className="text-center py-8 text-slate-500">
              <Users className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
              <p className="text-sm">部门绩效数据需要从API获取</p>
            </div>
            }
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default DepartmentPerformanceCard;
