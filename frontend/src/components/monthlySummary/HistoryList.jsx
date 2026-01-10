import { Calendar, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { cn } from '../../lib/utils'
import { getStatusBadge, getLevelColor, fadeIn } from '../../utils/monthlySummaryUtils'
import { motion } from 'framer-motion'

/**
 * 历史记录列表组件
 */
export const HistoryList = ({ showHistory, onToggle, isLoading, history }) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
        <button
          onClick={onToggle}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-700/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Calendar className="h-5 w-5 text-slate-400" />
            <span className="text-white font-medium">历史总结记录</span>
            <span className="text-sm text-slate-400">（共 {history.length} 条）</span>
          </div>
          {showHistory ? (
            <ChevronUp className="h-5 w-5 text-slate-400" />
          ) : (
            <ChevronDown className="h-5 w-5 text-slate-400" />
          )}
        </button>

        {showHistory && (
          <div className="border-t border-slate-700/50">
            <div className="p-6 space-y-4">
              {isLoading ? (
                <div className="text-center py-8 text-slate-400">
                  <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                  <p>加载中...</p>
                </div>
              ) : history.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>暂无历史记录</p>
                </div>
              ) : (
                history.map((record, index) => (
                  <motion.div
                    key={record.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50 hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="text-white font-medium text-lg mb-1">
                          {record.period.split('-')[0]}年{record.period.split('-')[1]}月
                        </p>
                        <p className="text-sm text-slate-400">
                          提交时间: {record.submit_date || record.submitDate}
                        </p>
                      </div>
                      <span className={cn(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getStatusBadge(record.status).color
                      )}>
                        {getStatusBadge(record.status).label}
                      </span>
                    </div>

                    {record.status === 'COMPLETED' && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-700/50">
                        <div>
                          <p className="text-xs text-slate-400 mb-1">综合得分</p>
                          <p className={cn('text-2xl font-bold', getLevelColor(record.level))}>
                            {record.score} <span className="text-base">({record.level}级)</span>
                          </p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-400 mb-1">部门经理评分</p>
                          <p className="text-xl font-medium text-blue-400">{record.dept_score || record.deptScore}</p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-400 mb-2">项目经理评分</p>
                          {(record.project_scores || record.projectScores || []).map((ps, idx) => (
                            <div key={idx} className="flex items-center justify-between text-sm mb-1">
                              <span className="text-slate-400">{ps.project_name || ps.projectName}</span>
                              <span className="text-purple-400 font-medium">
                                {ps.score} (权重{ps.weight}%)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  )
}
