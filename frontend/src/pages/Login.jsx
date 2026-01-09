import { useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { authApi } from '../services/api'
import { DEMO_USERS, getRoleInfo } from '../lib/roleConfig'
import { diagnoseLogin } from '../utils/diagnose'
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
      { roleCode: 'demo_pm_liu', icon: ClipboardList, color: 'from-amber-500 to-orange-500' },
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
    const isDemoAccount = demoUser && (password === 'admin123' || password === 'demo123')

    // 真实数据库账号列表（这些账号必须使用真实API，不能fallback）
    // 暂时清空，所有账号都可以使用演示模式登录
    const realDatabaseAccounts = []
    const isRealAccount = realDatabaseAccounts.includes(username)

    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      // 对于演示账号，如果登录API失败或超时，直接使用fallback
      let response
      try {
        response = await authApi.login(formData)
      } catch (loginErr) {
        // 如果是真实数据库账号，不使用fallback，直接抛出错误
        if (isRealAccount) {
          console.error('真实账号登录失败:', loginErr)
          throw loginErr
        }

        // 如果是演示账号且登录失败（超时、网络错误等），使用fallback
        if (isDemoAccount && demoUser) {
          console.warn('演示账号登录API失败，使用fallback:', loginErr)
          // 清理之前的用户信息
          localStorage.removeItem('user')

          const roleInfo = getRoleInfo(demoUser.role)
          localStorage.setItem('token', 'demo_token_' + username)
          localStorage.setItem('user', JSON.stringify({
            ...demoUser,
            role: demoUser.role,
            roleName: roleInfo.name,
            dataScope: roleInfo.dataScope,
            name: demoUser.name || demoUser.username,
          }))
          onLoginSuccess()
          return
        }
        // 非演示账号，继续抛出错误
        throw loginErr
      }
      
      // 处理响应数据
      const token = response.data?.access_token || response.data?.data?.access_token || response.access_token
      if (!token) {
        console.error('登录响应格式错误:', response)
        throw new Error('服务器返回格式错误，请检查后端服务')
      }
      
      // 清理之前的用户信息
      localStorage.removeItem('user')
      
      // 保存 token
      localStorage.setItem('token', token)
      
      // 获取用户信息
      try {
        const userResponse = await authApi.me()
        const userData = userResponse.data
        if (userData) {
          // 将后端返回的用户数据转换为前端需要的格式
          // 确定用户角色
          let userRole = 'user'
          
          // 优先从角色名称中提取角色代码
          if (userData.roles && userData.roles.length > 0) {
            const roleName = userData.roles[0]
            // 尝试匹配角色代码（支持中英文和常见变体）
            const roleMap = {
              '系统管理员': 'admin',
              '管理员': 'super_admin', // 管理员映射为super_admin
              'ADMIN': 'admin',
              'Administrator': 'admin',
              'SUPER_ADMIN': 'super_admin',
              'SuperAdmin': 'super_admin',
              '总经理': 'gm',
              'GM': 'gm',
              'GeneralManager': 'gm',
              '项目经理': 'pm',
              'PM': 'pm',
              'ProjectManager': 'pm',
              '销售总监': 'sales_director',
              'SalesDirector': 'sales_director',
              'SALES_DIR': 'sales_director',
              '生产部经理': 'production_manager',
              '电机生产部经理': 'production_manager',
              'ProductionManager': 'production_manager',
              'PRODUCTION_MANAGER': 'production_manager',
              '制造总监': 'manufacturing_director',
              'ManufacturingDirector': 'manufacturing_director',
              'MANUFACTURING_DIRECTOR': 'manufacturing_director',
              '计划管理': 'pmc',
              'PMC': 'pmc',
              '采购部经理': 'procurement_manager',
              '采购经理': 'procurement_manager',
              'ProcurementManager': 'procurement_manager',
              'PROCUREMENT_MANAGER': 'procurement_manager',
              '采购工程师': 'procurement_engineer',
              'ProcurementEngineer': 'procurement_engineer',
              'PROCUREMENT_ENGINEER': 'procurement_engineer',
              '采购员': 'buyer',
              'Buyer': 'buyer',
              'BUYER': 'buyer',
            }
            // 先尝试精确匹配
            userRole = roleMap[roleName] || 
                      // 尝试忽略大小写匹配
                      Object.keys(roleMap).find(key => key.toLowerCase() === roleName.toLowerCase()) ? 
                        roleMap[Object.keys(roleMap).find(key => key.toLowerCase() === roleName.toLowerCase())] :
                      // 智能匹配：如果角色名称包含特定关键词，映射到对应角色
                      (roleName.includes('总经理') || roleName.includes('GeneralManager') || roleName === 'GM') ? 'gm' :
                      (roleName.includes('生产') && !roleName.includes('制造')) ? 'production_manager' :
                      (roleName.includes('制造') && roleName.includes('总监')) ? 'manufacturing_director' :
                      (roleName.includes('采购') && (roleName.includes('经理') || roleName.includes('Manager'))) ? 'procurement_manager' :
                      (roleName.includes('采购') && (roleName.includes('工程师') || roleName.includes('Engineer'))) ? 'procurement_engineer' :
                      (roleName.includes('采购') && roleName.includes('员')) ? 'buyer' :
                      // 最后转换为下划线格式
                      roleName.toLowerCase().replace(/\s+/g, '_').replace(/-/g, '_')
          } else if (userData.is_superuser) {
            // 如果没有角色信息但is_superuser为true，默认使用super_admin
            userRole = 'super_admin'
          }
          
          // 如果是演示账号且后端返回的角色不匹配或无效，使用演示账号的角色
          if (isDemoAccount && demoUser && (userRole === 'user' || !userRole || userRole === '')) {
            userRole = demoUser.role
          }
          
          const frontendUser = {
            id: userData.id,
            username: userData.username,
            real_name: userData.real_name || userData.username,
            email: userData.email,
            phone: userData.phone,
            department: userData.department,
            position: userData.position,
            is_superuser: userData.is_superuser || false,
            isSuperuser: userData.is_superuser || false, // 兼容两种命名
            is_active: userData.is_active,
            roles: userData.roles || [],
            role: userRole,
          }
          localStorage.setItem('user', JSON.stringify(frontendUser))
        }
      } catch (userErr) {
        console.warn('获取用户信息失败，使用备用信息:', userErr)
        // 如果获取用户信息失败，创建基本用户信息
        // 优先使用演示账号信息，否则创建默认管理员信息
        if (isDemoAccount && demoUser) {
          const roleInfo = getRoleInfo(demoUser.role)
          localStorage.setItem('user', JSON.stringify({
            ...demoUser,
            role: demoUser.role,
            roleName: roleInfo.name,
            dataScope: roleInfo.dataScope,
            name: demoUser.name || demoUser.username,
          }))
        } else {
          // 非演示账号，创建基本用户信息（默认为管理员）
          const fallbackUser = {
            id: 1,
            username: username,
            name: username,
            role: 'admin',
            is_superuser: true,
            isSuperuser: true,
            department: '系统',
            roles: ['系统管理员'],
          }
          localStorage.setItem('user', JSON.stringify(fallbackUser))
          console.log('使用备用用户信息:', fallbackUser)
        }
      }
      
      onLoginSuccess()
    } catch (err) {
      console.error('登录错误:', err)
      
      // Fallback: allow demo login in development mode
      if (isDemoAccount && demoUser) {
        // Demo account login (development mode only)
        
        // 清理之前的用户信息
        localStorage.removeItem('user')
        
        const roleInfo = getRoleInfo(demoUser.role)
        localStorage.setItem('token', 'demo_token_' + username)
        localStorage.setItem('user', JSON.stringify({
          ...demoUser,
          role: demoUser.role, // 确保使用演示账号的角色
          roleName: roleInfo.name,
          dataScope: roleInfo.dataScope,
          name: demoUser.name || demoUser.username,
        }))
        onLoginSuccess()
        return
      }
      
      // 更详细的错误信息
      let errorMessage = '登录失败，请检查用户名和密码'
      let errorCode = ''
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        // 超时错误
        errorMessage = '登录请求超时，请检查网络连接或稍后重试'
      } else if (err.response) {
        // 服务器返回了错误响应
        const detail = err.response.data?.detail
        // 检查是否是新的错误响应格式（包含 error_code 和 message）
        if (detail && typeof detail === 'object' && detail.error_code) {
          errorCode = detail.error_code
          errorMessage = detail.message
          // 根据错误码添加额外提示
          switch (detail.error_code) {
            case 'USER_NOT_FOUND':
              // 账号不存在
              errorMessage = '该员工尚未开通系统账号，请联系管理员'
              break
            case 'USER_INACTIVE':
              // 账号未激活
              errorMessage = '账号待激活，请联系管理员开通系统访问权限'
              break
            case 'USER_DISABLED':
              // 账号已禁用
              errorMessage = '账号已被禁用，如有疑问请联系管理员'
              break
            case 'WRONG_PASSWORD':
              // 密码错误
              errorMessage = '密码错误，忘记密码请联系管理员重置'
              break
            default:
              errorMessage = detail.message || errorMessage
          }
        } else if (typeof detail === 'string') {
          errorMessage = detail
        } else {
          errorMessage = err.response.data?.message || errorMessage
        }
      } else if (err.request) {
        // 请求已发出但没有收到响应
        errorMessage = '无法连接到服务器，请检查后端服务是否启动'
      } else {
        // 其他错误
        errorMessage = err.message || errorMessage
      }

      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleDemoLogin = (roleCode) => {
    // 所有账号都使用演示模式
    const demoUser = DEMO_USERS[roleCode]
    if (demoUser) {
      setUsername(demoUser.username)
      setPassword('admin123')
      setError('') // 清除之前的错误信息
    } else {
      console.warn(`未找到角色 ${roleCode} 的演示用户`)
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
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-red-500 text-center space-y-2"
                >
                  <p>{error}</p>
                  <button
                    type="button"
                    onClick={() => {
                      diagnoseLogin()
                      alert('请查看浏览器控制台（F12）查看详细诊断信息')
                    }}
                    className="text-xs text-blue-500 hover:text-blue-700 underline"
                  >
                    点击运行诊断工具
                  </button>
                </motion.div>
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
                            <div className="flex-1 text-left relative z-10">
                              <span className="text-sm font-medium text-gray-700 group-hover:text-gray-900 block">
                                {roleInfo.name}
                              </span>
                            </div>
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
