/**
 * 验收卡片组件
 */

import {
  Clock
} from "lucide-react";


import { cn } from "../../lib/utils";
import { typeConfigs, statusConfigs } from "./acceptanceConfig";
import { Badge, Button, Progress } from "../ui";
import { Calendar, CheckCircle2, Edit3, Eye, XCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function AcceptanceCard({ acceptance, onView }) {
  const type = typeConfigs[acceptance.type] || {
    label: acceptance.type || "未知",
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
  };
  const status = statusConfigs[acceptance.status] || {
    label: acceptance.status || "未知",
    color: "bg-slate-500",
    icon: Clock,
  };
  const StatusIcon = status.icon;

  const totalItems = acceptance.totalItems || 0;
  const passedItems = acceptance.passedItems || 0;
  const failedItems = acceptance.failedItems || 0;
  const pendingItems = acceptance.pendingItems || 0;
  const progress = totalItems > 0 ? (passedItems / totalItems) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden hover:border-primary/30 transition-colors"
    >
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={cn("text-xs", type.bgColor, type.color)}>
                {type.label}
              </Badge>
              <Badge
                className={cn(
                  "text-xs flex items-center gap-1",
                  status.color,
                  "text-white"
                )}
              >
                <StatusIcon className="w-3 h-3" />
                {status.label}
              </Badge>
            </div>
            <h3 className="font-semibold text-white text-lg mb-1">
              {acceptance.projectName}
            </h3>
            <p className="text-sm text-slate-400 font-mono">
              {acceptance.id}
            </p>
          </div>
        </div>

        {/* Progress */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400">验收进度</span>
            <span className="text-white font-medium">
              {passedItems}/{totalItems}
            </span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              {passedItems}
            </span>
            <span className="flex items-center gap-1">
              <XCircle className="w-3 h-3 text-red-400" />
              {failedItems}
            </span>
            {pendingItems > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" />
                {pendingItems}
              </span>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {acceptance.scheduledDate || "未设置"}
          </span>
          {acceptance.inspector
            ? `检验员：${acceptance.inspector}`
            : "待分配检验员"}
        </div>
        <div className="flex gap-1 mt-3">
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
    </motion.div>
  );
}
