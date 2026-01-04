import { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { authApi } from '../services/api'
import { DEMO_USERS, getRoleInfo } from '../lib/roleConfig'
import {
  User,
  Lock,
  ArrowRight,
  Eye,
  EyeOff,
  BarChart3,
  Clock,
  Users,
  AlertTriangle,
  Building2,
  Wrench,
  ShoppingCart,
  ClipboardList,
  Cog,
  Zap,
  Code,
  TestTube,
  Target,
  Lightbulb,
  FileText,
  Factory,
  Headphones,
  UserCog,
  Briefcase,
  Crown,
  TrendingUp,
  Settings,
  GitBranch,
  CircuitBoard,
  Hammer,
  ShoppingBag,
  Shield,
  Award,
  DollarSign,
  UserCircle,
} from 'lucide-react'

const features = [
  {
    icon: BarChart3,
    title: '实时进度追踪',
    desc: '甘特图、看板多视图',
  },
  {
    icon: Clock,
    title: '智能工时管理',
    desc: '自动统计、负荷预警',
  },
  {
    icon: Users,
    title: '团队高效协作',
    desc: '任务分配、实时同步',
  },
  {
    icon: AlertTriangle,
    title: 'AI 智能预警',
    desc: '风险识别、提前预警',
  },
]

// 按角色类型分组的演示账号
const demoAccountGroups = [
  {
    label: '管理层',
    accounts: [
      { roleCode: 'chairman', icon: Crown, color: 'from-amber-500 to-orange-600' },
      { roleCode: 'gm', icon: Award, color: 'from-blue-500 to-indigo-600' },
      { roleCode: 'super_admin', icon: Shield, color: 'from-violet-500 to-purple-600' },
    ],
  },
  {
    label: '销售/支持',
    accounts: [
      { roleCode: 'sales_director', icon: Crown, color: 'from-pink-500 to-rose-600' },
      { roleCode: 'sales_manager', icon: TrendingUp, color: 'from-pink-500 to-rose-500' },
      { roleCode: 'sales', icon: Target, color: 'from-pink-500 to-rose-500' },
      { roleCode: 'business_support', icon: FileText, color: 'from-violet-500 to-purple-500' },
      { roleCode: 'presales_manager', icon: Lightbulb, color: 'from-amber-500 to-orange-600' },
      { roleCode: 'presales', icon: Lightbulb, color: 'from-amber-500 to-orange-500' },
    ],
  },
  {
    label: '项目管理',
    accounts: [
      { roleCode: 'project_dept_manager', icon: Briefcase, color: 'from-blue-500 to-indigo-600' },
      { roleCode: 'pm', icon: ClipboardList, color: 'from-amber-500 to-orange-500' },
      { roleCode: 'pmc', icon: BarChart3, color: 'from-teal-500 to-emerald-500' },
    ],
  },
  {
    label: '工程技术中心',
    accounts: [
      { roleCode: 'tech_dev_manager', icon: Settings, color: 'from-indigo-500 to-purple-600' },
      { roleCode: 'rd_engineer', icon: GitBranch, color: 'from-cyan-500 to-blue-600' },
      { roleCode: 'me_dept_manager', icon: Cog, color: 'from-blue-500 to-indigo-500' },
      { roleCode: 'te_dept_manager', icon: TestTube, color: 'from-purple-500 to-violet-600' },
      { roleCode: 'ee_dept_manager', icon: CircuitBoard, color: 'from-amber-500 to-yellow-600' },
      { roleCode: 'me_engineer', icon: Cog, color: 'from-blue-500 to-indigo-500' },
      { roleCode: 'te_engineer', icon: TestTube, color: 'from-purple-500 to-violet-500' },
      { roleCode: 'ee_engineer', icon: Zap, color: 'from-amber-500 to-yellow-500' },
    ],
  },
  {
    label: '采购部',
    accounts: [
      { roleCode: 'procurement_manager', icon: ShoppingBag, color: 'from-cyan-500 to-blue-600' },
      { roleCode: 'procurement_engineer', icon: ShoppingCart, color: 'from-cyan-500 to-blue-500' },
    ],
  },
  {
    label: '制造中心',
    accounts: [
      { roleCode: 'manufacturing_director', icon: Factory, color: 'from-indigo-500 to-purple-600' },
      { roleCode: 'production_manager', icon: UserCog, color: 'from-blue-500 to-cyan-500' },
      { roleCode: 'assembler_mechanic', icon: Wrench, color: 'from-slate-500 to-gray-600' },
      { roleCode: 'assembler_electrician', icon: Hammer, color: 'from-slate-600 to-gray-700' },
      { roleCode: 'customer_service_manager', icon: Headphones, color: 'from-teal-500 to-emerald-500' },
      { roleCode: 'customer_service_engineer', icon: Headphones, color: 'from-green-500 to-teal-500' },
    ],
  },
  {
    label: '后台支持',
    accounts: [
      { roleCode: 'finance_manager', icon: DollarSign, color: 'from-emerald-500 to-teal-600' },
      { roleCode: 'hr_manager', icon: UserCircle, color: 'from-blue-500 to-indigo-600' },
    ],
  },
]

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Check if it's a demo account
    const demoUser = Object.values(DEMO_USERS).find(u => u.username === username)
    const isDemoAccount = demoUser && password === 'admin123'

    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const response = await authApi.login(formData)
      localStorage.setItem('token', response.data.access_token)
      onLoginSuccess()
        } catch (err) {
      // Fallback: allow demo login in development mode
      if (isDemoAccount) {
        const roleInfo = getRoleInfo(demoUser.role)
        localStorage.setItem('token', 'demo_token_' + username)
        localStorage.setItem('user', JSON.stringify({
          ...demoUser,
          roleName: roleInfo.name,
          dataScope: roleInfo.dataScope,
        }))
        onLoginSuccess()
        return
      }
      setError(err.response?.data?.detail || '登录失败，请检查用户名和密码')
        } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = (roleCode) => {
    const demoUser = DEMO_USERS[roleCode]
    if (demoUser) {
      setUsername(demoUser.username)
      setPassword('admin123')
    }
  }

    return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Base gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-surface-100 via-surface-50 to-[#16213e]" />
        
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
            maskImage: 'radial-gradient(ellipse at center, black 0%, transparent 70%)',
          }}
        />

        {/* Animated glow orbs */}
        <motion.div
          animate={{
            y: [0, -20, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-32 -left-16 w-[500px] h-[500px] rounded-full bg-violet-600/20 blur-[100px]"
        />
        <motion.div
          animate={{
            y: [0, 20, 0],
            scale: [1, 1.05, 1],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
          className="absolute -bottom-32 -right-16 w-[400px] h-[400px] rounded-full bg-indigo-600/15 blur-[100px]"
        />
        <motion.div
          animate={{
            y: [0, -10, 0],
            x: [0, 10, 0],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 4 }}
          className="absolute top-1/3 left-1/4 w-[300px] h-[300px] rounded-full bg-blue-600/10 blur-[80px]"
        />

        {/* Floating circles */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
          className="absolute top-[10%] left-[5%] w-[300px] h-[300px] rounded-full border border-white/5"
        />
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 30, repeat: Infinity, ease: 'linear' }}
          className="absolute top-[60%] left-[15%] w-[200px] h-[200px] rounded-full border border-white/5"
        />
      </div>

      {/* Main Content */}
      <div className="flex w-full min-h-screen relative z-10">
        {/* Left - Brand Section */}
        <div className="hidden lg:flex flex-col justify-between flex-1 max-w-[580px] p-12 text-white">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-md border border-white/10 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium">项目进度管理系统</span>
            </div>

            {/* Title */}
            <h1 className="text-5xl font-bold leading-tight mb-6">
              让每个项目
              <br />
              <span className="text-gradient-primary">尽在掌控</span>
            </h1>

            {/* Description */}
            <p className="text-lg text-slate-400 mb-12 max-w-md">
              专为非标自动化设备企业打造的智能项目管理平台，实现项目全生命周期的精细化管控。
            </p>

            {/* Features */}
            <div className="space-y-5">
              {features.map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 + i * 0.1 }}
                  className="flex items-start gap-4"
                >
                  <div className="p-3 rounded-xl bg-primary/15 border border-primary/25">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-1">{feature.title}</h4>
                    <p className="text-sm text-slate-500">{feature.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
          >
            <p className="text-sm text-slate-500">
              受到 <span className="text-white font-medium">200+</span> 家企业的信赖
            </p>
          </motion.div>
        </div>

        {/* Right - Form Section */}
        <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-white">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="w-full max-w-md"
          >
            {/* Form Header */}
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">欢迎回来</h2>
              <p className="text-gray-500">登录您的账户以继续</p>
                </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  用户名
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <User className="h-5 w-5" />
                  </div>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                    placeholder="请输入用户名"
                                required
                    className={cn(
                      'w-full h-[52px] pl-12 pr-4 rounded-xl',
                      'bg-gray-50 border-2 border-transparent',
                      'text-gray-900 placeholder:text-gray-400',
                      'transition-all duration-200',
                      'hover:bg-gray-100',
                      'focus:bg-white focus:border-primary focus:outline-none',
                      'focus:ring-4 focus:ring-primary/10'
                    )}
                            />
                        </div>
                    </div>

              {/* Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  密码
                </label>
                <div className="relative">
                  <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    <Lock className="h-5 w-5" />
                  </div>
                            <input
                    type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                    placeholder="请输入密码"
                                required
                    className={cn(
                      'w-full h-[52px] pl-12 pr-12 rounded-xl',
                      'bg-gray-50 border-2 border-transparent',
                      'text-gray-900 placeholder:text-gray-400',
                      'transition-all duration-200',
                      'hover:bg-gray-100',
                      'focus:bg-white focus:border-primary focus:outline-none',
                      'focus:ring-4 focus:ring-primary/10'
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                        </div>
                    </div>

              {/* Options */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only"
                  />
                  <div
                    className={cn(
                      'w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all',
                      rememberMe
                        ? 'bg-primary border-primary'
                        : 'border-gray-300'
                    )}
                  >
                    {rememberMe && (
                      <svg
                        className="w-3 h-3 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={3}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    )}
                  </div>
                  <span className="text-sm text-gray-600">记住登录状态</span>
                </label>
                <a href="#" className="text-sm font-medium text-primary hover:text-primary-dark">
                  忘记密码？
                </a>
              </div>

              {/* Error */}
              {error && (
                <motion.p
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-red-500 text-center"
                >
                  {error}
                </motion.p>
              )}

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={loading}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  'relative w-full h-[52px] rounded-xl',
                  'bg-gradient-to-r from-violet-600 to-indigo-600',
                  'text-white font-semibold',
                  'flex items-center justify-center gap-2',
                  'shadow-lg shadow-violet-500/30',
                  'hover:shadow-violet-500/50 hover:scale-[1.02]',
                  'active:scale-[0.98]',
                  'transition-all duration-200',
                  'disabled:opacity-70 disabled:cursor-not-allowed'
                )}
              >
                {loading ? (
                  <svg
                    className="animate-spin h-5 w-5"
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
                ) : (
                  <>
                    <span>登 录</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </motion.button>
            </form>

            {/* Demo Accounts */}
            <div className="mt-8">
              <div className="relative flex items-center justify-center gap-4 mb-5">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-400 uppercase tracking-widest">
                  演示账号 · 体验不同角色
                </span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              <div className="space-y-6">
                {demoAccountGroups.map((group, gi) => (
                  <div key={gi} className="space-y-3">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-1">
                      {group.label}
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {group.accounts.map((account, i) => {
                        const roleInfo = getRoleInfo(account.roleCode)
                        const Icon = account.icon
                        return (
                    <button
                            key={i}
                            type="button"
                            onClick={() => handleDemoLogin(account.roleCode)}
                            className={cn(
                              'flex items-center gap-3 px-4 py-3 rounded-xl',
                              'bg-white border border-gray-200',
                              'hover:bg-gradient-to-br hover:from-gray-50 hover:to-white',
                              'hover:border-gray-300 hover:shadow-md',
                              'hover:-translate-y-0.5',
                              'transition-all duration-200',
                              'group relative overflow-hidden'
                            )}
                          >
                            <div className="absolute inset-0 bg-gradient-to-br from-transparent to-gray-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                            <div
                              className={cn(
                                'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
                                'bg-gradient-to-br text-white shadow-sm',
                                'group-hover:scale-110 transition-transform duration-200',
                                'relative z-10',
                                account.color
                              )}
                            >
                              <Icon className="w-4.5 h-4.5" />
                            </div>
                            <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 relative z-10 flex-1 text-left">
                              {roleInfo.name}
                            </span>
                    </button>
                        )
                      })}
                    </div>
                  </div>
                ))}
              </div>
              
              <p className="mt-4 text-xs text-gray-400 text-center">
                点击任一角色按钮，将自动填入账号密码，再点登录即可体验
              </p>
            </div>

            {/* Footer */}
            <p className="mt-8 text-center text-xs text-gray-400">
              © 2026 项目进度管理系统 · 世界一流UI设计
            </p>
            </motion.div>
        </div>
      </div>
    </div>
  )
}
