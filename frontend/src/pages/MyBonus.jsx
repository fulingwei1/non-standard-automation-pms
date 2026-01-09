/**
 * My Bonus - 我的奖金
 * 用户查看自己的奖金计算记录、发放记录和统计信息
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  Award, DollarSign, TrendingUp, Calendar, CheckCircle2, Clock,
  AlertCircle, Download, RefreshCw, FileText, Receipt, BarChart3
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { bonusApi } from '../services/api'
import { formatDate } from '../lib/utils'

const bonusTypeConfig = {
  'PERFORMANCE_BASED': { label: '绩效奖金', color: 'bg-blue-500/20 text-blue-400' },
  'PROJECT_BASED': { label: '项目奖金', color: 'bg-purple-500/20 text-purple-400' },
  'MILESTONE_BASED': { label: '里程碑奖金', color: 'bg-emerald-500/20 text-emerald-400' },
  'TEAM_BASED': { label: '团队奖金', color: 'bg-amber-500/20 text-amber-400' },
  'SALES_BASED': { label: '销售奖金', color: 'bg-green-500/20 text-green-400' },
  'SALES_DIRECTOR_BASED': { label: '销售总监奖金', color: 'bg-indigo-500/20 text-indigo-400' },
  'PRESALE_BASED': { label: '售前奖金', color: 'bg-pink-500/20 text-pink-400' },
}

const statusConfig = {
  'PENDING': { label: '待审批', color: 'bg-slate-500/20 text-slate-400', icon: Clock },
  'APPROVED': { label: '已审批', color: 'bg-blue-500/20 text-blue-400', icon: CheckCircle2 },
  'CANCELLED': { label: '已取消', color: 'bg-red-500/20 text-red-400', icon: AlertCircle },
}

const distributionStatusConfig = {
  'PENDING': { label: '待发放', color: 'bg-amber-500/20 text-amber-400', icon: Clock },
  'PAID': { label: '已发放', color: 'bg-emerald-500/20 text-emerald-400', icon: CheckCircle2 },
  'CANCELLED': { label: '已取消', color: 'bg-red-500/20 text-red-400', icon: AlertCircle },
}

export default function MyBonus() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [bonusData, setBonusData] = useState(null)
  const [statistics, setStatistics] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // overview, calculations, distributions

  // 获取当前用户信息
  const currentUser = JSON.parse(localStorage.getItem('user') || '{"name":"用户","department":"未知部门","position":"未知职位"}')

  // 加载我的奖金数据
  const loadMyBonus = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await bonusApi.getMyBonus()
      setBonusData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 加载统计信息
  const loadStatistics = async () => {
    try {
      const now = new Date()
      const startDate = new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0] // 年初
      const endDate = new Date().toISOString().split('T')[0] // 今天
      
      const response = await bonusApi.getMyBonusStatistics({
        start_date: startDate,
        end_date: endDate,
      })
      setStatistics(response.data)
    } catch (err) {
      console.error('操作失败:', err)
    }
  }

  useEffect(() => {
    loadMyBonus()
    loadStatistics()
  }, [])

  // 格式化金额
  const formatAmount = (amount) => {
    if (!amount) return '0.00'
    return parseFloat(amount).toLocaleString('zh-CN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  // 导出功能
  const handleExport = () => {
    if (!bonusData) {
      toast.warning('暂无数据可导出')
      return
    }

    try {
      const exportData = {
        '总金额': formatAmount(bonusData.total_amount),
        '已发放': formatAmount(bonusData.paid_amount),
        '待发放': formatAmount(bonusData.pending_amount),
        '计算记录数': bonusData.calculations?.length || 0,
        '发放记录数': bonusData.distributions?.length || 0,
        '导出日期': new Date().toLocaleDateString('zh-CN'),
      }

      const csvRows = [
        Object.keys(exportData).join(','),
        Object.values(exportData).join(','),
      ]

      const csvContent = csvRows.join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `我的奖金_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      toast.success('导出成功')
    } catch (error) {
      toast.error('导出失败: ' + error.message)
    }
  }

  if (loading && !bonusData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="我的奖金" description="查看个人奖金计算和发放记录" />
        <div className="container mx-auto px-4 py-6">
          <LoadingCard rows={5} />
        </div>
      </div>
    )
  }

  if (error && !bonusData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="我的奖金" description="查看个人奖金计算和发放记录" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage error={error} onRetry={loadMyBonus} />
        </div>
      </div>
    )
  }

  const data = bonusData || {
    total_amount: 0,
    pending_amount: 0,
    paid_amount: 0,
    calculations: [],
    distributions: [],
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="我的奖金"
        description="查看个人奖金计算和发放记录"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={async () => {
                await loadMyBonus()
                await loadStatistics()
                toast.success('数据已刷新')
              }}
              disabled={loading}
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              刷新
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExport}
            >
              <Download className="w-4 h-4" />
              导出
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border-blue-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-2">总奖金金额</p>
                    <p className="text-3xl font-bold text-white">
                      ¥{formatAmount(data.total_amount)}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Award className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/10 border-emerald-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-2">已发放金额</p>
                    <p className="text-3xl font-bold text-white">
                      ¥{formatAmount(data.paid_amount)}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/10 border-amber-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-2">待发放金额</p>
                    <p className="text-3xl font-bold text-white">
                      ¥{formatAmount(data.pending_amount)}
                    </p>
                  </div>
                  <div className="h-12 w-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Tab 导航 */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card className="bg-slate-800/30 border-slate-700">
            <CardContent className="p-4">
              <div className="flex gap-2">
                {[
                  { key: 'overview', label: '概览', icon: BarChart3 },
                  { key: 'calculations', label: '计算记录', icon: FileText },
                  { key: 'distributions', label: '发放记录', icon: Receipt },
                ].map((tab) => (
                  <Button
                    key={tab.key}
                    variant={activeTab === tab.key ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setActiveTab(tab.key)}
                    className="gap-2"
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* 概览 Tab */}
        {activeTab === 'overview' && (
          <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-4">
            {/* 统计信息 */}
            {statistics && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-white">年度统计</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">计算记录数</p>
                      <p className="text-2xl font-bold text-white">{statistics.calculation_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">发放记录数</p>
                      <p className="text-2xl font-bold text-white">{statistics.distribution_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">总计算金额</p>
                      <p className="text-2xl font-bold text-white">¥{formatAmount(statistics.total_calculated)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">总发放金额</p>
                      <p className="text-2xl font-bold text-white">¥{formatAmount(statistics.total_distributed)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 最近计算记录 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-white">最近计算记录</CardTitle>
              </CardHeader>
              <CardContent>
                {data.calculations && data.calculations.length > 0 ? (
                  <div className="space-y-3">
                    {data.calculations.slice(0, 5).map((calc) => {
                      const typeConfig = bonusTypeConfig[calc.bonus_type] || { label: calc.bonus_type, color: 'bg-slate-500/20 text-slate-400' }
                      const status = statusConfig[calc.status] || statusConfig.PENDING
                      return (
                        <div
                          key={calc.id}
                          className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg border border-slate-700"
                        >
                          <div className="flex items-center gap-4 flex-1">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <Badge className={typeConfig.color}>{typeConfig.label}</Badge>
                                <Badge className={status.color}>
                                  <status.icon className="w-3 h-3 mr-1" />
                                  {status.label}
                                </Badge>
                              </div>
                              <p className="text-sm text-slate-400">
                                {calc.calculation_basis || '奖金计算'}
                                {calc.project_name && ` · ${calc.project_name}`}
                              </p>
                              <p className="text-xs text-slate-500 mt-1">
                                {calc.calculated_at ? formatDate(calc.calculated_at) : '-'}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-xl font-bold text-white">
                                ¥{formatAmount(calc.calculated_amount)}
                              </p>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <EmptyState
                    icon={FileText}
                    title="暂无计算记录"
                    description="您还没有奖金计算记录"
                  />
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* 计算记录 Tab */}
        {activeTab === 'calculations' && (
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-white">计算记录</CardTitle>
              </CardHeader>
              <CardContent>
                {data.calculations && data.calculations.length > 0 ? (
                  <div className="space-y-3">
                    {data.calculations.map((calc) => {
                      const typeConfig = bonusTypeConfig[calc.bonus_type] || { label: calc.bonus_type, color: 'bg-slate-500/20 text-slate-400' }
                      const status = statusConfig[calc.status] || statusConfig.PENDING
                      return (
                        <div
                          key={calc.id}
                          className="p-4 bg-slate-800/50 rounded-lg border border-slate-700"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <Badge className={typeConfig.color}>{typeConfig.label}</Badge>
                              <Badge className={status.color}>
                                <status.icon className="w-3 h-3 mr-1" />
                                {status.label}
                              </Badge>
                            </div>
                            <p className="text-xl font-bold text-white">
                              ¥{formatAmount(calc.calculated_amount)}
                            </p>
                          </div>
                          <div className="space-y-1 text-sm text-slate-400">
                            <p>计算依据: {calc.calculation_basis || '-'}</p>
                            {calc.project_name && <p>项目: {calc.project_name}</p>}
                            {calc.rule_name && <p>规则: {calc.rule_name}</p>}
                            <p>计算时间: {calc.calculated_at ? formatDate(calc.calculated_at) : '-'}</p>
                            {calc.approved_at && (
                              <p>审批时间: {formatDate(calc.approved_at)}</p>
                            )}
                            {calc.approval_comment && (
                              <p>审批意见: {calc.approval_comment}</p>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <EmptyState
                    icon={FileText}
                    title="暂无计算记录"
                    description="您还没有奖金计算记录"
                  />
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* 发放记录 Tab */}
        {activeTab === 'distributions' && (
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-white">发放记录</CardTitle>
              </CardHeader>
              <CardContent>
                {data.distributions && data.distributions.length > 0 ? (
                  <div className="space-y-3">
                    {data.distributions.map((dist) => {
                      const status = distributionStatusConfig[dist.status] || distributionStatusConfig.PENDING
                      return (
                        <div
                          key={dist.id}
                          className="p-4 bg-slate-800/50 rounded-lg border border-slate-700"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <Badge className={status.color}>
                                <status.icon className="w-3 h-3 mr-1" />
                                {status.label}
                              </Badge>
                              {dist.distribution_code && (
                                <span className="text-sm text-slate-400">
                                  单号: {dist.distribution_code}
                                </span>
                              )}
                            </div>
                            <p className="text-xl font-bold text-white">
                              ¥{formatAmount(dist.distributed_amount)}
                            </p>
                          </div>
                          <div className="space-y-1 text-sm text-slate-400">
                            <p>发放日期: {dist.distribution_date ? formatDate(dist.distribution_date) : '-'}</p>
                            {dist.paid_at && <p>到账时间: {formatDate(dist.paid_at)}</p>}
                            {dist.payment_method && <p>支付方式: {dist.payment_method}</p>}
                            {dist.remark && <p>备注: {dist.remark}</p>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <EmptyState
                    icon={Receipt}
                    title="暂无发放记录"
                    description="您还没有奖金发放记录"
                  />
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  )
}


