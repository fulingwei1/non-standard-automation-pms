import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { pmoApi } from '../services/api'
import { formatDate } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  Badge,
  SkeletonCard,
} from '../components/ui'
import {
  AlertTriangle,
  TrendingUp,
  Building2,
  Target,
  ArrowRight,
} from 'lucide-react'

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
}

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

const getRiskLevelBadge = (level) => {
  const badges = {
    CRITICAL: {
      label: '严重',
      variant: 'danger',
      color: 'text-red-400',
      bgColor: 'bg-red-500/20',
      borderColor: 'border-red-500/30',
    },
    HIGH: {
      label: '高',
      variant: 'danger',
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/20',
      borderColor: 'border-orange-500/30',
    },
    MEDIUM: {
      label: '中',
      variant: 'warning',
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-500/20',
      borderColor: 'border-yellow-500/30',
    },
    LOW: {
      label: '低',
      variant: 'info',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20',
      borderColor: 'border-blue-500/30',
    },
  }
  return badges[level] || badges.LOW
}

export default function RiskWall() {
  const [loading, setLoading] = useState(true)
  const [riskData, setRiskData] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const res = await pmoApi.riskWall()
      const data = res.data || res
      setRiskData(data)
    } catch (err) {
      console.error('Failed to fetch risk wall data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="风险预警墙" description="全项目风险监控与预警" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array(4)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      </div>
    )
  }

  if (!riskData) {
    return (
      <div className="space-y-6">
        <PageHeader title="风险预警墙" description="全项目风险监控与预警" />
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无数据
          </CardContent>
        </Card>
      </div>
    )
  }

  const {
    total_risks,
    critical_risks,
    high_risks,
    by_category,
    by_project,
  } = riskData

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="风险预警墙"
        description="全项目风险监控与预警，重点关注严重和高风险"
      />

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">总风险数</p>
                <p className="text-2xl font-bold text-white">{total_risks || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Target className="h-6 w-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">严重风险</p>
                <p className="text-2xl font-bold text-red-400">
                  {critical_risks?.length || 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-red-500/20">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">高风险</p>
                <p className="text-2xl font-bold text-orange-400">
                  {high_risks?.length || 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-orange-500/20">
                <AlertTriangle className="h-6 w-6 text-orange-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical Risks */}
        <motion.div variants={staggerChild}>
          <Card className="border-l-4 border-red-500">
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5 bg-red-500/10">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <h3 className="text-lg font-semibold text-white">严重风险</h3>
                  <Badge variant="danger" className="ml-2">
                    {critical_risks?.length || 0}
                  </Badge>
                </div>
              </div>

              {critical_risks && critical_risks.length > 0 ? (
                <div className="divide-y divide-white/5">
                  {critical_risks.map((risk) => {
                    const levelBadge = getRiskLevelBadge(risk.risk_level)
                    return (
                      <Link
                        key={risk.id}
                        to={`/pmo/risks/${risk.project_id}`}
                        className="block p-5 hover:bg-white/[0.02] transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={cn(
                              'p-2 rounded-lg',
                              levelBadge.bgColor,
                              'ring-1',
                              levelBadge.borderColor
                            )}
                          >
                            <AlertTriangle
                              className={cn('h-4 w-4', levelBadge.color)}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-white mb-1 line-clamp-1">
                              {risk.risk_name}
                            </h4>
                            <p className="text-sm text-slate-400 line-clamp-2 mb-2">
                              {risk.description}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span>{risk.risk_category}</span>
                              {risk.owner_name && (
                                <>
                                  <span>•</span>
                                  <span>负责人: {risk.owner_name}</span>
                                </>
                              )}
                              {risk.created_at && (
                                <>
                                  <span>•</span>
                                  <span>{formatDate(risk.created_at)}</span>
                                </>
                              )}
                            </div>
                          </div>
                          <ArrowRight className="h-5 w-5 text-slate-500 flex-shrink-0" />
                        </div>
                      </Link>
                    )
                  })}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无严重风险
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* High Risks */}
        <motion.div variants={staggerChild}>
          <Card className="border-l-4 border-orange-500">
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5 bg-orange-500/10">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-400" />
                  <h3 className="text-lg font-semibold text-white">高风险</h3>
                  <Badge variant="danger" className="ml-2">
                    {high_risks?.length || 0}
                  </Badge>
                </div>
              </div>

              {high_risks && high_risks.length > 0 ? (
                <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto">
                  {high_risks.map((risk) => {
                    const levelBadge = getRiskLevelBadge(risk.risk_level)
                    return (
                      <Link
                        key={risk.id}
                        to={`/pmo/risks/${risk.project_id}`}
                        className="block p-5 hover:bg-white/[0.02] transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={cn(
                              'p-2 rounded-lg',
                              levelBadge.bgColor,
                              'ring-1',
                              levelBadge.borderColor
                            )}
                          >
                            <AlertTriangle
                              className={cn('h-4 w-4', levelBadge.color)}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-white mb-1 line-clamp-1">
                              {risk.risk_name}
                            </h4>
                            <p className="text-sm text-slate-400 line-clamp-2 mb-2">
                              {risk.description}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span>{risk.risk_category}</span>
                              {risk.owner_name && (
                                <>
                                  <span>•</span>
                                  <span>负责人: {risk.owner_name}</span>
                                </>
                              )}
                            </div>
                          </div>
                          <ArrowRight className="h-5 w-5 text-slate-500 flex-shrink-0" />
                        </div>
                      </Link>
                    )
                  })}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无高风险
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* By Category */}
        <motion.div variants={staggerChild}>
          <Card>
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">按类别统计</h3>
              </div>

              {by_category && Object.keys(by_category).length > 0 ? (
                <div className="p-5 space-y-3">
                  {Object.entries(by_category)
                    .sort(([, a], [, b]) => b - a)
                    .map(([category, count]) => (
                      <div
                        key={category}
                        className="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5"
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-primary/20">
                            <Target className="h-4 w-4 text-primary" />
                          </div>
                          <span className="text-white font-medium">{category}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-white">{count}</span>
                          <span className="text-sm text-slate-400">个</span>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无类别数据
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* By Project */}
        <motion.div variants={staggerChild}>
          <Card>
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">按项目统计</h3>
              </div>

              {by_project && by_project.length > 0 ? (
                <div className="p-5 space-y-3">
                  {by_project.map((item) => (
                    <Link
                      key={item.project_id}
                      to={`/pmo/risks/${item.project_id}`}
                      className="block p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-emerald-500/20">
                            <Building2 className="h-4 w-4 text-emerald-400" />
                          </div>
                          <div>
                            <p className="text-white font-medium">
                              {item.project_name}
                            </p>
                            <p className="text-xs text-slate-400">
                              {item.project_code}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold text-white">
                            {item.risk_count}
                          </span>
                          <span className="text-sm text-slate-400">个风险</span>
                          <ArrowRight className="h-4 w-4 text-slate-500" />
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无项目数据
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  )
}



