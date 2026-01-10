import {
  Target,
  Edit3,
  Lightbulb,
  AlertCircle,
  TrendingUp,
  Sparkles,
  Save,
  Send,
} from "lucide-react";
import { fadeIn } from "../../utils/monthlySummaryUtils";
import { motion } from "framer-motion";

/**
 * 月度总结表单组件
 */
export const SummaryForm = ({
  currentUser,
  formData,
  isDraft,
  isSaving,
  isSubmitting,
  error,
  onInputChange,
  onSaveDraft,
  onSubmit,
}) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="p-6 space-y-6">
          {/* 用户信息 */}
          <div className="flex items-center gap-4 pb-4 border-b border-slate-700/50">
            <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
              <span className="text-white font-bold text-lg">
                {currentUser.name.charAt(0)}
              </span>
            </div>
            <div>
              <p className="text-white font-medium">{currentUser.name}</p>
              <p className="text-sm text-slate-400">
                {currentUser.department} · {currentUser.position}
              </p>
            </div>
          </div>

          {/* AI 辅助按钮（未来功能，当前禁用）*/}
          <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/20">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-purple-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-white font-medium mb-1">
                  AI 智能总结助手（即将上线）
                </p>
                <p className="text-sm text-slate-400 mb-3">
                  系统将自动提取您参与的项目任务、工作记录，生成工作总结草稿，减少手动填写工作量
                </p>
                <button
                  disabled
                  className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg text-sm font-medium cursor-not-allowed opacity-50"
                >
                  功能开发中...
                </button>
              </div>
            </div>
          </div>

          {/* 表单字段 */}
          <div className="space-y-6">
            {/* 本月工作内容 */}
            <div>
              <label className="flex items-center gap-2 text-white font-medium mb-3">
                <Target className="h-4 w-4 text-blue-400" />
                本月工作内容
                <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.workContent}
                onChange={(e) => onInputChange("workContent", e.target.value)}
                placeholder="请详细描述本月完成的主要工作内容，包括参与的项目、完成的任务、产出的成果等..."
                className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                建议包含：项目名称、任务内容、完成情况、数据成果等
              </p>
            </div>

            {/* 自我评价 */}
            <div>
              <label className="flex items-center gap-2 text-white font-medium mb-3">
                <Edit3 className="h-4 w-4 text-emerald-400" />
                自我评价
                <span className="text-red-400">*</span>
              </label>
              <textarea
                value={formData.selfEvaluation}
                onChange={(e) =>
                  onInputChange("selfEvaluation", e.target.value)
                }
                placeholder="请客观评价本月工作表现，包括工作质量、工作效率、协作能力等方面..."
                className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 resize-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                建议包含：工作完成度、能力提升、团队贡献等
              </p>
            </div>

            {/* 工作亮点 */}
            <div>
              <label className="flex items-center gap-2 text-white font-medium mb-3">
                <Lightbulb className="h-4 w-4 text-amber-400" />
                工作亮点
              </label>
              <textarea
                value={formData.highlights}
                onChange={(e) => onInputChange("highlights", e.target.value)}
                placeholder="请列举本月工作中的亮点和突出成果，如创新方案、重要突破、优秀表现等..."
                className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 resize-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                建议包含：创新点、突破性成果、优秀表现等
              </p>
            </div>

            {/* 问题与挑战 */}
            <div>
              <label className="flex items-center gap-2 text-white font-medium mb-3">
                <AlertCircle className="h-4 w-4 text-orange-400" />
                问题与挑战
              </label>
              <textarea
                value={formData.problems}
                onChange={(e) => onInputChange("problems", e.target.value)}
                placeholder="请描述本月工作中遇到的问题、挑战以及解决方案..."
                className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-orange-500 resize-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                建议包含：遇到的问题、解决方案、经验总结等
              </p>
            </div>

            {/* 下月计划 */}
            <div>
              <label className="flex items-center gap-2 text-white font-medium mb-3">
                <TrendingUp className="h-4 w-4 text-purple-400" />
                下月计划
              </label>
              <textarea
                value={formData.nextMonthPlan}
                onChange={(e) => onInputChange("nextMonthPlan", e.target.value)}
                placeholder="请描述下月的工作计划和目标，包括重点任务、预期成果等..."
                className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
              />
              <p className="text-xs text-slate-500 mt-2">
                建议包含：重点任务、预期目标、工作计划等
              </p>
            </div>
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex items-center gap-3 pt-4 border-t border-slate-700/50">
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
              {isSubmitting ? "提交中..." : "提交总结"}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
