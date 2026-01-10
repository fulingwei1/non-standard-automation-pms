/**
 * HRRelationsTab Component
 * 员工关系 Tab 组件
 */
import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '../../ui'
import { AlertTriangle, CheckCircle2, Heart } from 'lucide-react'
import { cn } from '../../../lib/utils'

// 状态标签映射
const getStatusLabel = (status) => {
  const labels = {
    active: '在职',
    pending: '待处理',
    reviewing: '评审中',
    processing: '处理中',
    completed: '已完成',
  }
  return labels[status] || status
}

// 问题类型颜色
const getIssueTypeColor = (type) => {
  const colors = {
    conflict: 'bg-red-500/20 text-red-400 border-red-500/30',
    leave: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    complaint: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    performance: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  }
  return colors[type] || 'bg-slate-500/20 text-slate-400 border-slate-500/30'
}

export default function HRRelationsTab({
  mockHRStats,
  mockEmployeeIssues,
}) {
  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">待处理问题</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.pendingEmployeeIssues}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">已解决问题</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.resolvedIssues}
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-50 border-white/10">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">员工满意度</p>
                <p className="text-3xl font-bold text-white">
                  {mockHRStats.employeeSatisfaction}%
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-pink-500/20 flex items-center justify-center">
                <Heart className="w-6 h-6 text-pink-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Employee Issues List */}
      <Card className="bg-surface-50 border-white/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-primary" />
            员工关系问题
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockEmployeeIssues.map((issue, index) => (
              <motion.div
                key={issue.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge
                        className={cn('text-xs', getIssueTypeColor(issue.type))}
                      >
                        {issue.type === 'conflict'
                          ? '冲突'
                          : issue.type === 'leave'
                          ? '请假'
                          : issue.type === 'complaint'
                          ? '投诉'
                          : '绩效'}
                      </Badge>
                      <span className="text-sm font-semibold text-white">
                        {issue.title}
                      </span>
                      {issue.priority === 'high' && (
                        <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                          紧急
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 mb-2">
                      {issue.description}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span>
                        {issue.employee} · {issue.department}
                      </span>
                      <span>{issue.createdAt}</span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <Badge
                      className={cn(
                        'text-xs',
                        issue.status === 'pending' &&
                          'bg-amber-500/20 text-amber-400',
                        issue.status === 'reviewing' &&
                          'bg-blue-500/20 text-blue-400',
                        issue.status === 'processing' &&
                          'bg-purple-500/20 text-purple-400'
                      )}
                    >
                      {getStatusLabel(issue.status)}
                    </Badge>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
