

import { cn } from "../../lib/utils";
import { stageConfig, defaultStageConf, healthConfig, defaultHealthConf } from "./constants";

/**
 * ProjectListItem — a single project row card in the project list.
 */
export function ProjectListItem({ project, onClick }) {
  const stageConf = stageConfig[project.stage] || defaultStageConf;
  const healthConf = healthConfig[project.health] || defaultHealthConf;

  // Field name compatibility (API vs front-end)
  const contractAmount = project.contractAmount || project.contract_amount || 0;
  const paidAmount = project.paidAmount || project.paid_amount || 0;
  const paymentProgress =
    contractAmount > 0 ? (paidAmount / contractAmount) * 100 : 0;
  const projectName = project.name || project.project_name || "未命名项目";
  const customerName =
    project.customerShort ||
    project.customer_name ||
    project.customer?.name ||
    "-";
  const contractNo = project.contractNo || project.contract_no || "-";
  const pmName = project.pm || project.pm_name || "-";
  const progress = project.progress ?? project.completion_rate ?? 0;
  const expectedDelivery =
    project.expectedDelivery ||
    project.expected_delivery ||
    project.plan_delivery_date ||
    "-";
  const acceptanceDate = project.acceptanceDate || project.acceptance_date || "-";
  const milestones = project.milestones || [];
  const issues = project.issues || [];

  return (
    <Card
      onClick={() => onClick(project)}
      className="cursor-pointer hover:border-primary/30 transition-colors"
    >
      <CardContent className="p-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Project info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <div className={cn("w-3 h-3 rounded-full", healthConf.color)} />
              <h3 className="font-semibold text-white truncate">{projectName}</h3>
              <Badge
                variant="secondary"
                className={cn("text-xs", stageConf.textColor)}
              >
                {stageConf.label}
              </Badge>
              {issues?.length > 0 && (
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              )}
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-400">
              <span className="flex items-center gap-1">
                <Building2 className="w-4 h-4" />
                {customerName}
              </span>
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {contractNo}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-4 h-4" />
                PM: {pmName}
              </span>
            </div>
          </div>

          {/* Progress */}
          <div className="w-full lg:w-48">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-400">项目进度</span>
              <span className="text-xs text-white">{progress}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Dates */}
          <div className="flex flex-col gap-1 text-sm">
            <div className="flex items-center gap-2">
              <Truck className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">交付:</span>
              <span className="text-white">{expectedDelivery}</span>
            </div>
            <div className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">验收:</span>
              <span className="text-white">{acceptanceDate}</span>
            </div>
          </div>

          {/* Amount */}
          <div className="text-right">
            <div className="text-lg font-semibold text-amber-400">
              ¥{(contractAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400">
              已收 {paymentProgress.toFixed(0)}%
            </div>
          </div>

          <ChevronRight className="w-5 h-5 text-slate-500" />
        </div>

        {/* Milestone progress track */}
        {milestones.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/5">
            <div className="flex items-center gap-1">
              {milestones.map((milestone, index) => {
                const isCompleted = milestone.status === "completed";
                const isCurrent = milestone.status === "in_progress";

                return (
                  <div key={index} className="flex items-center">
                    <div
                      className={cn(
                        "w-6 h-6 rounded-full flex items-center justify-center text-xs",
                        isCompleted
                          ? "bg-emerald-500 text-white"
                          : isCurrent
                          ? "bg-primary text-white"
                          : "bg-surface-50 text-slate-500 border border-slate-600"
                      )}
                      title={`${milestone.name || ""}: ${milestone.date || ""}`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-3 h-3" />
                      ) : isCurrent ? (
                        <Flag className="w-3 h-3" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    {index < milestones.length - 1 && (
                      <div
                        className={cn(
                          "w-8 h-0.5",
                          isCompleted ? "bg-emerald-500" : "bg-slate-600"
                        )}
                      />
                    )}
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-2 text-xs text-slate-500">
              <span>{milestones[0]?.name}</span>
              <span>{milestones[milestones.length - 1]?.name}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
