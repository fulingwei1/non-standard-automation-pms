import { CheckCircle2, AlertCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

/**
 * 权重验证组件
 */
export const WeightValidation = ({ totalWeight, isValid }) => {
  return (
    <div className={cn(
      'mt-6 p-4 rounded-lg border-2',
      isValid
        ? 'bg-emerald-500/10 border-emerald-500/30'
        : 'bg-red-500/10 border-red-500/30'
    )}>
      <div className="flex items-center gap-3">
        {isValid ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-400" />
        ) : (
          <AlertCircle className="h-5 w-5 text-red-400" />
        )}
        <div className="flex-1">
          <div className="flex items-center gap-4">
            <span className={cn(
              'font-medium',
              isValid ? 'text-emerald-400' : 'text-red-400'
            )}>
              权重总和: {totalWeight}%
            </span>
            {isValid ? (
              <span className="text-emerald-300 text-sm">✓ 配置正确</span>
            ) : (
              <span className="text-red-300 text-sm">✗ 总和必须为100%</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
