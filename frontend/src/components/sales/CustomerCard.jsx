/**
 * Customer Card Component - Displays customer information in a card format
 */

import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'
import { fadeIn } from '../../lib/animations'
import {
  Building2,
  MapPin,
  Phone,
  Mail,
  Calendar,
  Star,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  MoreHorizontal,
} from 'lucide-react'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'

const gradeColors = {
  A: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  B: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  C: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  D: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
}

const statusConfig = {
  active: { label: '活跃', color: 'bg-emerald-500' },
  potential: { label: '潜在', color: 'bg-blue-500' },
  dormant: { label: '沉睡', color: 'bg-amber-500' },
  lost: { label: '流失', color: 'bg-red-500' },
}

export default function CustomerCard({ customer, onClick, compact = false }) {
  const {
    id,
    name,
    shortName,
    grade = 'B',
    status = 'active',
    industry,
    location,
    contactPerson,
    phone,
    email,
    lastContact,
    totalAmount = 0,
    pendingAmount = 0,
    projectCount = 0,
    opportunityCount = 0,
    tags = [],
    isWarning = false,
  } = customer

  const gradeClass = gradeColors[grade] || gradeColors.B
  const statusConf = statusConfig[status] || statusConfig.active

  if (compact) {
    return (
      <motion.div
        variants={fadeIn}
        onClick={() => onClick?.(customer)}
        className="flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 cursor-pointer transition-colors group"
      >
        <div className="flex items-center gap-3">
          <div className={cn('w-2 h-2 rounded-full', statusConf.color)} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-white">{shortName || name}</span>
              <Badge variant="outline" className={cn('text-xs', gradeClass)}>
                {grade}级
              </Badge>
            </div>
            <span className="text-xs text-slate-400">{industry}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {opportunityCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {opportunityCount}个商机
            </Badge>
          )}
          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors" />
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      variants={fadeIn}
      onClick={() => onClick?.(customer)}
      className={cn(
        'bg-surface-100/50 backdrop-blur-sm rounded-xl border border-white/5 p-4',
        'hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5 cursor-pointer transition-all',
        isWarning && 'border-amber-500/30'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
            <Building2 className="w-5 h-5 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-white">{shortName || name}</h3>
              <Badge variant="outline" className={cn('text-xs', gradeClass)}>
                {grade}级
              </Badge>
              {isWarning && (
                <AlertTriangle className="w-4 h-4 text-amber-500" />
              )}
            </div>
            <p className="text-xs text-slate-400">{name}</p>
          </div>
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <MoreHorizontal className="w-4 h-4 text-slate-400" />
        </Button>
      </div>

      {/* Info */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <MapPin className="w-3 h-3" />
          <span>{location || '未设置'}</span>
          <span className="text-slate-600">|</span>
          <span>{industry || '未分类'}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Phone className="w-3 h-3" />
          <span>{contactPerson || '未设置联系人'}</span>
          {phone && <span className="text-slate-500">· {phone}</span>}
        </div>
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {tags.slice(0, 3).map((tag, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {tags.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{tags.length - 3}
            </Badge>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-slate-400">累计金额</div>
          <div className="text-sm font-semibold text-white">
            ¥{(totalAmount / 10000).toFixed(0)}万
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-400">待回款</div>
          <div className={cn(
            'text-sm font-semibold',
            pendingAmount > 0 ? 'text-amber-400' : 'text-slate-500'
          )}>
            ¥{(pendingAmount / 10000).toFixed(0)}万
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-400">项目数</div>
          <div className="text-sm font-semibold text-white">{projectCount}</div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Calendar className="w-3 h-3" />
          <span>上次联系: {lastContact || '无记录'}</span>
        </div>
        <div className={cn('w-2 h-2 rounded-full', statusConf.color)} title={statusConf.label} />
      </div>
    </motion.div>
  )
}

