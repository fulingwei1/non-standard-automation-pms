/**
 * Opportunity Card Component - Displays sales opportunity information
 */

import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'
import { fadeIn } from '../../lib/animations'
import {
  Target,
  Building2,
  Calendar,
  DollarSign,
  User,
  MessageSquare,
  ChevronRight,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Flame,
} from 'lucide-react'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'

const stageConfig = {
  lead: { label: '潜在', color: 'bg-violet-500', progress: 10 },
  contact: { label: '意向', color: 'bg-blue-500', progress: 30 },
  quote: { label: '报价', color: 'bg-amber-500', progress: 50 },
  negotiate: { label: '谈判', color: 'bg-pink-500', progress: 75 },
  won: { label: '赢单', color: 'bg-emerald-500', progress: 100 },
  lost: { label: '输单', color: 'bg-red-500', progress: 0 },
}

const priorityConfig = {
  high: { label: '高', color: 'text-red-400 bg-red-500/20' },
  medium: { label: '中', color: 'text-amber-400 bg-amber-500/20' },
  low: { label: '低', color: 'text-slate-400 bg-slate-500/20' },
}

export default function OpportunityCard({ opportunity, onClick, draggable = false }) {
  const {
    name,
    customerName,
    customerShort,
    stage = 'lead',
    priority = 'medium',
    expectedAmount = 0,
    expectedCloseDate,
    probability = 50,
    owner,
    daysInStage = 0,
    isHot = false,
    isOverdue = false,
    tags = [],
  } = opportunity

  const stageConf = stageConfig[stage] || stageConfig.lead
  const priorityConf = priorityConfig[priority] || priorityConfig.medium

  const getDaysColor = () => {
    if (daysInStage > 14) return 'text-red-400'
    if (daysInStage > 7) return 'text-amber-400'
    return 'text-slate-400'
  }

  return (
    <motion.div
      variants={fadeIn}
      onClick={() => onClick?.(opportunity)}
      draggable={draggable}
      className={cn(
        'bg-surface-100/50 backdrop-blur-sm rounded-xl border border-white/5 p-4',
        'hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 cursor-pointer transition-all',
        isOverdue && 'border-red-500/30',
        isHot && 'border-amber-500/30',
        draggable && 'cursor-grab active:cursor-grabbing'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            {isHot && <Flame className="w-4 h-4 text-amber-500" />}
            <h3 className="font-semibold text-white truncate">{name}</h3>
          </div>
          <div className="flex items-center gap-2">
            <Building2 className="w-3 h-3 text-slate-400" />
            <span className="text-xs text-slate-400">{customerShort || customerName}</span>
          </div>
        </div>
        <Badge className={cn('text-xs', priorityConf.color)}>
          {priorityConf.label}
        </Badge>
      </div>

      {/* Stage Indicator */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className={cn('w-2 h-2 rounded-full', stageConf.color)} />
            <span className="text-xs text-slate-300">{stageConf.label}</span>
          </div>
          <span className="text-xs text-slate-400">成功率 {probability}%</span>
        </div>
        <Progress value={stageConf.progress} className="h-1.5" />
      </div>

      {/* Amount */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-amber-500" />
          <span className="text-lg font-semibold text-white">
            ¥{(expectedAmount / 10000).toFixed(0)}万
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Calendar className="w-3 h-3" />
          <span>预计: {expectedCloseDate || '未设置'}</span>
        </div>
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {tags.slice(0, 2).map((tag, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {tags.length > 2 && (
            <Badge variant="secondary" className="text-xs">
              +{tags.length - 2}
            </Badge>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <User className="w-3 h-3" />
            <span>{owner || '未分配'}</span>
          </div>
          <div className={cn('flex items-center gap-1 text-xs', getDaysColor())}>
            <Clock className="w-3 h-3" />
            <span>{daysInStage}天</span>
          </div>
        </div>
        {isOverdue && (
          <Badge variant="destructive" className="text-xs">
            <AlertTriangle className="w-3 h-3 mr-1" />
            逾期
          </Badge>
        )}
      </div>
    </motion.div>
  )
}

// Compact version for list views
export function OpportunityListItem({ opportunity, onClick }) {
  const {
    name,
    customerShort,
    stage,
    expectedAmount,
    expectedCloseDate,
    isHot,
    isOverdue,
  } = opportunity

  const stageConf = stageConfig[stage] || stageConfig.lead

  return (
    <motion.div
      variants={fadeIn}
      onClick={() => onClick?.(opportunity)}
      className="flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 cursor-pointer transition-colors group"
    >
      <div className="flex items-center gap-3">
        <div className={cn('w-2 h-2 rounded-full', stageConf.color)} />
        <div>
          <div className="flex items-center gap-2">
            {isHot && <Flame className="w-3 h-3 text-amber-500" />}
            <span className="font-medium text-white">{name}</span>
            {isOverdue && <AlertTriangle className="w-3 h-3 text-red-400" />}
          </div>
          <span className="text-xs text-slate-400">{customerShort}</span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-amber-400">
          ¥{(expectedAmount / 10000).toFixed(0)}万
        </span>
        <span className="text-xs text-slate-400">{expectedCloseDate}</span>
        <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
      </div>
    </motion.div>
  )
}

