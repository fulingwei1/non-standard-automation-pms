import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  FileText,
  Save,
  Send,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
  TrendingUp,
  Target,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Edit3
} from 'lucide-react'
import { cn } from '../lib/utils'
import { performanceApi } from '../services/api'
import { useNavigate } from 'react-router-dom'

const MonthlySummary = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    period: '',
    workContent: '',
    selfEvaluation: '',
    highlights: '',
    problems: '',
    nextMonthPlan: ''
  })

  const [isDraft, setIsDraft] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)

  // 获取当前用户信息
  const currentUser = JSON.parse(localStorage.getItem('user') || '{"name":"用户","department":"未知部门","position":"未知职位"}')

  // 当前考核周期
  const getCurrentPeriod = () => {
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1
    return {
      year,
      month,
      period: `${year}-${String(month).padStart(2, '0')}`,
      startDate: new Date(year, month - 1, 1).toISOString().split('T')[0],
      endDate: new Date(year, month, 0).toISOString().split('T')[0],
      daysLeft: new Date(year, month, 0).getDate() - now.getDate()
    }
  }

  const currentPeriod = getCurrentPeriod()

  // 加载历史记录
  const loadHistory = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await performanceApi.getMonthlySummaryHistory()
      setHistory(response.data || [])
    } catch (err) {
      console.error('加载历史记录失败:', err)
      // 使用 Mock 数据作为fallback
      setHistory([
        {
          id: 1,
          period: '2024-12',
          submit_date: '2024-12-28',
          status: 'COMPLETED',
          score: 92,
          level: 'A',
          dept_score: 90,
          project_scores: [
            { project_name: '项目A', score: 95, weight: 60 },
            { project_name: '项目B', score: 90, weight: 40 }
          ]
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // 页面加载时初始化
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      period: currentPeriod.period
    }))
    loadHistory()
  }, [])

  // 处理输入变化
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    setIsDraft(true)
  }

  // 保存草稿
  const handleSaveDraft = async () => {
    setIsSaving(true)
    setError(null)
    try {
      await performanceApi.saveMonthlySummaryDraft(formData.period, {
        work_content: formData.workContent,
        self_evaluation: formData.selfEvaluation,
        highlights: formData.highlights,
        problems: formData.problems,
        next_month_plan: formData.nextMonthPlan
      })
      setIsDraft(false)
      alert('草稿已保存')
    } catch (err) {
      console.error('保存草稿失败:', err)
      setError(err.response?.data?.detail || '保存草稿失败，请稍后重试')
      alert('保存草稿失败: ' + (err.response?.data?.detail || '请稍后重试'))
    } finally {
      setIsSaving(false)
    }
  }

  // 提交总结
  const handleSubmit = async () => {
    // 验证必填项
    if (!formData.workContent.trim()) {
      alert('请填写本月工作内容')
      return
    }
    if (!formData.selfEvaluation.trim()) {
      alert('请填写自我评价')
      return
    }

    if (!confirm('提交后将无法修改，确认提交吗？')) {
      return
    }

    setIsSubmitting(true)
    setError(null)
    try {
      await performanceApi.createMonthlySummary({
        period: formData.period,
        work_content: formData.workContent,
        self_evaluation: formData.selfEvaluation,
        highlights: formData.highlights,
        problems: formData.problems,
        next_month_plan: formData.nextMonthPlan
      })
      alert('提交成功！已流转到部门经理和项目经理进行评价')
      // 跳转到我的绩效页面
      navigate('/performance/my-performance')
    } catch (err) {
      console.error('提交失败:', err)
      setError(err.response?.data?.detail || '提交失败，请稍后重试')
      alert('提交失败: ' + (err.response?.data?.detail || '请稍后重试'))
    } finally {
      setIsSubmitting(false)
    }
  }

  // 获取状态标签
  const getStatusBadge = (status) => {
    const badges = {
      IN_PROGRESS: { label: '进行中', color: 'bg-blue-500/20 text-blue-400' },
      SUBMITTED: { label: '已提交', color: 'bg-emerald-500/20 text-emerald-400' },
      EVALUATING: { label: '评价中', color: 'bg-amber-500/20 text-amber-400' },
      COMPLETED: { label: '已完成', color: 'bg-slate-500/20 text-slate-400' }
    }
    return badges[status] || badges.IN_PROGRESS
  }

  // 获取等级颜色
  const getLevelColor = (level) => {
    const colors = {
      A: 'text-emerald-400',
      B: 'text-blue-400',
      C: 'text-amber-400',
      D: 'text-red-400'
    }
    return colors[level] || 'text-slate-400'
  }

  // 动画配置
  const fadeIn = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4 }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <motion.div
        className="max-w-5xl mx-auto space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {/* 页面标题 */}
        <motion.div {...fadeIn}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">月度工作总结</h1>
              <p className="text-slate-400">记录本月工作成果，为绩效评价提供依据</p>
            </div>
            <FileText className="h-12 w-12 text-blue-400" />
          </div>
        </motion.div>

        {/* 当前周期信息卡片 */}
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

        {/* 表单主体 */}
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
            <div className="p-6 space-y-6">
              {/* 用户信息 */}
              <div className="flex items-center gap-4 pb-4 border-b border-slate-700/50">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                  <span className="text-white font-bold text-lg">
                    {currentUser.name.charAt(0)}
                  </span>
                </div>
                <div>
                  <p className="text-white font-medium">{currentUser.name}</p>
                  <p className="text-sm text-slate-400">
                    {currentUser.department} · {currentUser.position}
                  </p>
                </div>
              </div>

              {/* AI 辅助按钮（未来功能，当前禁用）*/}
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg p-4 border border-purple-500/20">
                <div className="flex items-start gap-3">
                  <Sparkles className="h-5 w-5 text-purple-400 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-white font-medium mb-1">AI 智能总结助手（即将上线）</p>
                    <p className="text-sm text-slate-400 mb-3">
                      系统将自动提取您参与的项目任务、工作记录，生成工作总结草稿，减少手动填写工作量
                    </p>
                    <button
                      disabled
                      className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg text-sm font-medium cursor-not-allowed opacity-50"
                    >
                      功能开发中...
                    </button>
                  </div>
                </div>
              </div>

              {/* 表单字段 */}
              <div className="space-y-6">
                {/* 本月工作内容 */}
                <div>
                  <label className="flex items-center gap-2 text-white font-medium mb-3">
                    <Target className="h-4 w-4 text-blue-400" />
                    本月工作内容
                    <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={formData.workContent}
                    onChange={(e) => handleInputChange('workContent', e.target.value)}
                    placeholder="请详细描述本月完成的主要工作内容，包括参与的项目、完成的任务、产出的成果等..."
                    className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    建议包含：项目名称、任务内容、完成情况、数据成果等
                  </p>
                </div>

                {/* 自我评价 */}
                <div>
                  <label className="flex items-center gap-2 text-white font-medium mb-3">
                    <Edit3 className="h-4 w-4 text-emerald-400" />
                    自我评价
                    <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={formData.selfEvaluation}
                    onChange={(e) => handleInputChange('selfEvaluation', e.target.value)}
                    placeholder="请客观评价本月工作表现，包括工作质量、工作效率、协作能力等方面..."
                    className="w-full h-32 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 resize-none"
                  />
                  <p className="text-xs text-slate-500 mt-2">
                    建议包含：工作完成度、能力提升、团队贡献等
                  </p>
                </div>

                {/* 工作亮点 */}
                <div>
                  <label className="flex items-center gap-2 text-white font-medium mb-3">
                    <Lightbulb className="h-4 w-4 text-amber-400" />
                    工作亮点
                  </label>
                  <textarea
                    value={formData.highlights}
                    onChange={(e) => handleInputChange('highlights', e.target.value)}
                    placeholder="本月有哪些值得分享的成果或创新点？（选填）"
                    className="w-full h-24 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 resize-none"
                  />
                </div>

                {/* 遇到的问题 */}
                <div>
                  <label className="flex items-center gap-2 text-white font-medium mb-3">
                    <AlertCircle className="h-4 w-4 text-red-400" />
                    遇到的问题
                  </label>
                  <textarea
                    value={formData.problems}
                    onChange={(e) => handleInputChange('problems', e.target.value)}
                    placeholder="工作中遇到的困难、挑战或需要支持的地方（选填）"
                    className="w-full h-24 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-red-500 resize-none"
                  />
                </div>

                {/* 下月计划 */}
                <div>
                  <label className="flex items-center gap-2 text-white font-medium mb-3">
                    <TrendingUp className="h-4 w-4 text-purple-400" />
                    下月工作计划
                  </label>
                  <textarea
                    value={formData.nextMonthPlan}
                    onChange={(e) => handleInputChange('nextMonthPlan', e.target.value)}
                    placeholder="下个月的工作重点和目标（选填）"
                    className="w-full h-24 px-4 py-3 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
                  />
                </div>
              </div>

              {/* 操作按钮 */}
              <div className="flex items-center justify-between pt-6 border-t border-slate-700/50">
                <div className="flex items-center gap-2 text-sm">
                  {isDraft && (
                    <span className="text-amber-400">● 有未保存的修改</span>
                  )}
                  {!isDraft && (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4" />
                      已保存
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleSaveDraft}
                    disabled={isSaving || !isDraft}
                    className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <Save className="h-4 w-4" />
                    {isSaving ? '保存中...' : '保存草稿'}
                  </button>

                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                    className="px-6 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-blue-500/50 disabled:to-purple-500/50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center gap-2"
                  >
                    <Send className="h-4 w-4" />
                    {isSubmitting ? '提交中...' : '提交总结'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 历史记录 */}
        <motion.div {...fadeIn} transition={{ delay: 0.3 }}>
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
            <button
              onClick={() => setShowHistory(!showHistory)}
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

        {/* 提示信息 */}
        <motion.div {...fadeIn} transition={{ delay: 0.4 }}>
          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-slate-300 space-y-1">
                <p className="font-medium text-white mb-2">温馨提示：</p>
                <p>• 每月需在月底前提交工作总结，逾期将影响绩效评价</p>
                <p>• 提交后系统将自动流转给部门经理和相关项目经理进行评分</p>
                <p>• 部门经理评分占 50%，项目经理评分占 50%（权重可由HR调整）</p>
                <p>• 季度绩效分数 = 三个月分数的加权平均</p>
                <p>• 若参与多个项目，最终得分 = 各项目经理评分的加权平均</p>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default MonthlySummary
