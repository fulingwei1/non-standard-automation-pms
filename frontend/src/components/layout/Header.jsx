import { useState } from 'react'
import { cn } from '../../lib/utils'
import {
  Search,
  Bell,
  ChevronDown,
  Settings,
  User,
  LogOut,
  Command,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu'

export function Header({ sidebarCollapsed = false, user, onLogout }) {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30',
        'h-16 flex items-center justify-between px-6',
        'bg-surface-0/80 backdrop-blur-xl',
        'border-b border-white/5',
        'transition-all duration-300',
        sidebarCollapsed ? 'left-[72px]' : 'left-60'
      )}
    >
      {/* Search */}
      <button
        onClick={() => setSearchOpen(true)}
        className={cn(
          'flex items-center gap-3 px-4 py-2 rounded-xl',
          'bg-white/[0.03] border border-white/10',
          'text-sm text-slate-400',
          'hover:bg-white/[0.05] hover:border-white/15',
          'transition-all duration-200',
          'min-w-[280px]'
        )}
      >
        <Search className="h-4 w-4" />
        <span>搜索项目、设备...</span>
        <div className="ml-auto flex items-center gap-1 text-xs text-slate-500">
          <Command className="h-3 w-3" />
          <span>K</span>
        </div>
      </button>

      {/* Actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button
          className={cn(
            'relative p-2.5 rounded-xl',
            'text-slate-400 hover:text-white',
            'hover:bg-white/[0.05]',
            'transition-colors duration-200'
          )}
        >
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
        </button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                'flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-xl',
                'hover:bg-white/[0.05]',
                'transition-colors duration-200'
              )}
            >
              <Avatar className="h-8 w-8">
                {user?.avatar && <AvatarImage src={user.avatar} />}
                <AvatarFallback className="bg-gradient-to-br from-violet-600 to-indigo-600 text-white text-sm">
                  {user?.name?.[0] || '管'}
                </AvatarFallback>
              </Avatar>
              <div className="text-left">
                <p className="text-sm font-medium text-white">
                  {user?.name || '管理员'}
                </p>
                <p className="text-xs text-slate-500">
                  {user?.email || 'admin@example.com'}
                </p>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-500" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuItem>
              <User className="h-4 w-4 mr-2" />
              个人信息
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="h-4 w-4 mr-2" />
              账户设置
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-400" onClick={onLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

export default Header

