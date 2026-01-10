import { Calendar, Clock, CheckCircle2 } from 'lucide-react'
import { cn } from '../../lib/utils'
import { getStatusBadge } from '../../utils/monthlySummaryUtils'
import { fadeIn } from '../../utils/monthlySummaryUtils'
import { motion } from 'framer-motion'

/**
 * 当前周期信息卡片组件
 */
export const PeriodInfoCard = ({ currentPeriod }) => {
  return (
    <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
        <div className="flex items-start justify-between">
          <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Calendar className="h-4 w-4" />
                <span className="text-sm">考核周期</span>
              </div>
              <p className="text-2xl font-bold text-white">
                {currentPeriod.year}年{currentPeriod.month}月
              </p>
              <p className="text-sm text-slate-400 mt-1">
                {currentPeriod.startDate} 至 {currentPeriod.endDate}
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <Clock className="h-4 w-4" />
                <span className="text-sm">剩余天数</span>
              </div>
              <p className="text-2xl font-bold text-amber-400">
                {currentPeriod.daysLeft} 天
              </p>
              <p className="text-sm text-slate-400 mt-1">
                请及时提交工作总结
              </p>
            </div>

            <div>
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm">提交状态</span>
              </div>
              <div className="mt-2">
                <span className={cn(
                  'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium',
                  getStatusBadge(currentPeriod.status).color
                )}>
                  {getStatusBadge(currentPeriod.status).label}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
