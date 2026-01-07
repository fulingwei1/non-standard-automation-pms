import { memo } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'
import { getHealthConfig } from '../../lib/constants'
import { Progress } from '../ui'
import {
  User,
  Calendar,
  AlertTriangle,
  Clock,
  Building2,
  Star,
  ChevronRight,
} from 'lucide-react'

/**
 * 项目卡片组件
 * 显示项目的基本信息，左边框颜色表示健康度
 */
const ProjectCard = memo(function ProjectCard({
  project,
  isRelevant = false,
  onClick,
  compact = false,
}) {
  const healthConfig = getHealthConfig(project.health || 'H1')
  
  // 计算逾期天数
  const getOverdueDays = () => {
    if (!project.planned_end_date) return 0
    const today = new Date()
    const endDate = new Date(project.planned_end_date)
    const diff = Math.floor((today - endDate) / (1000 * 60 * 60 * 24))
    return diff > 0 ? diff : 0
  }
  
  const overdueDays = getOverdueDays()
  
  // 进度百分比
  const progress = project.progress || 0

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      whileHover={{ scale: 1.02, y: -2 }}
      onClick={onClick}
      className={cn(
        'group relative cursor-pointer rounded-lg border-l-4 transition-all duration-200',
        'bg-surface-1/80 hover:bg-surface-2/80 backdrop-blur-sm',
        'border border-white/5 hover:border-white/10',
        'shadow-lg hover:shadow-xl',
        healthConfig.borderClass,
        isRelevant && 'ring-2 ring-primary/30'
      )}
    >
      {/* 相关标记 */}
      {isRelevant && (
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
          <Star className="w-3 h-3 text-white fill-white" />
        </div>
      )}

      <div className={cn('p-3', compact && 'p-2')}>
        {/* 头部：项目编号和健康度 */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-slate-400">
            {project.project_code || project.id}
          </span>
          <span className={cn(
            'text-xs px-2 py-0.5 rounded-full',
            healthConfig.bgClass,
            healthConfig.textClass
          )}>
            {healthConfig.label}
          </span>
        </div>

        {/* 项目名称 */}
        <h4 className={cn(
          'font-medium text-white mb-2 line-clamp-2 group-hover:text-primary transition-colors',
          compact ? 'text-sm' : 'text-base'
        )}>
          {project.name || project.project_name}
        </h4>

        {/* 进度条 */}
        {!compact && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
              <span>进度</span>
              <span>{progress}%</span>
            </div>
            <Progress 
              value={progress} 
              className="h-1.5"
              indicatorClassName={cn(
                progress < 30 && 'bg-red-500',
                progress >= 30 && progress < 70 && 'bg-amber-500',
                progress >= 70 && 'bg-emerald-500'
              )}
            />
          </div>
        )}

        {/* 关键信息 */}
        <div className={cn(
          'flex flex-wrap gap-2 text-xs text-slate-400',
          compact && 'gap-1'
        )}>
          {/* 客户 */}
          {project.customer_name && (
            <div className="flex items-center gap-1">
              <Building2 className="w-3 h-3" />
              <span className="truncate max-w-[80px]">{project.customer_name}</span>
            </div>
          )}
          
          {/* 负责人 */}
          {project.pm_name && (
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span>{project.pm_name}</span>
            </div>
          )}
          
          {/* 截止日期 */}
          {project.planned_end_date && (
            <div className={cn(
              'flex items-center gap-1',
              overdueDays > 0 && 'text-red-400'
            )}>
              <Calendar className="w-3 h-3" />
              <span>{project.planned_end_date}</span>
            </div>
          )}
          
          {/* 逾期天数 */}
          {overdueDays > 0 && (
            <div className="flex items-center gap-1 text-red-400">
              <AlertTriangle className="w-3 h-3" />
              <span>逾期{overdueDays}天</span>
            </div>
          )}
        </div>

        {/* 设备数量 */}
        {project.machine_count > 0 && !compact && (
          <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {project.machine_count} 台设备
            </span>
            <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-primary transition-colors" />
          </div>
        )}
      </div>
    </motion.div>
  )
})

export default ProjectCard

