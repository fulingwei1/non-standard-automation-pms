import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  // Base styles
  [
    'inline-flex items-center justify-center gap-2',
    'text-sm font-medium whitespace-nowrap',
    'rounded-xl transition-all duration-200',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
    'disabled:pointer-events-none disabled:opacity-50',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-gradient-to-r from-violet-600 to-indigo-600',
          'text-white',
          'shadow-lg shadow-violet-500/25',
          'hover:shadow-violet-500/40 hover:scale-[1.02]',
          'active:scale-[0.98]',
        ],
        secondary: [
          'bg-white/[0.05]',
          'text-white',
          'border border-white/10',
          'hover:bg-white/[0.08] hover:border-white/20',
        ],
        outline: [
          'border border-white/20',
          'text-white',
          'bg-transparent',
          'hover:bg-white/[0.05] hover:border-primary/50',
        ],
        ghost: [
          'text-slate-400',
          'hover:text-white hover:bg-white/[0.05]',
        ],
        destructive: [
          'bg-red-500/10',
          'text-red-400',
          'border border-red-500/20',
          'hover:bg-red-500/20',
        ],
        success: [
          'bg-emerald-500/10',
          'text-emerald-400',
          'border border-emerald-500/20',
          'hover:bg-emerald-500/20',
        ],
        link: [
          'text-primary underline-offset-4',
          'hover:underline',
          'p-0 h-auto',
        ],
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 px-3 text-xs',
        lg: 'h-12 px-6 text-base',
        xl: 'h-14 px-8 text-lg',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, loading = false, children, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button'

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={loading || props.disabled}
        {...props}
      >
        {loading ? (
          <>
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span>加载中...</span>
          </>
        ) : (
          children
        )}
      </Comp>
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }

