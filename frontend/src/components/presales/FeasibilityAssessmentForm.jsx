/**
 * 可行性评估表单组件
 * 售前技术工程师评估销售线索/商机的可行性
 */
import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Save,
  Send,
  X,
  TrendingUp,
  Target,
  Zap,
  Users,
  Clock,
  DollarSign,
  Shield,
  Lightbulb,
  AlertCircle,
} from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { cn } from '../../lib/utils'

// 评估维度配置
const assessmentDimensions = [
  {
    id: 'technical',
    name: '技术可行性',
    icon: Zap,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    description: '技术方案是否可行，技术难度评估',
    factors: [
      { id: 'tech_maturity', label: '技术成熟度', weight: 0.3 },
      { id: 'complexity', label: '技术复杂度', weight: 0.25 },
      { id: 'innovation', label: '创新性要求', weight: 0.2 },
      { id: 'risk', label: '技术风险', weight: 0.25 },
    ],
  },
  {
    id: 'market',
    name: '市场可行性',
    icon: Target,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    description: '市场需求、竞争态势、客户价值',
    factors: [
      { id: 'demand', label: '市场需求', weight: 0.3 },
      { id: 'competition', label: '竞争态势', weight: 0.25 },
      { id: 'customer_value', label: '客户价值', weight: 0.25 },
      { id: 'market_trend', label: '市场趋势', weight: 0.2 },
    ],
  },
  {
    id: 'resource',
    name: '资源可行性',
    icon: Users,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    description: '人力资源、物料资源、时间资源',
    factors: [
      { id: 'human_resource', label: '人力资源', weight: 0.35 },
      { id: 'material', label: '物料资源', weight: 0.3 },
      { id: 'time', label: '时间资源', weight: 0.35 },
    ],
  },
  {
    id: 'financial',
    name: '财务可行性',
    icon: DollarSign,
    color: 'text-violet-400',
    bgColor: 'bg-violet-500/10',
    description: '成本控制、盈利能力、回款风险',
    factors: [
      { id: 'cost_control', label: '成本可控性', weight: 0.3 },
      { id: 'profitability', label: '盈利能力', weight: 0.35 },
      { id: 'payment_risk', label: '回款风险', weight: 0.35 },
    ],
  },
]

// 评分选项
const scoreOptions = [
  { value: 5, label: '优秀', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20' },
  { value: 4, label: '良好', color: 'text-blue-400', bgColor: 'bg-blue-500/20' },
  { value: 3, label: '一般', color: 'text-amber-400', bgColor: 'bg-amber-500/20' },
  { value: 2, label: '较差', color: 'text-orange-400', bgColor: 'bg-orange-500/20' },
  { value: 1, label: '很差', color: 'text-red-400', bgColor: 'bg-red-500/20' },
]

export default function FeasibilityAssessmentForm({ opportunity, onSave, onCancel }) {
  const [scores, setScores] = useState({})
  const [overallScore, setOverallScore] = useState(0)
  const [feasibility, setFeasibility] = useState('pending') // 'feasible', 'conditional', 'infeasible', 'pending'
  const [recommendation, setRecommendation] = useState('')
  const [riskAnalysis, setRiskAnalysis] = useState('')
  const [technicalNotes, setTechnicalNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // 计算总分
  const calculateOverallScore = (newScores) => {
    let totalScore = 0
    let totalWeight = 0

    assessmentDimensions.forEach((dimension) => {
      let dimensionScore = 0
      let dimensionWeight = 0

      dimension.factors.forEach((factor) => {
        const score = newScores[`${dimension.id}_${factor.id}`] || 0
        dimensionScore += score * factor.weight
        dimensionWeight += factor.weight
      })

      if (dimensionWeight > 0) {
        totalScore += (dimensionScore / dimensionWeight) * (1 / assessmentDimensions.length)
        totalWeight += 1 / assessmentDimensions.length
      }
    })

    const finalScore = totalWeight > 0 ? (totalScore / totalWeight) * 100 : 0
    setOverallScore(finalScore)

    // 根据总分判断可行性
    if (finalScore >= 80) {
      setFeasibility('feasible')
    } else if (finalScore >= 60) {
      setFeasibility('conditional')
    } else {
      setFeasibility('infeasible')
    }
  }

  // 更新评分
  const updateScore = (key, value) => {
    const newScores = { ...scores, [key]: value }
    setScores(newScores)
    calculateOverallScore(newScores)
  }

  // 获取可行性状态
  const getFeasibilityStatus = () => {
    switch (feasibility) {
      case 'feasible':
        return { label: '可行', color: 'text-emerald-400', bgColor: 'bg-emerald-500/20', icon: CheckCircle }
      case 'conditional':
        return { label: '有条件可行', color: 'text-amber-400', bgColor: 'bg-amber-500/20', icon: AlertTriangle }
      case 'infeasible':
        return { label: '不可行', color: 'text-red-400', bgColor: 'bg-red-500/20', icon: XCircle }
      default:
        return { label: '待评估', color: 'text-slate-400', bgColor: 'bg-slate-500/20', icon: Clock }
    }
  }

  // 提交评估
  const handleSubmit = () => {
    setIsSubmitting(true)
    setTimeout(() => {
      setIsSubmitting(false)
      onSave?.({
        scores,
        overallScore,
        feasibility,
        recommendation,
        riskAnalysis,
        technicalNotes,
        assessedAt: new Date().toISOString(),
      })
    }, 500)
  }

  const feasibilityStatus = getFeasibilityStatus()
  const StatusIcon = feasibilityStatus.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* 商机信息 */}
      <Card className="bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border border-violet-500/20">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white mb-1">{opportunity?.name || '商机名称'}</h3>
              <p className="text-sm text-slate-400">{opportunity?.customerName || '客户名称'}</p>
              {opportunity?.expectedAmount && (
                <p className="text-sm text-emerald-400 mt-1">预计金额：¥{(opportunity.expectedAmount / 10000).toFixed(0)}万</p>
              )}
            </div>
            <Badge className={cn('text-xs', feasibilityStatus.bgColor, feasibilityStatus.color)}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {feasibilityStatus.label}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* 评估维度 */}
      <div className="space-y-4">
        {assessmentDimensions.map((dimension) => {
          const Icon = dimension.icon
          const dimensionScore = dimension.factors.reduce((sum, factor) => {
            const score = scores[`${dimension.id}_${factor.id}`] || 0
            return sum + score * factor.weight
          }, 0)
          const dimensionMaxScore = dimension.factors.reduce((sum, factor) => sum + 5 * factor.weight, 0)
          const dimensionPercentage = dimensionMaxScore > 0 ? (dimensionScore / dimensionMaxScore) * 100 : 0

          return (
            <Card key={dimension.id} className="bg-surface-50/50 border border-white/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', dimension.bgColor)}>
                      <Icon className={cn('w-5 h-5', dimension.color)} />
                    </div>
                    <div>
                      <CardTitle className="text-base text-white">{dimension.name}</CardTitle>
                      <p className="text-xs text-slate-400 mt-0.5">{dimension.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">{dimensionPercentage.toFixed(0)}分</p>
                    <p className="text-xs text-slate-400">满分100</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {dimension.factors.map((factor) => {
                  const factorKey = `${dimension.id}_${factor.id}`
                  const currentScore = scores[factorKey] || 0

                  return (
                    <div key={factor.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="text-sm text-slate-300">{factor.label}</label>
                        <span className="text-xs text-slate-500">权重 {factor.weight * 100}%</span>
                      </div>
                      <div className="flex gap-2">
                        {scoreOptions.map((option) => (
                          <button
                            key={option.value}
                            onClick={() => updateScore(factorKey, option.value)}
                            className={cn(
                              'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all',
                              'hover:scale-105 active:scale-95',
                              currentScore === option.value
                                ? cn(option.bgColor, option.color, 'ring-2 ring-primary')
                                : 'bg-surface-100 text-slate-400 hover:bg-surface-50'
                            )}
                          >
                            {option.value} - {option.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 综合评分 */}
      <Card className="bg-gradient-to-br from-primary/10 to-indigo-500/10 border border-primary/20">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              <h4 className="text-base font-semibold text-white">综合评分</h4>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-primary">{overallScore.toFixed(1)}</p>
              <p className="text-xs text-slate-400">满分100</p>
            </div>
          </div>
          <Progress value={overallScore} className="h-2" />
          <div className="mt-3 flex items-center gap-2">
            <StatusIcon className={cn('w-4 h-4', feasibilityStatus.color)} />
            <span className={cn('text-sm font-medium', feasibilityStatus.color)}>
              {feasibilityStatus.label}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* 评估建议 */}
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-slate-400 mb-2 block">评估建议</label>
          <textarea
            value={recommendation}
            onChange={(e) => setRecommendation(e.target.value)}
            placeholder="基于评估结果，给出是否推进的建议及理由..."
            className="w-full h-24 px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-slate-400 mb-2 block">风险分析</label>
          <textarea
            value={riskAnalysis}
            onChange={(e) => setRiskAnalysis(e.target.value)}
            placeholder="识别主要风险点及应对措施..."
            className="w-full h-24 px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-slate-400 mb-2 block">技术说明</label>
          <textarea
            value={technicalNotes}
            onChange={(e) => setTechnicalNotes(e.target.value)}
            placeholder="技术方案要点、关键技术难点、技术路线建议等..."
            className="w-full h-32 px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
          />
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2 pt-2">
        <Button
          variant="outline"
          onClick={onCancel}
          className="flex-1"
        >
          <X className="w-4 h-4 mr-2" />
          取消
        </Button>
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || overallScore === 0}
          className="flex-1"
        >
          <Send className="w-4 h-4 mr-2" />
          {isSubmitting ? '提交中...' : '提交评估'}
        </Button>
      </div>
    </motion.div>
  )
}

