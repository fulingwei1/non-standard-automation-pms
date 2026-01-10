import { Edit3 } from "lucide-react";
import { fadeIn } from "../../utils/weightConfigUtils";
import { motion } from "framer-motion";

/**
 * 计算示例组件
 */
export const CalculationExamples = ({ weights }) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
        <div className="flex items-center gap-3 mb-6">
          <Edit3 className="h-5 w-5 text-emerald-400" />
          <h3 className="text-xl font-bold text-white">计算示例</h3>
        </div>

        <div className="space-y-4">
          {/* 示例1：参与项目 */}
          <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <h4 className="text-white font-medium mb-3">
              示例1：员工参与1个项目
            </h4>
            <div className="space-y-2 text-sm text-slate-300">
              <p>• 部门经理评分：85分（权重 {weights.deptManager}%）</p>
              <p>• 项目经理评分：90分（权重 {weights.projectManager}%）</p>
              <p className="pt-2 border-t border-slate-700/50 text-blue-400 font-medium">
                最终得分 = 85 × {weights.deptManager}% + 90 ×{" "}
                {weights.projectManager}% ={" "}
                {(
                  (85 * weights.deptManager) / 100 +
                  (90 * weights.projectManager) / 100
                ).toFixed(1)}
                分
              </p>
            </div>
          </div>

          {/* 示例2：参与多个项目 */}
          <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <h4 className="text-white font-medium mb-3">
              示例2：员工参与2个项目
            </h4>
            <div className="space-y-2 text-sm text-slate-300">
              <p>• 部门经理评分：88分（权重 {weights.deptManager}%）</p>
              <p>• 项目A经理评分：92分（项目权重 60%）</p>
              <p>• 项目B经理评分：85分（项目权重 40%）</p>
              <p className="text-slate-400">
                → 项目经理综合评分 = 92 × 60% + 85 × 40% ={" "}
                {(92 * 0.6 + 85 * 0.4).toFixed(1)}分
              </p>
              <p className="pt-2 border-t border-slate-700/50 text-purple-400 font-medium">
                最终得分 = 88 × {weights.deptManager}% +{" "}
                {(92 * 0.6 + 85 * 0.4).toFixed(1)} × {weights.projectManager}% ={" "}
                {(
                  (88 * weights.deptManager) / 100 +
                  ((92 * 0.6 + 85 * 0.4) * weights.projectManager) / 100
                ).toFixed(1)}
                分
              </p>
            </div>
          </div>

          {/* 示例3：未参与项目 */}
          <div className="p-4 bg-slate-900/30 rounded-lg border border-slate-700/50">
            <h4 className="text-white font-medium mb-3">
              示例3：员工未参与项目
            </h4>
            <div className="space-y-2 text-sm text-slate-300">
              <p>• 部门经理评分：82分</p>
              <p>• 项目经理评分：无</p>
              <p className="pt-2 border-t border-slate-700/50 text-emerald-400 font-medium">
                最终得分 = 82分（直接使用部门经理评分）
              </p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
