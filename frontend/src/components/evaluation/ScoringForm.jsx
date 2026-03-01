import React from "react";
import { Star, MessageSquare, Save, Send, CheckCircle2 } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * 评分表单组件
 */
export const ScoringForm = ({
  score,
  comment,
  isDraft,
  isSaving,
  isSubmitting,
  scoringGuidelines,
  commentTemplates,
  onScoreChange,
  onCommentChange,
  onInsertTemplate,
  onSaveDraft,
  onSubmit,
}) => {
  // 获取评分等级
  const getScoreLevel = (score) => {
    if (!score) {return null;}
    const numScore = Number(score);
    return (scoringGuidelines || []).find((g) => {
      const [min, max] = g.range.split("-").map(Number);
      return numScore >= min && numScore <= max;
    });
  };

  const currentLevel = getScoreLevel(score);

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
      <div className="p-6 border-b border-slate-700/50">
        <h3 className="text-xl font-bold text-white">评价打分</h3>
      </div>

      <div className="p-6 space-y-6">
        {/* 评分输入 */}
        <div>
          <label className="flex items-center gap-2 text-white font-medium mb-3">
            <Star className="h-5 w-5 text-amber-400" />
            绩效评分
            <span className="text-red-400">*</span>
            <span className="text-sm text-slate-400 font-normal">
              (60-100分)
            </span>
          </label>

          <div className="flex items-start gap-6">
            <div className="flex-shrink-0">
              <input
                type="number"
                min="60"
                max="100"
                value={score || "unknown"}
                onChange={(e) => onScoreChange(e.target.value)}
                placeholder="请输入分数"
                className="w-32 h-16 px-4 text-center text-3xl font-bold bg-slate-900/50 border-2 border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {currentLevel && (
              <div className="flex-1 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20">
                <div className="flex items-center gap-3 mb-2">
                  <span
                    className={cn("text-2xl font-bold", currentLevel.color)}
                  >
                    {currentLevel.level}
                  </span>
                  <span className="text-slate-400">·</span>
                  <span className="text-slate-300">
                    {currentLevel.description}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 评分指南 */}
          <div className="mt-4 p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-3">评分参考标准：</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {(scoringGuidelines || []).map((guide, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-slate-400">{guide.range}分</span>
                  <span className={cn("font-medium", guide.color)}>
                    {guide.level}
                  </span>
                  <span className="text-slate-500">{guide.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 评价意见 */}
        <div>
          <label className="flex items-center gap-2 text-white font-medium mb-3">
            <MessageSquare className="h-5 w-5 text-blue-400" />
            评价意见
            <span className="text-red-400">*</span>
          </label>

          <textarea
            value={comment || "unknown"}
            onChange={(e) => onCommentChange(e.target.value)}
            placeholder="请填写具体的评价意见，包括优点、不足及改进建议..."
            className="w-full h-40 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
          />

          <p className="text-xs text-slate-500 mt-2">
            建议包含：工作表现评价、优点、不足、改进建议等
          </p>

          {/* 评价模板 */}
          <div className="mt-4">
            <p className="text-sm text-slate-400 mb-3">快速插入模板：</p>
            <div className="space-y-3">
              {(commentTemplates || []).map((category, idx) => (
                <div key={idx}>
                  <p className="text-xs text-slate-500 mb-2">
                    {category.category}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {(category.templates || []).map((template, tidx) => (
                      <button
                        key={tidx}
                        onClick={() => onInsertTemplate(template)}
                        className="px-3 py-1.5 bg-slate-700/50 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
                      >
                        {template}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-700/50">
          <div className="flex items-center gap-2 text-sm">
            {isDraft && (
              <span className="text-amber-400">● 有未保存的修改</span>
            )}
            {!isDraft && (
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" />
                已保存
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onSaveDraft}
              disabled={isSaving || !isDraft}
              className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {isSaving ? "保存中..." : "保存草稿"}
            </button>

            <button
              onClick={onSubmit}
              disabled={isSubmitting}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-blue-500/50 disabled:to-purple-500/50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              {isSubmitting ? "提交中..." : "提交评价"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
