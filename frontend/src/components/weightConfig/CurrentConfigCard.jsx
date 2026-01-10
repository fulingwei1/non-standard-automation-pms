import { Info, RotateCcw, Save, Users, Briefcase } from "lucide-react";
import { fadeIn } from "../../utils/weightConfigUtils";
import { motion } from "framer-motion";
import { WeightInputCard } from "./WeightInputCard";
import { WeightValidation } from "./WeightValidation";

/**
 * 当前配置卡片组件
 */
export const CurrentConfigCard = ({
  weights,
  isDirty,
  isValidWeight,
  totalWeight,
  isSaving,
  onWeightChange,
  onReset,
  onSave,
}) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
        <div className="flex items-center gap-3 mb-6">
          <Info className="h-5 w-5 text-blue-400" />
          <h2 className="text-xl font-bold text-white">当前权重配置</h2>
          {isDirty && (
            <span className="px-3 py-1 bg-amber-500/20 text-amber-400 text-sm rounded-full">
              未保存
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 部门经理权重 */}
          <WeightInputCard
            type="dept"
            label="部门经理评价"
            description="直属上级评价"
            icon={Users}
            iconColor="text-blue-400"
            weight={weights.deptManager}
            onChange={onWeightChange}
          />

          {/* 项目经理权重 */}
          <WeightInputCard
            type="project"
            label="项目经理评价"
            description="项目绩效评价"
            icon={Briefcase}
            iconColor="text-purple-400"
            weight={weights.projectManager}
            onChange={onWeightChange}
          />
        </div>

        {/* 权重总和验证 */}
        <WeightValidation totalWeight={totalWeight} isValid={isValidWeight} />

        {/* 操作按钮 */}
        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={onReset}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            重置为默认
          </button>

          <button
            onClick={onSave}
            disabled={!isDirty || !isValidWeight || isSaving}
            className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-700 disabled:to-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isSaving ? "保存中..." : "保存配置"}
          </button>
        </div>
      </div>
    </motion.div>
  );
};
