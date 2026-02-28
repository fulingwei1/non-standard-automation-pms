/**
 * Contract Card Component - Displays contract information with payment progress
 * Used in BusinessSupportWorkstation and contract listings
 */

import { motion } from "framer-motion";
import {
  Briefcase,
  ChevronRight,
  Download,
  Eye,
  Edit,
  MoreVertical,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { Card, CardContent, Badge, Button, Progress } from "../ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

const PaymentStageItem = ({ stage, index }) => {
  const statusConfig = {
    paid: {
      color: "text-emerald-400",
      bg: "bg-emerald-500/20",
      label: "已到账",
    },
    pending: {
      color: "text-slate-400",
      bg: "bg-slate-700/40",
      label: "待回款",
    },
    overdue: { color: "text-red-400", bg: "bg-red-500/20", label: "已逾期" },
  };

  const config = statusConfig[stage.status] || statusConfig.pending;

  return (
    <motion.div
      key={index}
      variants={fadeIn}
      className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2.5 text-xs transition-all hover:bg-slate-800/50"
    >
      <div className="flex flex-1 items-center gap-3">
        <span className="font-medium text-slate-300">{stage.type}</span>
        <span className="text-slate-500">|</span>
        <span className="font-semibold text-slate-200">
          {formatCurrency(stage.amount)}
        </span>
      </div>
      <Badge className={cn("text-xs", config.bg, config.color)}>
        {config.label}
      </Badge>
    </motion.div>
  );
};

const ContractHealthIndicator = ({ health }) => {
  const healthConfig = {
    good: { color: "text-emerald-400", icon: CheckCircle2, label: "正常" },
    warning: { color: "text-amber-400", icon: AlertTriangle, label: "有风险" },
    danger: { color: "text-red-400", icon: AlertTriangle, label: "阻塞" },
  };

  const config = healthConfig[health];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-1.5">
      <Icon className={cn("h-4 w-4", config.color)} />
      <span className={cn("text-xs font-medium", config.color)}>
        {config.label}
      </span>
    </div>
  );
};

export function ContractCard({
  contract,
  onViewDetails,
  onEdit,
  onDownload,
  showActions = true,
}) {
  const paidStages = (contract.paymentStages || []).filter(
    (s) => s.status === "paid",
  ).length;
  const totalStages = contract.paymentStages?.length;

  return (
    <motion.div
      variants={fadeIn}
      whileHover={{ y: -2 }}
      className="group overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all duration-200 hover:border-slate-600 hover:shadow-lg hover:shadow-violet-500/10"
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex flex-1 items-start gap-3">
          <div className="rounded-lg bg-blue-500/20 p-2">
            <Briefcase className="h-5 w-5 text-blue-400" />
          </div>
          <div className="flex-1">
            <h3 className="line-clamp-1 font-semibold text-slate-100">
              {contract.projectName}
            </h3>
            <p className="mt-0.5 text-sm text-slate-400">
              {contract.customerName}
            </p>
            <p className="mt-1 text-xs text-slate-500">{contract.id}</p>
          </div>
        </div>

        <div className="flex flex-shrink-0 flex-col items-end gap-1">
          <p className="text-lg font-bold text-amber-400">
            {formatCurrency(contract.contractAmount)}
          </p>
          <p className="text-xs text-slate-500">合同金额</p>
        </div>
      </div>

      {/* Health Status */}
      <div className="mb-4 flex items-center justify-between rounded-lg bg-slate-700/20 px-3 py-2">
        <ContractHealthIndicator health={contract.health} />
        <span className="text-xs text-slate-400">
          {paidStages}/{totalStages} 款已到账
        </span>
      </div>

      {/* Payment Progress */}
      <div className="mb-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">回款进度</span>
          <span className="text-sm font-medium text-slate-300">
            {formatCurrency(contract.paidAmount)} /{" "}
            {formatCurrency(contract.contractAmount)}
          </span>
        </div>
        <Progress
          value={contract.paymentProgress}
          className="h-2 bg-slate-700/50"
        />
      </div>

      {/* Payment Stages */}
      <div className="mb-4 space-y-1.5">
        {(contract.paymentStages || []).map((stage, idx) => (
          <PaymentStageItem key={idx} stage={stage} index={idx} />
        ))}
      </div>

      {/* Status Badges */}
      <div className="flex flex-wrap gap-2 border-t border-slate-700/30 pt-4">
        <Badge
          className={cn(
            "text-xs",
            contract.invoiceStatus === "complete"
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-slate-700/40 text-slate-400",
          )}
        >
          发票: {contract.invoiceCount}张
        </Badge>
        <Badge
          className={cn(
            "text-xs",
            contract.acceptanceStatus === "completed"
              ? "bg-emerald-500/20 text-emerald-400"
              : contract.acceptanceStatus === "in_progress"
                ? "bg-blue-500/20 text-blue-400"
                : "bg-slate-700/40 text-slate-400",
          )}
        >
          {contract.acceptanceStatus === "completed" && "✓ "}
          验收:{" "}
          {contract.acceptanceStatus === "completed"
            ? "已完成"
            : contract.acceptanceStatus === "in_progress"
              ? "进行中"
              : "待验收"}
        </Badge>
      </div>

      {/* Actions */}
      {showActions && (
        <div className="absolute right-4 top-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-100"
            onClick={() => onViewDetails?.(contract)}
            title="查看详情"
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-100"
            onClick={() => onEdit?.(contract)}
            title="编辑"
          >
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0 text-slate-400 hover:text-slate-100"
            onClick={() => onDownload?.(contract)}
            title="下载"
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      )}
    </motion.div>
  );
}

export default ContractCard;
