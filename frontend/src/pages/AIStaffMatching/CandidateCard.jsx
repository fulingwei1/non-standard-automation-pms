// -*- coding: utf-8 -*-
import { cn } from "../../lib/utils";
import { RECOMMENDATION_CONFIG, DIMENSIONS } from "./constants";
import { getScoreColor, getRecommendationBadge } from "./utils";

export default function CandidateCard({
  candidate,
  index,
  priorityThreshold,
  onAccept,
  onReject
}) {
  const config =
    RECOMMENDATION_CONFIG[candidate.recommendation_type] ||
    RECOMMENDATION_CONFIG.WEAK;
  const isQualified =
    candidate.total_score >= (priorityThreshold || 65);

  return (
    <motion.div
      key={candidate.employee_id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className={cn(
        "p-4 rounded-lg border",
        isQualified ?
          "border-green-500/30 bg-green-500/5" :
          "border-white/10 bg-white/5"
      )}>

      <div className="flex gap-6">
        {/* 左：基本信息 */}
        <div className="w-48 flex-shrink-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="relative">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                {candidate.employee_name?.charAt(0)}
              </div>
              <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-yellow-500 text-black text-xs font-bold flex items-center justify-center">
                {candidate.rank}
              </div>
            </div>
            <div>
              <div className="font-medium text-white">
                {candidate.employee_name}
              </div>
              <div className="text-xs text-slate-500">
                {candidate.employee_code}
              </div>
              <div className="text-xs text-slate-500">
                {candidate.department}
              </div>
            </div>
          </div>

          <div className="flex gap-1 mb-3">
            <Badge
              className={getRecommendationBadge(
                candidate.recommendation_type
              )}>
              {config.text}
            </Badge>
            {isQualified &&
              <Badge className="bg-green-500/20 text-green-400">
                达标
              </Badge>
            }
          </div>

          <div className="text-center">
            <div
              className={cn(
                "text-3xl font-bold",
                getScoreColor(candidate.total_score)
              )}>
              {candidate.total_score.toFixed(1)}
            </div>
            <div className="text-xs text-slate-500">
              匹配总分
            </div>
          </div>
        </div>

        {/* 中：维度得分 */}
        <div className="flex-1">
          <div className="text-xs text-slate-400 mb-2">
            维度得分
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2">
            {(DIMENSIONS || []).map((dim) =>
              <div key={dim.key}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-500">
                    {dim.label} ({dim.weight}%)
                  </span>
                  <span
                    className={getScoreColor(
                      candidate.dimension_scores[dim.key]
                    )}>
                    {candidate.dimension_scores[dim.key]}
                  </span>
                </div>
                <Progress
                  value={candidate.dimension_scores[dim.key]}
                  className="h-1.5" />
              </div>
            )}
          </div>
        </div>

        {/* 右：技能和操作 */}
        <div className="w-40 flex-shrink-0 space-y-3">
          <div>
            <div className="text-xs text-slate-400 mb-1">
              当前负载
            </div>
            <div className="flex items-center gap-2">
              <Progress
                value={candidate.current_workload_pct}
                className="h-2 flex-1" />
              <span
                className={cn(
                  "text-xs font-medium",
                  candidate.current_workload_pct >= 90 ?
                    "text-red-400" :
                    candidate.current_workload_pct >= 70 ?
                      "text-yellow-400" :
                      "text-green-400"
                )}>
                {candidate.current_workload_pct}%
              </span>
            </div>
            <div className="text-xs text-slate-500">
              可用: {candidate.available_hours}小时/周
            </div>
          </div>

          <div>
            <div className="text-xs text-slate-400 mb-1">
              匹配技能
            </div>
            <div className="flex flex-wrap gap-1">
              {candidate.matched_skills?.map(
                (skill) =>
                  <Badge
                    key={skill}
                    className="text-xs bg-green-500/20 text-green-400">
                    {skill}
                  </Badge>
              )}
            </div>
          </div>

          {candidate.missing_skills?.length > 0 &&
            <div>
              <div className="text-xs text-slate-400 mb-1">
                缺失技能
              </div>
              <div className="flex flex-wrap gap-1">
                {(candidate.missing_skills || []).map(
                  (skill) =>
                    <Badge
                      key={skill}
                      className="text-xs bg-red-500/20 text-red-400">
                      {skill}
                    </Badge>
                )}
              </div>
            </div>
          }

          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              className="flex-1"
              onClick={() => onAccept(candidate)}>
              <Check className="h-3 w-3 mr-1" />
              采纳
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="flex-1 text-red-400 border-red-500/30 hover:bg-red-500/10"
              onClick={() => onReject(candidate)}>
              <X className="h-3 w-3 mr-1" />
              拒绝
            </Button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
