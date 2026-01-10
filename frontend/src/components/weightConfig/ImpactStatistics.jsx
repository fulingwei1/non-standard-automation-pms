import { TrendingUp, Info } from 'lucide-react'
import { fadeIn } from '../../utils/weightConfigUtils'
import { motion } from 'framer-motion'

/**
 * 影响范围统计组件
 */
export const ImpactStatistics = ({ statistics }) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
        <div className="flex items-center gap-3 mb-6">
          <TrendingUp className="h-5 w-5 text-purple-400" />
          <h3 className="text-xl font-bold text-white">影响范围统计</h3>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-2">总员工数</p>
            <p className="text-3xl font-bold text-blue-400">{statistics.totalEmployees}</p>
          </div>

          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-2">受影响员工</p>
            <p className="text-3xl font-bold text-purple-400">{statistics.affectedEmployees}</p>
            <p className="text-xs text-slate-500 mt-1">参与项目的员工</p>
          </div>

          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-2">涉及部门</p>
            <p className="text-3xl font-bold text-emerald-400">{statistics.departments}</p>
          </div>

          <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
            <p className="text-sm text-slate-400 mb-2">活跃项目</p>
            <p className="text-3xl font-bold text-amber-400">{statistics.activeProjects}</p>
          </div>
        </div>

        <div className="mt-4 p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-slate-300">
              <p className="font-medium text-white mb-1">说明</p>
              <p>• 对于参与项目的员工，最终得分 = 部门经理评分 × 部门权重 + 项目经理评分 × 项目权重</p>
              <p>• 对于未参与项目的员工，直接使用部门经理评分作为最终得分</p>
              <p>• 参与多个项目的员工，项目经理评分为各项目评分的加权平均</p>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
