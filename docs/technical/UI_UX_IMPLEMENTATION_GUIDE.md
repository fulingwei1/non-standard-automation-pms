# 🚀 UI/UX 实施指南

> 本文档提供具体的实施步骤和代码示例

---

## Step 1: 技术栈升级

### 1.1 安装依赖

```bash
cd frontend

# Tailwind CSS 4 + PostCSS
npm install -D tailwindcss@latest postcss autoprefixer
npm install -D @tailwindcss/forms @tailwindcss/typography tailwindcss-animate

# shadcn/ui 依赖
npm install class-variance-authority clsx tailwind-merge
npm install @radix-ui/react-slot @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install @radix-ui/react-select @radix-ui/react-tooltip @radix-ui/react-tabs
npm install @radix-ui/react-checkbox @radix-ui/react-switch @radix-ui/react-progress
npm install @radix-ui/react-avatar @radix-ui/react-scroll-area @radix-ui/react-separator

# 状态管理 & 表单
npm install zustand react-hook-form @hookform/resolvers zod

# 日期处理
npm install date-fns

# 图表
npm install recharts
```

### 1.2 配置 Tailwind

**postcss.config.js:**
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**tailwind.config.js:** (见主方案文档的完整配置)

### 1.3 更新 CSS 入口

**src/index.css:**
```css
@import url('https://rsms.me/inter/inter.css');

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ========================================
   全局样式变量
   ======================================== */
:root {
  /* 颜色系统 - 深色主题 */
  --background: 0 0% 1.5%;
  --foreground: 210 40% 98%;
  
  --card: 0 0% 5%;
  --card-foreground: 210 40% 98%;
  
  --popover: 0 0% 5%;
  --popover-foreground: 210 40% 98%;
  
  --primary: 262.1 83.3% 57.8%;
  --primary-foreground: 210 40% 98%;
  
  --secondary: 217.2 91.2% 59.8%;
  --secondary-foreground: 210 40% 98%;
  
  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;
  
  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;
  
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  
  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 262.1 83.3% 57.8%;
  
  --radius: 0.75rem;
  
  /* 自定义变量 */
  --surface-0: #030304;
  --surface-50: #09090b;
  --surface-100: #121215;
  --surface-200: #18181b;
  --surface-300: #27272a;
  
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-tertiary: #64748b;
  
  --violet-glow: rgba(139, 92, 246, 0.3);
  --indigo-glow: rgba(99, 102, 241, 0.3);
}

/* ========================================
   基础重置
   ======================================== */
* {
  @apply border-border;
}

html {
  @apply scroll-smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  @apply bg-[var(--surface-0)] text-[var(--text-primary)];
  font-family: 'Inter var', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
}

/* ========================================
   自定义工具类
   ======================================== */
@layer utilities {
  /* 文字渐变 */
  .text-gradient {
    @apply bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent;
  }
  
  .text-gradient-primary {
    @apply bg-gradient-to-r from-violet-400 to-indigo-400 bg-clip-text text-transparent;
  }
  
  /* 玻璃态效果 */
  .glass {
    @apply bg-white/[0.03] backdrop-blur-xl border border-white/10;
  }
  
  .glass-subtle {
    @apply bg-white/[0.02] backdrop-blur-md border border-white/5;
  }
  
  /* 辉光效果 */
  .glow-sm {
    box-shadow: 0 0 15px -3px var(--violet-glow);
  }
  
  .glow {
    box-shadow: 0 0 25px -5px var(--violet-glow);
  }
  
  .glow-lg {
    box-shadow: 0 0 50px -12px var(--violet-glow);
  }
  
  /* 自定义滚动条 */
  .custom-scrollbar {
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
  }
  
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }
  
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  
  /* 安全区域 */
  .safe-area-pb {
    padding-bottom: env(safe-area-inset-bottom);
  }
  
  .safe-area-pt {
    padding-top: env(safe-area-inset-top);
  }
}

/* ========================================
   动画
   ======================================== */
@layer utilities {
  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }
  
  .animate-shimmer {
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.05) 50%,
      transparent 100%
    );
    background-size: 200% 100%;
    animation: shimmer 2s infinite;
  }
}
```

---

## Step 2: 创建工具函数

**src/lib/utils.js:**
```javascript
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * 合并 Tailwind 类名，处理冲突
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/**
 * 格式化日期
 */
export function formatDate(date, format = 'yyyy-MM-dd') {
  // 使用 date-fns 或自定义实现
  return new Date(date).toLocaleDateString('zh-CN')
}

/**
 * 格式化货币
 */
export function formatCurrency(amount, currency = 'CNY') {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount)
}

/**
 * 格式化数字（千分位）
 */
export function formatNumber(num) {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * 生成唯一 ID
 */
export function generateId() {
  return Math.random().toString(36).substring(2, 9)
}
```

---

## Step 3: 创建基础组件

### 3.1 Button 组件

**src/components/ui/button.jsx:**
```jsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

const buttonVariants = cva(
  // 基础样式
  [
    "inline-flex items-center justify-center gap-2",
    "text-sm font-medium whitespace-nowrap",
    "rounded-xl transition-all duration-200",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500/50",
    "disabled:pointer-events-none disabled:opacity-50",
  ],
  {
    variants: {
      variant: {
        default: [
          "bg-gradient-to-r from-violet-600 to-indigo-600",
          "text-white",
          "shadow-lg shadow-violet-500/25",
          "hover:shadow-violet-500/40 hover:scale-[1.02]",
          "active:scale-[0.98]",
        ],
        secondary: [
          "bg-white/[0.05]",
          "text-white",
          "border border-white/10",
          "hover:bg-white/[0.08] hover:border-white/20",
        ],
        outline: [
          "border border-white/20",
          "text-white",
          "hover:bg-white/[0.05] hover:border-violet-500/50",
        ],
        ghost: [
          "text-slate-400",
          "hover:text-white hover:bg-white/[0.05]",
        ],
        destructive: [
          "bg-red-500/10",
          "text-red-400",
          "border border-red-500/20",
          "hover:bg-red-500/20",
        ],
        link: [
          "text-violet-400 underline-offset-4",
          "hover:underline",
        ],
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-lg",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
        "icon-lg": "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

// 带动画的按钮
const AnimatedButton = React.forwardRef(
  ({ className, ...props }, ref) => (
    <motion.div
      whileTap={{ scale: 0.97 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      <Button ref={ref} className={className} {...props} />
    </motion.div>
  )
)
AnimatedButton.displayName = "AnimatedButton"

export { Button, AnimatedButton, buttonVariants }
```

### 3.2 Input 组件

**src/components/ui/input.jsx:**
```jsx
import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef(
  ({ className, type, icon: Icon, error, ...props }, ref) => {
    return (
      <div className="relative">
        {Icon && (
          <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none">
            <Icon className="h-4.5 w-4.5" />
          </div>
        )}
        <input
          type={type}
          className={cn(
            // 基础样式
            "flex w-full h-11 rounded-xl text-sm",
            "bg-white/[0.03] border border-white/10",
            "text-white placeholder:text-slate-500",
            "transition-all duration-200",
            // 内边距
            Icon ? "pl-10 pr-4" : "px-4",
            // Focus 状态
            "focus:outline-none focus:border-violet-500/50",
            "focus:ring-2 focus:ring-violet-500/20",
            "focus:bg-white/[0.05]",
            // Hover 状态
            "hover:border-white/20 hover:bg-white/[0.04]",
            // 错误状态
            error && "border-red-500/50 focus:border-red-500 focus:ring-red-500/20",
            // Disabled 状态
            "disabled:opacity-50 disabled:cursor-not-allowed",
            className
          )}
          ref={ref}
          {...props}
        />
        {/* 聚焦辉光效果 */}
        <div className="absolute inset-0 rounded-xl pointer-events-none opacity-0 focus-within:opacity-100 transition-opacity">
          <div className="absolute inset-0 rounded-xl shadow-[0_0_20px_rgba(139,92,246,0.15)]" />
        </div>
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
```

### 3.3 Card 组件

**src/components/ui/card.jsx:**
```jsx
import * as React from "react"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

const Card = React.forwardRef(({ className, hover = true, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-2xl",
      "bg-gradient-to-br from-white/[0.05] to-white/[0.02]",
      "border border-white/10",
      hover && [
        "transition-all duration-300",
        "hover:border-white/20",
        "hover:shadow-lg hover:shadow-violet-500/10",
      ],
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

// 带动画的卡片
const AnimatedCard = React.forwardRef(({ className, ...props }, ref) => (
  <motion.div
    ref={ref}
    whileHover={{ y: -4, scale: 1.01 }}
    whileTap={{ scale: 0.99 }}
    transition={{ type: "spring", stiffness: 400, damping: 25 }}
  >
    <Card className={className} {...props} />
  </motion.div>
))
AnimatedCard.displayName = "AnimatedCard"

const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-5 pb-0", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("text-lg font-semibold leading-none tracking-tight", className)}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-slate-400", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-5", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-5 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, AnimatedCard, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
```

### 3.4 Badge 组件

**src/components/ui/badge.jsx:**
```jsx
import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-violet-500/15 text-violet-400 border border-violet-500/30",
        secondary: "bg-white/5 text-slate-400 border border-white/10",
        success: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30",
        warning: "bg-amber-500/15 text-amber-400 border border-amber-500/30",
        danger: "bg-red-500/15 text-red-400 border border-red-500/30",
        info: "bg-blue-500/15 text-blue-400 border border-blue-500/30",
        outline: "bg-transparent text-slate-400 border border-white/20",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
```

### 3.5 Skeleton 组件

**src/components/ui/skeleton.jsx:**
```jsx
import { cn } from "@/lib/utils"

function Skeleton({ className, ...props }) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg bg-white/[0.06]",
        "after:absolute after:inset-0",
        "after:bg-gradient-to-r after:from-transparent after:via-white/10 after:to-transparent",
        "after:animate-shimmer",
        className
      )}
      {...props}
    />
  )
}

// 预设骨架
function SkeletonText({ lines = 1, className }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array(lines).fill(null).map((_, i) => (
        <Skeleton 
          key={i} 
          className={cn(
            "h-4",
            i === lines - 1 && lines > 1 ? "w-3/4" : "w-full"
          )} 
        />
      ))}
    </div>
  )
}

function SkeletonAvatar({ className }) {
  return <Skeleton className={cn("h-10 w-10 rounded-full", className)} />
}

function SkeletonCard({ className }) {
  return (
    <div className={cn("rounded-2xl border border-white/10 bg-white/[0.02] p-5 space-y-4", className)}>
      <div className="flex items-center gap-3">
        <SkeletonAvatar className="h-10 w-10" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-2 w-full rounded-full" />
        <div className="flex justify-between">
          <Skeleton className="h-3 w-12" />
          <Skeleton className="h-3 w-8" />
        </div>
      </div>
    </div>
  )
}

export { Skeleton, SkeletonText, SkeletonAvatar, SkeletonCard }
```

### 3.6 Progress 组件

**src/components/ui/progress.jsx:**
```jsx
import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cn } from "@/lib/utils"

const Progress = React.forwardRef(({ className, value, showValue = false, ...props }, ref) => (
  <div className="relative">
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full",
        "bg-white/[0.05]",
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          "h-full rounded-full transition-all duration-500 ease-out",
          "bg-gradient-to-r from-violet-500 to-indigo-500"
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
))
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
```

---

## Step 4: 创建布局组件

### 4.1 Sidebar 组件

**src/components/layout/sidebar.jsx:**
```jsx
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Briefcase,
  Box,
  ShoppingCart,
  AlertTriangle,
  FileText,
  Users,
  Settings,
  LogOut,
  ChevronLeft,
} from 'lucide-react'

const navGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: LayoutDashboard },
    ]
  },
  {
    label: '项目管理',
    items: [
      { name: '项目列表', path: '/projects', icon: Briefcase },
      { name: '设备管理', path: '/machines', icon: Box },
    ]
  },
  {
    label: '运营管理',
    items: [
      { name: '采购管理', path: '/purchases', icon: ShoppingCart },
      { name: '预警中心', path: '/alerts', icon: AlertTriangle, badge: '3' },
    ]
  },
  {
    label: '系统',
    items: [
      { name: '文档中心', path: '/docs', icon: FileText },
      { name: '组织架构', path: '/org', icon: Users },
      { name: '系统设置', path: '/settings', icon: Settings },
    ]
  },
]

export function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen z-40",
        "flex flex-col",
        "bg-surface-50/80 backdrop-blur-xl",
        "border-r border-white/5",
        "transition-all duration-300 ease-out",
        collapsed ? "w-[72px]" : "w-60"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "flex items-center h-16 px-4",
        "border-b border-white/5"
      )}>
        <div className={cn(
          "flex items-center justify-center",
          "w-10 h-10 rounded-xl",
          "bg-gradient-to-br from-violet-600 to-indigo-600",
          "shadow-lg shadow-violet-500/30"
        )}>
          <Box className="h-5 w-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="ml-3 text-lg font-semibold text-white whitespace-nowrap overflow-hidden"
            >
              PMS 系统
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto custom-scrollbar py-4 px-3">
        {navGroups.map((group, gi) => (
          <div key={gi} className="mb-6">
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-3 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wider"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "relative flex items-center gap-3 px-3 py-2.5 rounded-xl",
                      "text-sm font-medium transition-all duration-200",
                      "group",
                      isActive
                        ? "text-white bg-white/[0.08]"
                        : "text-slate-400 hover:text-white hover:bg-white/[0.04]",
                      collapsed && "justify-center"
                    )}
                  >
                    {/* 激活指示器 */}
                    {isActive && (
                      <motion.div
                        layoutId="activeNav"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-full bg-violet-500"
                        transition={{ type: "spring", duration: 0.5 }}
                      />
                    )}
                    
                    <item.icon className={cn(
                      "h-5 w-5 flex-shrink-0",
                      isActive ? "text-violet-400" : "text-slate-500 group-hover:text-slate-300"
                    )} />
                    
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          className="whitespace-nowrap overflow-hidden"
                        >
                          {item.name}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    
                    {/* 徽章 */}
                    {item.badge && !collapsed && (
                      <span className="ml-auto px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">
                        {item.badge}
                      </span>
                    )}
                    
                    {/* Tooltip for collapsed state */}
                    {collapsed && (
                      <div className={cn(
                        "absolute left-full ml-2 px-3 py-1.5 rounded-lg",
                        "bg-surface-200 text-white text-sm whitespace-nowrap",
                        "opacity-0 invisible group-hover:opacity-100 group-hover:visible",
                        "transition-all duration-200 z-50"
                      )}>
                        {item.name}
                        <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-surface-200 rotate-45" />
                      </div>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-white/5">
        <button
          onClick={onToggle}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl",
            "text-sm font-medium text-slate-400",
            "hover:text-white hover:bg-white/[0.04]",
            "transition-all duration-200",
            collapsed && "justify-center"
          )}
        >
          <ChevronLeft className={cn(
            "h-5 w-5 transition-transform duration-300",
            collapsed && "rotate-180"
          )} />
          {!collapsed && <span>收起侧边栏</span>}
        </button>
      </div>
    </aside>
  )
}
```

### 4.2 Header 组件

**src/components/layout/header.jsx:**
```jsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import {
  Search,
  Bell,
  ChevronDown,
  Settings,
  User,
  LogOut,
  Command,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export function Header({ sidebarCollapsed }) {
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header
      className={cn(
        "fixed top-0 right-0 z-30",
        "h-16 flex items-center justify-between px-6",
        "bg-surface-0/80 backdrop-blur-xl",
        "border-b border-white/5",
        "transition-all duration-300",
        sidebarCollapsed ? "left-[72px]" : "left-60"
      )}
    >
      {/* Search */}
      <button
        onClick={() => setSearchOpen(true)}
        className={cn(
          "flex items-center gap-3 px-4 py-2 rounded-xl",
          "bg-white/[0.03] border border-white/10",
          "text-sm text-slate-400",
          "hover:bg-white/[0.05] hover:border-white/15",
          "transition-all duration-200",
          "min-w-[280px]"
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
        <button className={cn(
          "relative p-2.5 rounded-xl",
          "text-slate-400 hover:text-white",
          "hover:bg-white/[0.05]",
          "transition-colors duration-200"
        )}>
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500" />
        </button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className={cn(
              "flex items-center gap-3 pl-3 pr-2 py-1.5 rounded-xl",
              "hover:bg-white/[0.05]",
              "transition-colors duration-200"
            )}>
              <Avatar className="h-8 w-8">
                <AvatarImage src="/avatar.jpg" />
                <AvatarFallback className="bg-violet-600 text-white text-sm">
                  管
                </AvatarFallback>
              </Avatar>
              <div className="text-left">
                <p className="text-sm font-medium text-white">管理员</p>
                <p className="text-xs text-slate-500">admin@jinkabo.com</p>
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
            <DropdownMenuItem className="text-red-400">
              <LogOut className="h-4 w-4 mr-2" />
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
```

---

## Step 5: 创建动画预设

**src/lib/animations.js:**
```javascript
// Framer Motion 动画预设
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 }
}

export const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
}

export const slideDown = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
}

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  transition: { type: "spring", duration: 0.4, bounce: 0.2 }
}

export const modalAnimation = {
  overlay: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 }
  },
  content: {
    initial: { opacity: 0, scale: 0.95, y: 20 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.95, y: 20 },
    transition: { type: "spring", duration: 0.5, bounce: 0.3 }
  }
}

// 列表项动画 (需要配合 stagger)
export const listItem = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
  transition: { type: "spring", stiffness: 300, damping: 30 }
}

// Stagger 容器
export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
}

// Hover/Tap 效果
export const hoverScale = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 },
  transition: { type: "spring", stiffness: 400, damping: 25 }
}

export const hoverLift = {
  whileHover: { y: -4 },
  transition: { type: "spring", stiffness: 300, damping: 20 }
}

// 页面切换
export const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
}
```

---

## Step 6: 项目文件结构

升级后的推荐文件结构：

```
frontend/
├── public/
│   └── fonts/              # 自定义字体
├── src/
│   ├── components/
│   │   ├── ui/             # 基础 UI 组件
│   │   │   ├── button.jsx
│   │   │   ├── input.jsx
│   │   │   ├── card.jsx
│   │   │   ├── badge.jsx
│   │   │   ├── skeleton.jsx
│   │   │   ├── progress.jsx
│   │   │   ├── avatar.jsx
│   │   │   ├── dropdown-menu.jsx
│   │   │   ├── dialog.jsx
│   │   │   ├── tabs.jsx
│   │   │   ├── tooltip.jsx
│   │   │   ├── scroll-area.jsx
│   │   │   └── index.js    # 统一导出
│   │   ├── layout/         # 布局组件
│   │   │   ├── sidebar.jsx
│   │   │   ├── header.jsx
│   │   │   ├── mobile-nav.jsx
│   │   │   └── page-header.jsx
│   │   ├── data-display/   # 数据展示组件
│   │   │   ├── data-table.jsx
│   │   │   ├── stat-card.jsx
│   │   │   ├── project-card.jsx
│   │   │   └── empty-state.jsx
│   │   └── forms/          # 表单组件
│   │       ├── project-form.jsx
│   │       ├── machine-form.jsx
│   │       └── search-input.jsx
│   ├── pages/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   ├── machines/
│   │   └── auth/
│   ├── hooks/              # 自定义 Hooks
│   │   ├── use-media-query.js
│   │   ├── use-debounce.js
│   │   └── use-local-storage.js
│   ├── lib/
│   │   ├── utils.js        # 工具函数
│   │   └── animations.js   # 动画预设
│   ├── services/
│   │   └── api.js
│   ├── store/              # Zustand 状态
│   │   ├── use-auth.js
│   │   └── use-sidebar.js
│   ├── styles/
│   │   └── globals.css
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── package.json
├── tailwind.config.js
├── postcss.config.js
└── vite.config.js
```

---

## 下一步行动

1. **立即开始**：按照 Step 1 安装依赖
2. **创建组件**：按照 Step 2-4 创建基础组件
3. **迁移页面**：逐个页面使用新组件重构
4. **添加动画**：使用 Step 5 的动画预设
5. **响应式适配**：确保每个组件都有移动端样式

---

> 💡 **提示**：建议按优先级分批实施，先完成核心页面（登录、项目列表），
> 再逐步扩展到其他页面。

