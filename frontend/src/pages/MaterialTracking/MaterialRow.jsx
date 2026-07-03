/**
 * Material Tracking - MaterialRow component
 * Displays a single material item with status, progress bars, and actions
 */

import { motion } from "framer-motion";
import { Eye } from "lucide-react";
import { Badge, Button, Progress } from "../../components/ui";
import { cn, formatDate } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { statusConfig, qualityStatusConfig } from "./constants";

const toFiniteNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const MaterialRow = ({ material, onView }) => {
  const statusCfg = statusConfig[material.status];
  const StatusIcon = statusCfg.icon;
  const totalQuantity = toFiniteNumber(material.totalQuantity);
  const arrivedQuantity = toFiniteNumber(material.arrivedQuantity);
  const usedQuantity = toFiniteNumber(material.usedQuantity);
  const arrivalProgress =
  totalQuantity > 0 ? arrivedQuantity / totalQuantity * 100 : 0;
  const usageProgress =
  arrivedQuantity > 0
    ? usedQuantity / arrivedQuantity * 100
    : 0;

  return (
    <motion.div
      variants={fadeIn}
      className="group rounded-lg border border-slate-700/50 bg-slate-800/40 p-4 hover:bg-slate-800/60 transition-all">

      <div className="space-y-3">
        {/* Header Row */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-100">{material.name}</h3>
            <p className="text-sm text-slate-500 mt-1">
              {material.code} • {material.category} • {material.supplier}
            </p>
          </div>
          <Badge className={cn("text-sm", statusCfg.color)}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {statusCfg.label}
          </Badge>
        </div>

        {/* Quantity and Value Info */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-slate-400 mb-1">订购数量</p>
            <p className="font-semibold text-slate-100">
              {material.totalQuantity}
            </p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">已到数量</p>
            <p className="font-semibold text-emerald-400">
              {material.arrivedQuantity}
            </p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">已用数量</p>
            <p className="font-semibold text-blue-400">
              {material.usedQuantity}
            </p>
          </div>
          <div>
            <p className="text-slate-400 mb-1">剩余数量</p>
            <p className="font-semibold text-amber-400">
              {material.remainingQuantity}
            </p>
          </div>
        </div>

        {/* Progress Bars */}
        <div className="space-y-2">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-400">到货进度</span>
              <span className="text-xs font-medium text-slate-300">
                {arrivalProgress.toFixed(0)}%
              </span>
            </div>
            <Progress value={arrivalProgress} className="h-1.5" />
          </div>
          {arrivedQuantity > 0 &&
          <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">使用进度</span>
                <span className="text-xs font-medium text-slate-300">
                  {usageProgress.toFixed(0)}%
                </span>
              </div>
              <Progress value={usageProgress} className="h-1.5" />
          </div>
          }
        </div>

        {/* Timeline and Status */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm pt-2 border-t border-slate-700/30">
          <div>
            <p className="text-slate-500 text-xs mb-1">预期日期</p>
            <p className="text-slate-300">
              {formatDate(material.expectedDate)}
            </p>
          </div>
          {material.actualArrivalDate &&
          <div>
              <p className="text-slate-500 text-xs mb-1">实际日期</p>
              <p className="text-slate-300">
                {formatDate(material.actualArrivalDate)}
              </p>
          </div>
          }
          <div>
            <p className="text-slate-500 text-xs mb-1">位置</p>
            <p className="text-slate-300">{material.location || "—"}</p>
          </div>
          {material.daysUntilExpiry &&
          <div>
              <p className="text-slate-500 text-xs mb-1">保质期</p>
              <p
              className={cn(
                "text-sm font-medium",
                material.daysUntilExpiry < 30 ?
                "text-red-400" :
                "text-slate-300"
              )}>

                {material.daysUntilExpiry} 天
              </p>
          </div>
          }
        </div>

        {/* Action Bar */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-700/30">
          <div className="flex gap-2">
            {material.qualityStatus &&
            <Badge
              className={cn(
                "text-xs",
                qualityStatusConfig[material.qualityStatus]?.color
              )}>

                {qualityStatusConfig[material.qualityStatus]?.label}
            </Badge>
            }
            <Badge className="bg-slate-700/50 text-slate-300 text-xs">
              {material.nextAction}
            </Badge>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0"
            onClick={() => onView(material)}>

            <Eye className="w-4 h-4 text-blue-400" />
          </Button>
        </div>
      </div>
    </motion.div>);

};

export default MaterialRow;
