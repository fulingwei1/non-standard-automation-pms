import { motion } from "framer-motion";
import {
  X,
  Building2,
  User,
  Calendar,
  Truck,
  ClipboardCheck,
  Clock,
  DollarSign,
  FileText,
  Phone,
  MessageSquare,
  Eye,
  CheckCircle2,
  Flag,
  AlertTriangle,
} from "lucide-react";
import { Badge, Button, Progress } from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  stageConfig,
  defaultStageConf,
  healthConfig,
  defaultHealthConf,
} from "./constants";

/**
 * ProjectDetailPanel — slide-in side panel showing full project details.
 */
export function ProjectDetailPanel({ project, onClose }) {
  const stageConf = stageConfig[project.stage] || defaultStageConf;
  const healthConf = healthConfig[project.health] || defaultHealthConf;

  // Field name compatibility
  const contractAmount = project.contractAmount || project.contract_amount || 0;
  const paidAmount = project.paidAmount || project.paid_amount || 0;
  const paymentProgress =
    contractAmount > 0 ? (paidAmount / contractAmount) * 100 : 0;
  const projectName = project.name || project.project_name || "未命名项目";
  const projectCode = project.project_code || project.id;
  const customerName =
    project.customerShort ||
    project.customer_name ||
    project.customer?.name ||
    "-";
  const contractNo = project.contractNo || project.contract_no || "-";
  const pmName = project.pm || project.pm_name || "-";
  const progress = project.progress ?? project.completion_rate ?? 0;
  const startDate =
    project.startDate || project.start_date || project.created_at || "-";
  const expectedDelivery =
    project.expectedDelivery ||
    project.expected_delivery ||
    project.plan_delivery_date ||
    "-";
  const acceptanceDate =
    project.acceptanceDate || project.acceptance_date || "-";
  const lastUpdate = project.lastUpdate || project.updated_at || "-";
  const milestones = project.milestones || [];
  const issues = project.issues || [];

  return (
    <motion.div
      initial={{ x: "100%" }}
      animate={{ x: 0 }}
      exit={{ x: "100%" }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className={cn("w-3 h-3 rounded-full", healthConf.color)} />
              <h2 className="text-lg font-semibold text-white">{projectName}</h2>
            </div>
            <p className="text-sm text-slate-400">
              {projectCode} · {contractNo}
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Badge
            variant="secondary"
            className={cn("text-xs", stageConf.textColor)}
          >
            {stageConf.label}
          </Badge>
          <Badge
            variant="secondary"
            className={cn("text-xs", healthConf.textColor)}
          >
            {healthConf.label}
          </Badge>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Progress & Amount */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-surface-50 rounded-xl">
            <div className="text-sm text-slate-400 mb-2">项目进度</div>
            <div className="text-2xl font-bold text-white mb-2">{progress}%</div>
            <Progress value={progress} className="h-2" />
          </div>
          <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
            <div className="text-sm text-slate-400 mb-2">合同金额</div>
            <div className="text-2xl font-bold text-amber-400">
              ¥{(contractAmount / 10000).toFixed(0)}万
            </div>
            <div className="text-xs text-slate-400 mt-1">
              已收 {paymentProgress.toFixed(0)}% (¥
              {(paidAmount / 10000).toFixed(0)}万)
            </div>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">项目信息</h3>
          <div className="space-y-2 text-sm">
            {[
              { Icon: Building2, label: "客户:", value: customerName },
              { Icon: User, label: "项目经理:", value: pmName },
              { Icon: Calendar, label: "启动日期:", value: startDate },
              { Icon: Truck, label: "预计交付:", value: expectedDelivery },
              { Icon: ClipboardCheck, label: "验收日期:", value: acceptanceDate },
              { Icon: Clock, label: "最近更新:", value: lastUpdate },
            ].map(({ Icon, label, value }) => (
              <div key={label} className="flex items-center gap-3">
                <Icon className="w-4 h-4 text-slate-500" />
                <span className="text-slate-400">{label}</span>
                <span className="text-white">{value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Milestones */}
        {milestones.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">里程碑</h3>
            <div className="space-y-2">
              {milestones.map((milestone, index) => {
                const isCompleted = milestone.status === "completed";
                const isCurrent = milestone.status === "in_progress";
                const isDelayed =
                  milestone.actual && milestone.actual > milestone.date;

                return (
                  <div
                    key={index}
                    className={cn(
                      "p-3 rounded-lg border",
                      isCompleted
                        ? "bg-emerald-500/10 border-emerald-500/20"
                        : isCurrent
                        ? "bg-primary/10 border-primary/20"
                        : "bg-surface-50 border-white/5"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isCompleted ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : isCurrent ? (
                          <Flag className="w-4 h-4 text-primary" />
                        ) : (
                          <Clock className="w-4 h-4 text-slate-400" />
                        )}
                        <span className="text-sm text-white">
                          {milestone.name || "-"}
                        </span>
                        {isDelayed && (
                          <Badge variant="destructive" className="text-xs">
                            延期
                          </Badge>
                        )}
                      </div>
                      <span className="text-xs text-slate-400">
                        {isCompleted ? milestone.actual : milestone.date}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Issues */}
        {issues?.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">问题与风险</h3>
            {issues.map((issue, index) => (
              <div
                key={index}
                className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg"
              >
                <div className="flex items-center gap-2 text-amber-400 text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  {issue.content || issue.description || "-"}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">快捷操作</h3>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm" className="justify-start">
              <Phone className="w-4 h-4 mr-2 text-blue-400" />
              联系客户
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <MessageSquare className="w-4 h-4 mr-2 text-green-400" />
              联系PM
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <DollarSign className="w-4 h-4 mr-2 text-amber-400" />
              查看回款
            </Button>
            <Button variant="outline" size="sm" className="justify-start">
              <FileText className="w-4 h-4 mr-2 text-purple-400" />
              查看合同
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button className="flex-1">
          <Eye className="w-4 h-4 mr-2" />
          查看详情
        </Button>
      </div>
    </motion.div>
  );
}
