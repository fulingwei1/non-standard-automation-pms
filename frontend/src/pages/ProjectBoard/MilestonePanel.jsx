import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { Button } from "../../components/ui/button";
import { Badge, Card, CardContent, Skeleton } from "../../components/ui";
import {
  Target,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Calendar,
} from "lucide-react";

// 里程碑状态配置
const statusConfig = {
  PENDING: { label: "待开始", color: "bg-slate-500", textColor: "text-slate-400", Icon: Clock },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500", textColor: "text-blue-400", Icon: Clock },
  COMPLETED: { label: "已完成", color: "bg-emerald-500", textColor: "text-emerald-400", Icon: CheckCircle2 },
  OVERDUE: { label: "已逾期", color: "bg-red-500", textColor: "text-red-400", Icon: AlertTriangle },
};

// 获取里程碑状态（兼容 actual_date 和 completed_at 字段）
const getMilestoneStatus = (milestone) => {
  if (milestone.actual_date || milestone.completed_at || milestone.status === "COMPLETED") return "COMPLETED";
  if (milestone.status === "OVERDUE") return "OVERDUE";
  if (milestone.status === "IN_PROGRESS") return "IN_PROGRESS";

  // 基于日期判断
  if (milestone.planned_date) {
    const now = new Date();
    const planned = new Date(milestone.planned_date);
    if (planned < now) return "OVERDUE";
  }
  return "PENDING";
};

export default function MilestonePanel({ milestones, loading, onRefresh }) {
  if (loading) {
    return (
      <Card className="bg-surface-1 border-white/10">
        <CardContent className="p-6">
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!milestones || milestones.length === 0) {
    return (
      <Card className="bg-surface-1 border-white/10">
        <CardContent className="p-8 text-center">
          <Target className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">暂无里程碑</h3>
          <p className="text-slate-400">该项目尚未设置里程碑</p>
        </CardContent>
      </Card>
    );
  }

  // 统计数据
  const stats = milestones.reduce((acc, m) => {
    const status = getMilestoneStatus(m);
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(statusConfig).map(([key, config]) => {
          const count = stats[key] || 0;
          const IconComp = config.Icon;
          return (
            <Card key={key} className="bg-surface-1 border-white/10">
              <CardContent className="p-4 flex items-center gap-3">
                <div className={cn("p-2 rounded-lg", config.color + "/20")}>
                  <IconComp className={cn("w-5 h-5", config.textColor)} />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{count}</div>
                  <div className="text-xs text-slate-400">{config.label}</div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 里程碑列表 */}
      <Card className="bg-surface-1 border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-white">里程碑列表</h3>
            <Button variant="ghost" size="sm" onClick={onRefresh} className="text-slate-400 hover:text-white">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
          <div className="space-y-3">
            {milestones.map((milestone) => {
              const status = getMilestoneStatus(milestone);
              const config = statusConfig[status];
              const IconComp = config.Icon;
              return (
                <motion.div
                  key={milestone.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start gap-4 p-4 rounded-lg bg-surface-2/50 border border-white/5 hover:border-white/10 transition-colors"
                >
                  {/* 状态图标 */}
                  <div className={cn("p-2 rounded-lg", config.color + "/20")}>
                    <IconComp className={cn("w-5 h-5", config.textColor)} />
                  </div>

                  {/* 内容 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h4 className="font-medium text-white truncate">
                        {milestone.milestone_name || milestone.name}
                      </h4>
                      <Badge className={cn(config.color + "/20", config.textColor, "text-xs")}>
                        {config.label}
                      </Badge>
                    </div>
                    {(milestone.remark || milestone.description) && (
                      <p className="text-sm text-slate-400 line-clamp-2 mb-2">
                        {milestone.remark || milestone.description}
                      </p>
                    )}
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        计划: {milestone.planned_date || "未设置"}
                      </span>
                      {(milestone.actual_date || milestone.completed_at) && (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <CheckCircle2 className="w-3 h-3" />
                          完成: {milestone.actual_date || milestone.completed_at}
                        </span>
                      )}
                      {milestone.is_key && (
                        <Badge className="bg-amber-500/20 text-amber-400 text-xs">关键</Badge>
                      )}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
