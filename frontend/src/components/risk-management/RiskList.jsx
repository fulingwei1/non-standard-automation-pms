import React from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Target,
  FileText,
  Clock,
  CheckCircle2,
  Eye,
  XCircle
} from "lucide-react";
import {
  Card,
  CardContent
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { SkeletonCard } from "../../components/ui/skeleton";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/utils";
import { fadeInUp } from "../../lib/animations";
import {
  getRiskLevelBadge,
  getStatusBadge,
  getProbabilityLabel,
  getImpactLabel
} from "./riskUtils";

export function RiskList({
  loading,
  error,
  risks,
  onRetry,
  onAssess,
  onResponse,
  onStatusUpdate,
  onClose,
  onDetail
}) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4">
        {Array(3)
          .fill(null)
          .map((_, i) => (
            <SkeletonCard key={i} />
          ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="mb-6 border-red-500/30 bg-red-500/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <XCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={onRetry}
              className="border-red-500/30 text-red-400 hover:bg-red-500/20"
            >
              重试
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (risks.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-slate-500">
          该项目暂无风险数据
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {risks.map((risk) => {
        const levelBadge = getRiskLevelBadge(risk.risk_level);
        const statusBadge = getStatusBadge(risk.status);

        return (
          <motion.div key={risk.id} variants={fadeInUp}>
            <Card
              className={cn(
                "hover:bg-white/[0.02] transition-colors border-l-4",
                levelBadge.borderColor
              )}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        "p-2.5 rounded-xl",
                        levelBadge.bgColor,
                        "ring-1",
                        levelBadge.borderColor
                      )}
                    >
                      <AlertTriangle
                        className={cn("h-5 w-5", levelBadge.color)}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-white">
                          {risk.risk_name}
                        </h3>
                        <Badge
                          variant={levelBadge.variant}
                          className={levelBadge.bgColor}
                        >
                          {levelBadge.label}
                        </Badge>
                        <Badge variant={statusBadge.variant}>
                          {statusBadge.label}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {risk.risk_no} • {risk.risk_category}
                      </p>
                    </div>
                  </div>
                </div>

                {risk.description && (
                  <p className="text-sm text-slate-300 mb-4 line-clamp-2">
                    {risk.description}
                  </p>
                )}

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div>
                    <span className="text-xs text-slate-400">发生概率</span>
                    <p className="text-white font-medium">
                      {getProbabilityLabel(risk.probability)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400">影响程度</span>
                    <p className="text-white font-medium">
                      {getImpactLabel(risk.impact)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400">负责人</span>
                    <p className="text-white font-medium">
                      {risk.owner_name || "未分配"}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400">跟踪日期</span>
                    <p className="text-white font-medium">
                      {risk.follow_up_date
                        ? formatDate(risk.follow_up_date)
                        : "未设置"}
                    </p>
                  </div>
                </div>

                {risk.response_strategy && (
                  <div className="mb-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-xs text-slate-400">应对策略</span>
                    <p className="text-sm text-white mt-1">
                      {risk.response_strategy}
                    </p>
                  </div>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  <div className="flex items-center gap-2 flex-wrap">
                    {risk.status === "IDENTIFIED" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onAssess(risk.id)}
                      >
                        <Target className="h-4 w-4 mr-2" />
                        风险评估
                      </Button>
                    )}
                    {risk.status === "ANALYZING" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onResponse(risk.id)}
                      >
                        <FileText className="h-4 w-4 mr-2" />
                        制定应对
                      </Button>
                    )}
                    {risk.status !== "CLOSED" && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onStatusUpdate(risk.id)}
                        >
                          <Clock className="h-4 w-4 mr-2" />
                          更新状态
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onClose(risk.id)}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          关闭风险
                        </Button>
                      </>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onDetail(risk)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    查看详情
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
