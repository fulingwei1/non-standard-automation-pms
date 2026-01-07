import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { pmoApi } from '../services/api'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  StatCard,
  Progress,
  SkeletonCard,
} from '../components/ui'
import {
  Users,
  UserCheck,
  UserX,
  AlertTriangle,
  Building2,
  TrendingUp,
  Activity,
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

export default function ResourceOverview() {
  const [loading, setLoading] = useState(true)
  const [resourceData, setResourceData] = useState(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const res = await pmoApi.resourceOverview()
      const data = res.data || res
      setResourceData(data)
    } catch (err) {
      console.error('Failed to fetch resource overview:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="资源总览" description="项目资源分配与负荷分析" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array(4)
            .fill(null)
            .map((_, i) => (
              <SkeletonCard key={i} />
            ))}
        </div>
      </div>
    )
  }

  if (!resourceData) {
    return (
      <div className="space-y-6">
        <PageHeader title="资源总览" description="项目资源分配与负荷分析" />
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无数据
          </CardContent>
        </Card>
      </div>
    )
  }

  const {
    total_resources,
    allocated_resources,
    available_resources,
    overloaded_resources,
    by_department,
  } = resourceData

  const allocationRate =
    total_resources > 0
      ? ((allocated_resources / total_resources) * 100).toFixed(1)
      : 0

  const statCards = [
    {
      icon: Users,
      label: '总资源数',
      value: total_resources || 0,
      change: '人员总数',
      trend: 'up',
      color: 'text-blue-400',
    },
    {
      icon: UserCheck,
      label: '已分配',
      value: allocated_resources || 0,
      change: `${allocationRate}% 分配率`,
      trend: 'up',
      color: 'text-emerald-400',
    },
    {
      icon: UserX,
      label: '可用资源',
      value: available_resources || 0,
      change: '可分配',
      trend: 'up',
      color: 'text-violet-400',
    },
    {
      icon: AlertTriangle,
      label: '超负荷',
      value: overloaded_resources || 0,
      change: overloaded_resources > 0 ? '需关注' : '正常',
      trend: overloaded_resources > 0 ? 'down' : 'up',
      color: 'text-red-400',
    },
  ]

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="资源总览"
        description="项目资源分配与负荷分析"
      />

      {/* Stats Grid */}
      <motion.div
        variants={staggerChild}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {statCards.map((stat, i) => (
          <StatCard key={i} {...stat} />
        ))}
      </motion.div>

      {/* Overall Allocation */}
      <motion.div variants={staggerChild} className="mb-6">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">资源分配概览</h3>
              <div className="text-2xl font-bold text-primary">
                {allocationRate}%
              </div>
            </div>
            <Progress value={parseFloat(allocationRate)} />
            <div className="flex items-center justify-between mt-4 text-sm text-slate-400">
              <span>已分配: {allocated_resources || 0} 人</span>
              <span>可用: {available_resources || 0} 人</span>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* By Department */}
      <motion.div variants={staggerChild}>
        <Card>
          <CardContent className="p-0">
            <div className="flex items-center justify-between p-5 border-b border-white/5">
              <h3 className="text-lg font-semibold text-white">按部门统计</h3>
            </div>

            {by_department && by_department.length > 0 ? (
              <div className="divide-y divide-white/5">
                {by_department.map((dept, index) => {
                  const deptAllocationRate =
                    dept.total_resources > 0
                      ? ((dept.allocated_resources / dept.total_resources) * 100).toFixed(1)
                      : 0
                  const isOverloaded = parseFloat(deptAllocationRate) > 90

                  return (
                    <div
                      key={dept.department_id || index}
                      className="p-5 hover:bg-white/[0.02] transition-colors"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={cn(
                              'p-2.5 rounded-xl',
                              isOverloaded
                                ? 'bg-red-500/20 ring-1 ring-red-500/30'
                                : 'bg-primary/20 ring-1 ring-primary/20'
                            )}
                          >
                            <Building2
                              className={cn(
                                'h-5 w-5',
                                isOverloaded ? 'text-red-400' : 'text-primary'
                              )}
                            />
                          </div>
                          <div>
                            <h4 className="font-semibold text-white">
                              {dept.department_name}
                            </h4>
                            <p className="text-xs text-slate-400">
                              总资源: {dept.total_resources || 0} 人
                            </p>
                          </div>
                        </div>
                        {isOverloaded && (
                          <div className="flex items-center gap-2 text-red-400">
                            <AlertTriangle className="h-4 w-4" />
                            <span className="text-sm font-medium">超负荷</span>
                          </div>
                        )}
                      </div>

                      <div className="mb-3">
                        <div className="flex justify-between text-xs mb-2">
                          <span className="text-slate-400">分配率</span>
                          <span className="text-white font-medium">
                            {deptAllocationRate}%
                          </span>
                        </div>
                        <Progress
                          value={parseFloat(deptAllocationRate)}
                          color={isOverloaded ? 'danger' : 'primary'}
                        />
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-slate-400">已分配</span>
                          <p className="text-white font-medium mt-1">
                            {dept.allocated_resources || 0} 人
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-400">可用</span>
                          <p className="text-white font-medium mt-1">
                            {dept.available_resources || 0} 人
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-400">利用率</span>
                          <p
                            className={cn(
                              'font-medium mt-1',
                              isOverloaded ? 'text-red-400' : 'text-emerald-400'
                            )}
                          >
                            {deptAllocationRate}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="p-12 text-center text-slate-500">
                暂无部门数据
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}



