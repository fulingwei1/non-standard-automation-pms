import { AlertCircle, RefreshCw, XCircle, Inbox } from 'lucide-react'
import { Button } from '../ui/button'
import { Card, CardContent } from '../ui/card'
import { cn } from '../../lib/utils'

export function ErrorMessage({ 
  error, 
  onRetry, 
  title = '加载失败',
  className,
  showDetails = false 
}) {
  const errorMessage = error?.message || error?.response?.data?.detail || '未知错误'
  
  return (
    <Card className={cn('border-red-500/20 bg-red-500/5', className)}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-red-400 mb-2">{title}</h3>
            <p className="text-slate-300 mb-4">{errorMessage}</p>
            {showDetails && error?.response?.data && (
              <details className="mb-4">
                <summary className="text-sm text-slate-500 cursor-pointer mb-2">
                  详细信息
                </summary>
                <pre className="text-xs text-slate-500 bg-slate-900 p-3 rounded overflow-auto">
                  {JSON.stringify(error.response.data, null, 2)}
                </pre>
              </details>
            )}
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                重试
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function EmptyState({ 
  icon: Icon = Inbox,
  title = '暂无数据',
  description,
  action,
  className 
}) {
  const IconComponent = Icon
  return (
    <Card className={className}>
      <CardContent className="p-12 text-center">
        <IconComponent className="w-16 h-16 text-slate-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        {description && <p className="text-slate-400 mb-4">{description}</p>}
        {action && <div className="mt-4">{action}</div>}
      </CardContent>
    </Card>
  )
}

