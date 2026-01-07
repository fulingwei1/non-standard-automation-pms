import * as React from 'react'
import * as ProgressPrimitive from '@radix-ui/react-progress'
import { cn } from '../../lib/utils'

const Progress = React.forwardRef(
  ({ className, value, showValue = false, size = 'default', color = 'primary', ...props }, ref) => {
    const sizes = {
      sm: 'h-1.5',
      default: 'h-2',
      lg: 'h-3',
    }

    const colors = {
      primary: 'bg-gradient-to-r from-violet-500 to-indigo-500',
      success: 'bg-gradient-to-r from-emerald-500 to-green-500',
      warning: 'bg-gradient-to-r from-amber-500 to-orange-500',
      danger: 'bg-gradient-to-r from-red-500 to-rose-500',
    }

    return (
      <div className="relative w-full">
        <ProgressPrimitive.Root
          ref={ref}
          className={cn(
            'relative w-full overflow-hidden rounded-full',
            'bg-white/[0.05]',
            sizes[size],
            className
          )}
          {...props}
        >
          <ProgressPrimitive.Indicator
            className={cn(
              'h-full rounded-full transition-all duration-500 ease-out',
              colors[color]
            )}
            style={{ width: `${value || 0}%` }}
          />
        </ProgressPrimitive.Root>
        {showValue && (
          <span className="absolute right-0 -top-6 text-xs text-slate-400">
            {value || 0}%
          </span>
        )}
      </div>
    )
  }
)
Progress.displayName = ProgressPrimitive.Root.displayName

// Progress with label
const ProgressWithLabel = React.forwardRef(
  ({ label, value, className, ...props }, ref) => (
    <div className={cn('space-y-2', className)}>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-medium">{value}%</span>
      </div>
      <Progress ref={ref} value={value} {...props} />
    </div>
  )
)
ProgressWithLabel.displayName = 'ProgressWithLabel'

// Circular progress
function CircularProgress({ value = 0, size = 60, strokeWidth = 6, className }) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (value / 100) * circumference

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="url(#progressGradient)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
        />
        {/* Gradient definition */}
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#6366f1" />
          </linearGradient>
        </defs>
      </svg>
      <span className="absolute text-sm font-medium text-white">{value}%</span>
    </div>
  )
}

export { Progress, ProgressWithLabel, CircularProgress }

