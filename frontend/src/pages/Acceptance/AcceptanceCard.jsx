import { motion } from "framer-motion";
import {
  Building2,
  Calendar,
  AlertCircle,
  Eye,
  Edit3,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { typeConfigs, statusConfigs } from "./constants";

function AcceptanceCard({ acceptance, onView }) {
  const type = typeConfigs[acceptance.type] || {
    label: acceptance.type || "未知",
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
  };
  const status = statusConfigs[acceptance.status] || {
    label: acceptance.status || "未知",
    color: "bg-slate-500",
    icon: AlertCircle,
  };
  const StatusIcon = status.icon;

  const openIssues = (acceptance.issues || []).filter(
    (i) => i.status === "open",
  ).length;

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden"
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge className={cn("text-[10px]", type.bgColor, type.color)}>
                {type.label}
              </Badge>
              <span className="font-mono text-xs text-slate-500">
                {acceptance.id}
              </span>
            </div>
            <h3 className="font-medium text-white">{acceptance.projectName}</h3>
            <p className="text-sm text-slate-400">{acceptance.machineNo}</p>
          </div>
          <Badge className={cn("gap-1", status.color)}>
            <StatusIcon className="w-3 h-3" />
            {status.label}
          </Badge>
        </div>

        {/* Customer */}
        <div className="flex items-center gap-4 mb-3 text-sm text-slate-400">
          <span className="flex items-center gap-1">
            <Building2 className="w-3.5 h-3.5" />
            {acceptance.customer}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {acceptance.scheduledDate}
          </span>
        </div>

        {/* Progress */}
        {acceptance.status !== "pending" && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">验收进度</span>
              <span className="text-white">
                {acceptance.passedItems + acceptance.failedItems}/
                {acceptance.totalItems} 项
              </span>
            </div>
            <div className="h-2 bg-surface-2 rounded-full overflow-hidden flex">
              <div
                className="bg-emerald-500 transition-all"
                style={{
                  width: `${(acceptance.passedItems / acceptance.totalItems) * 100}%`,
                }}
              />
              <div
                className="bg-red-500 transition-all"
                style={{
                  width: `${(acceptance.failedItems / acceptance.totalItems) * 100}%`,
                }}
              />
            </div>
            <div className="flex items-center justify-between mt-1 text-xs">
              <span className="text-emerald-400">
                通过 {acceptance.passedItems}
              </span>
              <span className="text-red-400">
                不通过 {acceptance.failedItems}
              </span>
              <span className="text-slate-500">
                待检 {acceptance.pendingItems}
              </span>
            </div>
          </div>
        )}

        {/* Issues */}
        {openIssues > 0 && (
          <div className="p-2 rounded-lg bg-amber-500/10 text-xs text-amber-300 flex items-center gap-2 mb-3">
            <AlertCircle className="w-3 h-3" />
            {openIssues} 个待解决问题
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <div className="text-xs text-slate-500">
            {acceptance.inspector
              ? `检验员：${acceptance.inspector}`
              : "待分配检验员"}
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2"
              onClick={() => onView(acceptance)}
            >
              <Eye className="w-3.5 h-3.5" />
            </Button>
            {acceptance.status === "in_progress" && (
              <Button variant="ghost" size="sm" className="h-7 px-2">
                <Edit3 className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default AcceptanceCard;
