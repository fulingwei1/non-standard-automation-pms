// -*- coding: utf-8 -*-

export default function MatchingResults({
  matching,
  matchingResult,
  onAccept,
  onReject
}) {
  return (
    <div className="col-span-8">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-300">
          匹配结果
        </span>
        {matchingResult &&
          <div className="flex gap-2">
            <Badge variant="secondary">
              候选人: {matchingResult.total_candidates}
            </Badge>
            <Badge className="bg-green-500/20 text-green-400">
              达标: {matchingResult.qualified_count}
            </Badge>
          </div>
        }
      </div>

      {matching ?
        <div className="flex flex-col items-center justify-center py-20">
          <RefreshCw className="h-12 w-12 text-primary animate-spin mb-4" />
          <p className="text-slate-400">
            AI正在分析员工档案，计算匹配得分...
          </p>
        </div> :
        matchingResult ?
          <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
            {/* 提示信息 */}
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm text-blue-400">
              匹配请求: {matchingResult.request_id} | 优先级:{" "}
              {matchingResult.priority} | 最低分阈值:{" "}
              {matchingResult.priority_threshold}分
            </div>

            {/* 候选人卡片列表 */}
            {matchingResult.candidates?.length > 0 ?
              (matchingResult.candidates || []).map((candidate, index) =>
                <CandidateCard
                  key={candidate.employee_id}
                  candidate={candidate}
                  index={index}
                  priorityThreshold={matchingResult.priority_threshold}
                  onAccept={onAccept}
                  onReject={onReject}
                />
              ) :
              <div className="text-center py-12 text-slate-400">
                暂无匹配的候选人
              </div>
            }
          </div> :
          <div className="flex flex-col items-center justify-center py-20 text-slate-400">
            <Users className="h-12 w-12 mb-4 opacity-50" />
            <p>请选择人员需求并执行AI匹配</p>
          </div>
      }
    </div>
  );
}
