import { useState, useEffect, useMemo } from 'react'
import { performanceApi } from '../services/api'
import { calculateTaskStatistics, filterTasks } from '../utils/evaluationTaskUtils'

/**
 * 自定义Hook：管理评价任务数据
 */
export const useEvaluationTasks = (periodFilter, statusFilter, searchTerm, typeFilter, mockTasks = []) => {
  const [isLoading, setIsLoading] = useState(false)
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState(null)

  // 加载任务列表
  const loadTasks = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await performanceApi.getEvaluationTasks({
        period: periodFilter,
        status_filter: statusFilter === 'all' ? undefined : statusFilter.toUpperCase()
      })
      setTasks(response.data.tasks || [])
    } catch (err) {
      console.error('加载评价任务失败:', err)
      setError(err.response?.data?.detail || '加载失败')
      // Fallback to mock data
      setTasks(mockTasks)
    } finally {
      setIsLoading(false)
    }
  }

  // 监听筛选条件变化
  useEffect(() => {
    loadTasks()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodFilter, statusFilter])

  // 过滤任务
  const filteredTasks = useMemo(() => {
    return filterTasks(tasks, searchTerm, typeFilter)
  }, [tasks, searchTerm, typeFilter])

  // 统计数据
  const statistics = useMemo(() => {
    return calculateTaskStatistics(tasks)
  }, [tasks])

  // 获取可选周期列表
  const availablePeriods = useMemo(() => {
    const allTasks = [...tasks, ...mockTasks]
    const periods = [...new Set(allTasks.map(task => task.period))]
    return periods.sort().reverse()
  }, [tasks, mockTasks])

  return {
    tasks,
    filteredTasks,
    statistics,
    availablePeriods,
    isLoading,
    error,
    refetch: loadTasks
  }
}
