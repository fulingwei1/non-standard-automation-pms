import * as React from 'react'
import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn } from '../../lib/utils'
import { getInitials } from '../../lib/utils'

const Avatar = React.forwardRef(({ className, size = 'default', ...props }, ref) => {
  const sizes = {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8',
    default: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
    '2xl': 'h-20 w-20',
  }

  return (
    <AvatarPrimitive.Root
      ref={ref}
      className={cn(
        'relative flex shrink-0 overflow-hidden rounded-full',
        sizes[size],
        className
      )}
      {...props}
    />
  )
})
Avatar.displayName = AvatarPrimitive.Root.displayName

const AvatarImage = React.forwardRef(({ className, ...props }, ref) => (
  <AvatarPrimitive.Image
    ref={ref}
    className={cn('aspect-square h-full w-full', className)}
    {...props}
  />
))
AvatarImage.displayName = AvatarPrimitive.Image.displayName

const AvatarFallback = React.forwardRef(({ className, ...props }, ref) => (
  <AvatarPrimitive.Fallback
    ref={ref}
    className={cn(
      'flex h-full w-full items-center justify-center rounded-full',
      'bg-gradient-to-br from-violet-600 to-indigo-600',
      'text-white text-sm font-medium',
      className
    )}
    {...props}
  />
))
AvatarFallback.displayName = AvatarPrimitive.Fallback.displayName

// Convenience component for user avatars
function UserAvatar({ user, size = 'default', className }) {
  return (
    <Avatar size={size} className={className}>
      {user?.avatar ? (
        <AvatarImage src={user.avatar} alt={user.name} />
      ) : null}
      <AvatarFallback>{getInitials(user?.name || 'U')}</AvatarFallback>
    </Avatar>
  )
}

// Avatar group
function AvatarGroup({ users, max = 3, size = 'default', className }) {
  const displayed = users?.slice(0, max) || []
  const remaining = (users?.length || 0) - max

  return (
    <div className={cn('flex -space-x-2', className)}>
      {displayed.map((user, i) => (
        <UserAvatar
          key={user.id || i}
          user={user}
          size={size}
          className="ring-2 ring-surface-0"
        />
      ))}
      {remaining > 0 && (
        <div
          className={cn(
            'flex items-center justify-center rounded-full',
            'bg-surface-300 text-xs text-slate-400 font-medium',
            'ring-2 ring-surface-0',
            size === 'sm' ? 'h-8 w-8' : 'h-10 w-10'
          )}
        >
          +{remaining}
        </div>
      )}
    </div>
  )
}

export { Avatar, AvatarImage, AvatarFallback, UserAvatar, AvatarGroup }

