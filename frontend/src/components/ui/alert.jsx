/**
 * Alert Component - 警告/提示组件
 * Based on shadcn/ui pattern
 */

import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'
import * as React from 'react'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'
import { AlertCircle, CheckCircle2, Info, AlertTriangle, XCircle } from 'lucide-react'

const alertVariants = cva(
  'relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground',
  {
    variants: {
      variant: {
        default: 'bg-background text-foreground',
        destructive:
          'border-red-500/50 text-red-600 dark:border-red-500 [&>svg]:text-red-600 bg-red-50 dark:bg-red-950/50',
        warning:
          'border-amber-500/50 text-amber-600 dark:border-amber-500 [&>svg]:text-amber-600 bg-amber-50 dark:bg-amber-950/50',
        success:
          'border-green-500/50 text-green-600 dark:border-green-500 [&>svg]:text-green-600 bg-green-50 dark:bg-green-950/50',
        info:
          'border-blue-500/50 text-blue-600 dark:border-blue-500 [&>svg]:text-blue-600 bg-blue-50 dark:bg-blue-950/50',
        default: 'bg-slate-800/50 border-slate-700 text-slate-300',
        destructive: 'border-red-500/50 bg-red-500/10 text-red-400 [&>svg]:text-red-400',
        warning: 'border-amber-500/50 bg-amber-500/10 text-amber-400 [&>svg]:text-amber-400',
        success: 'border-emerald-500/50 bg-emerald-500/10 text-emerald-400 [&>svg]:text-emerald-400',
        info: 'border-blue-500/50 bg-blue-500/10 text-blue-400 [&>svg]:text-blue-400',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const Alert = React.forwardRef(({ className, variant, ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants({ variant }), className)}
    {...props}
  />
))
const iconMap = {
  default: Info,
  destructive: XCircle,
  warning: AlertTriangle,
  success: CheckCircle2,
  info: Info,
}

const Alert = React.forwardRef(({ className, variant = 'default', children, ...props }, ref) => {
  const Icon = iconMap[variant]
  return (
    <div
      ref={ref}
      role="alert"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    >
      <Icon className="h-4 w-4" />
      {children}
    </div>
  )
})
Alert.displayName = 'Alert'

const AlertTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn('mb-1 font-medium leading-none tracking-tight', className)}
    {...props}
  />
))
AlertTitle.displayName = 'AlertTitle'

const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('text-sm [&_p]:leading-relaxed', className)}
    {...props}
  />
))
AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertTitle, AlertDescription, alertVariants }
export { Alert, AlertTitle, AlertDescription }
