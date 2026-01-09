import React, { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Award,
  TrendingUp,
  TrendingDown,
  Calendar,
  Target,
  Users,
  Briefcase,
  BarChart3,
  MessageSquare,
  Download,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react'
import { cn } from '../lib/utils'
import { performanceApi } from '../services/api'

const MyPerformance = () => {
  const [activeTab, setActiveTab] = useState('overview') // overview, history, details
  const [isLoading, setIsLoading] = useState(false)
  const [performanceData, setPerformanceData] = useState(null)
  const [error, setError] = useState(null)

  // 获取当前用户信息
  const currentUser = JSON.parse(localStorage.getItem('user') || '{"name":"用户","department":"未知部门","position":"未知职位"}')

  // Mock 历史记录（月度）- 作为fallback
  const mockMonthlyHistory = [
    {
      period: '2024-12',
      submitDate: '2024-12-28',
      status: 'COMPLETED',
      totalScore: 92,
      level: 'A',
      deptScore: 90,
      projectScores: [
        { projectName: '项目A', score: 95, weight: 60, evaluator: '王经理' },
        { projectName: '项目B', score: 90, weight: 40, evaluator: '刘经理' }
      ],
      comments: [
        {
          evaluator: '李经理',
          role: '部门经理',
          score: 90,
          comment: '工作态度认真，按时完成任务，技术能力强'
        },
        {
          evaluator: '王经理',
          role: '项目A经理',
          score: 95,
          comment: '在项目A中表现优异，技术攻关能力突出'
        }
      ]
    },
    {
      period: '2024-11',
      submitDate: '2024-11-30',
      status: 'COMPLETED',
      totalScore: 88,
      level: 'B',
      deptScore: 88,
      projectScores: [
        { projectName: '项目A', score: 88, weight: 100, evaluator: '王经理' }
      ],
      comments: [
        {
          evaluator: '李经理',
          role: '部门经理',
          score: 88,
          comment: '工作完成度良好，建议加强跨部门协作'
        }
      ]
    },
    {
      period: '2024-10',
      submitDate: '2024-10-31',
      status: 'COMPLETED',
      totalScore: 90,
      level: 'A',
      deptScore: 89,
      projectScores: [
        { projectName: '项目A', score: 92, weight: 70, evaluator: '王经理' },
        { projectName: '项目C', score: 85, weight: 30, evaluator: '赵经理' }
      ],
      comments: []
    }
  ]

  // Mock 绩效概览数据
  const performanceOverview = {
    currentPeriod: {
      year: 2025,
      quarter: 1,
      status: 'EVALUATING', // IN_PROGRESS, SUBMITTED, EVALUATING, COMPLETED
      submitDate: '2025-01-28',
      deptEvaluation: {
        status: 'PENDING',
        evaluator: '李经理',
        score: null
      },
      projectEvaluations: [
        {
          projectId: 1,
          projectName: '项目A',
          status: 'COMPLETED',
          evaluator: '王经理',
          score: 92,
          weight: 60
        },
        {
          projectId: 2,
          projectName: '项目B',
          status: 'PENDING',
          evaluator: '刘经理',
          score: null,
          weight: 40
        }
      ]
    },
    latestScore: {
      period: '2024-Q4',
      totalScore: 90,
      level: 'A',
      rank: 5,
      totalEmployees: 48,
      deptScore: 88,
      projectScores: [
        { projectName: '项目A', score: 92, weight: 60 },
        { projectName: '项目C', score: 85, weight: 40 }
      ]
    },
    quarterlyTrend: [
      { quarter: '2024-Q1', score: 85, level: 'B' },
      { quarter: '2024-Q2', score: 88, level: 'B' },
      { quarter: '2024-Q3', score: 87, level: 'B' },
      { quarter: '2024-Q4', score: 90, level: 'A' }
    ],
    yearlyStats: {
      averageScore: 87.5,
      highestScore: 90,
      lowestScore: 85,
      trend: '+5%'
    }
  }

  // 加载绩效数据
  const loadPerformanceData = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await performanceApi.getMyPerformance()
      setPerformanceData(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || '加载失败')
      // Fallback to mock data
      setPerformanceData({
        current_status: performanceOverview.currentPeriod,
        latest_result: performanceOverview.latestScore,
        quarterly_trend: performanceOverview.quarterlyTrend,
        history: mockMonthlyHistory
      })
    } finally {
      setIsLoading(false)
    }
  }

  // 页面加载时获取数据
  useEffect(() => {
    loadPerformanceData()
  }, [])

  // 使用加载的数据或fallback到mock
  const currentData = performanceData || {
    current_status: performanceOverview.currentPeriod,
    latest_result: performanceOverview.latestScore,
    quarterly_trend: performanceOverview.quarterlyTrend,
    history: mockMonthlyHistory
  }

  // 获取状态标签
  const getStatusBadge = (status) => {
    const badges = {
      IN_PROGRESS: { label: '填写中', color: 'bg-slate-500/20 text-slate-400', icon: Clock },
      SUBMITTED: { label: '已提交', color: 'bg-blue-500/20 text-blue-400', icon: CheckCircle2 },
      EVALUATING: { label: '评价中', color: 'bg-amber-500/20 text-amber-400', icon: Clock },
      COMPLETED: { label: '已完成', color: 'bg-emerald-500/20 text-emerald-400', icon: CheckCircle2 },
      PENDING: { label: '待评价', color: 'bg-orange-500/20 text-orange-400', icon: AlertCircle }
    }
    return badges[status] || badges.IN_PROGRESS
  }

  // 获取等级颜色和名称
  const getLevelInfo = (level) => {
    const levels = {
      A: { name: '优秀', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20', borderColor: 'border-emerald-500/30' },
      B: { name: '良好', color: 'text-blue-400', bgColor: 'bg-blue-500/20', borderColor: 'border-blue-500/30' },
      C: { name: '合格', color: 'text-amber-400', bgColor: 'bg-amber-500/20', borderColor: 'border-amber-500/30' },
      D: { name: '待改进', color: 'text-red-400', bgColor: 'bg-red-500/20', borderColor: 'border-red-500/30' }
    }
    return levels[level] || levels.C
  }

  // 获取趋势图标和颜色
  const getTrendIcon = (current, previous) => {
    if (!previous) return { icon: Minus, color: 'text-slate-400' }
    if (current > previous) return { icon: ArrowUpRight, color: 'text-emerald-400' }
    if (current < previous) return { icon: ArrowDownRight, color: 'text-red-400' }
    return { icon: Minus, color: 'text-slate-400' }
  }

  // 计算季度对比
  const quarterComparison = useMemo(() => {
    const trend = performanceOverview.quarterlyTrend
    if (trend.length < 2) return null
    const current = trend[trend.length - 1]
    const previous = trend[trend.length - 2]
    return {
      current: current.score,
      previous: previous.score,
      change: current.score - previous.score,
      percentChange: ((current.score - previous.score) / previous.score * 100).toFixed(1)
    }
  }, [performanceOverview.quarterlyTrend])

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-6xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">我的绩效</h1>
              <p className="text-slate-400">查看个人绩效评价结果和历史记录</p>
            </div>
            <button className="px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg font-medium transition-colors flex items-center gap-2">
              <Download className="h-4 w-4" />
              导出报告
            </button>
          </div>
        </motion.div>

        {/* 个人信息卡片 */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                <span className="text-white font-bold text-2xl">
                  {currentUser.name.charAt(0)}
                </span>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white mb-1">{currentUser.name}</h2>
                <p className="text-slate-400">{currentUser.department} · {currentUser.position}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Tab 导航 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="flex gap-2">
            {[
              { key: 'overview', label: '绩效概览', icon: Award },
              { key: 'history', label: '历史记录', icon: Calendar },
              { key: 'details', label: '评价详情', icon: MessageSquare }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'px-6 py-3 rounded-lg font-medium transition-all flex items-center gap-2',
                  activeTab === tab.key
                    ? 'bg-blue-500 text-white'
                    : 'bg-slate-800/50 text-slate-400 hover:text-white hover:bg-slate-700/50'
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </motion.div>

        {/* 绩效概览 Tab */}
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* 当前季度评价状态 */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white">当前评价状态</h3>
                <span className="text-slate-400">
                  {performanceOverview.currentPeriod.year}年 Q{performanceOverview.currentPeriod.quarter}
                </span>
              </div>

              <div className="space-y-4">
                {/* 总体状态 */}
                <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'h-10 w-10 rounded-full flex items-center justify-center',
                      getStatusBadge(performanceOverview.currentPeriod.status).color
                    )}>
                      {React.createElement(getStatusBadge(performanceOverview.currentPeriod.status).icon, {
                        className: 'h-5 w-5'
                      })}
                    </div>
                    <div>
                      <p className="text-white font-medium">评价状态</p>
                      <p className="text-sm text-slate-400">
                        提交时间: {performanceOverview.currentPeriod.submitDate}
                      </p>
                    </div>
                  </div>
                  <span className={cn(
                    'px-4 py-2 rounded-full text-sm font-medium',
                    getStatusBadge(performanceOverview.currentPeriod.status).color
                  )}>
                    {getStatusBadge(performanceOverview.currentPeriod.status).label}
                  </span>
                </div>

                {/* 部门经理评价 */}
                <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Users className="h-5 w-5 text-blue-400" />
                      <div>
                        <p className="text-white font-medium">部门经理评价 (50%)</p>
                        <p className="text-sm text-slate-400">
                          {performanceOverview.currentPeriod.deptEvaluation.evaluator}
                        </p>
                      </div>
                    </div>
                    {performanceOverview.currentPeriod.deptEvaluation.score ? (
                      <div className="text-right">
                        <p className="text-2xl font-bold text-blue-400">
                          {performanceOverview.currentPeriod.deptEvaluation.score}
                        </p>
                        <p className="text-xs text-slate-400">已评分</p>
                      </div>
                    ) : (
                      <span className={cn(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getStatusBadge('PENDING').color
                      )}>
                        {getStatusBadge('PENDING').label}
                      </span>
                    )}
                  </div>
                </div>

                {/* 项目经理评价 */}
                <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                  <div className="flex items-center gap-3 mb-3">
                    <Briefcase className="h-5 w-5 text-purple-400" />
                    <p className="text-white font-medium">项目经理评价 (50%)</p>
                  </div>
                  <div className="space-y-3">
                    {performanceOverview.currentPeriod.projectEvaluations.map((proj, idx) => (
                      <div key={idx} className="flex items-center justify-between pl-8">
                        <div>
                          <p className="text-slate-300">{proj.projectName}</p>
                          <p className="text-xs text-slate-400">
                            {proj.evaluator} · 权重 {proj.weight}%
                          </p>
                        </div>
                        {proj.score ? (
                          <div className="text-right">
                            <p className="text-xl font-bold text-purple-400">{proj.score}</p>
                            <p className="text-xs text-slate-400">已评分</p>
                          </div>
                        ) : (
                          <span className={cn(
                            'px-3 py-1 rounded-full text-xs font-medium',
                            getStatusBadge('PENDING').color
                          )}>
                            {getStatusBadge('PENDING').label}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 最新绩效结果 */}
            {performanceOverview.latestScore && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
                <h3 className="text-xl font-bold text-white mb-6">最新绩效结果</h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  {/* 综合得分 */}
                  <div className={cn(
                    'p-6 rounded-xl border-2',
                    getLevelInfo(performanceOverview.latestScore.level).bgColor,
                    getLevelInfo(performanceOverview.latestScore.level).borderColor
                  )}>
                    <div className="flex items-center gap-3 mb-3">
                      <Award className={cn('h-6 w-6', getLevelInfo(performanceOverview.latestScore.level).color)} />
                      <span className="text-slate-400">综合得分</span>
                    </div>
                    <p className={cn(
                      'text-4xl font-bold mb-2',
                      getLevelInfo(performanceOverview.latestScore.level).color
                    )}>
                      {performanceOverview.latestScore.totalScore}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        'px-3 py-1 rounded-full text-sm font-medium',
                        getLevelInfo(performanceOverview.latestScore.level).color,
                        getLevelInfo(performanceOverview.latestScore.level).bgColor
                      )}>
                        {performanceOverview.latestScore.level}级 · {getLevelInfo(performanceOverview.latestScore.level).name}
                      </span>
                    </div>
                  </div>

                  {/* 部门排名 */}
                  <div className="p-6 bg-blue-500/10 rounded-xl border-2 border-blue-500/20">
                    <div className="flex items-center gap-3 mb-3">
                      <Target className="h-6 w-6 text-blue-400" />
                      <span className="text-slate-400">部门排名</span>
                    </div>
                    <p className="text-4xl font-bold text-blue-400 mb-2">
                      #{performanceOverview.latestScore.rank}
                    </p>
                    <p className="text-sm text-slate-400">
                      共 {performanceOverview.latestScore.totalEmployees} 人
                    </p>
                  </div>

                  {/* 季度趋势 */}
                  <div className="p-6 bg-purple-500/10 rounded-xl border-2 border-purple-500/20">
                    <div className="flex items-center gap-3 mb-3">
                      <TrendingUp className="h-6 w-6 text-purple-400" />
                      <span className="text-slate-400">季度趋势</span>
                    </div>
                    {quarterComparison && (
                      <>
                        <div className="flex items-baseline gap-2 mb-2">
                          <p className="text-4xl font-bold text-purple-400">
                            {quarterComparison.change > 0 ? '+' : ''}{quarterComparison.change}
                          </p>
                          {React.createElement(getTrendIcon(quarterComparison.current, quarterComparison.previous).icon, {
                            className: cn('h-6 w-6', getTrendIcon(quarterComparison.current, quarterComparison.previous).color)
                          })}
                        </div>
                        <p className="text-sm text-slate-400">
                          相比上季度 {quarterComparison.percentChange}%
                        </p>
                      </>
                    )}
                  </div>
                </div>

                {/* 评分构成 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 部门经理评分 */}
                  <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400">部门经理评分</span>
                      <span className="text-sm text-slate-500">(权重 50%)</span>
                    </div>
                    <p className="text-3xl font-bold text-blue-400">
                      {performanceOverview.latestScore.deptScore}
                    </p>
                  </div>

                  {/* 项目经理评分 */}
                  <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400">项目经理评分</span>
                      <span className="text-sm text-slate-500">(权重 50%)</span>
                    </div>
                    <div className="space-y-2">
                      {performanceOverview.latestScore.projectScores.map((ps, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-sm text-slate-400">{ps.projectName}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-bold text-purple-400">{ps.score}</span>
                            <span className="text-xs text-slate-500">({ps.weight}%)</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 季度趋势图 */}
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50">
              <h3 className="text-xl font-bold text-white mb-6">季度绩效趋势</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {performanceOverview.quarterlyTrend.map((item, idx) => (
                  <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors">
                    <p className="text-sm text-slate-400 mb-2">{item.quarter}</p>
                    <p className={cn('text-2xl font-bold mb-1', getLevelInfo(item.level).color)}>
                      {item.score}
                    </p>
                    <span className={cn(
                      'inline-block px-2 py-0.5 rounded text-xs font-medium',
                      getLevelInfo(item.level).color,
                      getLevelInfo(item.level).bgColor
                    )}>
                      {item.level}级
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* 历史记录 Tab */}
        {activeTab === 'history' && (
          <motion.div
            key="history"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
              <div className="p-6 border-b border-slate-700/50">
                <h3 className="text-xl font-bold text-white">月度绩效记录</h3>
                <p className="text-sm text-slate-400 mt-1">共 {mockMonthlyHistory.length} 条记录</p>
              </div>

              <div className="divide-y divide-slate-700/50">
                {mockMonthlyHistory.map((record, index) => (
                  <motion.div
                    key={record.period}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-6 hover:bg-slate-700/20 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-lg font-bold text-white mb-1">
                          {record.period.split('-')[0]}年{record.period.split('-')[1]}月
                        </h4>
                        <p className="text-sm text-slate-400">提交时间: {record.submitDate}</p>
                      </div>
                      <span className={cn(
                        'px-4 py-2 rounded-full text-sm font-medium',
                        getStatusBadge(record.status).color
                      )}>
                        {getStatusBadge(record.status).label}
                      </span>
                    </div>

                    {record.status === 'COMPLETED' && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-900/30 rounded-lg">
                        <div>
                          <p className="text-xs text-slate-400 mb-2">综合得分</p>
                          <div className="flex items-baseline gap-2">
                            <p className={cn('text-3xl font-bold', getLevelInfo(record.level).color)}>
                              {record.totalScore}
                            </p>
                            <span className={cn(
                              'px-2 py-0.5 rounded text-xs font-medium',
                              getLevelInfo(record.level).color,
                              getLevelInfo(record.level).bgColor
                            )}>
                              {record.level}级
                            </span>
                          </div>
                        </div>

                        <div>
                          <p className="text-xs text-slate-400 mb-2">部门经理评分</p>
                          <p className="text-2xl font-bold text-blue-400">{record.deptScore}</p>
                        </div>

                        <div>
                          <p className="text-xs text-slate-400 mb-2">项目经理评分</p>
                          {record.projectScores.map((ps, idx) => (
                            <div key={idx} className="flex items-center justify-between text-sm mb-1">
                              <span className="text-slate-400">{ps.projectName}</span>
                              <span className="text-purple-400 font-medium">
                                {ps.score} ({ps.weight}%)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* 评价详情 Tab */}
        {activeTab === 'details' && (
          <motion.div
            key="details"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-4"
          >
            {mockMonthlyHistory
              .filter(record => record.comments && record.comments.length > 0)
              .map((record, index) => (
                <motion.div
                  key={record.period}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-bold text-white">
                      {record.period.split('-')[0]}年{record.period.split('-')[1]}月 评价
                    </h4>
                    <span className={cn(
                      'px-3 py-1 rounded-full text-sm font-medium',
                      getLevelInfo(record.level).color,
                      getLevelInfo(record.level).bgColor
                    )}>
                      综合得分: {record.totalScore} ({record.level}级)
                    </span>
                  </div>

                  <div className="space-y-4">
                    {record.comments.map((comment, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                              <span className="text-white font-bold">
                                {comment.evaluator.charAt(0)}
                              </span>
                            </div>
                            <div>
                              <p className="text-white font-medium">{comment.evaluator}</p>
                              <p className="text-sm text-slate-400">{comment.role}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-blue-400">{comment.score}</p>
                            <p className="text-xs text-slate-400">评分</p>
                          </div>
                        </div>
                        <div className="pl-13">
                          <p className="text-slate-300 leading-relaxed">{comment.comment}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              ))}

            {mockMonthlyHistory.filter(r => r.comments?.length > 0).length === 0 && (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-12 border border-slate-700/50 text-center">
                <MessageSquare className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无评价详情</p>
              </div>
            )}
          </motion.div>
        )}

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">绩效评价说明：</p>
                <p>• 每月需在月底前提交工作总结，逾期将影响绩效评价</p>
                <p>• 综合得分 = 部门经理评分 × 50% + 项目经理评分 × 50%</p>
                <p>• 参与多个项目时，项目经理评分按各项目权重加权平均</p>
                <p>• 季度绩效分数 = 三个月分数的加权平均</p>
                <p>• 等级标准：A级(90-100) B级(80-89) C级(70-79) D级(60-69)</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default MyPerformance
