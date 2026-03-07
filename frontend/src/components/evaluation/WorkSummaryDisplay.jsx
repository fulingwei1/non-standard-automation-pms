import {
  Target,
  FileText,
  TrendingUp,
  AlertCircle,
  ThumbsUp,
} from "lucide-react";

/**
 * 工作总结展示组件
 */
export const WorkSummaryDisplay = ({ workSummary }) => {
  if (!workSummary) {return null;}

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
      <div className="p-6 border-b border-slate-700/50">
        <h3 className="text-xl font-bold text-white">员工工作总结</h3>
      </div>

      <div className="p-6 space-y-6">
        {/* 工作内容 */}
        {workSummary.workContent && (
          <div>
            <div className="flex items-center gap-2 text-blue-400 mb-3">
              <Target className="h-5 w-5" />
              <h4 className="font-bold">本月工作内容</h4>
            </div>
            <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
              <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                {workSummary.workContent}
              </p>
            </div>
          </div>
        )}

        {/* 自我评价 */}
        {workSummary.selfEvaluation && (
          <div>
            <div className="flex items-center gap-2 text-emerald-400 mb-3">
              <FileText className="h-5 w-5" />
              <h4 className="font-bold">自我评价</h4>
            </div>
            <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
              <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                {workSummary.selfEvaluation}
              </p>
            </div>
          </div>
        )}

        {/* 工作亮点 */}
        {workSummary.highlights && (
          <div>
            <div className="flex items-center gap-2 text-amber-400 mb-3">
              <TrendingUp className="h-5 w-5" />
              <h4 className="font-bold">工作亮点</h4>
            </div>
            <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <p className="text-amber-200 whitespace-pre-wrap leading-relaxed">
                {workSummary.highlights}
              </p>
            </div>
          </div>
        )}

        {/* 遇到的问题 */}
        {workSummary.problems && (
          <div>
            <div className="flex items-center gap-2 text-red-400 mb-3">
              <AlertCircle className="h-5 w-5" />
              <h4 className="font-bold">遇到的问题</h4>
            </div>
            <div className="p-4 bg-red-500/10 rounded-lg border border-red-500/20">
              <p className="text-red-200 whitespace-pre-wrap leading-relaxed">
                {workSummary.problems}
              </p>
            </div>
          </div>
        )}

        {/* 下月计划 */}
        {workSummary.nextMonthPlan && (
          <div>
            <div className="flex items-center gap-2 text-purple-400 mb-3">
              <ThumbsUp className="h-5 w-5" />
              <h4 className="font-bold">下月工作计划</h4>
            </div>
            <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
              <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                {workSummary.nextMonthPlan}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
