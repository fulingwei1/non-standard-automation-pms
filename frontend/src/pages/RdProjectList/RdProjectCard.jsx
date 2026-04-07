

import { formatDate, formatCurrency } from "../../lib/utils";
import { staggerChild, statusMap, approvalStatusMap, categoryTypeMap } from "./constants";

export function RdProjectCard({ project, onClick }) {
  const status = statusMap[project.status] || statusMap.DRAFT;
  const approvalStatus =
    approvalStatusMap[project.approval_status] || approvalStatusMap.PENDING;
  const categoryType =
    categoryTypeMap[project.category_type] || categoryTypeMap.SELF;

  return (
    <motion.div variants={staggerChild}>
      <Card
        className="group cursor-pointer overflow-hidden hover:border-primary/50 transition-colors"
        onClick={onClick}
      >
        <div className="h-1 bg-gradient-to-r from-primary to-indigo-500" />
        <CardContent className="p-5">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-indigo-500/10 ring-1 ring-primary/20 group-hover:scale-105 transition-transform">
                <FlaskConical className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-white line-clamp-1 group-hover:text-primary transition-colors">
                  {project.project_name}
                </h3>
                <p className="text-xs text-slate-500">{project.project_no}</p>
              </div>
            </div>
            <div className="flex flex-col gap-1 items-end">
              <Badge variant={status.color}>{status.label}</Badge>
              {project.approval_status === "PENDING" && (
                <Badge variant={approvalStatus.color} className="text-xs">
                  {approvalStatus.label}
                </Badge>
              )}
            </div>
          </div>

          {/* Meta info */}
          <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Users className="h-4 w-4" />
              <span className="truncate">
                {project.project_manager_name || "未指定"}
              </span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <Calendar className="h-4 w-4" />
              <span>
                {project.planned_end_date
                  ? formatDate(project.planned_end_date)
                  : "未设置"}
              </span>
            </div>
          </div>

          {/* Category and Budget */}
          <div className="flex items-center justify-between mb-4">
            <Badge variant="outline">{categoryType.label}</Badge>
            <div className="flex items-center gap-1 text-sm text-slate-400">
              <DollarSign className="h-4 w-4" />
              <span>{formatCurrency(project.budget_amount || 0)}</span>
            </div>
          </div>

          {/* Stats */}
          {project.total_cost !== undefined && (
            <div className="mb-4 p-3 rounded-lg bg-white/[0.03] border border-white/5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">已归集费用</span>
                <span className="text-white font-medium">
                  {formatCurrency(project.total_cost || 0)}
                </span>
              </div>
              {project.total_hours && (
                <div className="flex items-center justify-between text-sm mt-2">
                  <span className="text-slate-400">总工时</span>
                  <span className="text-white font-medium">
                    {Number(project.total_hours).toFixed(1)} 小时
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              {project.status === "COMPLETED" && (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              )}
              {project.status === "IN_PROGRESS" && (
                <Clock className="h-4 w-4 text-primary" />
              )}
              {project.status === "CANCELLED" && (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-xs text-slate-500">
                {project.initiation_date
                  ? formatDate(project.initiation_date)
                  : "未立项"}
              </span>
            </div>
            <div className="flex items-center gap-1 text-sm text-slate-500 group-hover:text-primary transition-colors">
              查看详情
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
