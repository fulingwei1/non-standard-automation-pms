import { motion } from "framer-motion";
import { Building2, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

export default function DepartmentStatusCard({ departmentStatus }) {
  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-5 w-5 text-blue-400" />
              部门运营状态
            </CardTitle>
            <Button variant="ghost" size="sm" className="text-xs text-primary">
              详情 <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {departmentStatus.length > 0 ? (
            (departmentStatus || []).map((dept) => (
              <div
                key={dept.id}
                className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center",
                        dept.status === "excellent" &&
                          "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10",
                        dept.status === "good" &&
                          "bg-gradient-to-br from-blue-500/20 to-blue-600/10",
                        dept.status === "warning" &&
                          "bg-gradient-to-br from-amber-500/20 to-amber-600/10"
                      )}
                    >
                      <Building2
                        className={cn(
                          "h-4 w-4",
                          dept.status === "excellent" && "text-emerald-400",
                          dept.status === "good" && "text-blue-400",
                          dept.status === "warning" && "text-amber-400"
                        )}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white text-sm">
                          {dept.name}
                        </span>
                        {dept.issues > 0 && (
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                            {dept.issues} 个问题
                          </Badge>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {dept.manager}
                      </div>
                    </div>
                  </div>
                  {dept.achievement > 0 && (
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">
                        {dept.achievement.toFixed(1)}%
                      </div>
                      <div className="text-xs text-slate-400">完成率</div>
                    </div>
                  )}
                </div>
                {dept.achievement > 0 && (
                  <Progress
                    value={dept.achievement}
                    className="h-1.5 bg-slate-700/50"
                  />
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Building2 className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
              <p className="text-sm">部门状态数据需要从API获取</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
