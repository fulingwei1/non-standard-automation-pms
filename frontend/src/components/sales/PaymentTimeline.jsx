/**
 * Payment Timeline Component - Displays payment schedule and status
 */

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { fadeIn, staggerContainer } from "../../lib/animations";
import {
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
} from "lucide-react";
import { Badge } from "../ui/badge";

const paymentTypeLabels = {
  deposit: "签约款",
  progress: "进度款",
  delivery: "发货款",
  acceptance: "验收款",
  warranty: "质保金",
};

const statusConfig = {
  paid: {
    label: "已到账",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    icon: CheckCircle2,
  },
  pending: {
    label: "待收款",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    icon: Clock,
  },
  overdue: {
    label: "已逾期",
    color: "bg-red-500",
    textColor: "text-red-400",
    icon: AlertTriangle,
  },
  invoiced: {
    label: "已开票",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    icon: FileText,
  },
};

export default function PaymentTimeline({ payments = [], compact = false }) {
  const sortedPayments = [...payments].sort(
    (a, b) => new Date(a.dueDate) - new Date(b.dueDate),
  );

  if (compact) {
    return (
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-2"
      >
        {sortedPayments.slice(0, 5).map((payment, index) => (
          <PaymentListItem key={payment.id || index} payment={payment} />
        ))}
        {sortedPayments.length > 5 && (
          <div className="text-center text-xs text-slate-400 py-2">
            还有 {sortedPayments.length - 5} 条记录
          </div>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="relative"
    >
      {/* Timeline line */}
      <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary/50 via-slate-600 to-slate-700" />

      {/* Payment items */}
      <div className="space-y-4">
        {sortedPayments.map((payment, index) => (
          <PaymentTimelineItem key={payment.id || index} payment={payment} />
        ))}
      </div>
    </motion.div>
  );
}

function PaymentTimelineItem({ payment }) {
  const {
    type,
    projectName,
    amount,
    dueDate,
    paidDate,
    status = "pending",
    invoiceNo,
    notes,
  } = payment;

  const statusConf = statusConfig[status] || statusConfig.pending;
  const StatusIcon = statusConf.icon;

  const isOverdue = status === "pending" && new Date(dueDate) < new Date();
  const actualStatus = isOverdue ? "overdue" : status;
  const actualStatusConf = statusConfig[actualStatus];

  return (
    <motion.div variants={fadeIn} className="relative pl-10">
      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-2 w-5 h-5 rounded-full flex items-center justify-center",
          "border-2 border-surface-0",
          actualStatusConf.color,
        )}
      >
        <StatusIcon className="w-3 h-3 text-white" />
      </div>

      {/* Content */}
      <div
        className={cn(
          "bg-surface-100/50 backdrop-blur-sm rounded-lg border border-white/5 p-4",
          "hover:border-primary/20 transition-colors",
        )}
      >
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {paymentTypeLabels[type] || type}
              </Badge>
              <Badge
                className={cn(
                  "text-xs",
                  actualStatusConf.textColor,
                  "bg-transparent",
                )}
              >
                {actualStatusConf.label}
              </Badge>
            </div>
            <h4 className="font-medium text-white mt-1">{projectName}</h4>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold text-amber-400">
              ¥{(amount / 10000).toFixed(1)}万
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            <span>
              {status === "paid" ? `已收: ${paidDate}` : `应收: ${dueDate}`}
            </span>
          </div>
          {invoiceNo && (
            <div className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              <span>发票: {invoiceNo}</span>
            </div>
          )}
        </div>

        {notes && (
          <p className="text-xs text-slate-500 mt-2 line-clamp-1">{notes}</p>
        )}
      </div>
    </motion.div>
  );
}

function PaymentListItem({ payment }) {
  const { type, projectName, amount, dueDate, status = "pending" } = payment;

  const isOverdue = status === "pending" && new Date(dueDate) < new Date();
  const actualStatus = isOverdue ? "overdue" : status;
  const statusConf = statusConfig[actualStatus];

  return (
    <motion.div
      variants={fadeIn}
      className="flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 transition-colors cursor-pointer"
    >
      <div className="flex items-center gap-3">
        <div className={cn("w-2 h-2 rounded-full", statusConf.color)} />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">{dueDate}</span>
            <Badge variant="secondary" className="text-xs">
              {paymentTypeLabels[type] || type}
            </Badge>
          </div>
          <span className="text-xs text-slate-400">{projectName}</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "text-sm font-semibold",
            status === "paid"
              ? "text-emerald-400"
              : actualStatus === "overdue"
                ? "text-red-400"
                : "text-amber-400",
          )}
        >
          ¥{(amount / 10000).toFixed(1)}万
        </span>
        <Badge
          className={cn(
            "text-xs",
            statusConf.textColor,
            "bg-transparent border-0",
          )}
        >
          {statusConf.label}
        </Badge>
      </div>
    </motion.div>
  );
}

// Stats summary component
export function PaymentStats({ payments = [] }) {
  const stats = payments.reduce(
    (acc, p) => {
      const isOverdue =
        p.status === "pending" && new Date(p.dueDate) < new Date();
      if (p.status === "paid") {
        acc.paid += p.amount;
        acc.paidCount++;
      } else if (isOverdue) {
        acc.overdue += p.amount;
        acc.overdueCount++;
      } else {
        acc.pending += p.amount;
        acc.pendingCount++;
      }
      return acc;
    },
    {
      paid: 0,
      pending: 0,
      overdue: 0,
      paidCount: 0,
      pendingCount: 0,
      overdueCount: 0,
    },
  );

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="text-center p-3 bg-emerald-500/10 rounded-lg">
        <div className="text-xs text-emerald-400">已回款</div>
        <div className="text-lg font-semibold text-emerald-400">
          ¥{(stats.paid / 10000).toFixed(0)}万
        </div>
        <div className="text-xs text-slate-500">{stats.paidCount}笔</div>
      </div>
      <div className="text-center p-3 bg-blue-500/10 rounded-lg">
        <div className="text-xs text-blue-400">待回款</div>
        <div className="text-lg font-semibold text-blue-400">
          ¥{(stats.pending / 10000).toFixed(0)}万
        </div>
        <div className="text-xs text-slate-500">{stats.pendingCount}笔</div>
      </div>
      <div className="text-center p-3 bg-red-500/10 rounded-lg">
        <div className="text-xs text-red-400">已逾期</div>
        <div className="text-lg font-semibold text-red-400">
          ¥{(stats.overdue / 10000).toFixed(0)}万
        </div>
        <div className="text-xs text-slate-500">{stats.overdueCount}笔</div>
      </div>
    </div>
  );
}
