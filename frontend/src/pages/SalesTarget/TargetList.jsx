import { motion } from "framer-motion";
import { Target, Edit } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";
import { getTargetTypeLabel, getTargetPeriodLabel } from "./utils";
import { statusConfigs } from "./constants";

function StatusBadge({ status }) {
  const config = statusConfigs[status] || statusConfigs.ACTIVE;
  return (
    <Badge variant="outline" className={cn("text-xs", config.textColor)}>
      {config.label}
    </Badge>
  );
}

export default function TargetList({ filteredTargets, loading, onEdit }) {
  return (
    <motion.div variants={fadeIn}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-400" />
            销售目标列表 ({filteredTargets.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredTargets.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              暂无目标数据
            </div>
          ) : (
            <div className="space-y-4">
              {(filteredTargets || []).map((target) => {
                const completionRate = Number(target.completion_rate || 0);
                const isCompleted = completionRate >= 100;
                const isWarning = completionRate < 70;

                return (
                  <div
                    key={target.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium text-white">
                            {getTargetTypeLabel(target.target_type)}
                          </span>
                          <StatusBadge status={target.status} />
                          <Badge
                            variant="outline"
                            className="text-xs bg-slate-700/40"
                          >
                            {getTargetPeriodLabel(target.target_period)}
                          </Badge>
                          <span className="text-sm text-slate-400">
                            {target.period_value}
                          </span>
                        </div>
                        <div className="text-sm text-slate-400 mb-2">
                          {target.target_scope === "PERSONAL" &&
                            target.user_name && (
                              <span>负责人: {target.user_name}</span>
                            )}
                          {target.target_scope === "DEPARTMENT" &&
                            target.department_name && (
                              <span>部门: {target.department_name}</span>
                            )}
                          {target.meta?.industry && <span className="ml-4">行业: {target.meta.industry}</span>}
                          {target.meta?.region && <span className="ml-4">大区: {target.meta.region}</span>}
                          {target.meta?.target_customer && <span className="ml-4">目标客户: {target.meta.target_customer}</span>}
                          {target.description && (
                            <span className="ml-4">
                              描述: {(target.description || "").split("[meta]")[0].trim()}
                            </span>
                          )}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(target)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                    </div>

                    {/* Progress */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">目标值</span>
                        <span className="text-white font-medium">
                          {target.target_type.includes("AMOUNT")
                            ? formatCurrency(target.target_value)
                            : `${target.target_value} 个`}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">实际完成</span>
                        <span
                          className={cn(
                            "font-medium",
                            isCompleted
                              ? "text-emerald-400"
                              : isWarning
                                ? "text-red-400"
                                : "text-amber-400",
                          )}
                        >
                          {target.target_type.includes("AMOUNT")
                            ? formatCurrency(target.actual_value || 0)
                            : `${target.actual_value || 0} 个`}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-slate-400">完成率</span>
                        <span
                          className={cn(
                            "font-medium",
                            isCompleted
                              ? "text-emerald-400"
                              : isWarning
                                ? "text-red-400"
                                : "text-amber-400",
                          )}
                        >
                          {completionRate.toFixed(1)}%
                        </span>
                      </div>
                      <Progress
                        value={Math.min(completionRate, 100)}
                        className={cn(
                          "h-2",
                          isCompleted && "bg-emerald-500/20",
                          isWarning && "bg-red-500/20",
                        )}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
