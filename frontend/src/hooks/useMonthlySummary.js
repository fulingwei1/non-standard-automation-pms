import { useState, useEffect } from 'react'
import { performanceApi } from '../services/api'
import { getCurrentPeriod } from '../utils/monthlySummaryUtils'

/**
 * 月度总结自定义 Hook
 */
export const useMonthlySummary = () => {
  const currentPeriod = getCurrentPeriod()
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

  // 页面加载时初始化
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      period: currentPeriod.period
    }))
  }, [currentPeriod.period])

  // 处理输入变化
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    setIsDraft(true)
  }

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
  const handleSubmit = async (navigate) => {
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
      navigate('/personal/my-performance')
    } catch (err) {
      console.error('提交失败:', err)
      setError(err.response?.data?.detail || '提交失败，请稍后重试')
      alert('提交失败: ' + (err.response?.data?.detail || '请稍后重试'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return {
    currentPeriod,
    formData,
    isDraft,
    isSaving,
    isSubmitting,
    showHistory,
    setShowHistory,
    isLoading,
    history,
    error,
    handleInputChange,
    loadHistory,
    handleSaveDraft,
    handleSubmit
  }
}
