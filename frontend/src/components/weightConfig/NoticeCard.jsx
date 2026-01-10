import { AlertCircle } from 'lucide-react'
import { fadeIn } from '../../utils/weightConfigUtils'
import { motion } from 'framer-motion'

/**
 * 注意事项卡片组件
 */
export const NoticeCard = () => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.5 }}>
      <div className="bg-amber-500/10 rounded-lg p-4 border border-amber-500/20">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-slate-300 space-y-1">
            <p className="font-medium text-white mb-2">配置注意事项：</p>
            <p>• 权重配置会立即生效，影响所有员工的绩效计算</p>
            <p>• 建议在绩效评价周期开始前调整权重配置</p>
            <p>• 部门经理权重 + 项目经理权重必须等于100%</p>
            <p>• 权重调整应基于公司战略和管理需求，建议每季度评估一次</p>
            <p>• 所有配置变更都会记录在历史记录中，便于追溯</p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
