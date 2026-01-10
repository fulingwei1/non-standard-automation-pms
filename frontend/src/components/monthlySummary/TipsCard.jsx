import { AlertCircle } from 'lucide-react'
import { fadeIn } from '../../utils/monthlySummaryUtils'
import { motion } from 'framer-motion'

/**
 * 提示信息卡片组件
 */
export const TipsCard = () => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
      <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-300 space-y-1">
            <p className="font-medium text-white mb-2">温馨提示：</p>
            <p>• 每月需在月底前提交工作总结，逾期将影响绩效评价</p>
            <p>• 提交后系统将自动流转给部门经理和相关项目经理进行评分</p>
            <p>• 部门经理评分占 50%，项目经理评分占 50%（权重可由HR调整）</p>
            <p>• 季度绩效分数 = 三个月分数的加权平均</p>
            <p>• 若参与多个项目，最终得分 = 各项目经理评分的加权平均</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
