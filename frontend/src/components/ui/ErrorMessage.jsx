import { AlertCircle, RefreshCw, XCircle } from 'lucide-react'
import { Card, CardContent } from './card'
import { Button } from './button'
import { cn } from '../../lib/utils'

export function ErrorMessage({
  title = '加载失败',
  message = '数据加载失败，请稍后重试',
  onRetry,
  className,
  variant = 'default',
}) {
  const variantStyles = {
    default: 'bg-red-500/10 border-red-500/20',
    warning: 'bg-amber-500/10 border-amber-500/20',
    info: 'bg-blue-500/10 border-blue-500/20',
  }

  return (
    <Card className={cn('border', variantStyles[variant], className)}>
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            {variant === 'warning' ? (
              <AlertCircle className="w-6 h-6 text-amber-400" />
            ) : variant === 'info' ? (
              <AlertCircle className="w-6 h-6 text-blue-400" />
            ) : (
              <XCircle className="w-6 h-6 text-red-400" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
            <p className="text-slate-400 text-sm">{message}</p>
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="mt-4 gap-2"
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
  icon: Icon,
  title = '暂无数据',
  message = '当前没有数据可显示',
  action,
  actionLabel,
  className,
}) {
  return (
    <Card className={className}>
      <CardContent className="p-12 text-center">
        {Icon && (
          <div className="flex justify-center mb-4">
            <Icon className="w-16 h-16 text-slate-500" />
          </div>
        )}
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-slate-400 mb-4">{message}</p>
        {action && actionLabel && (
          <Button onClick={action} variant="outline">
            {actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}



