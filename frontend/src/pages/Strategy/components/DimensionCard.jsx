/**
 * BSC 维度卡片组件
 * 展示单个 BSC 维度的健康度和 KPI 状态
 */
import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";
import { Card, CardContent, Button, Badge, Progress } from "../../../components/ui";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { getHealthConfig } from "../../../lib/constants/strategy";

export function DimensionCard({ dimension: _dimension, config, data }) {
  const Icon = config.icon;
  const healthConfig = data?.level ? getHealthConfig(data.level) : null;

  return (
    <motion.div variants={fadeIn}>
      <Card
        className={cn(
          "bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50",
          "hover:border-slate-600/80 transition-all cursor-pointer group"
        )}
      >
        <CardContent className="p-4">
          {/* 头部 */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className={cn("p-2 rounded-lg", config.bgColor)}>
                <Icon className="w-4 h-4" style={{ color: config.color }} />
              </div>
              <span className="font-medium text-white text-sm">{config.name}</span>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
          </div>

          {/* 评分 */}
          <div className="mb-3">
            <div className="flex items-baseline gap-1">
              <span
                className="text-2xl font-bold"
                style={{ color: config.color }}
              >
                {data?.score?.toFixed(1) || 0}
              </span>
              <span className="text-sm text-slate-400">%</span>
            </div>
            {healthConfig && (
              <Badge
                variant="outline"
                className={cn(
                  "mt-1 text-xs",
                  healthConfig.bgColor,
                  healthConfig.textColor
                )}
              >
                {healthConfig.label}
              </Badge>
            )}
          </div>

          {/* 进度条 */}
          <Progress
            value={data?.score || 0}
            className="h-1.5 mb-3"
          />

          {/* KPI 统计 */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">
              KPI: {data?.kpiCount || 0}
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-emerald-400">{data?.kpiOnTrack || 0} 达标</span>
            {(data?.kpiAtRisk || 0) > 0 && (
              <span className="text-amber-400">{data.kpiAtRisk} 预警</span>
            )}
            {(data?.kpiOffTrack || 0) > 0 && (
              <span className="text-red-400">{data.kpiOffTrack} 落后</span>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
