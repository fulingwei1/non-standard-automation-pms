/**
 * Bidding Card Component - Displays bidding project information
 * Used in BusinessSupportWorkstation and bidding management
 */

import { motion } from "framer-motion";
import {
  Target,
  Calendar,
  FileText,
  Download,
  Eye,
  Edit,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Calculator,
} from "lucide-react";
import { Card, CardContent, Badge, Button, Progress } from "../ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

const statusConfig = {
  inquiry: {
    label: "询价阶段",
    color: "bg-slate-500/20 text-slate-300",
    icon: Clock,
  },
  bidding_phase: {
    label: "投标阶段",
    color: "bg-blue-500/20 text-blue-400",
    icon: Target,
  },
  technical_evaluation: {
    label: "技术评标",
    color: "bg-purple-500/20 text-purple-400",
    icon: FileText,
  },
  commercial_evaluation: {
    label: "商务评标",
    color: "bg-orange-500/20 text-orange-400",
    icon: Calculator,
  },
  won: {
    label: "中标",
    color: "bg-emerald-500/20 text-emerald-400",
    icon: CheckCircle2,
  },
  lost: {
    label: "未中标",
    color: "bg-red-500/20 text-red-400",
    icon: AlertTriangle,
  },
};

const documentStatusConfig = {
  draft: { label: "编制中", color: "bg-slate-700/40 text-slate-300" },
  review: { label: "审核中", color: "bg-amber-500/20 text-amber-400" },
  submitted: { label: "已提交", color: "bg-emerald-500/20 text-emerald-400" },
};

const getDaysColor = (daysLeft) => {
  if (daysLeft === 0) return "text-red-400";
  if (daysLeft <= 3) return "text-orange-400";
  if (daysLeft <= 7) return "text-amber-400";
  return "text-cyan-400";
};

export function BiddingCard({
  bid,
  onViewDetails,
  onEdit,
  onDownload,
  showActions = true,
}) {
  const bidStatusConfig = statusConfig[bid.status] || statusConfig.inquiry;
  const docStatusConfig = documentStatusConfig[bid.documentStatus];

  return (
    <motion.div
      variants={fadeIn}
      whileHover={{ y: -2 }}
      className="group overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all duration-200 hover:border-slate-600 hover:shadow-lg hover:shadow-purple-500/10"
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex-1">
          <h3 className="line-clamp-2 font-semibold text-slate-100">
            {bid.projectName}
          </h3>
          <p className="mt-1 text-sm text-slate-400">{bid.customerName}</p>
          <p className="mt-2 text-lg font-bold text-purple-400">
            {formatCurrency(bid.bidAmount)}
          </p>
        </div>

        <div className="flex flex-shrink-0 flex-col gap-2">
          <Badge className={cn("text-xs", bidStatusConfig.color)}>
            {bidStatusConfig.label}
          </Badge>
          <Badge className={cn("text-xs", docStatusConfig.color)}>
            {docStatusConfig.label}
          </Badge>
        </div>
      </div>

      {/* Document Progress */}
      <div className="mb-4 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">标书进度</span>
          <span className="text-sm font-medium text-slate-300">
            {bid.progress}%
          </span>
        </div>
        <Progress value={bid.progress} className="h-2 bg-slate-700/50" />
      </div>

      {/* Deadline Info */}
      <div className="mb-4 rounded-lg bg-slate-800/30 px-3 py-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="h-4 w-4 text-slate-400" />
            <span className="text-slate-400">截止日期</span>
          </div>
          <span className={cn("font-semibold", getDaysColor(bid.daysLeft))}>
            {bid.daysLeft === 0 ? "今日截止" : `${bid.daysLeft}天`}
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500">{bid.bidDeadline}</p>
      </div>

      {/* Status Pills */}
      <div className="mb-4 flex flex-wrap gap-2">
        {bid.status === "won" && (
          <Badge className="bg-emerald-500/20 text-emerald-400">✓ 已中标</Badge>
        )}
        {bid.status === "lost" && (
          <Badge className="bg-red-500/20 text-red-400">✗ 未中标</Badge>
        )}
        {bid.daysLeft === 0 && (
          <Badge className="bg-red-500/20 text-red-400">🔴 紧急</Badge>
        )}
        {bid.progress === 100 && bid.documentStatus === "submitted" && (
          <Badge className="bg-emerald-500/20 text-emerald-400">✓ 已提交</Badge>
        )}
      </div>

      {/* Actions */}
      {showActions && (
        <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 flex-1 gap-1 text-xs text-slate-400 hover:text-slate-100"
            onClick={() => onViewDetails?.(bid)}
          >
            <Eye className="h-3.5 w-3.5" />
            详情
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 flex-1 gap-1 text-xs text-slate-400 hover:text-slate-100"
            onClick={() => onEdit?.(bid)}
          >
            <Edit className="h-3.5 w-3.5" />
            编辑
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 flex-1 gap-1 text-xs text-slate-400 hover:text-slate-100"
            onClick={() => onDownload?.(bid)}
          >
            <Download className="h-3.5 w-3.5" />
            下载
          </Button>
        </div>
      )}
    </motion.div>
  );
}

export default BiddingCard;
