import React, { useMemo } from "react";
import { motion } from "framer-motion";
import { Settings, AlertCircle } from "lucide-react";
import { useWeightConfig } from "../hooks/useWeightConfig";
import { fadeIn, validateWeights } from "../utils/weightConfigUtils";
import { CurrentConfigCard } from "../components/weightConfig/CurrentConfigCard";
import { ImpactStatistics } from "../components/weightConfig/ImpactStatistics";
import { CalculationExamples } from "../components/weightConfig/CalculationExamples";
import { ConfigHistory } from "../components/weightConfig/ConfigHistory";
import { NoticeCard } from "../components/weightConfig/NoticeCard";

const EvaluationWeightConfig = () => {
  const {
    weights,
    isDirty,
    isSaving,
    isLoading,
    error,
    configHistory,
    impactStatistics,
    handleWeightChange,
    handleReset,
    handleSave,
  } = useWeightConfig();

  // 验证权重总和
  const { totalWeight, isValid: isValidWeight } = useMemo(
    () => validateWeights(weights),
    [weights],
  );

  // 加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-slate-400">加载配置中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                绩效评价权重配置
              </h1>
              <p className="text-slate-400">
                调整部门经理和项目经理的评价权重分配
              </p>
            </div>
            <Settings className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 错误提示 */}
        {error && (
          <motion.div {...fadeIn}>
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-400" />
                <p className="text-red-300">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* 当前配置卡片 */}
        <CurrentConfigCard
          weights={weights}
          isDirty={isDirty}
          isValidWeight={isValidWeight}
          totalWeight={totalWeight}
          isSaving={isSaving}
          onWeightChange={handleWeightChange}
          onReset={handleReset}
          onSave={handleSave}
        />

        {/* 影响范围统计 */}
        <ImpactStatistics statistics={impactStatistics} />

        {/* 配置示例 */}
        <CalculationExamples weights={weights} />

        {/* 配置历史 */}
        <ConfigHistory history={configHistory} />

        {/* 注意事项 */}
        <NoticeCard />
      </motion.div>
    </div>
  );
};

export default EvaluationWeightConfig;
