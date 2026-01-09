/**
 * ChartContainer - 图表容器组件
 * 统一处理图表的加载状态、错误状态和空数据状态
 */

import { useState, useEffect } from 'react'
import { Loader2, AlertCircle, RefreshCw, BarChart3 } from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * ChartContainer - 图表容器
 * @param {React.ReactNode} children - 图表组件
 * @param {boolean} loading - 是否加载中
 * @param {string} error - 错误信息
 * @param {boolean} empty - 是否无数据
 * @param {string} emptyText - 空数据提示文本
 * @param {string} title - 图表标题
 * @param {string} description - 图表描述
 * @param {number} height - 容器高度
 * @param {function} onRetry - 重试回调
 * @param {string} className - 自定义样式类
 */
export default function ChartContainer({
  children,
  loading = false,
  error = null,
  empty = false,
  emptyText = '暂无数据',
  title,
  description,
  height = 300,
  onRetry,
  className,
  headerActions,
}) {
  // 加载状态
  if (loading) {
    return (
      <div className={cn('bg-surface-100 rounded-xl border border-white/5', className)}>
        {(title || headerActions) && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
            <div>
              {title && <h3 className="text-sm font-medium text-white">{title}</h3>}
              {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
            </div>
            {headerActions}
          </div>
        )}
        <div
          className="flex flex-col items-center justify-center"
          style={{ height }}
        >
          <Loader2 className="w-8 h-8 text-primary animate-spin mb-3" />
          <span className="text-sm text-slate-400">加载中...</span>
        </div>
      </div>
    )
  }

  // 错误状态
  if (error) {
    return (
      <div className={cn('bg-surface-100 rounded-xl border border-white/5', className)}>
        {(title || headerActions) && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
            <div>
              {title && <h3 className="text-sm font-medium text-white">{title}</h3>}
              {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
            </div>
            {headerActions}
          </div>
        )}
        <div
          className="flex flex-col items-center justify-center"
          style={{ height }}
        >
          <AlertCircle className="w-8 h-8 text-red-400 mb-3" />
          <span className="text-sm text-red-400 mb-3">{error}</span>
          {onRetry && (
            <button
              onClick={onRetry}
              className="flex items-center gap-2 px-3 py-1.5 text-xs bg-surface-200 hover:bg-surface-300 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              重试
            </button>
          )}
        </div>
      </div>
    )
  }

  // 空数据状态
  if (empty) {
    return (
      <div className={cn('bg-surface-100 rounded-xl border border-white/5', className)}>
        {(title || headerActions) && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
            <div>
              {title && <h3 className="text-sm font-medium text-white">{title}</h3>}
              {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
            </div>
            {headerActions}
          </div>
        )}
        <div
          className="flex flex-col items-center justify-center"
          style={{ height }}
        >
          <BarChart3 className="w-8 h-8 text-slate-500 mb-3" />
          <span className="text-sm text-slate-400">{emptyText}</span>
        </div>
      </div>
    )
  }

  // 正常渲染
  return (
    <div className={cn('bg-surface-100 rounded-xl border border-white/5', className)}>
      {(title || headerActions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
          <div>
            {title && <h3 className="text-sm font-medium text-white">{title}</h3>}
            {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
          </div>
          {headerActions}
        </div>
      )}
      <div className="p-4">
        {children}
      </div>
    </div>
  )
}

/**
 * useChartData - 图表数据加载 Hook
 * 封装数据加载、错误处理、缓存等逻辑
 * @param {function} fetchFn - 数据获取函数
 * @param {Array} deps - 依赖数组
 * @param {object} options - 配置选项
 */
export function useChartData(fetchFn, deps = [], options = {}) {
  const {
    initialData = null,
    transform = (data) => data,
    cacheKey,
    cacheDuration = 5 * 60 * 1000, // 5分钟缓存
  } = options

  const [data, setData] = useState(initialData)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    // 检查缓存
    if (cacheKey) {
      const cached = sessionStorage.getItem(cacheKey)
      if (cached) {
        try {
          const { data: cachedData, timestamp } = JSON.parse(cached)
          if (Date.now() - timestamp < cacheDuration) {
            setData(transform(cachedData))
            setLoading(false)
            return
          }
        } catch (e) {
          // 缓存解析失败，继续获取
        }
      }
    }

    try {
      const result = await fetchFn()
      const transformedData = transform(result)
      setData(transformedData)

      // 保存缓存
      if (cacheKey) {
        sessionStorage.setItem(cacheKey, JSON.stringify({
          data: result,
          timestamp: Date.now(),
        }))
      }
    } catch (err) {
      setError(err.message || '数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, deps)

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    setData,
  }
}
